import math
from django.conf import settings


class InputError(ValueError):
    pass


def clean_text(value, label, limit, required=True):
    if not isinstance(value, str):
        raise InputError(f'{label} must be text.')
    value = value.strip()
    if required and not value:
        raise InputError(f'{label} is required.')
    if len(value) > limit:
        raise InputError(f'{label} must be {limit} characters or fewer.')
    return value


def clean_point(point, label):
    if not isinstance(point, dict):
        raise InputError(f'{label}: enter a location.')
    result = {'name': clean_text(point.get('name', ''), f'{label} name', 100),
              'address': clean_text(point.get('address', ''), f'{label} address', 300, False),
              'notes': clean_text(point.get('notes', ''), f'{label} notes', 1000, False)}
    for key, limit in [('lat', 90), ('lng', 180)]:
        try:
            raw = point.get(key)
            if isinstance(raw, bool) or raw is None or raw == '':
                raise ValueError
            value = float(raw)
            if not math.isfinite(value) or not -limit <= value <= limit:
                raise ValueError
        except (ValueError, TypeError, OverflowError):
            raise InputError(f'{label}: enter a valid {"latitude (-90 to 90)" if key == "lat" else "longitude (-180 to 180)"}. Search an address, select the map, or enter coordinates.')
        result[key] = value
    return result


def clean_route(data):
    if not isinstance(data, dict):
        raise InputError('Enter a route object.')
    stops = data.get('stops')
    if not isinstance(stops, list) or not 1 <= len(stops) <= settings.MAX_STOPS:
        raise InputError(f'Add between 1 and {settings.MAX_STOPS} delivery stops, plus a starting location.')
    start = clean_point(data.get('start'), 'Starting location')
    stops = [clean_point(p, f'Stop {i+1}') for i, p in enumerate(stops)]
    positions = [(round(p['lat'], 6), round(p['lng'], 6)) for p in [start] + stops]
    if len(set(positions)) != len(positions):
        raise InputError('Two locations have the same coordinates. Combine duplicate deliveries or choose distinct locations.')
    if type(data.get('return_to_start')) is not bool:
        raise InputError('Choose whether to return to the starting location.')
    if data.get('mode') not in ('demo', 'road'):
        raise InputError('Choose road routing or the straight-line demo.')
    return {'start': start, 'stops': stops, 'return_to_start': data['return_to_start'], 'mode': data['mode']}
