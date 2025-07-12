document.addEventListener('DOMContentLoaded', async () => {
  async function loadInitial() {
    try {
      const res = await fetch('/neos');
      if (!res.ok) throw new Error('bad');
      return await res.json();
    } catch (e) {
      return [];
    }
  }

  const data = await loadInitial();
  const stats = {};
  data.forEach(n => {
    const d = n.close_approach_date;
    if (!stats[d]) stats[d] = {count:0, min: Infinity};
    stats[d].count += 1;
    stats[d].min = Math.min(stats[d].min, n.miss_distance_au);
  });

  const labels = Object.keys(stats).sort();
  const countData = labels.map(d => stats[d].count);
  const minData = labels.map(d => stats[d].min);

  const ctx = document.getElementById('neoChart').getContext('2d');
  const neoChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        { label: 'Count', data: countData, borderColor: 'blue', backgroundColor: 'rgba(0,0,255,0.2)', yAxisID: 'y' },
        { label: 'Min Distance (AU)', data: minData, borderColor: 'red', backgroundColor: 'rgba(255,0,0,0.2)', yAxisID: 'y1' },
      ]
    },
    options: {
      interaction: { mode: 'index', intersect: false },
      scales: {
        y: { type: 'linear', position: 'left' },
        y1: { type: 'linear', position: 'right', grid: { drawOnChartArea: false } }
      }
    }
  });
  window.neoChart = neoChart;

  function update(neo) {
    const d = neo.close_approach_date;
    if (!stats[d]) {
      stats[d] = {count:0, min: Infinity};
    }
    stats[d].count += 1;
    stats[d].min = Math.min(stats[d].min, neo.miss_distance_au);
    const lbls = Object.keys(stats).sort();
    neoChart.data.labels = lbls;
    neoChart.data.datasets[0].data = lbls.map(k => stats[k].count);
    neoChart.data.datasets[1].data = lbls.map(k => stats[k].min);
    neoChart.update();
  }

  const evtSource = new EventSource('/stream/neos');
  evtSource.onmessage = e => {
    try {
      const neo = JSON.parse(e.data);
      update(neo);
    } catch {}
  };

  const form = document.getElementById('subForm');
  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const url = document.getElementById('subUrl').value;
      try {
        await fetch('/subscribe', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({url})});
      } catch {}
      document.getElementById('subUrl').value = '';
    });
  }
});
