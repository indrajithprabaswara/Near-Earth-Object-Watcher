const { test, expect } = require('@playwright/test');
const path = require('path');

test('test_dashboard_load', async ({ page }) => {
  const filePath = path.resolve(__dirname, '../../static/index.html');
  await page.goto('file://' + filePath);
  await expect(page).toHaveTitle(/NEO Watcher/);
});
