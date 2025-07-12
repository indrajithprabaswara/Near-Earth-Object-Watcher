const { test, expect } = require('@playwright/test');
const path = require('path');

test('subscribers panel add and delete', async ({ page }) => {
  const filePath = path.resolve(__dirname, '../../static/index.html');

  await page.addInitScript(() => {
    window.__subs = [{ id: 1, url: 'http://a.com' }];
    const origFetch = window.fetch.bind(window);
    window.fetch = (input, init = {}) => {
      const url = typeof input === 'string' ? input : input.url;
      const method = (init.method || 'GET').toUpperCase();
      if (url.endsWith('/subscribers') && method === 'GET') {
        return Promise.resolve(new Response(JSON.stringify(window.__subs), { status: 200 }));
      }
      if (url.endsWith('/subscribe') && method === 'POST') {
        const body = JSON.parse(init.body || '{}');
        const rec = { id: 2, url: body.url };
        window.__subs.push(rec);
        return Promise.resolve(new Response(JSON.stringify(rec), { status: 201 }));
      }
      const delMatch = url.match(/\/subscribers\/(\d+)/);
      if (delMatch && method === 'DELETE') {
        window.__subs = window.__subs.filter(s => s.id !== Number(delMatch[1]));
        return Promise.resolve(new Response('', { status: 204 }));
      }
      return origFetch(input, init);
    };
  });

  await page.goto('file://' + filePath);

  await page.waitForSelector('#subscriberList li');

  await page.fill('#newUrl', 'http://b.com');
  await page.click('#addSub');

  await page.waitForFunction(() => document.querySelectorAll('#subscriberList li').length === 2);

  const newLi = page.locator('#subscriberList li', { hasText: 'http://b.com' });
  await expect(newLi).toBeVisible();

  await newLi.locator('button.del').click();
  await expect(newLi).toBeHidden();
});
