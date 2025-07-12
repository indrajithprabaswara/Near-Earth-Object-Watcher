const { test, expect } = require('@playwright/test');
const path = require('path');

const sampleData = [
  {
    id: 1,
    neo_id: '1',
    name: 'Test1',
    close_approach_date: '2020-01-01',
    diameter_km: 1,
    velocity_km_s: 1,
    miss_distance_au: 0.5,
    hazardous: false
  }
];

test('chart renders and updates', async ({ page }) => {
  const filePath = path.resolve(__dirname, '../../static/index.html');

  await page.route('**/neos', route => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(sampleData)
    });
  });

  await page.addInitScript(() => {
    class FakeEventSource {
      constructor(url) { FakeEventSource.instance = this; this.url = url; }
      close() {}
    }
    window.EventSource = FakeEventSource;
  });

  await page.goto('file://' + filePath);

  await expect(page.locator('#neoChart')).toBeVisible();

  await page.waitForFunction(() => window.neoChart && window.neoChart.data.datasets.length > 1);

  const labels = await page.evaluate(() => window.neoChart.data.datasets.map(d => d.label));
  expect(labels).toContain('Count');
  expect(labels).toContain('Min Distance (AU)');

  await page.evaluate(() => {
    const neo = {
      id: 2,
      neo_id: '2',
      name: 'Test2',
      close_approach_date: '2020-01-02',
      diameter_km: 1,
      velocity_km_s: 1,
      miss_distance_au: 0.4,
      hazardous: false
    };
    window.EventSource.instance.onmessage({ data: JSON.stringify(neo) });
  });

  await page.waitForFunction(() => window.neoChart.data.labels.includes('2020-01-02'));
});
