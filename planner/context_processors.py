from django.conf import settings


def map_settings(request):
    return {'map_settings': {'url': settings.MAP_TILE_URL, 'attribution': settings.MAP_TILE_ATTRIBUTION}}
