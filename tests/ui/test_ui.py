import os
import pytest
from playwright.sync_api import sync_playwright

@pytest.mark.skip("Playwright browsers not installed")
def test_dashboard_load():
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        page = browser.new_page()
        page.goto('http://localhost:8000/')
        assert 'NEO Watcher' in page.title()
        browser.close()
