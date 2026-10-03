"""Start a local-network preview for a phone on the same trusted Wi-Fi."""
import argparse
import ipaddress
import os
from pathlib import Path
import socket
import sys
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--host', help='This computer\'s private Wi-Fi IPv4 address; auto-detected when unambiguous.')
parser.add_argument('--port', type=int, default=8001)
parser.add_argument('--check', action='store_true', help='Print the URL without starting the server.')
args = parser.parse_args()
addresses = sorted({entry[4][0] for entry in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)
                    if ipaddress.ip_address(entry[4][0]).is_private
                    and not ipaddress.ip_address(entry[4][0]).is_loopback
                    and not ipaddress.ip_address(entry[4][0]).is_link_local})
if args.host:
    if args.host not in addresses:
        parser.error('--host must be a private IPv4 address assigned to this computer.')
    host = args.host
elif len(addresses) == 1:
    host = addresses[0]
else:
    parser.error(f'Use --host with your Wi-Fi IPv4 address. Detected: {", ".join(addresses) or "none"}.')
if not 1024 <= args.port <= 65535:
    parser.error('Choose a port between 1024 and 65535.')
print(f'Phone URL: http://{host}:{args.port}/', flush=True)
print('Connect the phone to the same trusted Wi-Fi. Keep this computer awake. Ctrl+C stops sharing.', flush=True)
if args.check:
    sys.exit(0)
load_dotenv(ROOT / '.env')
os.environ['DJANGO_ALLOWED_HOSTS'] = ','.join(dict.fromkeys(['localhost', '127.0.0.1', host]))
os.environ['DJANGO_DEBUG'] = 'True'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, str(ROOT))
from django.core.management import execute_from_command_line
execute_from_command_line(['manage.py', 'runserver', f'{host}:{args.port}', '--noreload'])
