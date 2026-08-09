"""Create static, presentation-ready wireframes for the Streamlit narrative."""
from pathlib import Path
from textwrap import wrap

from PIL import Image, ImageDraw, ImageFont


OUT = Path('docs/wireframes')
OUT.mkdir(parents=True, exist_ok=True)
W, H = 1600, 1000
PURPLE, TEAL, INK, MUTED, PANEL, BG = '#5B2C83', '#00AB8E', '#25232A', '#6D6875', '#FFFFFF', '#F5F3F7'

FONT = 'C:/Windows/Fonts/arial.ttf'
BOLD = 'C:/Windows/Fonts/arialbd.ttf'


def font(size, bold=False):
    path = BOLD if bold else FONT
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def text(draw, xy, value, size=22, colour=INK, bold=False):
    draw.text(xy, value, fill=colour, font=font(size, bold))


def paragraph(draw, xy, value, width=66, size=21, colour=INK, leading=7):
    x, y = xy
    lines = []
    for para in value.split('\n'):
        lines.extend(wrap(para, width=width) or [''])
    f = font(size)
    for line in lines:
        draw.text((x, y), line, fill=colour, font=f)
        y += size + leading
    return y


def rounded(draw, box, fill=PANEL, outline='#E0DDE5', radius=18, width=2):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def base(title, eyebrow, subtitle, narrative):
    im = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 92), fill=PURPLE)
    text(d, (48, 22), 'Moorhouse · AI reputation intelligence', 24, '#FFFFFF', True)
    text(d, (1220, 28), 'UoS Prompt Library · OpenRouter run', 18, '#EBDFF3')
    d.rectangle((0, 92, 290, H), fill='#2F2638')
    nav = ['OpenRouter execution', 'Executive dashboard', 'Prompt bank explorer', 'Audience journey simulator', 'Visibility analysis', 'Competitor analysis', 'Recommendations']
    for i, item in enumerate(nav):
        y = 135 + i * 55
        active = item.lower() in title.lower()
        if active:
            d.rounded_rectangle((22, y - 10, 268, y + 35), radius=10, fill=TEAL)
        text(d, (40, y), item, 17, '#FFFFFF' if active else '#D7CEDD', active)
    text(d, (340, 130), eyebrow.upper(), 15, PURPLE, True)
    text(d, (340, 160), title, 38, INK, True)
    text(d, (340, 215), subtitle, 21, MUTED)
    rounded(d, (340, 270, 1550, 370), fill='#EFE8F4', outline='#D7C7E0')
    text(d, (370, 292), 'Narrative', 20, PURPLE, True)
    paragraph(d, (510, 290), narrative, width=100, size=20, colour=INK)
    return im, d


def card(d, x, y, w, h, label, value, accent=PURPLE):
    rounded(d, (x, y, x + w, y + h))
    d.rectangle((x, y, x + 8, y + h), fill=accent)
    text(d, (x + 26, y + 18), label, 17, MUTED)
    text(d, (x + 26, y + 53), value, 31, INK, True)


def chart(d, box, title, bars, accent=PURPLE):
    x1, y1, x2, y2 = box
    rounded(d, box)
    text(d, (x1 + 22, y1 + 18), title, 20, INK, True)
    base_y = y2 - 55
    maxv = max(v for _, v in bars) or 1
    bw = (x2 - x1 - 70) / len(bars)
    for i, (label, value) in enumerate(bars):
        left = x1 + 35 + i * bw
        top = base_y - (value / maxv) * 170
        d.rounded_rectangle((left, top, left + bw * .58, base_y), radius=7, fill=accent)
        text(d, (left, base_y + 12), label, 14, MUTED)
        text(d, (left, top - 27), str(value), 14, INK, True)


def save(name, im):
    im.save(OUT / f'{name}.png', quality=95)


