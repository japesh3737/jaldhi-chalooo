(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const blankPoint = () => ({name: '', address: '', lat: '', lng: '', notes: ''});
  const empty = () => ({name: '', start: {...blankPoint(), name: 'Starting point'}, stops: [], mode: 'demo', return_to_start: true});
  const storageKey = 'smart-delivery-draft-v1';
  const initial = JSON.parse($('initial-data').textContent);
  let state = initial || empty(), result = null, selecting = null, busy = false;
  if (!initial) { try { const draft = JSON.parse(sessionStorage.getItem(storageKey)); if (draft && Array.isArray(draft.stops) && draft.start) state = draft; } catch {} }
  const map = window.makeMap('planner-map');
  const layer = map ? L.layerGroup().addTo(map) : null;
  const phoneLayout = window.matchMedia('(max-width: 600px)');
  function switchView(view, scroll = false) {
    $('planner-layout').dataset.mobileView = view;
    $('view-stops').setAttribute('aria-pressed', String(view === 'stops'));
    $('view-map').setAttribute('aria-pressed', String(view === 'map'));
    requestAnimationFrame(() => {
      map?.invalidateSize();
      if (view === 'map') {
        if (result && selecting === null) showRoute($('show-original').getAttribute('aria-pressed') === 'true' ? 'original' : 'optimized');
        else fitPoints();
      }
      if (scroll && phoneLayout.matches) document.querySelector('.mobile-planner-nav').scrollIntoView({block: 'start'});
    });
  }
  $('view-stops').addEventListener('click', () => switchView('stops', true));
  $('view-map').addEventListener('click', () => switchView('map', true));
  phoneLayout.addEventListener('change', () => { map?.invalidateSize(); });
  const esc = text => String(text ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const persist = () => { try { sessionStorage.setItem(storageKey, JSON.stringify(state)); } catch {} };
  const announce = (message, kind = 'success') => { $('feedback').textContent = message; $('feedback').dataset.kind = kind; };
  const pointAt = index => index === 'start' ? state.start : state.stops[Number(index)];
  const km = meters => `${(meters / 1000).toFixed(2)} km`;
  const duration = seconds => { const mins = Math.max(1, Math.round(seconds / 60)); return mins >= 60 ? `${Math.floor(mins / 60)} h ${mins % 60} min` : `${mins} min`; };
  function fields(point, index) {
    const prefix = `point-${index}`;
    return `<div class="point-fields" data-point="${index}">
      <label class="field-label" for="${prefix}-name">${index === 'start' ? 'Location name' : 'Customer name'}</label><input id="${prefix}-name" data-field="name" value="${esc(point.name)}" maxlength="100" placeholder="${index === 'start' ? 'Your depot or starting point' : 'Customer or delivery location'}" required>
      <label class="field-label" for="${prefix}-address">Address</label><input id="${prefix}-address" data-field="address" value="${esc(point.address)}" maxlength="300" placeholder="Shop, street, area, city, PIN code">
      <div class="location-actions"><button type="button" class="button secondary" data-search="${index}"><i data-lucide="search"></i> Find address</button><button type="button" class="button secondary" data-pick="${index}"><i data-lucide="map-pin"></i> Select on map</button></div>
      <div class="search-results" data-results="${index}" aria-live="polite"></div>
      <div class="coordinate-row"><div><label class="field-label" for="${prefix}-lat">Latitude</label><input id="${prefix}-lat" data-field="lat" type="number" step="any" min="-90" max="90" value="${esc(point.lat)}" placeholder="28.6315" required></div><div><label class="field-label" for="${prefix}-lng">Longitude</label><input id="${prefix}-lng" data-field="lng" type="number" step="any" min="-180" max="180" value="${esc(point.lng)}" placeholder="77.2167" required></div></div>
      ${index === 'start' ? '' : `<label class="field-label" for="${prefix}-notes">Delivery notes <span class="subtle">(optional)</span></label><textarea id="${prefix}-notes" data-field="notes" maxlength="1000" rows="2" placeholder="Shop number, nearby landmark, or delivery instructions">${esc(point.notes)}</textarea>`}
    </div>`;
  }
  function render() {
    $('start-fields').innerHTML = fields(state.start, 'start');
    $('stops').innerHTML = state.stops.length ? state.stops.map((point, i) => `<details class="stop-card" open><summary><span class="stop-badge">${i+1}</span><span data-stop-title="${i}">${esc(point.name || 'New delivery stop')}</span></summary>${fields(point, i)}<div class="stop-actions"><button type="button" class="icon-button" data-move="${i}" data-direction="-1" aria-label="Move stop ${i+1} up" ${i === 0 ? 'disabled' : ''}><i data-lucide="arrow-up"></i></button><button type="button" class="icon-button" data-move="${i}" data-direction="1" aria-label="Move stop ${i+1} down" ${i === state.stops.length-1 ? 'disabled' : ''}><i data-lucide="arrow-down"></i></button><button type="button" class="icon-button" data-remove="${i}" aria-label="Remove stop ${i+1}"><i data-lucide="trash-2"></i></button></div></details>`).join('') : '<div class="no-stops">No deliveries yet.<br>Add your first stop or load the sample route.</div>';
    $('stop-count').textContent = `${state.stops.length} / 20`;
    $('add-stop').disabled = state.stops.length >= 20;
    $('mode').value = state.mode;
    $('return-to-start').checked = state.return_to_start;
    if ($('route-name')) $('route-name').value = state.name || '';
    modeHelp(); refreshIcons(); drawPoints(); persist();
  }
  const valid = p => p.lat !== '' && p.lng !== '' && Number.isFinite(Number(p.lat)) && Number.isFinite(Number(p.lng)) && Math.abs(Number(p.lat)) <= 90 && Math.abs(Number(p.lng)) <= 180;
  function drawPoints(fit = false) {
    if (!map) return;
    layer.clearLayers();
    const points = [state.start, ...state.stops];
    points.forEach((p, i) => { if (valid(p)) window.numberMarker(p, i === 0 ? 'S' : i, layer); });
    if (fit) fitPoints();
  }
  function fitPoints() { if (!map) return; const coords = [state.start, ...state.stops].filter(valid).map(p => [Number(p.lat), Number(p.lng)]); if (coords.length) map.fitBounds(coords, {padding: [35,35], maxZoom: 15}); }
  function invalidate() {
    result = null; selecting = null; $('results').hidden = true; $('empty-result').hidden = false;
    $('download-csv').removeAttribute('href'); $('feedback').textContent = '';
    $('map-help').textContent = 'Your locations are shown in the entered order. Optimize to calculate your route.';
    drawPoints(); persist();
  }
  function modeHelp() { $('mode-help').textContent = state.mode === 'demo' ? 'Straight-line approximation at 25 km/h. Not for navigation.' : 'Road distances and estimated travel time from OSRM. No live traffic. Coordinates are sent to the routing provider.'; }
  async function api(url, payload) {
    const controller = new AbortController(); const timer = setTimeout(() => controller.abort(), 65000);
    try {
      const response = await fetch(url, {method: 'POST', headers: {'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value}, body: JSON.stringify(payload), signal: controller.signal});
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.error || (response.status === 403 ? 'Your session has changed. Reload this page; your draft is preserved.' : 'The request could not be completed. Your entries are preserved.'));
      return data;
    } catch (error) { if (error.name === 'AbortError') throw new Error('The request timed out. Your entries are preserved. Please retry.'); throw error; }
    finally { clearTimeout(timer); }
  }
  function setBusy(value, label = 'Calculating…') {
    busy = value;
    document.querySelectorAll('#route-form input, #route-form textarea, #route-form select, #route-form button, #load-sample, #reset, #save-route, #route-name, #empty-sample').forEach(el => { el.disabled = value; });
    $('optimize').querySelector('span').textContent = value ? label : 'Optimize route';
    $('mobile-optimize').disabled = value;
    $('mobile-optimize').querySelector('span').textContent = value ? label : 'Find my route';
    $('route-form').setAttribute('aria-busy', String(value));
    if (!value) { $('add-stop').disabled = state.stops.length >= 20; document.querySelectorAll('[data-move]').forEach(el => { const i = Number(el.dataset.move) + Number(el.dataset.direction); el.disabled = i < 0 || i >= state.stops.length; }); }
  }
  $('route-form').addEventListener('input', e => {
    const field = e.target.dataset.field;
    if (!field) return;
    const index = e.target.closest('[data-point]').dataset.point;
    const point = pointAt(index); point[field] = e.target.value;
    // Editing an address invalidates its former coordinates, preventing accidental stale routing.
    if (field === 'address') { point.lat = ''; point.lng = ''; $(`point-${index}-lat`).value = ''; $(`point-${index}-lng`).value = ''; }
    if (field === 'name' && index !== 'start') document.querySelector(`[data-stop-title="${index}"]`).textContent = point.name || 'New delivery stop';
    invalidate();
  });
  $('mode').addEventListener('change', () => { state.mode = $('mode').value; modeHelp(); invalidate(); });
  $('return-to-start').addEventListener('change', () => { state.return_to_start = $('return-to-start').checked; invalidate(); });
  $('route-name')?.addEventListener('input', e => { state.name = e.target.value; persist(); });
  $('add-stop').addEventListener('click', () => { if (busy || state.stops.length >= 20) return; state.stops.push(blankPoint()); invalidate(); render(); $(`point-${state.stops.length-1}-name`).focus(); });
  $('route-form').addEventListener('click', async e => {
    const button = e.target.closest('button'); if (!button || busy) return;
    if (button.dataset.remove !== undefined) { const index = Number(button.dataset.remove); state.stops.splice(index, 1); invalidate(); render(); $('add-stop').focus(); announce('Delivery stop removed.'); }
    if (button.dataset.move !== undefined) { const from = Number(button.dataset.move), to = from + Number(button.dataset.direction); if (to < 0 || to >= state.stops.length) return; [state.stops[from], state.stops[to]] = [state.stops[to], state.stops[from]]; invalidate(); render(); $(`point-${to}-name`).focus(); announce('Original delivery order updated. Optimize again to compare.'); }
    if (button.dataset.pick !== undefined) { if (!map) { announce('The map is unavailable. Please enter coordinates.', 'error'); return; } selecting = button.dataset.pick; switchView('map', true); $('map-help').textContent = `Tap a location on the map for ${selecting === 'start' ? 'your starting point' : `stop ${Number(selecting)+1}`}. Press Escape to cancel. Coordinate inputs are also available.`; if (!phoneLayout.matches) $('planner-map').scrollIntoView({behavior: 'smooth', block: 'center'}); announce('Map selection is active. Choose a point on the map.'); }
    if (button.dataset.search !== undefined) {
      const index = button.dataset.search, point = pointAt(index), container = document.querySelector(`[data-results="${index}"]`);
      setBusy(true, 'Searching…'); container.textContent = 'Searching for this address…';
      try {
        const data = await api('/api/geocode/', {query: point.address}); container.textContent = '';
        if (!data.results.length) { container.textContent = 'No matching address found. Refine the address or use the map / coordinates.'; return; }
        data.results.forEach(match => { const choice = document.createElement('button'); choice.type = 'button'; choice.textContent = `${match.address} (${match.lat.toFixed(5)}, ${match.lng.toFixed(5)})`; choice.addEventListener('click', () => { Object.assign(point, match); invalidate(); render(); fitPoints(); announce('Location selected. Review the map to confirm it is correct.'); }); container.appendChild(choice); });
      } catch (error) { container.textContent = error.message; announce(error.message, 'error'); }
      finally { setBusy(false); }
    }
  });
  map?.on('click', e => { if (selecting === null || busy) return; const point = pointAt(selecting); point.lat = Number(e.latlng.lat.toFixed(6)); point.lng = Number(e.latlng.lng.toFixed(6)); invalidate(); render(); announce('Map location selected. Check the address label and coordinates before continuing.'); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && selecting !== null) { selecting = null; $('map-help').textContent = 'Map selection canceled. You can enter coordinates at any time.'; } });
  async function loadSample() {
    if (busy) return;
    if (state.stops.length && !confirm('Replace your current draft with the sample route?')) return;
    setBusy(true, 'Loading sample…');
    try { const response = await fetch('/api/sample/'); if (!response.ok) throw new Error('Could not load the sample. Your draft is preserved.'); const sample = await response.json(); state = sample; invalidate(); render(); fitPoints(); announce('Sample loaded: four fictional deliveries at New Delhi landmarks. Select Optimize route to try it.'); }
    catch (error) { announce(error.message, 'error'); } finally { setBusy(false); }
  }
  $('load-sample').addEventListener('click', loadSample); $('empty-sample').addEventListener('click', loadSample);
  $('reset').addEventListener('click', () => { if (busy || !confirm('Clear all planner entries and start again? Saved routes will remain in your dashboard.')) return; state = empty(); invalidate(); render(); announce('Planner reset. Add a starting point and your first delivery.'); });
  $('fit-map').addEventListener('click', () => { if (result) showRoute($('show-original').getAttribute('aria-pressed') === 'true' ? 'original' : 'optimized'); else fitPoints(); });
  $('route-form').addEventListener('submit', async e => {
    e.preventDefault(); if (busy) return;
    setBusy(true); announce('Calculating your original and suggested routes…');
    try { result = await api('/api/optimize/', state); displayResults(); switchView('map', true); announce('Route calculated. Review the suggested order and comparison below.'); }
    catch (error) { announce(error.message, 'error'); $('feedback').focus(); }
    finally { setBusy(false); }
  });
  function displayResults() {
    $('empty-result').hidden = true; $('results').hidden = false;
    $('result-label').textContent = result.label;
    $('total-distance').textContent = km(result.optimized.distance); $('total-duration').textContent = duration(result.optimized.duration); $('total-stops').textContent = state.stops.length;
    $('comparison').innerHTML = `Original: <b>${km(result.original.distance)}</b> · ${duration(result.original.duration)} estimated<br>Suggested: <b>${km(result.optimized.distance)}</b> · ${duration(result.optimized.duration)} estimated<br><strong>${result.saved_distance > 0.5 ? `${km(result.saved_distance)} less distance than your entered order.` : 'Your original order is already as efficient as this suggestion.'}</strong>`;
    $('download-csv').href = `/export/${result.result_id}/`;
    showRoute('optimized');
  }
  function showRoute(which) {
    if (!result) return;
    const route = result[which];
    $('total-distance').textContent = km(route.distance); $('total-duration').textContent = duration(route.duration);
    $('show-optimized').setAttribute('aria-pressed', String(which === 'optimized')); $('show-original').setAttribute('aria-pressed', String(which === 'original'));
    $('show-optimized').classList.toggle('selected', which === 'optimized'); $('show-original').classList.toggle('selected', which === 'original');
    $('itinerary-title').textContent = which === 'optimized' ? 'Suggested delivery order' : 'Original delivery order';
    $('itinerary').innerHTML = `<li><span class="stop-badge">S</span><div><strong>Start · ${esc(result.start.name)}</strong><p>${esc(result.start.address)}</p></div></li>` + route.itinerary.map((p,i) => `<li><span class="stop-badge">${p.original_index === 0 ? 'S' : i+1}</span><div><strong>${p.original_index === 0 ? 'Return · ' : ''}${esc(p.name)}</strong><p>${esc(p.address)}</p>${p.notes ? `<p>${esc(p.notes)}</p>` : ''}<small>${km(p.distance)} · ${duration(p.duration)} estimated from previous stop</small></div></li>`).join('');
    $('map-help').textContent = `${which === 'optimized' ? 'Suggested' : 'Original'} order shown · ${km(route.distance)} · ${result.label}`;
    if (map) { layer.clearLayers(); const line = L.geoJSON(route.geometry, {style: {color: which === 'optimized' ? '#007F78' : '#102A43', weight: 4, dashArray: result.mode === 'demo' ? '8 7' : null}}).addTo(layer); window.numberMarker(result.start, 'S', layer); route.itinerary.forEach((p, i) => { if (p.original_index !== 0) window.numberMarker(p, i+1, layer); }); map.fitBounds(line.getBounds(), {padding: [35,35], maxZoom: 16}); }
  }
  $('show-original').addEventListener('click', () => showRoute('original')); $('show-optimized').addEventListener('click', () => showRoute('optimized'));
  $('save-route')?.addEventListener('click', async () => {
    if (busy) return; setBusy(true, 'Saving…');
    try { const saved = await api('/api/routes/save/', state); state.id = saved.id; state.name = saved.name; persist(); announce(`“${saved.name}” saved. You can reopen it from My routes.`); }
    catch (error) { announce(error.message, 'error'); }
    finally { setBusy(false); }
  });
  render(); fitPoints();
})();
