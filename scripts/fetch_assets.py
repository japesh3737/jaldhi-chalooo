"""Download pinned browser libraries and credited visual assets for local serving."""
from pathlib import Path
import re
import requests

ROOT = Path(__file__).resolve().parent.parent / 'static'
FILES = {
    'vendor/leaflet.js': 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js',
    'vendor/leaflet.css': 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css',
    'vendor/leaflet-LICENSE': 'https://unpkg.com/leaflet@1.9.4/LICENSE',
    'vendor/images/layers.png': 'https://unpkg.com/leaflet@1.9.4/dist/images/layers.png',
    'vendor/images/layers-2x.png': 'https://unpkg.com/leaflet@1.9.4/dist/images/layers-2x.png',
    'vendor/images/marker-icon.png': 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
    'vendor/images/marker-icon-2x.png': 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
    'vendor/images/marker-shadow.png': 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
    'vendor/lucide.js': 'https://unpkg.com/lucide@0.468.0/dist/umd/lucide.min.js',
    'vendor/lucide-LICENSE': 'https://unpkg.com/lucide@0.468.0/LICENSE',
    'images/india-delivery.jpg': 'https://images.pexels.com/photos/3881112/pexels-photo-3881112.jpeg?auto=compress&cs=tinysrgb&w=1400&q=85',
    'fonts/OFL.txt': 'https://raw.githubusercontent.com/google/fonts/main/ofl/manrope/OFL.txt',
}

def download(url):
    response = requests.get(url, timeout=40)
    response.raise_for_status()
    return response.content

for name, url in FILES.items():
    path = ROOT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(download(url))
    print(f'Saved {name}')
css = download('https://fonts.googleapis.com/css2?family=Manrope:wght@200..800&display=swap').decode()
font_url = re.findall(r'url\((https://[^)]+)\)', css)[-1]
(ROOT / 'fonts/manrope.woff2').write_bytes(download(font_url))
print('Saved Manrope font')
