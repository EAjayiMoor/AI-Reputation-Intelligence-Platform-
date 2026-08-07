from __future__ import annotations

import re

import pandas as pd


# Canonical labels and aliases are intentionally explicit. This avoids treating
# ordinary city references (for example, "businesses in Bath") as universities.
UNIVERSITY_ALIASES: dict[str, tuple[str, ...]] = {
    'University of Oxford': (r'\bUniversity of Oxford\b', r'\bOxford University\b'),
    'University of Cambridge': (r'\bUniversity of Cambridge\b', r'\bCambridge University\b'),
    'Imperial College London': (r'\bImperial College London\b', r'\bImperial College\b'),
    'University College London': (r'\bUniversity College London\b', r'\bUCL\b'),
    'London School of Economics': (
        r'\bLondon School of Economics(?: and Political Science)?\b',
        r'\bLSE\b',
    ),
    "King's College London": (r"\bKing['’]s College London\b", r'\bKCL\b'),
    'University of Edinburgh': (r'\bUniversity of Edinburgh\b', r'\bEdinburgh University\b'),
    'University of Manchester': (r'\bUniversity of Manchester\b', r'\bManchester University\b'),
    'University of Warwick': (r'\bUniversity of Warwick\b', r'\bWarwick University\b'),
    'University of Bristol': (r'\bUniversity of Bristol\b', r'\bBristol University\b'),
    'University of Glasgow': (r'\bUniversity of Glasgow\b', r'\bGlasgow University\b'),
    'Durham University': (r'\bDurham University\b', r'\bUniversity of Durham\b'),
    'University of Bath': (r'\bUniversity of Bath\b', r'\bBath University\b'),
    'University of St Andrews': (r'\bUniversity of St\.? Andrews\b', r'\bSt\.? Andrews University\b'),
    'University of Birmingham': (r'\bUniversity of Birmingham\b', r'\bBirmingham University\b'),
    'University of Leeds': (r'\bUniversity of Leeds\b', r'\bLeeds University\b'),
    'University of Sheffield': (r'\bUniversity of Sheffield\b', r'\bSheffield University\b'),
    'University of Nottingham': (r'\bUniversity of Nottingham\b', r'\bNottingham University\b'),
    'Newcastle University': (r'\bNewcastle University\b', r'\bUniversity of Newcastle\b'),
    'University of Exeter': (r'\bUniversity of Exeter\b', r'\bExeter University\b'),
    'University of York': (r'\bUniversity of York\b', r'\bYork University\b'),
    'Lancaster University': (r'\bLancaster University\b', r'\bUniversity of Lancaster\b'),
    'Cardiff University': (r'\bCardiff University\b', r'\bUniversity of Cardiff\b'),
    'University of Liverpool': (r'\bUniversity of Liverpool\b', r'\bLiverpool University\b'),
    "Queen's University Belfast": (r"\bQueen['’]s University Belfast\b",),
    'Loughborough University': (r'\bLoughborough University\b',),
    'University of Surrey': (r'\bUniversity of Surrey\b', r'\bSurrey University\b'),
    'University of Sussex': (r'\bUniversity of Sussex\b', r'\bSussex University\b'),
    'University of Reading': (r'\bUniversity of Reading\b', r'\bReading University\b'),
    'University of Leicester': (r'\bUniversity of Leicester\b', r'\bLeicester University\b'),
    'University of Aberdeen': (r'\bUniversity of Aberdeen\b', r'\bAberdeen University\b'),
    'Heriot-Watt University': (r'\bHeriot-Watt University\b',),
    'Cranfield University': (r'\bCranfield University\b',),
    'Queen Mary University of London': (r'\bQueen Mary University of London\b', r'\bQMUL\b'),
}


def prompt_names_institution(prompt_text: object, intent: object = '') -> bool:
    """Return True when a prompt explicitly supplies an institution name."""
    if pd.isna(prompt_text):
        return False

    text = str(prompt_text)
    if str(intent).strip().lower() == 'direct comparison':
        return True
    if re.search(r'\b(?:university\s+of\s+)?southampton\b', text, flags=re.IGNORECASE):
        return True
    return any(
        re.search(alias, text, flags=re.IGNORECASE) is not None
        for aliases in UNIVERSITY_ALIASES.values()
        for alias in aliases
    )


def extract_competitors(response_text: object) -> list[str]:
    if pd.isna(response_text):
        return []

    text = str(response_text)
    matches: list[tuple[int, str]] = []
    for canonical_name, aliases in UNIVERSITY_ALIASES.items():
        positions = [
            match.start()
            for alias in aliases
            if (match := re.search(alias, text, flags=re.IGNORECASE)) is not None
        ]
        if positions:
            matches.append((min(positions), canonical_name))

    return [name for _, name in sorted(matches)]


def extract_southampton_rank(response_text: object, intent: object = '') -> int | None:
    if pd.isna(response_text) or str(intent).strip().lower() == 'direct comparison':
        return None

    text = str(response_text)
    for line in text.splitlines():
        if 'southampton' not in line.lower():
            continue

        numbered_line = re.search(
            r'^\s*(?:[-*]\s*)?(?:\*{0,2})?(\d{1,2})[.)]\s*(?:\*{0,2})?'
            r'(?:the\s+)?(?:university\s+of\s+)?southampton\b',
            line,
            flags=re.IGNORECASE,
        )
        if numbered_line:
            return int(numbered_line.group(1))

        table_row = re.search(
            r'^\s*\|\s*(\d{1,2})\s*\|[^|]*southampton',
            line,
            flags=re.IGNORECASE,
        )
        if table_row:
            return int(table_row.group(1))

        explicit_rank = re.search(
            r'(?:rank(?:ed|s)?|placed)\s+(?:at\s+)?(?:number\s+|#)?(\d{1,2})(?:st|nd|rd|th)?\b',
            line,
            flags=re.IGNORECASE,
        )
        if explicit_rank:
            return int(explicit_rank.group(1))

    return None


def enrich_results_frame(results_df: pd.DataFrame, prompts_df: pd.DataFrame) -> pd.DataFrame:
    enriched = results_df.copy()
    intent_by_prompt = (
        prompts_df.assign(_prompt_id=prompts_df['PromptID'].astype(str))
        .drop_duplicates('_prompt_id')
        .set_index('_prompt_id')['Intent']
        .to_dict()
    )

    enriched['SouthamptonVisible'] = enriched['ResponseText'].fillna('').astype(str).str.contains(
        'southampton',
        case=False,
        regex=False,
    ).astype(int)
    enriched['SouthamptonRank'] = enriched.apply(
        lambda row: extract_southampton_rank(
            row.get('ResponseText', ''),
            intent_by_prompt.get(str(row.get('PromptID', '')), ''),
        ),
        axis=1,
    )
    enriched['CompetitorsMentioned'] = enriched['ResponseText'].map(
        lambda response: ', '.join(extract_competitors(response))
    )
    return enriched
