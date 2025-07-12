const { test, expect } = require('@playwright/test');
const path = require('path');

test('danger map renders and updates', async ({ page }) => {
  const filePath = path.resolve(__dirname, '../../static/index.html');
  const today = new Date().toISOString().slice(0,10);
  const sampleToday = [
    { id: 1, neo_id: '1', name: 'Now', close_approach_date: today, diameter_km: 1.5, velocity_km_s: 1, miss_distance_au: 0.01, hazardous: true }
  ];

  await page.route('**/neos?*', route => {
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(sampleToday) });
  });

  await page.addInitScript(() => {
    class FakeEventSource {
      constructor(url) { FakeEventSource.instance = this; this.url = url; }
      close() {}
      onmessage() {}
    }
    window.EventSource = FakeEventSource;
  });

  await page.goto('file://' + filePath);

  await page.waitForSelector('svg#dangerMap circle');
  const props = await page.evaluate(() => {
    const c = document.querySelector('svg#dangerMap circle');
    return { r: c.getAttribute('r'), fill: c.getAttribute('fill') };
  });
  expect(props.fill).toBe('red');
  expect(Number(props.r)).toBeCloseTo(15, 1);

  await page.evaluate(() => {
    const neo = { id: 2, neo_id: '2', name: 'Later', close_approach_date: new Date().toISOString().slice(0,10), diameter_km: 1, velocity_km_s: 1, miss_distance_au: 0.02, hazardous: false };
    window.EventSource.instance.onmessage({ data: JSON.stringify(neo) });
  });

  await page.waitForFunction(() => document.querySelectorAll('svg#dangerMap circle').length === 2);
});