def main():
    im, d = base('OpenRouter execution', 'Execution control', 'Operational capture and audit view', 'The UoS prompt library is the source of truth. This page confirms what was run, which models were assigned, and how many outputs were captured before analysis begins.')
    card(d, 340, 420, 270, 110, 'Total prompts', '1,016')
    card(d, 635, 420, 270, 110, 'Generated prompts', '1,016', TEAL)
    card(d, 930, 420, 270, 110, 'Models used', '5')
    card(d, 1225, 420, 270, 110, 'Captured outputs', '2,664', TEAL)
    rounded(d, (340, 575, 1550, 900)); text(d, (370, 600), 'Captured output table', 24, INK, True)
    headers = ['Prompt ID', 'Model', 'Market', 'Prompt', 'Southampton visible']
    for i, h in enumerate(headers): text(d, (370 + [0, 210, 520, 710, 1340][i], 650), h, 16, PURPLE, True)
    for r in range(6):
        y = 705 + r * 30; d.line((370, y - 8, 1510, y - 8), fill='#E8E3EC'); text(d, (370, y), f'UOS-{r+1:04d}', 15, INK); text(d, (580, y), ['GPT-4.1 Mini', 'Gemini Flash', 'Claude Haiku'][r % 3], 15, INK); text(d, (890, y), ['UK', 'India', 'UAE'][r % 3], 15, INK); text(d, (1080, y), 'How does the university...', 15, MUTED); text(d, (1410, y), 'Yes' if r % 2 else 'No', 15, TEAL if r % 2 else MUTED)
    save('01_openrouter_execution', im)

    im, d = base('Executive dashboard', 'Executive view', 'Headline metrics and visibility patterns', 'Start here: establish the overall visibility position, then compare markets and subjects. The competitor index and organic mentions by model explain who is being surfaced without naming Southampton in the prompt.')
    for i, (label, value, colour) in enumerate([('Overall visibility', '— / 100', PURPLE), ('Reputation score', '— / 100', TEAL), ('Prompts in view', '1,016', PURPLE), ('Southampton mentions', 'Captured', TEAL), ('Average rank', '—', PURPLE)]): card(d, 340 + i * 245, 420, 225, 110, label, value, colour)
    chart(d, (340, 575, 920, 890), 'Visibility by market', [('UK', 78), ('HK', 62), ('UAE', 57), ('China', 49), ('India', 44)], PURPLE)
    chart(d, (950, 575, 1550, 890), 'Visibility by subject', [('General', 72), ('Med', 61), ('CS', 54), ('Eng', 48), ('Bus', 43)], PURPLE)
    save('02_executive_dashboard', im)

    im, d = base('Prompt bank explorer', 'Prompt intelligence', 'Inspect the questions that drive the analysis', 'Use this page to validate the underlying question set. Filters reveal whether a result is driven by market, persona, subject, expertise area, or prompt type before interpreting model performance.')
    rounded(d, (340, 420, 1550, 525)); text(d, (370, 455), 'Filters', 19, PURPLE, True)
    for i, label in enumerate(['Market: All', 'Persona: All', 'Subject: All', 'Expertise: All', 'Prompt mode: Organic']): rounded(d, (500 + i * 205, 445, 680 + i * 205, 495), fill='#FAF9FB'); text(d, (520 + i * 205, 459), label, 15, INK)
    rounded(d, (340, 560, 1550, 900)); text(d, (370, 585), '1,016 prompt records', 24, INK, True)
    for r in range(7):
        y = 645 + r * 34; d.line((370, y - 8, 1510, y - 8), fill='#E8E3EC'); text(d, (370, y), f'UOS-{r+1:04d}', 15, PURPLE, True); text(d, (500, y), ['UK', 'Hong Kong', 'UAE', 'China', 'India'][r % 5], 15, INK); text(d, (690, y), ['General', 'Medicine', 'Engineering'][r % 3], 15, INK); text(d, (930, y), 'Prospective student', 15, INK); text(d, (1220, y), 'How does the university...', 15, MUTED)
    save('03_prompt_bank_explorer', im)

    im, d = base('Audience journey simulator', 'Journey simulation', 'Follow one audience pathway from question to recommendation', 'Move from a selected market and persona to the exact prompts and model responses that shape the journey. The narrative summary turns a filtered slice into an audience-ready story.')
    rounded(d, (340, 420, 1550, 520)); text(d, (370, 455), 'Journey controls', 20, PURPLE, True); text(d, (620, 455), 'Market  UK', 17, INK); text(d, (850, 455), 'Persona  Prospective student', 17, INK); text(d, (1200, 455), 'Subject  General', 17, INK)
    for i, (label, value) in enumerate([('Prompts', '—'), ('Responses', '—'), ('Mentions', '—'), ('Avg rank', '—')]): card(d, 340 + i * 300, 560, 270, 100, label, value, TEAL if i == 2 else PURPLE)
    rounded(d, (340, 700, 920, 900)); text(d, (370, 730), 'Narrative summary', 23, INK, True); paragraph(d, (370, 780), 'What this audience asks, what models answer, and where Southampton appears in the decision journey.', width=47, size=21)
    rounded(d, (950, 700, 1550, 900)); text(d, (980, 730), 'Relevant prompts and results', 23, INK, True); paragraph(d, (980, 780), 'Prompt → model response → visibility signal → implication', width=40, size=21)
    save('04_audience_journey_simulator', im)

    im, d = base('Visibility analysis', 'Visibility diagnostics', 'Locate strengths and gaps by segment', 'This is the diagnostic layer: the heatmap shows where visibility is strongest or weakest, while average rank by subject and model identifies which platform/model combinations need attention.')
    chart(d, (340, 420, 1050, 900), 'Visibility heatmap · market × subject', [('UK', 78), ('HK', 62), ('UAE', 57), ('China', 49), ('India', 44)], PURPLE)
    rounded(d, (1080, 420, 1550, 900)); text(d, (1110, 450), 'Legend', 21, INK, True); text(d, (1110, 510), 'Higher score', 17, MUTED); d.rectangle((1110, 550, 1480, 595), fill=PURPLE); text(d, (1110, 640), 'Blank', 17, MUTED); d.rectangle((1110, 680, 1480, 725), fill='#EAE7ED'); text(d, (1110, 770), 'Zero', 17, MUTED); text(d, (1110, 805), 'No qualifying mention/rank', 16, INK)
    save('05_visibility_analysis', im)

    im, d = base('Competitor analysis', 'Competitor diagnostics', 'Understand who is mentioned organically', 'Answer the strategic question: when people ask broad university questions, who gets mentioned? Organic counts exclude prompts that explicitly name an institution, so Southampton is compared fairly against competitors.')
    chart(d, (340, 420, 950, 900), 'Organic mentions by model', [('GPT', 74), ('Gemini', 68), ('Claude', 55), ('DeepSeek', 42), ('Sonar', 39)], PURPLE)
    chart(d, (990, 420, 1550, 650), 'Competitors by subject', [('Oxford', 92), ('Cambridge', 86), ('Imperial', 70), ('Durham', 48)], PURPLE)
    chart(d, (990, 690, 1550, 900), 'Competitors by market', [('UK', 95), ('HK', 72), ('UAE', 58), ('India', 45)], TEAL)
    save('06_competitor_analysis', im)

    im, d = base('Recommendations', 'Action planning', 'Turn evidence into prioritised action', 'Finish with the action plan. Recommendations connect the evidence to a specific market, subject, model or audience, with a priority, timing and measurable next step.')
    rounded(d, (340, 420, 1550, 670)); text(d, (370, 450), 'Action plan', 24, INK, True)
    for r, row in enumerate([('High', 'Strengthen organic visibility for priority subjects', 'UK · Medicine · 30 days'), ('Medium', 'Improve evidence and citation coverage in model responses', 'All markets · 60 days'), ('Medium', 'Create audience-specific content for weak journey stages', 'India · Prospective students · 90 days')]):
        y = 520 + r * 45; d.line((370, y - 10, 1510, y - 10), fill='#E8E3EC'); text(d, (370, y), row[0], 16, '#B04A4A' if r == 0 else PURPLE, True); text(d, (500, y), row[1], 17, INK); text(d, (1230, y), row[2], 15, MUTED)
    chart(d, (340, 720, 930, 900), 'Recommendation priority', [('High', 1), ('Medium', 2), ('Low', 0)], TEAL)
    rounded(d, (980, 720, 1550, 900)); text(d, (1010, 750), 'Close the loop', 22, INK, True); paragraph(d, (1010, 805), 'Re-run the same prompt library after implementation and compare visibility, rank and organic mention rates.', width=38, size=20)
    save('07_recommendations', im)

    # A compact flow image for the report cover.
    im = Image.new('RGB', (W, 420), BG); d = ImageDraw.Draw(im); text(d, (60, 45), 'The narrative flow', 40, INK, True); text(d, (60, 105), 'From captured evidence to an actionable reputation plan', 22, MUTED)
    labels = [('01', 'Capture', 'What was run?'), ('02', 'Orient', 'What is the headline position?'), ('03', 'Diagnose', 'Where are the gaps?'), ('04', 'Explain', 'Who is mentioned and why?'), ('05', 'Act', 'What should change next?')]
    for i, (num, head, desc) in enumerate(labels):
        x = 70 + i * 300; rounded(d, (x, 190, x + 240, 330), fill=PANEL, outline='#D7C7E0'); text(d, (x + 22, 210), num, 18, TEAL, True); text(d, (x + 22, 245), head, 24, PURPLE, True); text(d, (x + 22, 285), desc, 16, INK)
        if i < len(labels) - 1: text(d, (x + 250, 245), '→', 32, TEAL, True)
    save('00_narrative_flow', im)


if __name__ == '__main__':
    main()
