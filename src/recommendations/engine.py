from __future__ import annotations

import math

import pandas as pd

from src.recommendations.comparator import comparator_context
from src.scoring import aggregate_scores, competitor_mentions


RECOMMENDATION_COLUMNS = [
    'Priority',
    'Action',
    'Category',
    'Scope',
    'Evidence',
    'Objective',
    'Action plan',
    'Owner',
    'Timing',
    'Success measure',
    'Intervention level',
    'Affected signal',
    'Why this may matter',
    'Evidence strength',
    'Method basis',
    'Baseline',
    'Target calculation',
    'Validation method',
    'Confidence',
    'Comparator',
    'Comparative performance',
    'Comparator evidence pattern',
    'Organisation evidence position',
    'Comparator sources',
    'Evidence quality score',
    'Evidence quality rating',
    'Comparative limitation',
    'Comparable peer',
    'Peer performance',
    'Peer evidence pattern',
    'Peer sources',
]

MIN_BENCHMARK_RESPONSES = 30

CATEGORY_METHOD = {
    'Visibility': (
        'Firm-wide',
        'Discoverability and entity clarity',
        'Crawlable, internally linked pages with explicit factual descriptions help retrieval systems discover and interpret an organisation. Whether a foundation model uses that evidence remains model- and query-dependent.',
        'Supported retrieval practice; model outcome experimental',
        'Google Search: how crawling, indexing and serving work — https://developers.google.com/search/docs/fundamentals/how-search-works',
    ),
    'Citations': (
        'Firm-wide',
        'Evidence retrievability and authority',
        'Stable primary-source pages make claims easier to retrieve and cite. Publication alone does not guarantee that a model will select or cite the source.',
        'Supported retrieval practice; model outcome experimental',
        'Google Search: helpful, reliable content and crawlable links — https://developers.google.com/search/docs/fundamentals/creating-helpful-content',
    ),
    'Subject visibility': (
        'Sector/service',
        'Topic relevance and evidence coverage',
        'Evidence that directly answers the observed subject-level decision needs can improve retrieval relevance for that segment. The effect must be tested on the same prompts.',
        'Evidence-led hypothesis',
        'Observed subject benchmark plus Google people-first content guidance — https://developers.google.com/search/docs/fundamentals/creating-helpful-content',
    ),
    'Market visibility': (
        'Market',
        'Market relevance and local proof',
        'Market-specific evidence can answer location-dependent evaluation criteria that generic pages miss. Any change in model inclusion must be verified experimentally.',
        'Evidence-led hypothesis',
        'Observed market benchmark; intervention outcome requires matched testing',
    ),
    'Audience journey': (
        'Persona',
        'Audience relevance and decision-fit',
        'Content aligned to the measured persona questions may be more retrievable for those needs, but persona targeting is an experimental intervention rather than a guaranteed model signal.',
        'Experimental hypothesis',
        'Observed persona benchmark; no external causal claim',
    ),
    'Rank': (
        'Firm-wide',
        'Comparative evidence and prominence',
        'Clear, attributable evidence against the criteria present in low-ranked responses may strengthen comparative relevance. Proprietary model ordering logic is not observable.',
        'Experimental hypothesis',
        'Observed ranked-response benchmark; proprietary ordering logic is unknown',
    ),
    'Model variance': (
        'Model/platform',
        'Retrieval and model-specific coverage',
        'A model-specific gap can reflect retrieval, evidence coverage, response policy or measurement error. Diagnosis must precede intervention and cannot be generalised to other models.',
        'Diagnostic hypothesis',
        'Observed model-level benchmark; no cross-model causal claim',
    ),
    'Measurement': (
        'Firm-wide',
        'Measurement stability',
        'A fixed prompt and model benchmark makes changes comparable over time, although repeated model outputs remain variable and are not perfectly independent observations.',
        'Measurement practice',
        'Matched benchmark design and documented one-sided binomial threshold',
    ),
}


def _response_count(frame: pd.DataFrame) -> int:
    return int(len(frame))


def _organisation_name(frame: pd.DataFrame) -> str:
    if 'Organisation' in frame.columns:
        values = frame['Organisation'].dropna().astype(str).str.strip()
        values = values[values != '']
        if not values.empty:
            return str(values.iloc[0])
    if 'SouthamptonVisible' in frame.columns or 'SouthamptonRank' in frame.columns:
        return 'University of Southampton'
    return 'Primary organisation'


