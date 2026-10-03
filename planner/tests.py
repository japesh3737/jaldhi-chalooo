import csv
import io
import json
import random
from unittest.mock import patch, Mock
import requests
from django.contrib.auth import get_user_model
from django.test import TestCase, SimpleTestCase, Client, override_settings
from .models import SavedRoute
from .providers import OSRMProvider, ProviderError, geocode, provider_get
from .routing import calculate, cost, optimize_order
from .sample import sample_route
from .validation import clean_route, InputError


class RouteAlgorithmTests(SimpleTestCase):
    def test_demo_open_and_round_trip_consistent(self):
        for round_trip in (True, False):
            data = sample_route()
            data['return_to_start'] = round_trip
            result = calculate(clean_route(data))
            self.assertLessEqual(result['optimized']['distance'], result['original']['distance'])
            route = result['optimized']
            self.assertEqual(route['order'][0], 0)
            self.assertEqual(len(route['itinerary']), 4 + int(round_trip))
            self.assertEqual(route['distance'], sum(p['distance'] for p in route['itinerary']))
            self.assertEqual(route['duration'], sum(p['duration'] for p in route['itinerary']))
            self.assertEqual(len(route['geometry']['coordinates']), len(route['itinerary']) + 1)
            self.assertEqual(route['order'][-1] == 0, round_trip)

    def test_directed_matrices_never_worse(self):
        rng = random.Random(42)
        for n in range(2, 15):
            for round_trip in (False, True):
                matrix = [[0 if a == b else rng.randint(1, 1000) for b in range(n)] for a in range(n)]
                order = optimize_order(matrix, round_trip)
                self.assertEqual(sorted(order), list(range(1, n)))
                self.assertLessEqual(cost(order, matrix, round_trip), cost(list(range(1, n)), matrix, round_trip))

    def test_one_stop(self):
        data = sample_route(); data['stops'] = data['stops'][:1]
        self.assertEqual(calculate(clean_route(data))['optimized']['order'], [0, 1, 0])

    def test_recheck_actual_provider_route(self):
        data = clean_route(sample_route()); data['mode'] = 'road'
        from .providers import DemoProvider
        demo = DemoProvider()
        calls = []
        def road(points):
            result = demo.route(points)
            calls.append(1)
            if len(calls) == 2:
                result['distance'] = 1e9
            return result
        with patch.object(OSRMProvider, 'matrix', side_effect=demo.matrix), patch.object(OSRMProvider, 'route', side_effect=road):
            result = calculate(data)
        self.assertEqual(result['original'], result['optimized'])


class ValidationTests(SimpleTestCase):
    def test_invalid_coordinates_and_shape(self):
        for value in ('bad', '', None, True, float('nan'), float('inf'), 91, -91):
            data = sample_route(); data['start']['lat'] = value
            with self.assertRaises(InputError): clean_route(data)
        for data in (None, [], {}, {'stops': 'bad'}):
            with self.assertRaises(InputError): clean_route(data)

    def test_limits_duplicates_settings_names(self):
        variants = []
        data = sample_route(); data['stops'] = []; variants.append(data)
        data = sample_route(); data['stops'] *= 6; variants.append(data)
        data = sample_route(); data['stops'][0] = data['start']; variants.append(data)
        data = sample_route(); data['return_to_start'] = 'false'; variants.append(data)
        data = sample_route(); data['mode'] = 'unknown'; variants.append(data)
        data = sample_route(); data['stops'][0]['name'] = ' '; variants.append(data)
        data = sample_route(); data['stops'][0]['notes'] = 'x' * 1001; variants.append(data)
        for data in variants:
            with self.assertRaises(InputError): clean_route(data)

    def test_coordinate_only_and_extremes(self):
        data = sample_route(); data['start'].update(address='', lat=-90, lng=180)
        self.assertEqual(clean_route(data)['start']['lat'], -90)


@override_settings(PROVIDER_MIN_INTERVAL=0)
class ProviderTests(SimpleTestCase):
    def test_timeout_http_and_invalid_json(self):
        for error in (requests.Timeout(), requests.ConnectionError(), requests.HTTPError(), ValueError()):
            with patch('planner.providers.requests.get', side_effect=error):
                with self.assertRaises(ProviderError): provider_get('https://example.test', {})

    def test_null_matrix_and_bad_geometry(self):
        provider = OSRMProvider(); points = [sample_route()['start'], sample_route()['stops'][0]]
        for matrix in ([[0, None], [5, 0]], [[0]], 'bad'):
            with patch('planner.providers.provider_get', return_value={'code': 'Ok', 'distances': matrix}):
                with self.assertRaises(ProviderError): provider.matrix(points)
        with patch('planner.providers.provider_get', return_value={'code': 'Ok', 'routes': []}):
            with self.assertRaises(ProviderError): provider.route(points)

    def test_osrm_legs_and_geometry(self):
        points = [sample_route()['start'], sample_route()['stops'][0]]
        route = {'legs': [{'distance': 800, 'duration': 100}], 'geometry': {'type': 'LineString', 'coordinates': [[-0.1, 51.5], [-0.12, 51.51]]}}
        with patch('planner.providers.provider_get', return_value={'code': 'Ok', 'routes': [route]}):
            self.assertEqual(OSRMProvider().route(points)['distance'], 800)

    @override_settings(GEOCODER_BASE_URL='')
    def test_sample_search_and_unconfigured_search(self):
        self.assertEqual(len(geocode('Connaught Place')), 1)
        with self.assertRaises(ProviderError): geocode('Unknown address 123')

    @override_settings(GEOCODER_BASE_URL='https://geocoder.example.test')
    def test_geocoder_empty_invalid_and_success(self):
        with patch('planner.providers.provider_get', return_value=[]): self.assertEqual(geocode('Unknown sample 4921'), [])
        with patch('planner.providers.provider_get', return_value=[{'display_name':'Bad','lat':'nan','lon':'0'}]):
            with self.assertRaises(ProviderError): geocode('Invalid sample 4912')
        with patch('planner.providers.provider_get', return_value=[{'display_name':'Example','lat':'51','lon':'-0.1'}]):
            self.assertEqual(geocode('Unique valid 4219')[0]['lat'], 51)


