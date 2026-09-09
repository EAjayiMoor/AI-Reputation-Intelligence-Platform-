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

SOUTHAMPTON_PATTERN = r'\b(?:university\s+of\s+)?southampton\b'


def organisation_name_pattern(
    organisation_name: str,
    aliases: list[str] | tuple[str, ...] = (),
) -> str:
    """Build a case-insensitive-safe regex for a tenant name and its aliases."""
    names = [organisation_name, *aliases]
    escaped = [re.escape(name.strip()) for name in names if name and name.strip()]
    escaped = list(dict.fromkeys(escaped))
    return rf'(?<!\w)(?:{"|".join(escaped)})(?!\w)' if escaped else r'(?!x)x'


def _competitor_patterns(
    competitor_aliases: dict[str, tuple[str, ...] | list[str]],
) -> dict[str, tuple[str, ...]]:
    return {
        canonical: tuple(
            dict.fromkeys(
                [
                    rf'(?<!\w){re.escape(value.strip())}(?!\w)'
                    for value in [canonical, *aliases]
                    if value and value.strip()
                ]
            )
        )
        for canonical, aliases in competitor_aliases.items()
        if canonical and canonical.strip()
    }


def prompt_names_institution(
    prompt_text: object,
    intent: object = '',
    target_institution_pattern: str = SOUTHAMPTON_PATTERN,
    competitor_aliases: dict[str, tuple[str, ...] | list[str]] | None = None,
) -> bool:
    """Return True when a prompt explicitly supplies the target or competitor name."""
    if pd.isna(prompt_text):
        return False

    text = str(prompt_text)
    if str(intent).strip().lower() == 'direct comparison':
        return True
    if re.search(target_institution_pattern, text, flags=re.IGNORECASE):
        return True
    patterns = (
        _competitor_patterns(competitor_aliases)
        if competitor_aliases is not None
        else UNIVERSITY_ALIASES
    )
    return any(
        re.search(alias, text, flags=re.IGNORECASE) is not None
        for aliases in patterns.values()
        for alias in aliases
    )


def extract_competitors(
    response_text: object,
    competitor_aliases: dict[str, tuple[str, ...] | list[str]] | None = None,
) -> list[str]:
    if pd.isna(response_text):
        return []

    text = str(response_text)
    matches: list[tuple[int, str]] = []
    patterns = (
        _competitor_patterns(competitor_aliases)
        if competitor_aliases is not None
        else UNIVERSITY_ALIASES
    )
    for canonical_name, aliases in patterns.items():
        positions = [
            match.start()
            for alias in aliases
            if (match := re.search(alias, text, flags=re.IGNORECASE)) is not None
        ]
        if positions:
            matches.append((min(positions), canonical_name))

    return [name for _, name in sorted(matches)]


def extract_institution_rank(
    response_text: object,
    intent: object = '',
    institution_pattern: str = SOUTHAMPTON_PATTERN,
) -> int | None:
    if pd.isna(response_text) or str(intent).strip().lower() == 'direct comparison':
        return None

    text = str(response_text)
    for line in text.splitlines():
        if re.search(institution_pattern, line, flags=re.IGNORECASE) is None:
            continue

        numbered_line = re.search(
            r'^\s*(?:[-*]\s*)?(?:\*{0,2})?(\d{1,2})[.)]\s*(?:\*{0,2})?'
            rf'(?:the\s+)?{institution_pattern}',
            line,
            flags=re.IGNORECASE,
        )
        if numbered_line:
            return int(numbered_line.group(1))

        table_row = re.search(
            rf'^\s*\|\s*(\d{{1,2}})\s*\|[^|]*{institution_pattern}',
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


def extract_southampton_rank(response_text: object, intent: object = '') -> int | None:
    return extract_institution_rank(
        response_text=response_text,
        intent=intent,
        institution_pattern=SOUTHAMPTON_PATTERN,
    )


def enrich_results_frame(
    results_df: pd.DataFrame,
    prompts_df: pd.DataFrame,
    *,
    organisation_name: str = 'University of Southampton',
    organisation_aliases: list[str] | tuple[str, ...] = ('Southampton',),
    competitor_aliases: dict[str, tuple[str, ...] | list[str]] | None = None,
) -> pd.DataFrame:
    enriched = results_df.copy()
    intent_by_prompt = (
        prompts_df.assign(_prompt_id=prompts_df['PromptID'].astype(str))
        .drop_duplicates('_prompt_id')
        .set_index('_prompt_id')['Intent']
        .to_dict()
    )

    target_pattern = organisation_name_pattern(organisation_name, organisation_aliases)
    enriched['OrgVisible'] = enriched['ResponseText'].fillna('').astype(str).str.contains(
        target_pattern, case=False, regex=True
    ).astype(int)
    enriched['OrgRank'] = enriched.apply(
        lambda row: extract_institution_rank(
            row.get('ResponseText', ''),
            intent_by_prompt.get(str(row.get('PromptID', '')), ''),
            institution_pattern=target_pattern,
        ),
        axis=1,
    )
    if organisation_name == 'University of Southampton':
        enriched['SouthamptonVisible'] = enriched['OrgVisible']
        enriched['SouthamptonRank'] = enriched['OrgRank']
    enriched['CompetitorsMentioned'] = enriched['ResponseText'].map(
        lambda response: ', '.join(extract_competitors(response, competitor_aliases))
    )
    return enriched
