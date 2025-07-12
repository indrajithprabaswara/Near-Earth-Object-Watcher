// playwright.config.js
module.exports = {
  testDir: './tests/ui',
  use: { headless: true, actionTimeout: 0, navigationTimeout: 30000 },
};
