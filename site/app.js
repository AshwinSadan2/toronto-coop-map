// Toronto Co-op Map: map, search, filters and co-op cards.
// Data comes from data/coops.json (built by builder/export_site.py, later by the publish step).

const CATEGORIES = {
  "Grocery & Food":    "#3d8b4f",
  "Shops":             "#0e7c86",
  "Arts & Culture":    "#b83b7a",
  "Health & Wellness": "#7a9e1e",
  "Banking":           "#2f6fb5",
  "Insurance":         "#6b5ca5",
  "Home & Hardware":   "#c25e17",
  "Childcare":         "#d39a12",
  "Getting Around":    "#3b4a5e",
  "Places to Stay":    "#9c4f2e",
};
const TORONTO = { center: [43.7, -79.4], zoom: 11 };
const SAME_SPOT_METRES = 30;  // co-ops closer than this share one pin
const DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

const state = { coops: [], groups: [], query: "", categories: new Set(), userPos: null, selected: null };
const markers = new Map();  // group id -> Leaflet marker
const $ = (id) => document.getElementById(id);

// ---------- helpers ----------

function escapeHtml(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function distanceM(a, b) {
  const rad = Math.PI / 180;
  const x = (b.lng - a.lng) * rad * Math.cos(((a.lat + b.lat) / 2) * rad);
  const y = (b.lat - a.lat) * rad;
  return 6371000 * Math.hypot(x, y);
}

function formatDistance(m) {
  return m < 1000 ? `${Math.round(m / 10) * 10} m` : `${(m / 1000).toFixed(m < 10000 ? 1 : 0)} km`;
}

function shortAddress(address) {
  return address.split(",")[0];
}

function websiteLabel(url) {
  try { return new URL(url).hostname.replace(/^www\./, ""); } catch { return url; }
}

// ---------- opening hours ("Monday: 9:00 AM – 5:00 PM") ----------

function cleanSpaces(s) {
  return s.replace(/[   ]/g, " ");
}

function toMinutes(t, fallbackMeridiem) {
  const m = t.trim().match(/^(\d{1,2})(?::(\d{2}))?\s*(AM|PM)?$/i);
  if (!m) return null;
  const meridiem = (m[3] || fallbackMeridiem || "").toUpperCase();
  let h = Number(m[1]) % 12;
  if (meridiem === "PM") h += 12;
  return h * 60 + Number(m[2] || 0);
}

function hoursFor(coop, dayIndex) {
  const line = coop.hours.find((h) => h.startsWith(DAYS[dayIndex] + ":"));
  return line ? cleanSpaces(line.slice(line.indexOf(":") + 1).trim()) : null;
}

function openStatus(coop, now = new Date()) {
  const today = hoursFor(coop, now.getDay());
  if (today === null) return null;
  if (/closed/i.test(today)) return { open: false, text: "Closed today" };
  if (/24 hours/i.test(today)) return { open: true, text: "Open 24 hours" };
  const nowMin = now.getHours() * 60 + now.getMinutes();
  let opensLater = null;
  for (const range of today.split(",")) {
    const [a, b] = range.split("–").map((s) => s.trim());
    if (!a || !b) continue;
    const endMeridiem = (b.match(/(AM|PM)$/i) || [])[1];
    const start = toMinutes(a, endMeridiem);
    let end = toMinutes(b);
    if (start === null || end === null) continue;
    if (end <= start) end += 24 * 60;
    if (nowMin >= start && nowMin < end) return { open: true, text: `Open until ${b}` };
    if (nowMin < start && opensLater === null) opensLater = a.match(/(AM|PM)$/i) ? a : `${a} ${endMeridiem}`;
  }
  return { open: false, text: opensLater ? `Closed, opens ${opensLater}` : "Closed now" };
}

function statusHtml(coop) {
  const s = openStatus(coop);
  if (!s) return "";
  return `<span class="${s.open ? "status-open" : "status-closed"}">${escapeHtml(s.text)}</span>`;
}

// ---------- grouping co-ops that share an address ----------

function buildGroups(coops) {
  const groups = [];
  for (const c of coops) {
    const g = groups.find((g) => distanceM(g, c) < SAME_SPOT_METRES);
    if (g) g.members.push(c);
    else groups.push({ id: c.id, lat: c.lat, lng: c.lng, members: [c] });
    c.group = g || groups[groups.length - 1];
  }
  return groups;
}

// ---------- filtering ----------

function matches(coop) {
  if (state.categories.size && !state.categories.has(coop.category)) return false;
  const q = state.query.trim().toLowerCase();
  if (!q) return true;
  const haystack = [coop.name, coop.category, coop.address, coop.note, ...coop.searchAreas].join(" ").toLowerCase();
  return q.split(/\s+/).every((word) => haystack.includes(word));
}

function visibleCoops() {
  const list = state.coops.filter(matches);
  if (state.userPos) {
    list.forEach((c) => (c.distance = distanceM(state.userPos, c)));
    list.sort((a, b) => a.distance - b.distance);
  } else {
    // Local shops and cafés first, chains and services after (same order as the filter chips)
    const order = Object.keys(CATEGORIES);
    list.sort((a, b) => order.indexOf(a.category) - order.indexOf(b.category) || a.name.localeCompare(b.name));
  }
  return list;
}

// ---------- map ----------

const map = L.map("map", { zoomControl: false }).setView(TORONTO.center, TORONTO.zoom);
L.control.zoom({ position: "bottomright" }).addTo(map);
// Round crosshair button above the zoom buttons; same job as "Near me"
const LocateControl = L.Control.extend({
  options: { position: "bottomright" },
  onAdd() {
    const btn = L.DomUtil.create("button", "locate leaflet-control");
    btn.id = "locate";
    btn.type = "button";
    btn.title = "Show my location";
    btn.setAttribute("aria-label", "Show my location");
    btn.innerHTML = `<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
      <circle cx="12" cy="12" r="7"/><circle cx="12" cy="12" r="2.5" fill="currentColor" stroke="none"/>
      <path d="M12 2v3M12 19v3M2 12h3M19 12h3"/></svg>`;
    L.DomEvent.disableClickPropagation(btn);
    L.DomEvent.on(btn, "click", () => askForLocation(true));
    return btn;
  },
});
new LocateControl().addTo(map);
L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
}).addTo(map);
let youMarker = null;

