# Smart Delivery Route Planner

A complete local Django application: a responsive landing page, guest route planner, Python route optimization, Leaflet maps, accounts, and private saved routes. Uses exactly two UI brand colors—navy `#102A43` and teal `#007F78`—with neutral supporting colors. Photography retains natural colors; map tiles are visually desaturated.

The website is localised for India: New Delhi sample locations, Indian street photography, kirana/parcel delivery examples, address hints for shop numbers, landmarks and PIN codes, and saved-route timestamps in IST (`Asia/Kolkata`). The interface remains in English. The sample uses approximate points around public landmarks, not verified delivery entrances or real customer addresses. Coordinates still support locations elsewhere in India; arbitrary address search requires the configured geocoder described below. Existing user-saved routes are preserved.

## Start here (Windows PowerShell)

Requires Python 3.12 or newer with pip. Install Python from https://www.python.org/downloads/ if needed. Node.js is **not** required.

```powershell
cd C:\Users\japesh\Desktop\manju
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -c "from pathlib import Path; import secrets; p=Path('.env'); p.write_text(p.read_text().replace('DJANGO_SECRET_KEY=', 'DJANGO_SECRET_KEY='+secrets.token_urlsafe(64)))"
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Open **http://127.0.0.1:8000/**. Leave the terminal running; press Ctrl+C to stop. On subsequent runs, use only the final command. If `.venv`, `.env`, and the database already exist, keep them—do not overwrite your secret or database. This delivered workspace has already been configured and migrated.

If the `py` launcher is unavailable but `python` works, substitute `python` for `py -3.12`. No activation script or PowerShell execution-policy change is needed.

### macOS / Linux

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
.venv/bin/python -c "from pathlib import Path; import secrets; p=Path('.env'); p.write_text(p.read_text().replace('DJANGO_SECRET_KEY=', 'DJANGO_SECRET_KEY='+secrets.token_urlsafe(64)))"
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver 127.0.0.1:8000
```

## Try the demo

### Open it on a phone

The website adapts to a phone browser. At phone widths, the planner has **Stops** and **Map & route** views, larger input text, touch-sized controls, and a fixed **Find my route** button. Calculating a route opens the map view. All existing desktop features remain available.

To open your computer's copy on a phone, connect both devices to the **same trusted Wi-Fi** and run this in a separate terminal:

```powershell
cd C:\Users\japesh\Desktop\manju
.\.venv\Scripts\python.exe scripts/serve_phone.py
```

Open the **Phone URL** printed by the launcher in Chrome or Safari on the phone. Do not use `localhost` or `127.0.0.1` on the phone: those mean the phone itself. Keep this computer awake and the terminal running. Ctrl+C stops the phone preview. The launcher uses port 8001, binds only to the detected private network address, and temporarily adds that exact address to Django's allowed hosts; it does not change your `.env` or firewall.

If more than one network address is detected, select your Wi-Fi adapter's IPv4 address (shown by `ipconfig`), for example:

```powershell
.\.venv\Scripts\python.exe scripts/serve_phone.py --host 192.168.1.42
```

Use your own address in that command. If Windows asks about network access, allow Python on your trusted **Private** network only. Guest Wi-Fi/client isolation, a VPN, or a firewall may prevent devices from reaching each other. This is a development preview over local HTTP; use sample data, not real customer details or reused passwords. The launcher does not open router ports or publish the site on the internet.

For use away from the same Wi-Fi or while the computer is off, deploy Django to an HTTPS host with a public domain. This website is not an offline standalone phone app: the Python backend must be running, and road maps/providers need internet. Real Android/iPhone device testing remains separate from the browser size checks.

### Load the sample

1. Open **Route Planner**, then **Load sample**, or use http://127.0.0.1:8000/planner/?sample=1.
2. The sample contains four fictional deliveries at public New Delhi landmarks. No real customer information is included.
3. Select **Optimize route**. Demo mode uses straight-line distances and an assumed 25 km/h speed; it needs no paid key or routing network connection.
4. Switch between **Suggested order** and **Original order** to compare the map, totals, and itinerary. Toggle return to start to try an open route.
5. Download **CSV**. CSV always exports the suggested itinerary, including the start, return leg if selected, notes, per-leg values, and total.
6. Register using the **Sign in → Create an account** link. Open the planner, name your route, and save it. Use **My routes** to reopen, rename, or delete it.

The landing-page preview is calculated in Python from the same sample data used by the planner. No fictional business claims, testimonials, ratings, or customer logos are present.

Optional: save the sample directly for an existing registered username:

```powershell
.\.venv\Scripts\python.exe manage.py seed_sample --username YOUR_USERNAME
```

No default account or password is supplied. `seed_sample` never creates credentials.

## Using the planner

