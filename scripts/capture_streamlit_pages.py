"""Capture the real Streamlit pages for the read-only HTML stakeholder pack."""
from __future__ import annotations

import asyncio
from pathlib import Path

from playwright.async_api import async_playwright

BASE = 'http://localhost:8501'
OUT = Path('docs/app_snapshots')
PAGES = [
    ('OpenRouter execution', 'OpenRouter_Execution', '01_openrouter_execution.png'),
    ('Executive dashboard', 'Executive_Dashboard', '02_executive_dashboard.png'),
    ('Prompt bank explorer', 'Prompt_Bank_Explorer', '03_prompt_bank_explorer.png'),
    ('Audience journey simulator', 'Audience_Journey_Simulator', '04_audience_journey_simulator.png'),
    ('Visibility analysis', 'Visibility_Analysis', '05_visibility_analysis.png'),
    ('Competitor analysis', 'Competitor_Analysis', '06_competitor_analysis.png'),
    ('Recommendations', 'Recommendations', '07_recommendations.png'),
]


async def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            executable_path=r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
            args=['--disable-gpu'],
        )
        page = await browser.new_page(viewport={'width': 1600, 'height': 1200}, device_scale_factor=1)
        for label, slug, filename in PAGES:
            await page.goto(f'{BASE}/{slug}', wait_until='domcontentloaded', timeout=90000)
            await page.wait_for_timeout(30000)
            await page.screenshot(path=str(OUT / filename), full_page=True)
            print(f'Captured {label}: {filename}', flush=True)
        await browser.close()


if __name__ == '__main__':
    asyncio.run(main())