function pinIcon(group, visibleMembers) {
  const count = visibleMembers.length;
  const size = count > 1 ? 24 : 16;
  const color = CATEGORIES[visibleMembers[0].category] || "#586579";
  const selected = state.selected && state.selected.group === group ? " is-selected" : "";
  return L.divIcon({
    className: "pin-wrap",
    iconSize: [size, size],
    html: `<span class="pin${selected}" style="--c:${color}">${count > 1 ? count : ""}</span>`,
  });
}

function renderMarkers(visible) {
  const visibleIds = new Set(visible.map((c) => c.id));
  for (const g of state.groups) {
    const members = g.members.filter((c) => visibleIds.has(c.id));
    let marker = markers.get(g.id);
    if (!members.length) {
      if (marker) marker.remove();
      continue;
    }
    if (!marker) {
      marker = L.marker([g.lat, g.lng], { keyboard: true });
      marker.on("click", () => (g.members.length > 1 ? showGroup(g) : showCoop(g.members[0])));
      markers.set(g.id, marker);
    }
    marker.setIcon(pinIcon(g, members));
    marker.bindTooltip(members.length > 1 ? `${members.length} co-ops at ${shortAddress(members[0].address)}` : members[0].name,
                       { direction: "top", offset: [0, -8] });
    if (!map.hasLayer(marker)) marker.addTo(map);
  }
}

// ---------- side panel: list ----------

function renderCategories() {
  const counts = {};
  state.coops.forEach((c) => (counts[c.category] = (counts[c.category] || 0) + 1));
  $("categories").innerHTML = Object.keys(CATEGORIES)
    .filter((cat) => counts[cat])
    .map((cat) => `<button class="chip" type="button" data-cat="${escapeHtml(cat)}" aria-pressed="${state.categories.has(cat)}" style="--c:${CATEGORIES[cat]}">
        <span class="dot"></span>${escapeHtml(cat)} <span class="count">${counts[cat]}</span></button>`)
    .join("");
}

function render() {
  const visible = visibleCoops();
  renderMarkers(visible);
  const q = state.query.trim();
  $("summary").textContent = visible.length
    ? `${visible.length} co-op${visible.length === 1 ? "" : "s"}${state.userPos ? ", nearest first" : ""}`
    : "";
  $("results").innerHTML = visible.map((c) => `
    <li><button class="result" type="button" data-id="${escapeHtml(c.id)}" style="--c:${CATEGORIES[c.category]}">
      <span class="dot"></span>
      <span class="name">${escapeHtml(c.name)}</span>
      <span class="distance">${c.distance !== undefined && state.userPos ? formatDistance(c.distance) : ""}</span>
      <span class="meta">${escapeHtml(c.category)}, ${escapeHtml(c.neighbourhood || shortAddress(c.address))} ${statusHtml(c) ? "<br>" + statusHtml(c) : ""}</span>
    </button></li>`).join("");

  const box = $("address-search");
  if (!visible.length && q.length > 2) {
    box.hidden = false;
    box.innerHTML = `<p>No co-ops match "${escapeHtml(q)}". If it's an address or place, find co-ops near it instead.</p>
      <button type="button" id="find-place">Show co-ops near "${escapeHtml(q)}"</button>`;
    $("find-place").addEventListener("click", () => findPlace(q));
  } else {
    box.hidden = true;
  }
}

