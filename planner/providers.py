import math
import threading
import time
from urllib.parse import urlparse
import requests
from django.conf import settings
from django.core.cache import cache
from .sample import sample_route


class ProviderError(Exception):
    pass


_lock = threading.Lock()
_last_request = 0.0


def provider_get(url, params):
    global _last_request
    # Single-process demo limiter. Production must use a shared rate limiter.
    with _lock:
        delay = settings.PROVIDER_MIN_INTERVAL - (time.monotonic() - _last_request)
        if delay > 0:
            time.sleep(delay)
        _last_request = time.monotonic()
        try:
            response = requests.get(url, params=params, headers={'User-Agent': settings.PROVIDER_USER_AGENT},
                                    timeout=(3.05, settings.PROVIDER_TIMEOUT))
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError):
            raise ProviderError('The location provider is unavailable or timed out. Your entries are preserved. Retry, or explicitly choose the straight-line demo.') from None


def haversine(a, b):
    lat1, lat2 = math.radians(a['lat']), math.radians(b['lat'])
    dlat, dlng = lat2 - lat1, math.radians(b['lng'] - a['lng'])
    h = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlng/2)**2
    return 6371000 * 2 * math.asin(min(1, math.sqrt(h)))


class DemoProvider:
    label = 'Straight-line approximation · not for navigation'

    def matrix(self, points):
        return [[haversine(a, b) for b in points] for a in points]

    def route(self, points):
        legs = [{'distance': haversine(a, b), 'duration': haversine(a, b) / (settings.DEMO_SPEED_KMH / 3.6)}
                for a, b in zip(points, points[1:])]
        return {'distance': sum(x['distance'] for x in legs), 'duration': sum(x['duration'] for x in legs),
                'legs': legs, 'geometry': {'type': 'LineString', 'coordinates': [[p['lng'], p['lat']] for p in points]}}


def valid_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0


class OSRMProvider:
    label = 'Road route · OSRM / OpenStreetMap'

    def call(self, service, points, params):
        coords = ';'.join(f'{p["lng"]:.6f},{p["lat"]:.6f}' for p in points)
        data = provider_get(f'{settings.OSRM_BASE_URL}/{service}/v1/driving/{coords}', params)
        if not isinstance(data, dict) or data.get('code') != 'Ok':
            raise ProviderError('No connected road route was found. Check your locations, or explicitly choose the straight-line demo.')
        return data

    def matrix(self, points):
        data = self.call('table', points, {'annotations': 'distance,duration'})
        matrix = data.get('distances')
        if not isinstance(matrix, list) or len(matrix) != len(points) or any(
            not isinstance(row, list) or len(row) != len(points) or any(not valid_number(v) for v in row) for row in matrix
        ):
            raise ProviderError('Some locations cannot be connected by road. Check the coordinates or use the explicit demo mode.')
        return matrix

    def route(self, points):
        data = self.call('route', points, {'overview': 'full', 'geometries': 'geojson', 'steps': 'false', 'continue_straight': 'false'})
        try:
            route = data['routes'][0]
            legs = route['legs']
            coords = route['geometry']['coordinates']
            if len(legs) != len(points) - 1 or len(coords) < 2 or route['geometry']['type'] != 'LineString':
                raise ValueError
            if any(not valid_number(x[k]) for x in legs for k in ('distance', 'duration')):
                raise ValueError
            for pair in coords:
                if len(pair) != 2 or not all(isinstance(v, (int, float)) and math.isfinite(v) for v in pair):
                    raise ValueError
                if not -180 <= pair[0] <= 180 or not -90 <= pair[1] <= 90:
                    raise ValueError
            # Totals and itinerary use the exact same returned legs.
            return {'distance': sum(x['distance'] for x in legs), 'duration': sum(x['duration'] for x in legs),
                    'legs': [{'distance': x['distance'], 'duration': x['duration']} for x in legs], 'geometry': route['geometry']}
        except (KeyError, IndexError, TypeError, ValueError):
            raise ProviderError('The routing provider returned an incomplete route. Retry later; your entries are preserved.') from None


def geocode(query):
    sample = sample_route()
    matches = [{'address': p['address'], 'lat': p['lat'], 'lng': p['lng']} for p in [sample['start']] + sample['stops']
               if query.casefold() in p['address'].casefold()]
    if matches:
        return matches
    if not settings.GEOCODER_BASE_URL:
        raise ProviderError('Live address search is not configured. Try a sample New Delhi landmark, enter coordinates, or select a point on the map.')
    if urlparse(settings.GEOCODER_BASE_URL).hostname == 'nominatim.openstreetmap.org':
        raise ProviderError('Configure a self-hosted or contracted Nominatim-compatible service. The public Nominatim endpoint is not enabled for this app.')
    import hashlib
    key = 'geocode:' + hashlib.sha256(query.casefold().encode()).hexdigest()
    cached = cache.get(key)
    if cached is not None:
        return cached
    data = provider_get(settings.GEOCODER_BASE_URL + '/search', {'q': query, 'format': 'jsonv2', 'limit': 5})
    try:
        if not isinstance(data, list):
            raise ValueError
        result = [{'address': str(p['display_name'])[:300], 'lat': float(p['lat']), 'lng': float(p['lon'])} for p in data[:5]]
        if any(not math.isfinite(p['lat']) or not math.isfinite(p['lng']) or not -90 <= p['lat'] <= 90 or not -180 <= p['lng'] <= 180 for p in result):
            raise ValueError
    except (KeyError, TypeError, ValueError, OverflowError):
        raise ProviderError('Address search returned invalid data. Use coordinates or try again later.') from None
    cache.set(key, result, 86400)
    return result
