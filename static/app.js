/* Shared interactions. Lucide is the only icon library. */
window.refreshIcons = () => window.lucide?.createIcons();
window.refreshIcons();
const toggle = document.querySelector('.menu-toggle');
const nav = document.querySelector('#main-nav');
toggle?.addEventListener('click', () => {
  const open = toggle.getAttribute('aria-expanded') !== 'true';
  toggle.setAttribute('aria-expanded', String(open));
  toggle.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
  nav.classList.toggle('open', open);
});
nav?.addEventListener('click', e => { if (e.target.closest('a')) { nav.classList.remove('open'); toggle.setAttribute('aria-expanded', 'false'); }});
document.addEventListener('keydown', e => { if (e.key === 'Escape' && nav?.classList.contains('open')) { nav.classList.remove('open'); toggle.setAttribute('aria-expanded', 'false'); toggle.focus(); }});
document.querySelectorAll('form[data-confirm]').forEach(form => form.addEventListener('submit', e => { if (!confirm(form.dataset.confirm)) e.preventDefault(); }));
window.makeMap = (id) => {
  if (!window.L) { document.getElementById(id).textContent = 'Map could not load. You can still plan using coordinates and the itinerary.'; return null; }
  const map = L.map(id, {scrollWheelZoom: false}).setView([28.621, 77.218], 13);
  map.attributionControl.setPrefix('<a href="https://leafletjs.com/">Leaflet</a>');
  const config = JSON.parse(document.getElementById('map-settings').textContent);
  const tiles = L.tileLayer(config.url, {maxZoom: 19, attribution: config.attribution}).addTo(map);
  tiles.on('tileerror', event => {
    event.tile.style.visibility = 'hidden';
    if (!document.getElementById(`${id}-tile-warning`)) {
      const warning = document.createElement('p'); warning.id = `${id}-tile-warning`;
      warning.className = 'map-disclaimer'; warning.setAttribute('role', 'status');
      warning.textContent = 'Some map tiles could not load. Stop markers and route calculations remain available. Check your connection and reload.';
      document.getElementById(id).insertAdjacentElement('afterend', warning);
    }
  });
  return map;
};
window.numberMarker = (point, number, map) => {
  const marker = L.marker([point.lat, point.lng], {title: `${number}: ${point.name}`, icon: L.divIcon({className: 'number-marker', html: `<span>${number}</span>`, iconSize: [30, 30], iconAnchor: [15, 15]})});
  const label = document.createElement('span'); label.textContent = point.name;
  marker.bindTooltip(label); marker.addTo(map); return marker;
};
if (document.querySelector('#preview-map')) {
  const map = window.makeMap('preview-map');
  if (map) {
    const data = JSON.parse(document.querySelector('#preview-data').textContent);
    const route = L.geoJSON(data.optimized.geometry, {style: {color: '#007F78', weight: 4, dashArray: '7 7'}}).addTo(map);
    window.numberMarker(data.start, 'S', map);
    data.optimized.itinerary.filter(p => p.original_index !== 0).forEach((p, i) => window.numberMarker(p, i + 1, map));
    map.fitBounds(route.getBounds(), {padding: [28, 28]});
  }
}
