/* ── MONITORING DASHBOARD (global functions) ── */
function getDashboardStats() {
    const payouts = JSON.parse(localStorage.getItem('kavach_payouts') || '[]');
    const today = new Date().toDateString();
    const todayPayouts = payouts.filter(p => new Date(p.timestamp).toDateString() === today);
    const approved = payouts.filter(p => p.status === 'approved').length;
    const pending = payouts.filter(p => p.status === 'pending').length;
    const rejected = payouts.filter(p => p.status === 'rejected').length;
    const avgScore = payouts.length ? Math.round(payouts.reduce((sum, p) => sum + p.trustScore, 0) / payouts.length) : 0;
    const activeAlerts = Math.random() > 0.8 ? 1 : 0;
    return { payoutsToday: todayPayouts.length, avgTrustScore: avgScore, pending, approved, rejected, activeAlerts };
}

function updateDashboard() {
    const stats = getDashboardStats();
    console.log('Dashboard stats:', stats);
    const payoutsTodayEl  = document.getElementById('payouts-today');
    const avgScoreEl      = document.getElementById('avg-trust-score');
    const pendingEl       = document.getElementById('pending-count');
    const approvedEl      = document.getElementById('approved-count');
    const rejectedEl      = document.getElementById('rejected-count');
    const activeAlertsEl  = document.getElementById('active-alerts');
    const lastUpdateEl    = document.getElementById('last-update');
    if (payoutsTodayEl)  payoutsTodayEl.innerText  = stats.payoutsToday;
    if (avgScoreEl)      avgScoreEl.innerText       = stats.avgTrustScore;
    if (pendingEl)       pendingEl.innerText        = stats.pending;
    if (approvedEl)      approvedEl.innerText       = stats.approved;
    if (rejectedEl)      rejectedEl.innerText       = stats.rejected;
    if (activeAlertsEl)  activeAlertsEl.innerText   = stats.activeAlerts;
    if (lastUpdateEl)    lastUpdateEl.innerText     = 'Last update: ' + new Date().toLocaleTimeString();
}

/* ── SIMULATION ── */
var simRunning = false, simDone = false;

function startSim() {
    if (simRunning) return;
    if (simDone) { resetSim(); return; }
    simRunning = true;
    document.getElementById('sim-btn').textContent = 'Running...';
    document.getElementById('sim-btn').disabled = true;

    var steps = [
        { id: 'step-1', delay: 0,    label: 'IMD API: red alert received...' },
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
    document.getElementById('map-label').style.color = '#FF5A5F';
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

        document.getElementById('notif-amount').style.display   = 'block';
        document.getElementById('blockchain-entry').style.display = 'block';
        document.getElementById('sim-status').textContent       = '✓ Complete — 7.2s elapsed';
        document.getElementById('sim-status').style.color       = '#16a34a';
        document.getElementById('prog-label').textContent       = 'Rajan has been paid. Ledger updated.';

        const payoutEvent = {
            timestamp:  new Date().toISOString(),
            trustScore: 88,
            status:     'approved',
            amount:     400
        };
        let payouts = JSON.parse(localStorage.getItem('kavach_payouts') || '[]');
        payouts.push(payoutEvent);
        localStorage.setItem('kavach_payouts', JSON.stringify(payouts));
        console.log('Payout stored. Total payouts:', payouts.length);

        document.getElementById('sim-btn').textContent = 'Run again';
        document.getElementById('sim-btn').disabled    = false;
        simRunning = false;
        simDone    = true;

        updateDashboard();
    }, 7200);
}

function resetSim() {
    simDone = false;
    document.getElementById('sim-btn').textContent      = 'Trigger storm';
    document.getElementById('sim-status').textContent   = 'Ready';
    document.getElementById('sim-status').style.color   = '';
    document.getElementById('zone-ring').classList.remove('active');
    document.getElementById('rider-dot').style.display  = 'none';
    document.getElementById('map-label').textContent    = 'Chennai grid · All zones nominal';
    document.getElementById('map-label').style.color    = '';
    document.getElementById('notif-box').classList.remove('visible');
    document.getElementById('notif-amount').style.display    = 'none';
    document.getElementById('blockchain-entry').style.display = 'none';
    document.getElementById('prog-bar').style.width     = '0%';
    document.getElementById('prog-label').textContent   = 'Press "Trigger storm" to start';
    [1, 2, 3, 4, 5, 6].forEach(function (n) {
        var el = document.getElementById('step-' + n);
        el.classList.remove('active', 'done');
        el.querySelector('.kv-step-dot').textContent = n;
    });
}

/* ── FRAUD DETECTION ── */
const fraudSliders = ["fs1", "fs2", "fs3", "fs4", "fs5", "fs6"].map(id => document.getElementById(id));

function fraudGetColor(s) {
    if (s < 45) return "#FF5A5F";
    if (s < 75) return "#FFD166";
    return "#4ade80";
}

function fraudUpdate() {
    const vals  = fraudSliders.map(s => +s.value);
    const score = Math.round(vals.reduce((a, b) => a + b, 0) / vals.length);
    const g   = document.getElementById("fd-gauge");
    const dec = document.getElementById("fd-dec");
    const exp = document.getElementById("fd-exp");

    g.innerText       = score;
    g.style.background = fraudGetColor(score);

    if (score < 45) {
        dec.innerText   = "Tier 3 — Payout paused. Human review queued.";
        dec.style.color = "#FF5A5F";
    } else if (score < 75) {
        dec.innerText   = "Tier 2 — Short hold. Verification requested.";
        dec.style.color = "#FFD166";
    } else {
        dec.innerText   = "Tier 1 — Auto-approved. UPI transfer initiated.";
        dec.style.color = "#4ade80";
    }

    const labels = ["GPS", "Motion", "Pressure", "Cell Tower", "Work History", "Order Status"];
    let pairs = vals.map((v, i) => ({ v, label: labels[i] }));
    pairs.sort((a, b) => b.v - a.v);
    exp.innerText = "Strongest signals: " + pairs.slice(0, 2).map(p => p.label).join(", ");

    if (scoreChart) {
        scoreChart.data.datasets[0].data = [score, 100 - score];
        scoreChart.update();
    }
}

function fdSet(arr) {
    fraudSliders.forEach((s, i) => s.value = arr[i]);
    fraudUpdate();
}

fraudSliders.forEach(s => s.addEventListener("input", fraudUpdate));

/* ── CHART.JS ── */
let scoreChart = null;

function initScoreChart() {
    const ctx = document.getElementById('scoreChart');
    if (!ctx) return;
    scoreChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Trust Score', 'Remaining'],
            datasets: [{
                data:            [50, 50],
                backgroundColor: ['#4ade80', '#E0E0E0'],
                borderWidth:     0,
                cutout:          '70%'
            }]
        },
        options: { plugins: { legend: { display: false } } }
    });
}

/* ── INITIALIZATION ── */
document.addEventListener("DOMContentLoaded", function () {
    initScoreChart();
    fraudUpdate();
    updateDashboard();
    setInterval(updateDashboard, 5000);
});

/* ── FIX: expose all functions to global window scope ── */
window.updateDashboard  = updateDashboard;
window.getDashboardStats = getDashboardStats;
window.startSim         = startSim;
window.resetSim         = resetSim;
window.fraudUpdate      = fraudUpdate;
window.fdSet            = fdSet;
window.initScoreChart   = initScoreChart;