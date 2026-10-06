from __future__ import annotations


REVIEWED_ON = '2026-10-06'

PUBLIC_EVIDENCE = {
    'Deloitte': {
        'pattern': (
            'Connects transformation propositions to named client stories, sector pages, '
            'current research with stated methodology, client quotations and quantified outcomes.'
        ),
        'sources': (
            'https://www.deloitte.com/uk/en/what-we-do/case-studies-stories-of-impact.html',
            'https://www.deloitte.com/uk/en/services/consulting/research/measuring-value-from-digital-transformation.html',
        ),
    },
    'Accenture': {
        'pattern': (
            'Reinforces a consistent reinvention proposition through research, repeatable frameworks, '
            'named client stories and prominently quantified operational outcomes.'
        ),
        'sources': (
            'https://www.accenture.com/gb-en/insights/consulting/total-enterprise-reinvention',
            'https://www.accenture.com/en/case-studies/technology/continuous-reinvention-powered-with-workday',
        ),
    },
    'PA Consulting': {
        'pattern': (
            'Links multidisciplinary capability to named or clearly framed client problems, '
            'implementation detail, skill transfer and quantified commercial or operational outcomes.'
        ),
        'sources': (
            'https://www.paconsulting.com/services/reimagine-ai-digital-and-data/digital-transformation',
            'https://www.paconsulting.com/client-story/global-pharmaceutical-company-bringing-the-factory-of-the-future-to-life',
        ),
    },
    'Baringa': {
        'pattern': (
            'Builds specialist authority around regulated sectors through focused propositions, '
            'sector research, expert commentary and client evidence.'
        ),
        'sources': (
            'https://www.baringa.com/en/industries/energy-and-resources/',
            'https://www.baringa.com/en/insights/',
        ),
    },
    'Moorhouse': {
        'pattern': (
            'Has credible sector pages and some strong quantified client outcomes, but the depth, '
            'recency and connection of proof to the central transformation proposition are uneven.'
        ),
        'sources': (
            'https://www.moorhouseconsulting.com/client-stories/',
            'https://www.moorhouseconsulting.com/sectors/energy-and-utilities/',
            'https://www.moorhouseconsulting.com/insights/case-studies/how-preparation-and-diagnostic-delivered-a-better-outcome-for-a-struggling-nhs-trust/',
        ),
    },
}


def public_evidence_for(organisation: str) -> dict[str, object]:
    evidence = PUBLIC_EVIDENCE.get(organisation)
    if evidence is None:
        return {
            'status': 'Not curated',
            'reviewed_on': '',
            'pattern': 'No curated public-evidence snapshot is available; manual review is required before using competitor practices in a recommendation.',
            'sources': (),
        }
    return {
        'status': 'Curated',
        'reviewed_on': REVIEWED_ON,
        'pattern': evidence['pattern'],
        'sources': evidence['sources'],
    }
