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

  const today = new Date().toISOString().slice(0,10);
  let todayNeos = [];
  try {
    todayNeos = await fetch(`/neos?start_date=${today}&end_date=${today}`).then(r => r.json());
  } catch {}

  const svg = d3.select('#dangerMap');
  const width = +svg.attr('width');
  const height = +svg.attr('height');
  const radiusFor = d => Math.max(2, Math.min(20, d.diameter_km * 10));

  const nodes = todayNeos.map(n => ({...n}));
  let circles = svg.selectAll('circle')
    .data(nodes)
    .enter()
    .append('circle')
    .attr('fill', d => d.hazardous ? 'red' : 'green')
    .attr('r', d => radiusFor(d));

  const simulation = d3.forceSimulation(nodes)
    .force('charge', d3.forceManyBody().strength(5))
    .force('center', d3.forceCenter(width/2, height/2))
    .force('collision', d3.forceCollide().radius(d => radiusFor(d)+2))
    .on('tick', () => {
      svg.selectAll('circle')
        .attr('cx', d => d.x)
        .attr('cy', d => d.y);
    });
  window.dangerSim = simulation;

  function addDangerNode(neo) {
    nodes.push(neo);
    circles = svg.selectAll('circle')
      .data(nodes);
    const enter = circles.enter().append('circle')
      .attr('fill', neo.hazardous ? 'red' : 'green')
      .attr('r', 0);
    anime({ targets: enter.nodes(), r: radiusFor(neo), duration: 500, easing: 'easeOutBack' });
    circles = enter.merge(circles);
    simulation.nodes(nodes);
    simulation.alpha(1).restart();
  }

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
      if (neo.close_approach_date === today) {
        addDangerNode({...neo});
      }
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