- A starting point and **1–20 customer stops** are required. A single stop is valid, though there is no order to improve.
- Every point needs a name and valid coordinates. The address can be blank for coordinate-only points; delivery notes are optional, up to 1,000 characters.
- Add, edit, remove, or reorder stops with the up/down buttons. Stop headings can collapse their fields.
- **Find address** is an explicit search, never autocomplete. Select one of the results and review its map position. In the default demo, only the five bundled New Delhi landmark addresses are searchable.
- **Select on map** activates the picker for that location. Click the map, or use latitude and longitude inputs as the keyboard-accessible alternative. Escape cancels selection.
- Editing an address clears its previous coordinates, so an old geocoded position cannot silently be reused.
- Changes invalidate old results. Optimize again to refresh distances, geometry, and CSV.
- **Reset** clears the local planner draft after confirmation; it does not delete saved routes.
- Form errors and provider failures preserve entries. The draft is saved in this browser tab's `sessionStorage`, across navigation and login. It is not synchronized across devices. Closing the tab or clearing browser data can remove it. Explicit sample/open-saved links replace the draft.
- A signed-in account can save at most 100 routes. Saved routes contain their original stop order and settings, not a promise of permanently unchanged road results. Recalculate after reopening.
- Guest result downloads are session-bound and limited to the three latest calculations; optimize again if a link expires.

## Configuration

Use `.env`; secrets are never committed. `.env.example` lists supported settings.

| Variable | Purpose / default |
|---|---|
| `DJANGO_SECRET_KEY` | Required random secret; no built-in fallback. |
| `DJANGO_DEBUG` | `True` for localhost; code defaults to `False`. |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated allowed hosts, defaults to `localhost,127.0.0.1`. |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated HTTPS origins for deployed use if needed. |
| `DATABASE_URL` | Optional PostgreSQL URL; unset uses `db.sqlite3`. |
| `OSRM_BASE_URL` | OSRM-compatible routing service, default `https://router.project-osrm.org`. |
| `GEOCODER_BASE_URL` | Empty by default; a self-hosted or contracted Nominatim-compatible service, without `/search`. |
| `PROVIDER_USER_AGENT` | Identifying User-Agent. Set a real application/contact identifier when using your service. |
| `PROVIDER_TIMEOUT` | Read timeout in seconds, default 10; connect timeout is 3.05 seconds. |
| `PROVIDER_MIN_INTERVAL` | Minimum gap between external backend requests, default 1.1 seconds. |
| `MAP_TILE_URL` | XYZ raster tile URL, defaults to OpenStreetMap's public tiles. |
| `MAP_TILE_ATTRIBUTION` | Optional trusted administrator HTML attribution for your tile provider. Never use user input here. |

### Road routing

Select **Road routing · OSRM**. The default public OSRM demo endpoint requires no API key and is intended for modest demonstration usage. It is best-effort, has no uptime guarantee, and must not be used as an unrestricted production dependency. Use a self-hosted OSRM instance or a contracted compatible endpoint for real usage, and honor that provider's terms and request limits. Backend requests are serialized and spaced by the configured interval in this **single-process** setup; there are no automatic retries or background polling.

The adapter uses OSRM's table service for road distance costs, and route service for geometry and per-leg distances/durations. Coordinates are sent to the configured provider; customer names, notes, and address strings are not sent to OSRM. Documentation: https://project-osrm.org/docs/v5.23.0/api/.

Optional live smoke check (sends only the bundled public landmark coordinates):

```powershell
.\.venv\Scripts\python.exe scripts/check_road_provider.py
```

If the service fails, the app displays an error. It **never** silently changes road results into approximations. The user must explicitly choose **Straight-line demo** and recalculate.

### Geocoding

Default demo address search is local and only supports the sample New Delhi landmarks. For arbitrary addresses, set `GEOCODER_BASE_URL` to a self-hosted or contracted Nominatim-compatible provider. It must support `/search?q=...&format=jsonv2&limit=5`. This adapter does not require a key for self-hosted instances; providers with other authentication schemes need a small adapter update in `planner/providers.py`. It caches successful searches, including no-match results, for 24 hours in Django's process-local cache.

The **public Nominatim service is deliberately blocked**: its usage policy restricts generic generated search applications, requires an identifying User-Agent, caching, and at most one request per second, and forbids autocomplete and confidential data submission. Review https://operations.osmfoundation.org/policies/nominatim/ before choosing any service. Address queries go only to your configured geocoder; protect customer privacy when selecting a provider. There is no paid-key requirement for the coordinate/map-based demo.

### Map tiles