def _organisation_mentions(overall: pd.Series) -> int:
    if 'org_mentions' in overall:
        return int(overall['org_mentions'])
    return int(overall.get('southampton_mentions', 0))


def _binomial_tail(successes: int, trials: int, probability: float) -> float:
    if successes <= 0:
        return 1.0
    if probability <= 0:
        return 0.0
    if probability >= 1:
        return 1.0 if successes <= trials else 0.0

    log_probability = (
        math.lgamma(trials + 1)
        - math.lgamma(successes + 1)
        - math.lgamma(trials - successes + 1)
        + successes * math.log(probability)
        + (trials - successes) * math.log1p(-probability)
    )
    term = math.exp(log_probability)
    total = term
    odds = probability / (1 - probability)
    for value in range(successes, trials):
        term *= (trials - value) / (value + 1) * odds
        total += term
    return min(total, 1.0)


def _measurement_plan(successes: int | None, responses: int) -> tuple[str, str, str, str]:
    if successes is None:
        return (
            f'{responses} relevant responses; this outcome is not a binary rate.',
            'No numeric uplift is forecast. Compare the same observations in a matched rerun and report the change with its sample size.',
            'Treat movement as directional until it repeats in a second matched rerun.',
            'Low — experimental outcome',
        )

    rate = successes / responses * 100 if responses else 0.0
    baseline = f'{successes} of {responses} responses ({rate:.1f}%).'
    if responses < MIN_BENCHMARK_RESPONSES:
        return (
            baseline,
            f'No percentage uplift target is set because this segment has fewer than {MIN_BENCHMARK_RESPONSES} responses. Expand or combine the matched benchmark before quantifying uplift.',
            'Rerun the same matched prompts and models; report counts and rates, but do not claim uplift from this sample alone.',
            'Low — directional sample',
        )

    baseline_probability = successes / responses
    if successes == 0:
        baseline_probability = 0.5 / responses
    threshold = next(
        (
            candidate
            for candidate in range(successes + 1, responses + 1)
            if _binomial_tail(candidate, responses, baseline_probability) <= 0.05
        ),
        responses,
    )
    threshold_rate = threshold / responses * 100
    target = (
        f'{threshold} of {responses} responses ({threshold_rate:.1f}%) is the minimum next-run signal '
        'above a one-sided 95% binomial threshold under the baseline rate. This is a measurement threshold, not a forecast.'
    )
    validation = (
        'Rerun the same matched prompts, models and scoring rules after the intervention. '
        'Investigate the signal only if the threshold is met, then require a second matched rerun before attributing a sustained effect.'
    )
    return baseline, target, validation, 'Medium — benchmark threshold'


def _top_competitor_text(frame: pd.DataFrame, limit: int = 3) -> str:
    mentions = competitor_mentions(frame).head(limit)
    if mentions.empty:
        return 'No consistently extracted competitor set is available'
    return ', '.join(
        f"{row['Competitor']} ({int(row['Mentions'])})"
        for _, row in mentions.iterrows()
    )


def _add_recommendation(
    rows: list[dict[str, str]],
    *,
    priority: str,
    action: str,
    category: str,
    scope: str,
    evidence: str,
    objective: str,
    steps: list[str],
    owner: str,
    timing: str,
    responses: int,
    successes: int | None,
    benchmark_frame: pd.DataFrame,
    organisation_name: str,
) -> None:
    intervention_level, affected_signal, rationale, evidence_strength, method_basis = CATEGORY_METHOD[category]
    baseline, target_calculation, validation_method, confidence = _measurement_plan(successes, responses)
    comparison = comparator_context(benchmark_frame, organisation_name)
    rows.append(
        {
            'Priority': priority,
            'Action': action,
            'Category': category,
            'Scope': scope,
            'Evidence': evidence,
            'Objective': objective,
            'Action plan': '\n'.join(f'{index}. {step}' for index, step in enumerate(steps, start=1)),
            'Owner': owner,
            'Timing': timing,
            'Success measure': target_calculation,
            'Intervention level': intervention_level,
            'Affected signal': affected_signal,
            'Why this may matter': rationale,
            'Evidence strength': evidence_strength,
            'Method basis': method_basis,
            'Baseline': baseline,
            'Target calculation': target_calculation,
            'Validation method': validation_method,
            'Confidence': confidence,
            'Comparator': comparison['comparator'],
            'Comparative performance': comparison['performance'],
            'Comparator evidence pattern': comparison['pattern'],
            'Organisation evidence position': comparison['organisation_position'],
            'Comparator sources': comparison['sources'],
            'Evidence quality score': comparison['score'],
            'Evidence quality rating': comparison['rating'],
            'Comparative limitation': comparison['limitation'],
            'Comparable peer': comparison['comparable_peer'],
            'Peer performance': comparison['peer_performance'],
            'Peer evidence pattern': comparison['peer_pattern'],
            'Peer sources': comparison['peer_sources'],
        }
    )