class AppTests(TestCase):
    def post_json(self, url, data, client=None):
        return (client or self.client).post(url, json.dumps(data), content_type='application/json')

    def test_pages_and_registration_login_logout(self):
        for url in ('/', '/planner/', '/planner/?sample=1', '/accounts/login/', '/accounts/register/'):
            self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(self.client.get('/dashboard/').status_code, 302)
        response = self.client.post('/accounts/register/', {'username':'deliverytester','password1':'Example-long-password-472!','password2':'Example-long-password-472!'})
        self.assertRedirects(response, '/dashboard/')
        self.assertEqual(self.client.get('/accounts/logout/').status_code, 405)
        self.assertEqual(self.client.post('/accounts/logout/').status_code, 302)
        self.assertRedirects(self.client.post('/accounts/login/', {'username':'deliverytester','password':'Example-long-password-472!'}), '/dashboard/')

    def test_guest_optimize_csv_session_isolation_and_formula_safety(self):
        data = sample_route(); data['stops'][0]['name'] = '=1+1'
        response = self.post_json('/api/optimize/', data)
        self.assertEqual(response.status_code, 200)
        token = response.json()['result_id']
        export = self.client.get(f'/export/{token}/')
        self.assertEqual(export.status_code, 200)
        rows = list(csv.reader(io.StringIO(export.content.decode('utf-8-sig'))))
        self.assertTrue(any(row[1] == "'=1+1" for row in rows))
        self.assertEqual(rows[-1][0], 'TOTAL')
        self.assertEqual(Client().get(f'/export/{token}/').status_code, 404)

    def test_errors_and_csrf(self):
        self.assertEqual(self.post_json('/api/optimize/', {}).status_code, 400)
        self.assertEqual(self.client.post('/api/optimize/', '{', content_type='application/json').status_code, 400)
        self.assertEqual(self.client.get('/api/optimize/').status_code, 405)
        self.assertEqual(self.post_json('/api/routes/save/', sample_route()).status_code, 401)
        csrf_client = Client(enforce_csrf_checks=True)
        self.assertEqual(self.post_json('/api/optimize/', sample_route(), csrf_client).status_code, 403)
        csrf_client.get('/planner/')
        token = csrf_client.cookies['csrftoken'].value
        self.assertEqual(csrf_client.post('/api/optimize/', json.dumps(sample_route()), content_type='application/json', HTTP_X_CSRFTOKEN=token).status_code, 200)

    def test_road_failure_does_not_fallback(self):
        data = sample_route(); data['mode'] = 'road'
        with patch.object(OSRMProvider, 'matrix', side_effect=ProviderError('Unavailable')):
            response = self.post_json('/api/optimize/', data)
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('optimized', response.json())

    def test_save_reopen_edit_rename_delete_and_owner_permissions(self):
        owner = get_user_model().objects.create_user(username='owner', password='Test-password-712')
        other = get_user_model().objects.create_user(username='other', password='Test-password-813')
        self.client.force_login(owner)
        data = sample_route()
        response = self.post_json('/api/routes/save/', data)
        self.assertEqual(response.status_code, 200)
        pk = response.json()['id']
        self.assertContains(self.client.get(f'/planner/?route={pk}'), 'New Delhi')
        data['id'] = pk; data['stops'].reverse(); data['stops'][0]['notes'] = 'Edited'; data['stops'].pop()
        self.assertEqual(self.post_json('/api/routes/save/', data).status_code, 200)
        saved = SavedRoute.objects.get(pk=pk)
        self.assertEqual(len(saved.data['stops']), 3)
        self.assertEqual(saved.data['stops'][0]['notes'], 'Edited')
        self.client.post(f'/routes/{pk}/rename/', {'name':'Renamed plan'})
        saved.refresh_from_db(); self.assertEqual(saved.name, 'Renamed plan')
        self.client.force_login(other)
        self.assertEqual(self.client.get(f'/planner/?route={pk}').status_code, 404)
        self.assertEqual(self.post_json('/api/routes/save/', data).status_code, 404)
        self.assertEqual(self.client.post(f'/routes/{pk}/rename/', {'name':'Unauthorized'}).status_code, 404)
        self.assertEqual(self.client.post(f'/routes/{pk}/delete/').status_code, 404)
        self.assertNotContains(self.client.get('/dashboard/'), 'Renamed plan')
        self.client.force_login(owner)
        self.assertEqual(self.client.get(f'/routes/{pk}/delete/').status_code, 405)
        self.assertEqual(self.client.post(f'/routes/{pk}/delete/').status_code, 302)
        self.assertFalse(SavedRoute.objects.filter(pk=pk).exists())

    def test_geocode_validation(self):
        self.assertEqual(self.post_json('/api/geocode/', {'query':'x'}).status_code, 400)
        self.assertEqual(self.post_json('/api/geocode/', []).status_code, 400)
        self.assertEqual(len(self.post_json('/api/geocode/', {'query':'Connaught Place'}).json()['results']), 1)

    def test_explicit_new_route_clears_previous_draft_identity(self):
        response = self.client.get('/planner/?new=1')
        self.assertEqual(response.context['initial']['stops'], [])
        self.assertNotIn('id', response.context['initial'])
