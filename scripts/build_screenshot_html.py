"""Build a single HTML pack from screenshots of the real Streamlit pages."""
from __future__ import annotations

import base64
from pathlib import Path
from html import escape

ROOT = Path(__file__).resolve().parents[1]
IMAGE_DIR = ROOT / 'docs' / 'app_snapshots'
OUT = ROOT / 'docs' / 'static_app_replica.html'
PAGES = [
    ('execution', 'OpenRouter execution', '01_openrouter_execution.png'),
    ('executive', 'Executive dashboard', '02_executive_dashboard.png'),
    ('prompts', 'Prompt bank explorer', '03_prompt_bank_explorer.png'),
    ('journey', 'Audience journey simulator', '04_audience_journey_simulator.png'),
    ('visibility', 'Visibility analysis', '05_visibility_analysis.png'),
    ('competitors', 'Competitor analysis', '06_competitor_analysis.png'),
    ('recommendations', 'Recommendations', '07_recommendations.png'),
]


def image_data(path: Path) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode('ascii')
    return f'data:image/png;base64,{encoded}'


def main() -> None:
    nav = ''.join(f'<a href="#{anchor}">{escape(title)}</a>' for anchor, title, _ in PAGES)
    sections = []
    for anchor, title, filename in PAGES:
        path = IMAGE_DIR / filename
        sections.append(
            f'<section id="{anchor}"><h2>{escape(title)}</h2>'
            f'<img src="{image_data(path)}" alt="Exact Streamlit page: {escape(title)}"></section>'
        )
    html = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI Reputation Intelligence · Exact Streamlit page captures</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;background:#f5f3f7;color:#25232a;font-family:Arial,sans-serif}}header{{position:sticky;top:0;z-index:3;background:#5b2c83;color:#fff;padding:24px 34px;display:flex;justify-content:space-between;align-items:center}}header h1{{font-size:24px;margin:0}}header span{{color:#eadff2}}.layout{{display:flex;max-width:1900px;margin:auto}}nav{{position:sticky;top:86px;height:calc(100vh - 86px);width:240px;background:#302638;padding:24px 14px;flex:0 0 240px}}nav a{{display:block;color:#ddd4e4;text-decoration:none;padding:12px 14px;border-radius:8px;margin:4px 0}}nav a:hover{{background:#00ab8e;color:white}}main{{padding:28px 34px 80px;width:100%}}section{{margin:0 0 64px;scroll-margin-top:110px}}section h2{{color:#5b2c83;font-size:28px;margin:0 0 14px}}section img{{display:block;width:100%;height:auto;background:white;border:1px solid #ded9e3;box-shadow:0 6px 20px #30263818}}.note{{background:#efe8f4;border:1px solid #d7c7e0;padding:16px 20px;border-radius:12px;margin-bottom:28px}}footer{{color:#6d6875;padding:12px 0 40px}}@media(max-width:900px){{nav{{display:none}}main{{padding:20px 12px}}header span{{display:none}}}}@media print{{header{{position:static}}nav{{display:none}}main{{padding:0}}section{{break-inside:avoid}}section img{{box-shadow:none}}}}
</style></head><body><header><h1>Moorhouse · AI reputation intelligence</h1><span>Exact Streamlit page captures · UoS Prompt Library</span></header><div class="layout"><nav>{nav}</nav><main><div class="note"><strong>Read-only visual snapshot:</strong> each image below is captured directly from the running Streamlit application at 1,600px width, using the current UoS Prompt Library results. The visuals, metrics, filters, charts, and page layout are the actual app—not a redraw.</div>{''.join(sections)}<footer>Use Print → Save as PDF to create a report-ready pack. This snapshot does not make API calls or provide interactive filters.</footer></main></div></body></html>'''
    OUT.write_text(html, encoding='utf-8')
    print(f'Wrote {OUT}')


if __name__ == '__main__':
    main()
