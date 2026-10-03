"""Optional live smoke test: sends only bundled public landmark coordinates."""
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from planner.sample import sample_route
from planner.validation import clean_route
from planner.routing import calculate

data = sample_route()
data['mode'] = 'road'
result = calculate(clean_route(data))
assert result['mode'] == 'road'
assert result['optimized']['distance'] <= result['original']['distance']
assert result['optimized']['distance'] == sum(p['distance'] for p in result['optimized']['itinerary'])
print(f"Road routing verified: {result['original']['distance']/1000:.2f} km original; {result['optimized']['distance']/1000:.2f} km suggested; {len(result['optimized']['geometry']['coordinates'])} geometry points.")