def generate_recommendations(scored_df: pd.DataFrame, *, max_recommendations: int = 8) -> pd.DataFrame:
    """Create evidence-led, owned and measurable recommendations from captured responses."""
    if scored_df.empty:
        return pd.DataFrame(columns=RECOMMENDATION_COLUMNS)

    recommendations: list[dict[str, str]] = []
    overall = aggregate_scores(scored_df).iloc[0]
    organisation_name = _organisation_name(scored_df)
    total_responses = _response_count(scored_df)
    visibility = float(overall['visibility_score'])
    citation = float(overall['citation_score'])
    mention_count = _organisation_mentions(overall)

    if visibility < 65:
        _add_recommendation(
            recommendations,
            priority='High',
            action=f'Build a model-readable {organisation_name} evidence hub',
            category='Visibility',
            scope='All captured audiences and markets',
            evidence=(
                f'{organisation_name} appears in {mention_count} of {total_responses} captured responses '
                f'({visibility:.1f}/100 visibility).'
            ),
            objective=f'Make {organisation_name} easier for answer engines to identify, verify and include in broad recommendations.',
            steps=[
                f'Audit the highest-value prompts where {organisation_name} is absent and group the missing evidence by decision need.',
                'Create or consolidate a central evidence hub linking services, capabilities, credentials, outcomes and market information.',
                'Rewrite key pages with explicit headings, concise factual summaries, dated proof points and direct links to primary evidence.',
                'Rerun the same prompt and model set after publication so the uplift is directly comparable.',
            ],
            owner='Digital marketing and SEO, with relevant data owners',
            timing='0–30 days',
            responses=total_responses,
            successes=mention_count,
            benchmark_frame=scored_df,
            organisation_name=organisation_name,
        )

    if citation < 60:
        cited_responses = int(scored_df['citation_score_row'].gt(0).sum())
        _add_recommendation(
            recommendations,
            priority='High',
            action='Strengthen citation-ready proof points on priority pages',
            category='Citations',
            scope=f'{organisation_name}-owned web content',
            evidence=(
                f'Only {cited_responses} of {total_responses} responses contain an extracted citation '
                f'({citation:.1f}/100 citation score).'
            ),
            objective=f'Increase the likelihood that models support {organisation_name} mentions with authoritative first-party evidence.',
            steps=[
                'Identify the claims most often needed in recommendation answers: service outcomes, credentials, capabilities, value and routes to engagement.',
                'Give each claim a stable source page with a publication date, named owner, plain-language summary and link to the underlying evidence.',
                'Add internal links from service and insight pages to those proof points using descriptive link text.',
                'Check citation extraction by model and manually review a sample before the next full sweep.',
            ],
            owner='Content governance, SEO and business intelligence',
            timing='0–45 days',
            responses=total_responses,
            successes=cited_responses,
            benchmark_frame=scored_df,
            organisation_name=organisation_name,
        )

    if 'Subject' in scored_df.columns:
        subject_scores = aggregate_scores(scored_df, ['Subject']).sort_values(
            ['reputation_score', 'visibility_score'], ascending=True
        )
        weak_subjects = subject_scores[subject_scores['visibility_score'] < 60].head(2)
        for _, row in weak_subjects.iterrows():
            subject = str(row['Subject'])
            subject_frame = scored_df[scored_df['Subject'].astype(str) == subject]
            subject_responses = _response_count(subject_frame)
            subject_mentions = int(row.get('org_mentions', row.get('southampton_mentions', 0)))
            competitor_text = _top_competitor_text(subject_frame)
            is_general = subject.strip().lower() == 'general'
            action = (
                'Fix broad market discovery coverage'
                if is_general
                else f'Build a stronger {subject} authority pathway'
            )
            content_focus = (
                'organisation-level comparison, reputation, customer experience, market coverage, outcomes and reasons-to-choose content'
                if is_general
                else f'{subject} services, distinctive capabilities, outcomes and external validation'
            )
            _add_recommendation(
                recommendations,
                priority='High' if float(row['visibility_score']) < 35 else 'Medium',
                action=action,
                category='Subject visibility',
                scope=subject,
                evidence=(
                    f'{subject} visibility is {float(row["visibility_score"]):.1f}/100 '
                    f'({subject_mentions} mentions across {subject_responses} responses). '
                    f'Leading extracted competitors: {competitor_text}.'
                ),
                objective=f'Increase {organisation_name} inclusion when users ask about {subject.lower()} options.',
                steps=[
                    f'Map absent prompts to gaps in {content_focus}.',
                    f'Create one authoritative {subject.lower()} overview page and strengthen the supporting pages around the three largest gaps.',
                    'Use clear comparison criteria and attributable evidence without unsupported superiority claims.',
                    f'Retest the {subject.lower()} prompt subset across every captured model.',
                ],
                owner='Relevant proposition marketing lead, supported by SEO and web publishing',
                timing='30–60 days',
                responses=subject_responses,
                successes=subject_mentions,
                benchmark_frame=subject_frame,
                organisation_name=organisation_name,
            )

    if 'Market' in scored_df.columns:
        market_scores = aggregate_scores(scored_df, ['Market']).sort_values('visibility_score')
        weak_markets = market_scores[market_scores['visibility_score'] < 50].head(2)
        for _, row in weak_markets.iterrows():
            market = str(row['Market'])
            market_frame = scored_df[scored_df['Market'].astype(str) == market]
            market_responses = _response_count(market_frame)
            _add_recommendation(
                recommendations,
                priority='High' if float(row['visibility_score']) < 30 else 'Medium',
                action=f'Create a {market}-specific decision journey',
                category='Market visibility',
                scope=market,
                evidence=(
                    f'{market} is at {float(row["visibility_score"]):.1f}/100 visibility with '
                    f'{int(row.get("org_mentions", row.get("southampton_mentions", 0)))} mentions across {market_responses} captured responses.'
                ),
                objective=f'Answer the practical and trust questions that matter to prospective audiences in {market}.',
                steps=[
                    f'Review the absent {market} prompts and identify recurring needs across cost, service fit, implementation, trust and proof.',
                    f'Create a {market}-specific landing journey with relevant evidence, customer outcomes, buying guidance and contacts.',
                    'Link the journey directly from the service and insight pages that models already discover.',
                    f'Rerun the {market} subset and compare visibility by subject and model.',
                ],
                owner='Regional marketing and commercial leads',
                timing='30–60 days',
                responses=market_responses,
                successes=int(row.get('org_mentions', row.get('southampton_mentions', 0))),
                benchmark_frame=market_frame,
                organisation_name=organisation_name,
            )

    if 'Persona' in scored_df.columns and scored_df['Persona'].nunique(dropna=True) > 1:
        persona_scores = aggregate_scores(scored_df, ['Persona']).sort_values('visibility_score')
        persona_row = persona_scores.iloc[0]
        persona = str(persona_row['Persona'])
        persona_frame = scored_df[scored_df['Persona'].astype(str) == persona]
        persona_responses = _response_count(persona_frame)
        _add_recommendation(
            recommendations,
            priority='Medium',
            action=f'Build an evidence journey for {persona.lower()} audiences',
            category='Audience journey',
            scope=persona,
            evidence=(
                f'{persona} is the weakest captured audience at '
                f'{float(persona_row["visibility_score"]):.1f}/100 visibility across {persona_responses} responses.'
            ),
            objective=f'Make {organisation_name} evidence directly answer the evaluation criteria used by {persona.lower()} audiences.',
            steps=[
                'Use the journey simulator to isolate the lowest-performing subjects and intents for this audience.',
                'Interview the relevant commercial or subject-matter team to confirm the five most important decision criteria.',
                'Create a concise audience landing page that answers those criteria and links to primary proof.',
                'Retest this persona separately and compare its uplift with the other audiences.',
            ],
            owner='Audience marketing lead with commercial and subject-matter teams',
            timing='45–75 days',
            responses=persona_responses,
            successes=int(persona_row.get('org_mentions', persona_row.get('southampton_mentions', 0))),
            benchmark_frame=persona_frame,
            organisation_name=organisation_name,
        )

    ranked = scored_df[scored_df['rank_float'].notna()]
    average_rank = overall['average_rank']
    if len(ranked) >= 5 and average_rank is not None and float(average_rank) > 5:
        top_competitors = _top_competitor_text(scored_df)
        _add_recommendation(
            recommendations,
            priority='Medium',
            action=f'Improve {organisation_name} placement in recommendation lists',
            category='Rank',
            scope='Explicitly ranked responses',
            evidence=(
                f'{organisation_name} averages position {float(average_rank):.2f} across {len(ranked)} responses with an explicit rank. '
                f'The most frequent competitors are {top_competitors}.'
            ),
            objective=f'Move {organisation_name} from lower-list inclusion into the consideration set users are most likely to inspect.',
            steps=[
                f'Compare {organisation_name} pages against the leading competitors for the decision criteria used in low-ranked prompts.',
                'Close evidence gaps with specific outcomes, capabilities, credentials and differentiators tied to those criteria.',
                'Publish transparent comparison content where it helps users make a defensible choice.',
                'Track both average rank and the number of ranked observations to avoid over-reading a small sample.',
            ],
            owner='SEO strategy and proposition content leads',
            timing='60–90 days',
            responses=len(ranked),
            successes=None,
            benchmark_frame=ranked,
            organisation_name=organisation_name,
        )

    if 'ModelName' in scored_df.columns:
        model_counts = scored_df.groupby('ModelName').size()
        eligible_models = model_counts[model_counts >= 10].index
        if len(eligible_models) > 1:
            model_scores = aggregate_scores(
                scored_df[scored_df['ModelName'].isin(eligible_models)], ['ModelName']
            ).sort_values('visibility_score')
            weak_model = model_scores.iloc[0]
            model_name = str(weak_model['ModelName'])
            model_frame = scored_df[scored_df['ModelName'].astype(str) == model_name]
            _add_recommendation(
                recommendations,
                priority='Medium',
                action=f'Run a focused discoverability sprint for {model_name}',
                category='Model variance',
                scope=model_name,
                evidence=(
                    f'{model_name} has the lowest sufficiently sampled visibility at '
                    f'{float(weak_model["visibility_score"]):.1f}/100 across {len(model_frame)} responses.'
                ),
                objective=f'Understand whether this model is missing {organisation_name} because of evidence, retrieval or response-format differences.',
                steps=[
                    'Sample absent responses and classify each gap as retrieval, evidence coverage, competitive preference or extraction error.',
                    f'Check whether {organisation_name} pages surface for the same query language outside the model response.',
                    'Apply the relevant content fixes, then rerun only the failed prompt subset before paying for a full sweep.',
                    'Keep model-level results separate so gains in one model do not mask weakness in another.',
                ],
                owner='AI visibility analyst with SEO technical lead',
                timing='0–30 days',
                responses=len(model_frame),
                successes=int(weak_model.get('org_mentions', weak_model.get('southampton_mentions', 0))),
                benchmark_frame=model_frame,
                organisation_name=organisation_name,
            )

    if not recommendations:
        _add_recommendation(
            recommendations,
            priority='Medium',
            action='Protect performance with a controlled monitoring cycle',
            category='Measurement',
            scope='All captured responses',
            evidence='No configured performance threshold is currently breached.',
            objective='Maintain visibility while detecting material changes early.',
            steps=[
                'Freeze the current prompt bank and model set as the comparison baseline.',
                'Rerun monthly and investigate any five-point movement by market, subject or audience.',
                'Record content changes between sweeps so movements can be linked to interventions.',
            ],
            owner='AI visibility analyst',
            timing='Monthly',
            responses=total_responses,
            successes=mention_count,
            benchmark_frame=scored_df,
            organisation_name=organisation_name,
        )

    priority_order = {'High': 0, 'Medium': 1, 'Low': 2}
    recommendations.sort(key=lambda row: (priority_order.get(row['Priority'], 9), row['Timing'], row['Action']))
    recommendations_df = pd.DataFrame(recommendations[:max_recommendations], columns=RECOMMENDATION_COLUMNS)

    return recommendations_df


def key_gap_text(filtered_df: pd.DataFrame) -> str:
    if filtered_df.empty:
        return 'No data is available for this journey selection.'

    overall = aggregate_scores(filtered_df).iloc[0]
    organisation_name = _organisation_name(filtered_df)
    if float(overall['visibility_score']) < 60:
        return f'Visibility is the main gap: {organisation_name} is not appearing often enough in responses.'
    if float(overall['citation_score']) < 60:
        return f'Citation strength is the main gap: {organisation_name} sources are not referenced consistently.'
    return 'Competitive pressure is the main gap: competitors are still mentioned strongly in this segment.'