Leaflet, Lucide, the font, and the delivery photograph are bundled locally. The basemap loads on demand from OpenStreetMap, so background streets require internet access. Markers, straight-line geometry, and calculations still work without tiles. No bulk download, prefetch, or offline tile cache is implemented. Keep attribution visible. The server sends `strict-origin-when-cross-origin` so tile requests carry an origin-only referrer as required by the provider. Policy: https://operations.osmfoundation.org/policies/tiles/.

For production or heavier usage, configure your own suitable tile service and its attribution. Do not remove the attribution or suppress the referrer required by your provider.

### PostgreSQL later

Create an empty PostgreSQL database and set, for example:

```dotenv
DATABASE_URL=postgresql://YOUR_USER:YOUR_PASSWORD@localhost:5432/smart_delivery
```

Use URL-encoded credentials where necessary. Run `manage.py migrate` again against that database. The Psycopg driver is included. Existing SQLite records are not automatically copied; migrate data separately if you need it. PostgreSQL deployment has not been exercised in this workspace.

## Routing assumptions

- Distance is the objective. A shorter route can take longer; both estimated durations are shown honestly.
- Nearest-neighbor initialization followed by 2-opt segment reversals keeps the depot fixed. Full directed costs are evaluated, so asymmetric road distances work correctly. The search is bounded to 100 improvement rounds for predictable execution at 20 stops.
- Both return-to-start and finish-at-last-delivery routes are supported. In open mode, the final delivery is chosen by the optimizer, not fixed by the user.
- The chosen matrix route is compared with the original. Actual provider legs are then compared again; the original wins if the candidate's actual distance is longer.
- OSRM typically returns its fastest driving paths. The optimizer minimizes distance **among those provider-supplied pairwise paths**, not every possible road path. It does not guarantee a globally shortest tour.
- The drawn geometry, total, and itinerary come from the same selected provider route. Totals sum its exact legs; UI values are rounded for readability.
- Demo mode uses great-circle (Haversine) distance and straight lines, with 25 km/h assumed travel speed. It is unsuitable for turn-by-turn navigation. It ignores roads, water, access restrictions, and traffic.
- No live traffic, departure-time modeling, service/delivery durations, time windows, vehicle capacity, truck restrictions, multiple drivers, or live navigation are implemented. Road providers may snap coordinates to nearby drivable roads. Review map access and legality before travel.

## Tests and checks

```powershell
.\.venv\Scripts\python.exe manage.py test
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

The suite covers directed route optimization, open/closed routes, one-stop routes, preservation of the better original route, malformed/duplicate coordinates, limits, provider timeouts/failures, invalid geocoder responses, registration/login/logout, CSRF, private route CRUD, and session-bound CSV export with spreadsheet-formula neutralization.

See `VALIDATION.md` for checks actually completed and remaining limitations. Automated provider tests use mocks; the optional live smoke test is separate so ordinary tests are fast and reliable without a network.

## Project layout

```text
config/                 Django configuration, URL routing, WSGI
planner/                Models, validation, providers, Python optimizer, views, tests
planner/migrations/     Versioned database schema
planner/sample.py       Shared fictional delivery sample at public landmarks
templates/              Landing page, planner, dashboard, authentication
static/                 CSS, lightweight JavaScript, local vendor assets, photo, font
scripts/                Asset refresh and optional live road smoke check
requirements.txt        Exact direct dependency versions
requirements-lock.txt   Full tested Python environment (Python 3.12, Windows)
.env.example            Configuration template without a secret
ASSETS.md               Photograph and third-party asset sources/licenses
```

## Before deployment

The delivered server is a **local development app**, not a production deployment. Use a production WSGI server, serve `collectstatic` output through your web server/CDN, enable HTTPS, set `DJANGO_DEBUG=False`, use a unique secret and real allowed hosts, and run `manage.py check --deploy`. Secure cookies and SSL redirection are enabled when debug is off. Configure proxy HTTPS settings only for a proxy you trust.

Add shared rate limiting for login, registration, and route endpoints before public exposure. The built-in provider throttle/cache is process-local and does not enforce aggregate limits across multiple workers. Use a shared limiter/cache and a production provider contract. Consider request quotas, backups, retention, and account recovery for real customers. The local MVP does not implement email verification or password reset, and it intentionally does not collect email addresses.

Do not commit `.env`, the SQLite database, or customer data. The app does not deliberately log customer addresses/notes. Standard Django development request logs show paths and statuses; avoid adding body logging. Session results and private saved routes contain delivery data, so protect the database. Logout ends authentication but the tab's local draft remains until reset or closed.

## Adding verified testimonials

There is intentionally **no public testimonials section** because none were supplied. To add one later, obtain the person's permission, keep a record of the approved quote/name and permission date, then add their exact approved text to `templates/planner/home.html`. Do not manufacture ratings, logos, quotes, or performance claims. The stock photograph is illustrative and is not an endorsement.
