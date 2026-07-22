const GAUGE_MAX_CPM = 1000; // ajusta según el rango normal de tu sensor
const GAUGE_ARC_LENGTH = 251;
const POLL_MS = 10000;
const BASE_PATH = window.BASE_PATH || "";

function apiUrl(path) {
    return `${BASE_PATH}${path}`;
}

let chart;
let map;
let markersLayer;
let lastIndice = null;
let currentSensor = "";

function fmt(value, fallback = "--") {
    return value === null || value === undefined || value === "" ? fallback : value;
}

function updateGauge(cpm) {
    const el = document.getElementById("gaugeFill");
    const ratio = Math.min(cpm / GAUGE_MAX_CPM, 1);
    const offset = GAUGE_ARC_LENGTH - ratio * GAUGE_ARC_LENGTH;
    el.style.strokeDashoffset = offset;

    if (cpm > GAUGE_MAX_CPM * 0.6) {
        el.style.stroke = "var(--danger)";
    } else {
        el.style.stroke = "var(--amber)";
    }
}

function pulseGauge() {
    const el = document.getElementById("gaugeFill");
    el.classList.remove("is-pulsing");
    // fuerza reflow para poder re-disparar la animación
    void el.offsetWidth;
    el.classList.add("is-pulsing");
}

async function loadStats() {
    const res = await fetch(apiUrl("/api/stats"));
    if (!res.ok) return;
    const data = await res.json();

    document.getElementById("gaugeCPM").textContent = fmt(data.valorCPM);
    document.getElementById("gaugeUsv").textContent =
        data.microSieverthora !== undefined ? `${data.microSieverthora} µSv/h` : "-- µSv/h";
    document.getElementById("statSensor").textContent = fmt(data.sensorID);
    document.getElementById("statSat").textContent = fmt(data.sat);
    document.getElementById("statHdop").textContent = fmt(data.hdop);
    document.getElementById("statTotal").textContent = fmt(data.total_registros);
    document.getElementById("lastUpdate").textContent = data.capturedTime
        ? `Última lectura: ${data.capturedTime}`
        : "Sin datos todavía";

    if (data.valorCPM !== undefined) {
        updateGauge(data.valorCPM);
    }
}

function buildChart(readings) {
    const ctx = document.getElementById("cpmChart");
    const labels = readings.map(r => r.capturedTime);
    const cpmData = readings.map(r => r.valorCPM);

    if (chart) {
        chart.data.labels = labels;
        chart.data.datasets[0].data = cpmData;
        chart.update();
        return;
    }

    chart = new Chart(ctx, {
        type: "line",
        data: {
            labels,
            datasets: [{
                label: "CPM",
                data: cpmData,
                borderColor: "#FFB238",
                backgroundColor: "rgba(255,178,56,0.12)",
                borderWidth: 2,
                pointRadius: 0,
                tension: 0.25,
                fill: true,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { ticks: { color: "#7C8798", maxTicksLimit: 6 }, grid: { color: "#2A323D" } },
                y: { ticks: { color: "#7C8798" }, grid: { color: "#2A323D" } },
            },
            plugins: { legend: { display: false } },
        },
    });
}

function buildMap(readings) {
    if (!map) {
        map = L.map("map", { zoomControl: true, attributionControl: false });
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            maxZoom: 19,
        }).addTo(map);
        markersLayer = L.layerGroup().addTo(map);
        map.setView([4.6097, -74.0817], 11); // Bogotá por defecto si no hay datos aún
    }

    markersLayer.clearLayers();
    const points = [];

    readings.forEach(r => {
        if (r.latitude === null || r.longitude === null) return;
        const marker = L.circleMarker([r.latitude, r.longitude], {
            radius: 5,
            color: "#FFB238",
            fillColor: "#FFB238",
            fillOpacity: 0.7,
        }).bindPopup(
            `<b>${r.capturedTime ?? ""}</b><br>CPM: ${r.valorCPM ?? "--"}<br>Sensor: ${r.sensorID ?? "--"}`
        );
        marker.addTo(markersLayer);
        points.push([r.latitude, r.longitude]);
    });

    if (points.length > 0) {
        map.fitBounds(points, { padding: [20, 20] });
    }
}

function buildTable(readings) {
    const tbody = document.querySelector("#readingsTable tbody");
    tbody.innerHTML = "";

    [...readings].reverse().forEach(r => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${fmt(r.capturedTime)}</td>
            <td>${fmt(r.sensorID)}</td>
            <td>${fmt(r.valorCPM)}</td>
            <td>${fmt(r.microSieverthora)}</td>
            <td>${fmt(r.sat)}</td>
            <td>${r.latitude !== null ? r.latitude.toFixed(5) : "--"}</td>
            <td>${r.longitude !== null ? r.longitude.toFixed(5) : "--"}</td>
        `;
        tbody.appendChild(row);
    });
}

async function loadSensores() {
    const res = await fetch(apiUrl("/api/sensores"));
    if (!res.ok) return;
    const sensores = await res.json();
    const select = document.getElementById("sensorSelect");
    const previous = select.value;
    select.innerHTML = '<option value="">Todos</option>';
    sensores.forEach(s => {
        const opt = document.createElement("option");
        opt.value = s;
        opt.textContent = s;
        select.appendChild(opt);
    });
    select.value = previous;
}

async function loadReadings() {
    const url = currentSensor
        ? apiUrl(`/api/readings?limit=100&sensorID=${encodeURIComponent(currentSensor)}`)
        : apiUrl("/api/readings?limit=100");
    const res = await fetch(url);
    if (!res.ok) return;
    const readings = await res.json();

    buildChart(readings);
    buildMap(readings);
    buildTable(readings);

    if (readings.length > 0) {
        const latest = readings[readings.length - 1];
        if (lastIndice !== null && latest.indice !== lastIndice) {
            pulseGauge();
        }
        lastIndice = latest.indice;
    }
}

async function refreshAll() {
    await Promise.all([loadStats(), loadReadings()]);
}

document.getElementById("sensorSelect").addEventListener("change", (e) => {
    currentSensor = e.target.value;
    loadReadings();
});

loadSensores();
refreshAll();
setInterval(refreshAll, POLL_MS);
