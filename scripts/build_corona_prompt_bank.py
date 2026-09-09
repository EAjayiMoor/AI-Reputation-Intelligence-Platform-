from __future__ import annotations

import csv
from pathlib import Path


OUTPUT_PATH = Path('data/corona_energy_prompts.csv')

PROMPT_SETS = [
    {
        'subject': 'Overall Market Reputation',
        'expertise': 'Brand Perception',
        'questions': [
            ('Industry Analyst', 'UK Business Energy', 'Market Reputation', 'Which independent UK business energy suppliers have the strongest market reputation, and what is each known for?'),
            ('Procurement Director', 'UK Corporate', 'Brand Reputation', 'How is Corona Energy generally perceived in the UK business energy market?'),
            ('Energy Consultant', 'UK Business Energy', 'Reputation Signals', 'What qualities most influence the reputation of a commercial energy supplier, and which providers demonstrate them best?'),
            ('Chief Financial Officer', 'UK Corporate', 'Supplier Discovery', 'Which UK business energy suppliers are viewed as credible alternatives to the largest incumbent providers?'),
            ('Industry Analyst', 'UK Business Energy', 'Brand Associations', 'What positive and negative associations are most commonly connected with Corona Energy?'),
        ],
    },
    {
        'subject': 'Competitive Positioning',
        'expertise': 'Market Differentiation',
        'questions': [
            ('Procurement Director', 'UK Corporate', 'Competitive Benchmark', 'Which UK commercial energy suppliers stand out for combining competitive pricing with strong service?'),
            ('Industry Analyst', 'UK Business Energy', 'Competitive Position', 'How does Corona Energy compare with other independent business energy suppliers on reputation and market standing?'),
            ('Energy Manager', 'UK Multi-site Enterprises', 'Supplier Shortlist', 'Which energy suppliers are most likely to make a shortlist for a complex multi-site business portfolio, and why?'),
            ('Energy Consultant', 'UK Business Energy', 'Differentiation', 'What separates the most respected independent business energy suppliers from the rest of the market?'),
            ('Chief Financial Officer', 'UK Corporate', 'Reasons to Choose', 'What are the strongest reasons a large business might choose Corona Energy over a larger incumbent supplier?'),
        ],
    },
    {
        'subject': 'Trust and Credibility',
        'expertise': 'Buyer Confidence',
        'questions': [
            ('Procurement Director', 'UK Corporate', 'Trust', 'Which UK business energy suppliers are most trusted for transparent contracts and dependable delivery?'),
            ('Chief Financial Officer', 'UK Corporate', 'Commercial Confidence', 'How credible is Corona Energy as a long-term energy partner for a large UK organisation?'),
            ('Risk Director', 'UK Corporate', 'Risk Perception', 'What reputation signals should a risk team examine before appointing a business energy supplier?'),
            ('Energy Manager', 'UK Multi-site Enterprises', 'Reliability', 'Which suppliers are known for handling complex business energy requirements reliably?'),
            ('Procurement Director', 'UK Corporate', 'Objection Handling', 'What concerns might buyers have about choosing Corona Energy, and what evidence would address them?'),
        ],
    },
    {
        'subject': 'Customer Experience',
        'expertise': 'Service Reputation',
        'questions': [
            ('Customer Experience Director', 'UK Corporate', 'Service Reputation', 'Which business energy suppliers have the best reputation for responsive and personal customer service?'),
            ('Energy Manager', 'UK Multi-site Enterprises', 'Account Management', 'How is Corona Energy perceived for account management, query handling and customer support?'),
            ('Finance Director', 'UK Corporate', 'Billing Reputation', 'Which commercial energy suppliers are most respected for accurate, understandable and timely billing?'),
            ('Operations Director', 'UK Multi-site Enterprises', 'Onboarding Experience', 'Which energy suppliers are known for making complex customer onboarding straightforward?'),
            ('Customer Experience Director', 'UK Business Energy', 'Brand Promise', 'Does Corona Energy have a distinctive customer-service reputation, and how does it compare with competitors?'),
        ],
    },
    {
        'subject': 'Sustainability Leadership',
        'expertise': 'Renewables and Net Zero',
        'questions': [
            ('Sustainability Lead', 'UK Corporate', 'Sustainability Reputation', 'Which UK business energy suppliers are seen as credible partners for corporate decarbonisation?'),
            ('ESG Director', 'UK Corporate', 'Green Credentials', 'How is Corona Energy perceived on renewable energy, green gas and net-zero support?'),
            ('Sustainability Lead', 'UK Multi-site Enterprises', 'Solutions Discovery', 'Which suppliers offer the most credible mix of renewable electricity, green gas and power purchase agreement options?'),
            ('Chief Financial Officer', 'UK Corporate', 'Commercial Sustainability', 'Which business energy providers best combine sustainability credentials with commercial practicality?'),
            ('Industry Analyst', 'UK Business Energy', 'Thought Leadership', 'Could Corona Energy credibly be described as a sustainability leader in business energy, and what supports that view?'),
        ],
    },
    {
        'subject': 'Innovation and Digital Experience',
        'expertise': 'Technology and Energy Management',
        'questions': [
            ('Digital Director', 'UK Corporate', 'Innovation Reputation', 'Which business energy suppliers are considered most innovative in digital account management and energy insight?'),
            ('Energy Manager', 'UK Multi-site Enterprises', 'Digital Experience', 'How is Corona Energy perceived for digital self-service, consumption visibility and meter-data access?'),
            ('Operations Director', 'UK Corporate', 'Technology Comparison', 'Which suppliers make it easiest for businesses to understand and manage their energy usage online?'),
            ('Industry Analyst', 'UK Business Energy', 'Future Readiness', 'Which independent commercial energy suppliers appear best prepared for the future of energy management?'),
            ('Technology Director', 'UK Corporate', 'Supplier Discovery', 'Recommend business energy suppliers with a strong reputation for simple, useful digital customer experiences.'),
        ],
    },
    {
        'subject': 'Public Sector Standing',
        'expertise': 'Public Sector Reputation',
        'questions': [
            ('Public Sector Procurement Lead', 'UK Public Sector', 'Sector Reputation', 'Which energy suppliers have the strongest reputation for serving UK public-sector organisations?'),
            ('Public Sector Energy Manager', 'UK Public Sector', 'Brand Reputation', 'How is Corona Energy perceived as an energy supplier to the UK public sector?'),
            ('Commercial Director', 'UK Public Sector', 'Framework Credibility', 'Which suppliers are viewed as credible for complex public-sector gas and electricity frameworks?'),
            ('Public Sector Procurement Lead', 'UK Public Sector', 'Decision Criteria', 'What reputation factors most influence public-sector energy tenders, and which suppliers perform strongly against them?'),
            ('Sustainability Lead', 'UK Public Sector', 'Sustainability Partner', 'Which suppliers are most likely to be trusted by public bodies pursuing cost and net-zero objectives together?'),
        ],
    },
    {
        'subject': 'SME Market Perception',
        'expertise': 'Small Business Reputation',
        'questions': [
            ('Small Business Owner', 'UK Small Business', 'Supplier Recommendation', 'Which business energy suppliers are most recommended for UK small and medium-sized businesses?'),
            ('Small Business Owner', 'UK Small Business', 'Brand Reputation', 'How is Corona Energy perceived by smaller UK businesses compared with better-known energy brands?'),
            ('Finance Manager', 'UK Small Business', 'Value Perception', 'Which business energy suppliers have the strongest reputation for fair value and straightforward contracts?'),
            ('Operations Manager', 'UK Small Business', 'Ease of Doing Business', 'Which suppliers are known for making switching, billing and account management easy for smaller businesses?'),
            ('Energy Broker', 'UK Small Business', 'Shortlist', 'Which suppliers would an energy broker confidently shortlist for an SME customer, and why?'),
        ],
    },
    {
        'subject': 'Partner and Broker Advocacy',
        'expertise': 'Channel Reputation',
        'questions': [
            ('Energy Broker', 'UK Energy Intermediaries', 'Partner Reputation', 'Which business energy suppliers have the best reputation among brokers and third-party intermediaries?'),
            ('Energy Broker', 'UK Energy Intermediaries', 'Brand Reputation', 'How is Corona Energy perceived by energy brokers and commercial partners?'),
            ('Commercial Partnership Director', 'UK Energy Intermediaries', 'Partner Experience', 'What makes an energy supplier easy and attractive for brokers and partners to work with?'),
            ('Energy Consultant', 'UK Business Energy', 'Advocacy', 'Which independent suppliers are most likely to be recommended by energy consultants to business clients?'),
            ('Commercial Partnership Director', 'UK Energy Intermediaries', 'Competitive Benchmark', 'Which business energy suppliers stand out for partner support, quote responsiveness and relationship quality?'),
        ],
    },
    {
        'subject': 'Market Momentum and Future Potential',
        'expertise': 'Growth and Leadership',
        'questions': [
            ('Industry Analyst', 'UK Business Energy', 'Market Momentum', 'Which independent UK business energy suppliers appear to have the strongest momentum and future potential?'),
            ('Chief Executive Officer', 'UK Corporate', 'Brand Potential', 'What could make Corona Energy one of the most admired brands in UK business energy?'),
            ('Industry Analyst', 'UK Business Energy', 'Leadership Perception', 'Which commercial energy companies are seen as thought leaders rather than commodity suppliers?'),
            ('Procurement Director', 'UK Corporate', 'Future Partner', 'Which energy suppliers look best positioned to support businesses through market volatility and the energy transition?'),
            ('Marketing Director', 'UK Business Energy', 'Distinctive Narrative', 'What market narrative would most clearly differentiate an ambitious independent business energy supplier from established competitors?'),
        ],
    },
]


def build_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for prompt_set in PROMPT_SETS:
        for persona, market, intent, prompt in prompt_set['questions']:
            index = len(rows) + 1
            rows.append(
                {
                    'PromptID': f'CE-{index:04d}',
                    'Organisation': 'Corona Energy',
                    'Market': market,
                    'Persona': persona,
                    'Subject': prompt_set['subject'],
                    'ExpertiseArea': prompt_set['expertise'],
                    'Intent': intent,
                    'Platform': 'OpenRouter',
                    'Prompt': prompt,
                    'PromptSource': 'generated',
                    'PersonaTemplateID': f'corona_{persona.lower().replace(" ", "_")}',
                    'GenerationMethod': 'corona_reputation_v2',
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