// ---------- side panel: detail cards ----------

function hoursTable(coop) {
  if (!coop.hours.length) return "Not listed";
  const todayIdx = new Date().getDay();
  const rows = [1, 2, 3, 4, 5, 6, 0].map((d) => `
    <tr class="${d === todayIdx ? "today" : ""}"><td>${DAYS[d].slice(0, 3)}</td><td>${escapeHtml(hoursFor(coop, d) ?? "")}</td></tr>`);
  return `<table class="hours">${rows.join("")}</table>`;
}

function signHtml(topper, name, sub) {
  return `<div class="sign">
    ${topper ? `<span class="sign-topper">${escapeHtml(topper)}</span>` : ""}
    <div class="sign-blade"><h2 class="sign-name">${escapeHtml(name)}</h2>${sub ? `<p class="sign-sub">${escapeHtml(sub)}</p>` : ""}</div>
  </div>`;
}

function showCoop(coop, { pan = true, focus = true } = {}) {
  state.selected = coop;
  const status = statusHtml(coop);
  $("detail").innerHTML = `
    ${signHtml(coop.neighbourhood, coop.name, coop.category)}
    ${coop.note ? `<p class="note" style="--c:${CATEGORIES[coop.category]}">${escapeHtml(coop.note)}</p>` : ""}
    <dl class="facts">
      <div class="fact"><dt>Address</dt><dd>${escapeHtml(coop.address)}</dd></div>
      <div class="fact"><dt>Hours</dt><dd>${status ? status + "<br>" : ""}${hoursTable(coop)}</dd></div>
      ${coop.phone ? `<div class="fact"><dt>Phone</dt><dd><a href="tel:${escapeHtml(coop.phone.replace(/[^\d+]/g, ""))}">${escapeHtml(coop.phone)}</a></dd></div>` : ""}
      ${coop.website ? `<div class="fact"><dt>Website</dt><dd><a href="${escapeHtml(coop.website)}" target="_blank" rel="noopener">${escapeHtml(websiteLabel(coop.website))}</a></dd></div>` : ""}
    </dl>
    <a class="directions" href="${escapeHtml(coop.directions)}" target="_blank" rel="noopener">Get directions in Google Maps</a>
    <p class="checked">Details last checked ${escapeHtml(coop.lastChecked)}.</p>`;
  openDetail(coop.group, pan, coop.id, focus);
}

function showGroup(group, { pan = true, focus = true } = {}) {
  state.selected = group.members[0];
  const members = group.members;
  const first = members[0];
  $("detail").innerHTML = `
    ${signHtml(first.neighbourhood, shortAddress(first.address), `${members.length} co-ops at this address`)}
    ${members.every((c) => c.note && c.note === first.note) ? `<p class="note" style="--c:${CATEGORIES[first.category]}">${escapeHtml(first.note)}</p>` : ""}
    <ul class="tenants">${members.map((c) => `
      <li class="tenant">
        <p class="tenant-name">${escapeHtml(c.name)}</p>
        <p>${escapeHtml(c.category)}${c.phone ? `, <a href="tel:${escapeHtml(c.phone.replace(/[^\d+]/g, ""))}">${escapeHtml(c.phone)}</a>` : ""}</p>
        ${statusHtml(c) ? `<p>${statusHtml(c)}</p>` : ""}
        <button type="button" data-id="${escapeHtml(c.id)}">See hours and details</button>
      </li>`).join("")}
    </ul>
    <a class="directions" href="${escapeHtml(first.directions)}" target="_blank" rel="noopener">Get directions in Google Maps</a>`;
  openDetail(group, pan, group.id, focus);
}

function openDetail(group, pan, hashId, focus) {
  $("list-view").hidden = true;
  $("detail-view").hidden = false;
  $("detail-view").scrollIntoView({ block: "start" });
  history.replaceState(null, "", `#${encodeURIComponent(hashId)}`);
  if (pan) map.flyTo([group.lat, group.lng], Math.max(map.getZoom(), 15), { duration: 0.6 });
  render();
  if (focus) $("back").focus({ preventScroll: true });
}

function closeDetail() {
  state.selected = null;
  $("detail-view").hidden = true;
  $("list-view").hidden = false;
  history.replaceState(null, "", location.pathname);
  render();
}

