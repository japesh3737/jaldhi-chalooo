import csv
import io
import json
import uuid
from functools import wraps
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import RequestDataTooBig
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST, require_GET
from .models import SavedRoute
from .providers import ProviderError, geocode
from .routing import calculate
from .sample import sample_route
from .validation import InputError, clean_route, clean_text


def api_errors(fn):
    @wraps(fn)
    def wrapped(request, *args, **kwargs):
        try:
            return fn(request, *args, **kwargs)
        except (InputError, json.JSONDecodeError, UnicodeDecodeError, RequestDataTooBig) as e:
            return JsonResponse({'error': str(e) if isinstance(e, InputError) else 'Invalid or oversized request.'}, status=400)
        except ProviderError as e:
            return JsonResponse({'error': str(e)}, status=503)
    return wrapped


def body(request):
    return json.loads(request.body)


def home(request):
    sample = sample_route()
    return render(request, 'planner/home.html', {'sample': sample, 'preview': calculate(sample)})


def planner(request):
    initial = None
    route_id = request.GET.get('route')
    if request.GET.get('new') == '1':
        initial = {'name': '', 'start': {'name': 'Starting point', 'address': '', 'lat': '', 'lng': '', 'notes': ''},
                   'stops': [], 'mode': 'demo', 'return_to_start': True}
    elif route_id:
        if not request.user.is_authenticated:
            return redirect('login')
        saved = get_object_or_404(SavedRoute, pk=route_id if route_id.isdigit() else 0, owner=request.user)
        initial = dict(saved.data, name=saved.name, id=saved.pk)
    elif request.GET.get('sample') == '1':
        initial = sample_route()
    return render(request, 'planner/planner.html', {'initial': initial, 'max_stops': settings.MAX_STOPS})


@require_GET
def sample(request):
    return JsonResponse(sample_route())


@require_POST
@api_errors
def optimize(request):
    data = clean_route(body(request))
    result = calculate(data)
    token = uuid.uuid4().hex
    results = request.session.get('route_results', {})
    results[token] = result
    request.session['route_results'] = dict(list(results.items())[-3:])
    return JsonResponse(dict(result, result_id=token))


@require_POST
@api_errors
def address_search(request):
    data = body(request)
    if not isinstance(data, dict):
        raise InputError('Enter an address.')
    query = clean_text(data.get('query', ''), 'Address', 300)
    if len(query) < 3:
        raise InputError('Enter at least 3 characters to search.')
    return JsonResponse({'results': geocode(query)})


@require_POST
@api_errors
def save_route(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Sign in to save routes. Your planner entries stay in this tab.'}, status=401)
    raw = body(request)
    data = clean_route(raw)
    name = clean_text(raw.get('name', ''), 'Route name', 100)
    route_id = raw.get('id')
    if route_id is not None:
        if type(route_id) is not int or route_id < 1:
            raise InputError('Invalid saved route.')
        saved = get_object_or_404(SavedRoute, pk=route_id, owner=request.user)
        saved.name, saved.data = name, data
        saved.save()
    else:
        if request.user.routes.count() >= 100:
            raise InputError('You have reached 100 saved routes. Delete an unused route first.')
        saved = SavedRoute.objects.create(owner=request.user, name=name, data=data)
    return JsonResponse({'id': saved.pk, 'name': saved.name})


def csv_cell(value):
    value = str(value)
    return "'" + value if value.lstrip().startswith(('=', '+', '-', '@', '\t', '\r', '\n')) else value


@require_GET
def export_csv(request, token):
    result = request.session.get('route_results', {}).get(token)
    if result is None:
        return HttpResponse('This result has expired. Optimize the route again to download it.', status=404)
    output = io.StringIO(newline='')
    writer = csv.writer(output)
    writer.writerow(['Order', 'Customer / location', 'Address', 'Latitude', 'Longitude', 'Delivery notes',
                     'Leg distance (km)', 'Estimated travel (min)', 'Calculation'])
    start = result['start']
    writer.writerow([0, csv_cell(start['name']), csv_cell(start['address']), start['lat'], start['lng'], csv_cell(start['notes']), 0, 0, result['label']])
    for i, point in enumerate(result['optimized']['itinerary'], 1):
        writer.writerow([i, csv_cell(point['name']), csv_cell(point['address']), point['lat'], point['lng'],
                         csv_cell(point['notes']), f'{point["distance"]/1000:.3f}', f'{point["duration"]/60:.2f}', result['label']])
    writer.writerow(['TOTAL', '', '', '', '', '', f'{result["optimized"]["distance"]/1000:.3f}', f'{result["optimized"]["duration"]/60:.2f}', result['label']])
    response = HttpResponse('\ufeff' + output.getvalue(), content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="delivery-itinerary.csv"'
    response['Cache-Control'] = 'no-store'
    return response


def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = UserCreationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect('dashboard')
    return render(request, 'registration/register.html', {'form': form})


@login_required
def dashboard(request):
    return render(request, 'planner/dashboard.html', {'routes': request.user.routes.all()})


@login_required
@require_POST
def rename_route(request, pk):
    saved = get_object_or_404(SavedRoute, pk=pk, owner=request.user)
    try:
        saved.name = clean_text(request.POST.get('name', ''), 'Route name', 100)
        saved.save(update_fields=['name', 'updated_at'])
        messages.success(request, 'Route renamed.')
    except InputError as e:
        messages.error(request, str(e))
    return redirect('dashboard')


@login_required
@require_POST
def delete_route(request, pk):
    saved = get_object_or_404(SavedRoute, pk=pk, owner=request.user)
    saved.delete()
    messages.success(request, 'Route deleted.')
    return redirect('dashboard')
