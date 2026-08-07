from __future__ import annotations

import math

import pandas as pd

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
]


def _response_count(frame: pd.DataFrame) -> int:
    return int(len(frame))


def _mention_target(response_count: int, target_score: float) -> int:
    return int(math.ceil(response_count * target_score / 100))


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
    success_measure: str,
) -> None:
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
            'Success measure': success_measure,
        }
    )


def generate_recommendations(scored_df: pd.DataFrame, *, max_recommendations: int = 8) -> pd.DataFrame:
    """Create evidence-led, owned and measurable recommendations from captured responses."""
    if scored_df.empty:
        return pd.DataFrame(columns=RECOMMENDATION_COLUMNS)

    recommendations: list[dict[str, str]] = []
    overall = aggregate_scores(scored_df).iloc[0]
    total_responses = _response_count(scored_df)
    visibility = float(overall['visibility_score'])
    citation = float(overall['citation_score'])
    mention_count = int(overall['southampton_mentions'])

    if visibility < 65:
        target_visibility = min(65.0, visibility + 10.0)
        target_mentions = _mention_target(total_responses, target_visibility)
        _add_recommendation(
            recommendations,
            priority='High',
            action='Build a model-readable Southampton evidence hub',
            category='Visibility',
            scope='All captured audiences and markets',
            evidence=(
                f'Southampton appears in {mention_count} of {total_responses} captured responses '
                f'({visibility:.1f}/100 visibility).'
            ),
            objective='Make Southampton easier for answer engines to identify, verify and include in broad recommendations.',
            steps=[
                'Audit the highest-value prompts where Southampton is absent and group the missing evidence by decision need.',
                'Create or consolidate a central evidence hub linking courses, research strengths, rankings, outcomes and location information.',
                'Rewrite key pages with explicit headings, concise factual summaries, dated proof points and direct links to primary evidence.',
                'Rerun the same prompt and model set after publication so the uplift is directly comparable.',
            ],
            owner='Digital marketing and SEO, with institutional data owners',
            timing='0–30 days',
            success_measure=(
                f'Reach at least {target_visibility:.1f}/100 visibility '
                f'({target_mentions} of {total_responses} responses) in the next matched sweep.'
            ),
        )

    if citation < 60:
        cited_responses = int(scored_df['citation_score_row'].gt(0).sum())
        target_citation = min(60.0, citation + 15.0)
        _add_recommendation(
            recommendations,
            priority='High',
            action='Strengthen citation-ready proof points on priority pages',
            category='Citations',
            scope='Southampton-owned web content',
            evidence=(
                f'Only {cited_responses} of {total_responses} responses contain an extracted citation '
                f'({citation:.1f}/100 citation score).'
            ),
            objective='Increase the likelihood that models support Southampton mentions with authoritative Southampton evidence.',
            steps=[
                'Identify the claims most often needed in recommendation answers: rankings, graduate outcomes, research impact, facilities and entry routes.',
                'Give each claim a stable source page with a publication date, named owner, plain-language summary and link to the underlying evidence.',
                'Add internal links from programme and research pages to those proof points using descriptive link text.',
                'Check citation extraction by model and manually review a sample before the next full sweep.',
            ],
            owner='Content governance, SEO and institutional research',
            timing='0–45 days',
            success_measure=f'Raise citation score to at least {target_citation:.1f}/100 in the next matched sweep.',
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
            subject_mentions = int(row['southampton_mentions'])
            target = min(65.0, float(row['visibility_score']) + 15.0)
            competitor_text = _top_competitor_text(subject_frame)
            is_general = subject.strip().lower() == 'general'
            action = (
                'Fix broad university discovery coverage'
                if is_general
                else f'Build a stronger {subject} authority pathway'
            )
            content_focus = (
                'institution-level comparison, reputation, student experience, location, outcomes and reasons-to-choose content'
                if is_general
                else f'{subject} courses, distinctive research, facilities, outcomes and external validation'
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
                objective=f'Increase Southampton inclusion when users ask about {subject.lower()} options.',
                steps=[
                    f'Map absent prompts to gaps in {content_focus}.',
                    f'Create one authoritative {subject.lower()} overview page and strengthen the supporting pages around the three largest gaps.',
                    'Use clear comparison criteria and attributable evidence without unsupported superiority claims.',
                    f'Retest the {subject.lower()} prompt subset across every captured model.',
                ],
                owner='Relevant faculty marketing lead, supported by SEO and web publishing',
                timing='30–60 days',
                success_measure=(
                    f'Raise {subject} visibility to at least {target:.1f}/100 '
                    f'({_mention_target(subject_responses, target)} of {subject_responses} responses).'
                ),
            )

    if 'Market' in scored_df.columns:
        market_scores = aggregate_scores(scored_df, ['Market']).sort_values('visibility_score')
        weak_markets = market_scores[market_scores['visibility_score'] < 50].head(2)
        for _, row in weak_markets.iterrows():
            market = str(row['Market'])
            market_frame = scored_df[scored_df['Market'].astype(str) == market]
            market_responses = _response_count(market_frame)
            target = min(60.0, float(row['visibility_score']) + 12.0)
            _add_recommendation(
                recommendations,
                priority='High' if float(row['visibility_score']) < 30 else 'Medium',
                action=f'Create a {market}-specific decision journey',
                category='Market visibility',
                scope=market,
                evidence=(
                    f'{market} is at {float(row["visibility_score"]):.1f}/100 visibility with '
                    f'{int(row["southampton_mentions"])} mentions across {market_responses} captured responses.'
                ),
                objective=f'Answer the practical and trust questions that matter to prospective audiences in {market}.',
                steps=[
                    f'Review the absent {market} prompts and identify recurring needs across admissions, cost, visas, careers, safety and recognition.',
                    f'Create a {market}-specific landing journey with localised proof, alumni outcomes, entry guidance and relevant contacts.',
                    'Link the journey directly from the international and programme pages that models already discover.',
                    f'Rerun the {market} subset and compare visibility by subject and model.',
                ],
                owner='International recruitment and regional marketing, supported by admissions',
                timing='30–60 days',
                success_measure=(
                    f'Raise {market} visibility to at least {target:.1f}/100 '
                    f'({_mention_target(market_responses, target)} of {market_responses} responses).'
                ),
            )

    if 'Persona' in scored_df.columns and scored_df['Persona'].nunique(dropna=True) > 1:
        persona_scores = aggregate_scores(scored_df, ['Persona']).sort_values('visibility_score')
        persona_row = persona_scores.iloc[0]
        persona = str(persona_row['Persona'])
        persona_frame = scored_df[scored_df['Persona'].astype(str) == persona]
        persona_responses = _response_count(persona_frame)
        target = min(60.0, float(persona_row['visibility_score']) + 12.0)
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
            objective=f'Make Southampton evidence directly answer the evaluation criteria used by {persona.lower()} audiences.',
            steps=[
                'Use the journey simulator to isolate the lowest-performing subjects and intents for this audience.',
                'Interview the relevant recruitment or research team to confirm the five most important decision criteria.',
                'Create a concise audience landing page that answers those criteria and links to primary proof.',
                'Retest this persona separately and compare its uplift with the other audiences.',
            ],
            owner='Audience marketing lead with recruitment or research communications',
            timing='45–75 days',
            success_measure=f'Raise this audience to at least {target:.1f}/100 visibility in the next matched sweep.',
        )

    ranked = scored_df[scored_df['rank_float'].notna()]
    average_rank = overall['average_rank']
    if len(ranked) >= 5 and average_rank is not None and float(average_rank) > 5:
        top_competitors = _top_competitor_text(scored_df)
        _add_recommendation(
            recommendations,
            priority='Medium',
            action='Improve Southampton placement in recommendation lists',
            category='Rank',
            scope='Explicitly ranked responses',
            evidence=(
                f'Southampton averages position {float(average_rank):.2f} across {len(ranked)} responses with an explicit rank. '
                f'The most frequent competitors are {top_competitors}.'
            ),
            objective='Move Southampton from lower-list inclusion into the consideration set users are most likely to inspect.',
            steps=[
                'Compare Southampton pages against the leading competitors for the decision criteria used in low-ranked prompts.',
                'Close evidence gaps with specific outcomes, facilities, research strengths and differentiators tied to those criteria.',
                'Publish transparent comparison content where it helps users make a defensible choice.',
                'Track both average rank and the number of ranked observations to avoid over-reading a small sample.',
            ],
            owner='SEO strategy and faculty content leads',
            timing='60–90 days',
            success_measure='Improve average explicit rank by at least 1.5 positions while increasing the ranked sample size.',
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
                objective='Understand whether this model is missing Southampton because of evidence, retrieval or response-format differences.',
                steps=[
                    'Sample absent responses and classify each gap as retrieval, evidence coverage, competitive preference or extraction error.',
                    'Check whether Southampton pages surface for the same query language outside the model response.',
                    'Apply the relevant content fixes, then rerun only the failed prompt subset before paying for a full sweep.',
                    'Keep model-level results separate so gains in one model do not mask weakness in another.',
                ],
                owner='AI visibility analyst with SEO technical lead',
                timing='0–30 days',
                success_measure='Reduce the gap between this model and the best sufficiently sampled model by at least 50%.',
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
            success_measure='Maintain all headline scores within five points of baseline or document the cause of movement.',
        )

    priority_order = {'High': 0, 'Medium': 1, 'Low': 2}
    recommendations.sort(key=lambda row: (priority_order.get(row['Priority'], 9), row['Timing'], row['Action']))
    return pd.DataFrame(recommendations[:max_recommendations], columns=RECOMMENDATION_COLUMNS)


def key_gap_text(filtered_df: pd.DataFrame) -> str:
    if filtered_df.empty:
        return 'No data is available for this journey selection.'

    overall = aggregate_scores(filtered_df).iloc[0]
    if float(overall['visibility_score']) < 60:
        return 'Visibility is the main gap: Southampton is not appearing often enough in responses.'
    if float(overall['citation_score']) < 60:
        return 'Citation strength is the main gap: Southampton sources are not referenced consistently.'
    return 'Competitive pressure is the main gap: competitors are still mentioned strongly in this segment.'