// ---------- location + address search ----------

function useLocation(pos, zoom = 14) {
  state.userPos = { lat: pos.lat, lng: pos.lng };
  if (youMarker) youMarker.remove();
  youMarker = L.marker([pos.lat, pos.lng], {
    icon: L.divIcon({ className: "pin-wrap", iconSize: [16, 16], html: '<span class="you-are-here"></span>' }),
    interactive: false,
  }).addTo(map);
  map.flyTo([pos.lat, pos.lng], zoom, { duration: 0.8 });
  $("near-me").setAttribute("aria-pressed", "true");
  $("locate").setAttribute("aria-pressed", "true");
  render();
}

function askForLocation(explicit) {
  if (!navigator.geolocation) {
    if (explicit) $("summary").textContent = "This browser can't share your location. Search an address instead.";
    return;
  }
  $("locate").classList.add("is-locating");
  navigator.geolocation.getCurrentPosition(
    (p) => {
      $("locate").classList.remove("is-locating");
      useLocation({ lat: p.coords.latitude, lng: p.coords.longitude });
    },
    () => {
      $("locate").classList.remove("is-locating");
      if (explicit) $("summary").textContent = "Your browser didn't share your location. Search an address instead.";
    },
    { timeout: 8000, maximumAge: 600000 },
  );
}

async function findPlace(q) {
  $("summary").textContent = `Looking up "${q}"…`;
  const url = "https://nominatim.openstreetmap.org/search?" + new URLSearchParams({
    q, format: "jsonv2", limit: "1", countrycodes: "ca", bounded: "1", viewbox: "-79.64,43.86,-79.11,43.58",
  });
  try {
    const res = await fetch(url, { headers: { "Accept-Language": "en" } });
    const [place] = await res.json();
    if (!place) {
      $("summary").textContent = `Couldn't find "${q}" in Toronto. Try a street address or a co-op name.`;
      return;
    }
    state.query = "";
    $("q").value = "";
    useLocation({ lat: Number(place.lat), lng: Number(place.lon) }, 15);
  } catch {
    $("summary").textContent = "The address lookup isn't responding. Try again in a moment.";
  }
}

// ---------- wiring ----------

$("q").addEventListener("input", (e) => {
  state.query = e.target.value;
  if (!$("detail-view").hidden) closeDetail();
  render();
});
$("q").addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !visibleCoops().length && state.query.trim().length > 2) findPlace(state.query.trim());
});
$("near-me").addEventListener("click", () => askForLocation(true));
$("back").addEventListener("click", closeDetail);
$("categories").addEventListener("click", (e) => {
  const chip = e.target.closest(".chip");
  if (!chip) return;
  const cat = chip.dataset.cat;
  state.categories.has(cat) ? state.categories.delete(cat) : state.categories.add(cat);
  chip.setAttribute("aria-pressed", state.categories.has(cat));
  if (!$("detail-view").hidden) closeDetail();
  render();
});
$("results").addEventListener("click", (e) => {
  const btn = e.target.closest(".result");
  if (btn) showCoop(state.coops.find((c) => c.id === btn.dataset.id));
});
$("detail").addEventListener("click", (e) => {
  const btn = e.target.closest("button[data-id]");
  if (btn) showCoop(state.coops.find((c) => c.id === btn.dataset.id), { pan: false });
});
$("results").addEventListener("mouseover", (e) => {
  const btn = e.target.closest(".result");
  document.querySelectorAll(".pin.is-hovered").forEach((p) => p.classList.remove("is-hovered"));
  if (!btn) return;
  const coop = state.coops.find((c) => c.id === btn.dataset.id);
  markers.get(coop.group.id)?.getElement()?.querySelector(".pin")?.classList.add("is-hovered");
});

fetch("data/coops.json")
  .then((r) => r.json())
  .then((data) => {
    state.coops = data.coops;
    state.groups = buildGroups(state.coops);
    $("updated").textContent = new Date(data.updated + "T12:00").toLocaleDateString("en-CA", { month: "long", day: "numeric", year: "numeric" });
    renderCategories();
    const hashId = decodeURIComponent(location.hash.slice(1));
    const linked = state.coops.find((c) => c.id === hashId);
    const linkedGroup = state.groups.find((g) => g.id === hashId && g.members.length > 1);
    if (linkedGroup) showGroup(linkedGroup, { focus: false });
    else if (linked) showCoop(linked, { focus: false });
    else {
      render();
      askForLocation(false);
    }
  })
  .catch(() => {
    $("summary").textContent = "The co-op list didn't load. Refresh the page to try again.";
  });
