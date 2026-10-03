# Validation record

Validated locally with Python 3.12, Django 5.2.17, SQLite, and the Codex in-app Chromium browser. Client date: 2 October 2026.

## India localisation update

### Phone usability update

- Added phone-only Stops / Map & route navigation, a fixed Find my route action, 16px inputs, safe-area bottom spacing, and full-width map/form views. Larger layouts retain both panels.
- Verified the fixed action submits, successful calculation selects the map view, validation errors remain visible, map selection works across views, and returning to desktop restores both panels.
- Measured no horizontal overflow in the planner at 320, 360, 390, 768, and 1440px. Captured `validation/phone-planner.jpg` with loaded New Delhi map tiles and the fixed action.
- Started `scripts/serve_phone.py`; the private-network URL loaded successfully from the local browser. No firewall/router settings were changed. A physical phone on the Wi-Fi has not been tested; network isolation or firewall rules may affect access.

- Replaced the default London sample with New Delhi: Connaught Place, Khan Market, Gole Market, Mandi House, and India Gate. Set the empty map view and coordinate hints to New Delhi.
- Localised landing/planner copy for Indian neighbourhood deliveries, kiranas, shops, landmark instructions, and PIN-code address hints. Updated the hero to licensed Delhi street photography and saved-route timestamps to IST.
- All **19 automated tests passed** after the sample and timezone update; `manage.py check` reported no issues.
- Live OSRM verification of the Indian sample passed: **21.84 km original → 13.16 km suggested**, 594 geometry points, with consistent itinerary totals. These are this sample's test results, not general performance claims.
- Browser check of the Indian sample passed: depot address is Connaught Place, New Delhi; demo result **14.71 km original → 10.11 km suggested**. Updated landing page checked at 360, 768, and 1440px without horizontal overflow; the Indian planner also fit at 360px. Current screenshot: `validation/india-home-desktop.jpg`.
- The original validation below records the earlier build; its London numerical examples and older screenshots are historical.

## Passed automated checks

- `manage.py migrate`: all Django and planner migrations applied successfully.
- `manage.py test`: **19 tests passed**, including directed/asymmetric distance matrices, both journey endings, actual provider-distance recheck, invalid coordinates, duplicates, empty/oversized stop lists, provider timeouts, malformed responses, geocoding validation, authentication, ownership checks, saved-route CRUD, CSRF, CSV session isolation, and spreadsheet-formula neutralization.
- `manage.py check`: no issues.
- `manage.py makemigrations --check --dry-run`: no missing migrations.
- `pip check`: no broken dependency requirements.
- JavaScript syntax checks: both application scripts passed.

## Passed browser checks

- Landing page and planner inspected at approximately **360 × 800**, **768 × 1000**, and **1440 × 1000**. Final measured document width did not exceed the viewport at any of these widths.
- Exactly five links in the main navigation. Mobile menu opens/closes and exposes the navigation links.
- Licensed delivery photograph, local font, Lucide icons, Leaflet map, numbered stops, and OSM attribution render.
- Shared sample loads into the planner. Demo optimization displayed **8.25 km original → 6.51 km suggested** for the supplied round trip (approximate distances, not a product performance claim).
- Added a fifth stop, edited its coordinates, moved it up, and removed it. Updated delivery notes survived a rejected latitude of 99.
- Unchecking return-to-start produced an itinerary ending at a delivery instead of the depot.
- Selecting a sample address result set coordinates. Map picking updated a stop and successfully recalculated.
- Live road mode completed through the running app: **12.26 km original → 10.13 km suggested** for the sample on this test. Road data can change. A separate live Python smoke check verified 787 geometry points and consistent totals/legs.
- Switching original/suggested routes updated the displayed distance and itinerary.
- Downloaded a real CSV via the browser and inspected its start, ordered stops, return leg, notes, road label, and total.
- Browser console had no JavaScript warnings/errors during the initial planner calculation.

Screenshots are in `validation/`. These are development evidence, not fabricated product mockups.

## Issues found and corrected

- Default same-origin referrer policy prevented OSM tile access. Changed to `strict-origin-when-cross-origin`; actual streets then loaded. Added a visible tile-failure message for network errors.
- A hidden line break joined two hero words and caused horizontal overflow at 360px. Restored the break and adjusted the mobile headline size; rechecked all widths.
- Original-order selection initially left suggested totals displayed. The totals now follow the selected route; CSV is explicitly labeled as the suggested export.
- The dashboard's New route action could resume an existing draft. It now explicitly starts an empty draft without a saved-route ID, with a regression test.
- Adjusted the hero crop so the delivery professional remains visible, and enlarged map zoom controls to 44px.

## Verification limits

- Registration, login/logout, saved-route persistence, rename/delete, and cross-user permissions were tested with Django's test client; no real customer accounts were created for UI testing.
- Provider failures/timeouts were exercised with automated mocks. Live road routing was verified; a live custom geocoder was **not** configured. Default search supports only sample landmarks.
- PostgreSQL support is configured and its driver installed, but no PostgreSQL server was provisioned or tested.
- No public deployment, production load test, cross-browser/device lab, full screen-reader audit, or independent security audit was performed. Keyboard alternatives, labels, focus styles, responsive widths, and visible controls were reviewed, but this is not a claim of formal WCAG certification.
- Third-party road services and map tiles require internet and may be unavailable. There is no live traffic, turn-by-turn guidance, or guarantee of a globally shortest route.

See `README.md` for exact setup commands, provider policies, assumptions, and deployment configuration.
