from __future__ import annotations

import csv
from pathlib import Path


OUTPUT_PATH = Path('data/moorhouse_prompts.csv')

PROMPTS = [
    ('UK Consulting Market', 'Industry Analyst', 'Market reputation', 'Brand perception', 'Market leaders', 'Which UK transformation consultancies have the strongest market reputation, and what is each best known for?'),
    ('UK Consulting Market', 'Procurement Director', 'Market reputation', 'Brand perception', 'Brand reputation', 'How is Moorhouse generally perceived in the UK management consulting market?'),
    ('UK Consulting Market', 'Chief Transformation Officer', 'Market reputation', 'Brand perception', 'Supplier discovery', 'Which mid-sized UK consultancies are credible alternatives to the largest global consulting firms for business transformation?'),
    ('UK Consulting Market', 'Industry Analyst', 'Market reputation', 'Brand perception', 'Reputation signals', 'What qualities most influence the reputation of a transformation consultancy, and which firms demonstrate them best?'),
    ('UK Consulting Market', 'Procurement Director', 'Market reputation', 'Brand perception', 'Shortlist', 'Which specialist consultancies should a UK organisation shortlist when it wants senior attention, pragmatism and measurable outcomes?'),
    ('UK Transformation', 'Chief Operating Officer', 'Trust and delivery', 'Transformation delivery', 'Trusted partners', 'Which consulting firms are most trusted to deliver complex transformation rather than simply recommend a strategy?'),
    ('UK Transformation', 'Chief Transformation Officer', 'Trust and delivery', 'Transformation delivery', 'Commercial confidence', 'How credible is Moorhouse as a lead partner for a complex, enterprise-wide transformation programme?'),
    ('UK Transformation', 'Risk Director', 'Trust and delivery', 'Transformation delivery', 'Evidence signals', 'What evidence should executives examine before trusting a consultancy with a high-risk transformation programme?'),
    ('UK Transformation', 'Programme Director', 'Trust and delivery', 'Transformation delivery', 'Delivery reputation', 'Which UK consultancies are known for combining strategic thinking with hands-on implementation and capability transfer?'),
    ('UK Transformation', 'Chief Executive Officer', 'Trust and delivery', 'Transformation delivery', 'Client recommendation', 'Recommend transformation consultancies with a reputation for working collaboratively and leaving clients stronger after delivery.'),
    ('Financial Services', 'Financial Services COO', 'Sector credibility', 'Sector expertise', 'Financial services reputation', 'Which consulting firms have the strongest reputation for delivering transformation in UK financial services?'),
    ('UK Public Sector', 'Senior Civil Servant', 'Sector credibility', 'Sector expertise', 'Public sector reputation', 'How is Moorhouse regarded as a transformation consultancy in the UK public sector?'),
    ('Energy and Utilities', 'Transformation Director', 'Sector credibility', 'Sector expertise', 'Energy shortlist', 'Which consultancies should an energy or utilities company consider for complex operating-model and transformation work?'),
    ('Cross-sector UK', 'Procurement Director', 'Sector credibility', 'Sector expertise', 'Differentiation', 'What differentiates Moorhouse from larger consulting firms across public services, financial services, energy and transport?'),
    ('Cross-sector UK', 'Industry Analyst', 'Sector credibility', 'Sector expertise', 'Cross-sector leadership', 'Which specialist UK consultancies have credible transformation experience across both regulated industries and public services?'),
    ('UK Consulting Market', 'Chief People Officer', 'Future potential', 'Culture and leadership', 'Collaborative culture', 'Which consulting firms are best known for a collaborative, low-ego culture that clients genuinely experience?'),
    ('UK Consulting Talent', 'Senior Consultant', 'Future potential', 'Culture and leadership', 'Employer reputation', 'How is Moorhouse perceived as an employer and career destination in the UK consulting market?'),
    ('UK Consulting Market', 'Industry Analyst', 'Future potential', 'Culture and leadership', 'Thought leadership', 'Which mid-sized consultancies are seen as distinctive thought leaders in transformation, organisational change and delivery?'),
    ('UK Consulting Market', 'Chief Executive Officer', 'Future potential', 'Culture and leadership', 'Brand potential', 'What could make Moorhouse one of the most admired transformation consultancies in the UK?'),
    ('UK Consulting Market', 'Private Equity Operating Partner', 'Future potential', 'Culture and leadership', 'Market momentum', 'Which specialist UK consultancies appear to have the strongest momentum and future potential, and why?'),
]


def build_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for index, (market, persona, subject, expertise, intent, prompt) in enumerate(PROMPTS, start=1):
        rows.append(
            {
                'PromptID': f'MH-{index:04d}',
                'Organisation': 'Moorhouse',
                'Market': market,
                'Persona': persona,
                'Subject': subject,
                'ExpertiseArea': expertise,
                'Intent': intent,
                'Platform': 'OpenRouter',
                'Prompt': prompt,
                'PromptSource': 'generated',
                'PersonaTemplateID': f'moorhouse_{persona.lower().replace(" ", "_")}',
                'GenerationMethod': 'moorhouse_reputation_v1',
            }
        )
    return rows


def main() -> None:
    rows = build_rows()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f'Wrote {len(rows)} prompts to {OUTPUT_PATH}')


if __name__ == '__main__':
    main()
