/* ── SIMULATION ── */
var simRunning = false, simDone = false;

function startSim() {
  if (simRunning) return;
  if (simDone) { resetSim(); return; }

  simRunning = true;
  document.getElementById('sim-btn').textContent = 'Running...';
  document.getElementById('sim-btn').disabled = true;

  var steps = [
    { id: 'step-1', delay: 0, label: 'IMD API: red alert received...' },
    { id: 'step-2', delay: 1200, label: 'Zone grid: 14 cells activated' },
    { id: 'step-3', delay: 2200, label: 'Eligibility engine: 3 checks passed' },
    { id: 'step-4', delay: 3400, label: 'ML scoring: 6 signals evaluated' },
    { id: 'step-5', delay: 5200, label: 'UPI transfer: ₹400 → Rajan' },
    { id: 'step-6', delay: 6400, label: 'Ledger entry: written to Hyperledger' },
  ];

  var totalDuration = 7200;

  document.getElementById('zone-ring').classList.add('active');
  document.getElementById('rider-dot').style.display = 'block';
  document.getElementById('map-label').textContent = 'RED ALERT: Coastal Chennai zones active';
  document.getElementById('map-label').style.color = '#dc2626';
  document.getElementById('sim-status').textContent = 'Running...';
  document.getElementById('notif-box').classList.add('visible');

  var startTime = Date.now();
  var progInterval = setInterval(function () {
    var elapsed = Date.now() - startTime;
    var pct = Math.min(100, Math.round(elapsed / totalDuration * 100));
    document.getElementById('prog-bar').style.width = pct + '%';
    if (pct >= 100) clearInterval(progInterval);
  }, 50);

  steps.forEach(function (s, i) {
    setTimeout(function () {
      if (i > 0) {
        var prev = document.getElementById(steps[i - 1].id);
        prev.classList.remove('active');
        prev.classList.add('done');
        prev.querySelector('.kv-step-dot').textContent = '✓';
      }
      document.getElementById(s.id).classList.add('active');
      document.getElementById('prog-label').textContent = s.label;
    }, s.delay);
  });

  setTimeout(function () {
    var last = document.getElementById('step-6');
    last.classList.remove('active');
    last.classList.add('done');
    last.querySelector('.kv-step-dot').textContent = '✓';

    document.getElementById('notif-amount').style.display = 'block';
    document.getElementById('blockchain-entry').style.display = 'block';
    document.getElementById('sim-status').textContent = '✓ Complete — 7.2s elapsed';
    document.getElementById('sim-status').style.color = '#16a34a';
    document.getElementById('prog-label').textContent = 'Rajan has been paid. Ledger updated.';
    document.getElementById('sim-btn').textContent = 'Run again';
    document.getElementById('sim-btn').disabled = false;
    simRunning = false;
    simDone = true;
  }, 7200);
}

function resetSim() {
  simDone = false;
  document.getElementById('sim-btn').textContent = 'Trigger storm';
  document.getElementById('sim-status').textContent = 'Ready';
  document.getElementById('sim-status').style.color = '';
}

/* ── FRAUD DETECTION ── */
const fraudSliders = ["fs1", "fs2", "fs3", "fs4", "fs5", "fs6"].map(id => document.getElementById(id));

function fraudGetColor(s) {
  if (s < 45) return "#dc2626";
  if (s < 75) return "#eab308";
  return "#16a34a";
}

/* 🔥 API CALL */
async function getFraudScore(signals) {
  const res = await fetch("http://127.0.0.1:8000/fraud-score", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(signals)
  });
  return await res.json();
}

/* 🔥 UPDATED FRAUD FUNCTION */
async function fraudUpdate() {
  const vals = fraudSliders.map(s => +s.value);

  const signals = {
    gps_natural_travel: vals[0],
    accelerometer_active: vals[1],
    pressure_consistency: vals[2],
    cell_tower_match: vals[3],
    work_history_match: vals[4],
    no_active_order: vals[5]
  };

  const g = document.getElementById("fd-gauge");
  const dec = document.getElementById("fd-dec");
  const exp = document.getElementById("fd-exp");

  // 🔄 Loading state (nice UX)
  g.innerText = "...";

  let result;
  try {
    result = await getFraudScore(signals);
  } catch (e) {
    console.error("API error:", e);
    g.innerText = "Err";
    return;
  }

  const score = result.score;

  // 🎯 Update gauge
  g.innerText = score;
  g.style.background = fraudGetColor(score);

  // 🎯 Decision text (from backend)
  if (result.tier === "reject") {
    dec.innerText = "Tier 3 — Fraud detected. Payout blocked.";
    dec.style.color = "#dc2626";
  } else if (result.tier === "hold") {
    dec.innerText = "Tier 2 — Needs verification.";
    dec.style.color = "#eab308";
  } else {
    dec.innerText = "Tier 1 — Auto-approved.";
    dec.style.color = "#16a34a";
  }

  // 🧠 Explanation (based on strongest signals)
  const labels = [
    "GPS",
    "Motion",
    "Pressure",
    "Cell Tower",
    "Work History",
    "Order Status"
  ];

  let pairs = vals.map((v, i) => ({ v, label: labels[i] }));
  pairs.sort((a, b) => b.v - a.v);

  exp.innerText =
    "Strongest signals: " +
    pairs.slice(0, 2).map(p => p.label).join(", ");

  // 📊 Update chart if exists
  if (typeof scoreChart !== "undefined" && scoreChart) {
    scoreChart.data.datasets[0].data = [score, 100 - score];
    scoreChart.update();
  }
}
  const labels = ["GPS", "Motion", "Pressure", "Cell", "History", "Order"];
  let pairs = vals.map((v, i) => ({ v, label: labels[i] }));
  pairs.sort((a, b) => b.v - a.v);
  exp.innerText = "Strongest signals: " + pairs.slice(0, 2).map(p => p.label).join(", ");

  if (scoreChart) {
    scoreChart.data.datasets[0].data = [score, 100 - score];
    scoreChart.update();
  }


fraudSliders.forEach(s => s.addEventListener("input", fraudUpdate));

/* 🔥 CHART.JS */
let scoreChart = null;

function initScoreChart() {
  const ctx = document.getElementById('scoreChart');
  if (!ctx) return;

  scoreChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Trust Score', 'Remaining'],
      datasets: [{
        data: [50, 50],
        backgroundColor: ['#16a34a', '#E0E0E0'],
        borderWidth: 0,
        cutout: '70%'
      }]
    },
    options: {
      plugins: { legend: { display: false } }
    }
  });
}

document.addEventListener("DOMContentLoaded", function () {
  initScoreChart();
  fraudUpdate();
});

