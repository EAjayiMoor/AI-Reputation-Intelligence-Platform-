from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from io import BytesIO
from typing import Mapping, Sequence
import zipfile

import pandas as pd

from src.analysis import (
    competitive_breakdown,
    compute_scope_metrics,
    outlier_responses,
    run_history_summary,
    segment_summary,
    split_scope_frames,
)
from src.recommendations import generate_recommendations
from src.scoring import aggregate_scores


MODEL_LABELS = {
    'openai/gpt-4.1-mini': 'GPT-4.1 Mini',
    'anthropic/claude-haiku-4.5': 'Claude Haiku 4.5',
    'google/gemini-3.6-flash': 'Gemini 3.6 Flash',
    'qwen/qwen3-max': 'Qwen3 Max',
    'deepseek/deepseek-chat': 'DeepSeek Chat',
    'perplexity/sonar': 'Perplexity Sonar',
}


def build_rendered_microsite_archive(
    *,
    scored_df: pd.DataFrame,
    scope_df: pd.DataFrame | None = None,
    organisation_name: str,
    org_id: str,
    prompt_scope: str = 'Combined',
    mention_mode: str = 'All',
    filters: Mapping[str, str] | None = None,
    owned_domains: tuple[str, ...] | list[str] | None = None,
    organisation_aliases: Sequence[str] = (),
    competitor_aliases: Mapping[str, Sequence[str]] | None = None,
) -> bytes:
    html = build_rendered_microsite_html(
        scored_df=scored_df,
        scope_df=scope_df,
        organisation_name=organisation_name,
        org_id=org_id,
        prompt_scope=prompt_scope,
        mention_mode=mention_mode,
        filters=filters,
        owned_domains=owned_domains,
        organisation_aliases=organisation_aliases,
        competitor_aliases=competitor_aliases,
    )
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, mode='w', compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('microsite/index.html', html.encode('utf-8'))
    return buffer.getvalue()


def build_rendered_microsite_html(
    *,
    scored_df: pd.DataFrame,
    scope_df: pd.DataFrame | None = None,
    organisation_name: str,
    org_id: str,
    prompt_scope: str = 'Combined',
    mention_mode: str = 'All',
    filters: Mapping[str, str] | None = None,
    owned_domains: tuple[str, ...] | list[str] | None = None,
    organisation_aliases: Sequence[str] = (),
    competitor_aliases: Mapping[str, Sequence[str]] | None = None,
) -> str:
    if scored_df.empty:
        raise ValueError('Rendered microsite export requires at least one filtered response row.')

    comparison_frame = scope_df if scope_df is not None else scored_df
    overall = aggregate_scores(scored_df).iloc[0]
    market_scores = aggregate_scores(scored_df, ['Market']).sort_values('visibility_score', ascending=False).head(10)
    subject_scores = aggregate_scores(scored_df, ['Subject']).sort_values('visibility_score', ascending=False).head(10)
    presence_metrics = _presence_metrics(scored_df)
    model_presence = _presence_by_model(scored_df)
    segment_columns = [column for column in ['Persona', 'Subject'] if column in scored_df.columns]
    segments = segment_summary(scored_df, segment_columns) if segment_columns else pd.DataFrame()
    segment_view_columns = [
        *segment_columns,
        'Responses',
        'MentionRate',
        'AverageProminence',
        'RecommendationRate',
        'ShortlistRate',
        'CitationRate',
        'PositiveAssociationRate',
        'AverageReputationScore',
        'OpportunityScore',
        'Diagnosis',
    ]
    segment_table = _render_table(segments.head(12), segment_view_columns)

    competitive_signals = competitive_breakdown(
        comparison_frame,
        organisation_name=organisation_name,
        organisation_aliases=organisation_aliases,
        competitor_aliases=competitor_aliases,
    )
    target_rows = competitive_signals[competitive_signals['EntityType'] == 'Target']
    competitor_rows = competitive_signals[competitive_signals['EntityType'] == 'Competitor'].sort_values(
        'MentionRate', ascending=False
    )
    target_signal = target_rows.iloc[0] if not target_rows.empty else None
    top_competitor = competitor_rows.iloc[0] if not competitor_rows.empty else None
    competitive_view = pd.concat([target_rows, competitor_rows.head(8)], ignore_index=True)
    competitive_table = _render_table(
        competitive_view,
        [
            'Entity', 'EntityType', 'EligibleResponses', 'MentionedResponses', 'MentionRate',
            'FirstMentionedRate', 'RecommendationRate', 'ShortlistRate',
        ],
    )
    recommendations = generate_recommendations(scored_df, max_recommendations=8)
    evidence = outlier_responses(scored_df, limit=8)
    history = run_history_summary(scored_df)

    visibility = float(overall['visibility_score'])
    reputation = float(overall['reputation_score'])
    prompts = int(scored_df['PromptID'].nunique()) if 'PromptID' in scored_df.columns else 0
    mentions = int(overall.get('org_mentions', overall.get('southampton_mentions', 0)))
    avg_rank = overall.get('average_rank')
    avg_rank_text = '-' if avg_rank is None or pd.isna(avg_rank) else f'{float(avg_rank):.2f}'
    generated_at = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

    active_filters = [
        f'{escape(column)}: {escape(str(value))}'
        for column, value in (filters or {}).items()
        if column != 'PromptMentionType' and str(value) != 'All'
    ]
    filter_text = ' | '.join(active_filters) if active_filters else 'No sidebar filters applied'

    scopes = split_scope_frames(comparison_frame)
    scope_rows = []
    for scope in scopes:
        scope_metrics = compute_scope_metrics(scope.frame, owned_domains=owned_domains or ())
        pressure = scope_metrics['competitor_pressure_ratio']
        pressure_text = '-' if pressure is None else f'{float(pressure):.2f}'
        scope_rows.append(
            {
                'Scope': scope.label,
                'Responses': int(scope_metrics['responses']),
                'Prompts': int(scope_metrics['prompts']),
                'Presence (responses)': f"{float(scope_metrics['presence_rate_response']):.1f}% ({int(scope_metrics['mention_responses'])}/{int(scope_metrics['responses'])})",
                'Presence (prompts)': f"{float(scope_metrics['presence_rate_prompt']):.1f}% ({int(scope_metrics['mention_prompts'])}/{int(scope_metrics['prompts'])})",
                'Citation coverage': f"{float(scope_metrics['citation_coverage']):.1f}% ({int(scope_metrics['citation_responses'])}/{int(scope_metrics['responses'])})",
                'Owned source share': f"{float(scope_metrics['owned_source_share']):.1f}%",
                'Pressure ratio': pressure_text,
            }
        )
    scope_table = _render_table(
        pd.DataFrame(scope_rows),
        [
            'Scope',
            'Responses',
            'Prompts',
            'Presence (responses)',
            'Presence (prompts)',
            'Citation coverage',
            'Owned source share',
            'Pressure ratio',
        ],
    )

    recommendation_cards = _render_recommendation_cards(recommendations)
    evidence_cards = _render_evidence_cards(evidence)

    history_columns = [
        'Run', 'Responses', 'Prompts', 'Models', 'MentionRate', 'CitationRate',
        'ReputationScore', 'MentionRateChange', 'ReputationScoreChange',
    ]
    history_table = _render_table(history, history_columns)
    model_presence_table = _render_table(
        model_presence,
        [
            'Model', 'Responses', 'Mentions', 'Mention rate', 'Average prominence',
            'Recommendation rate', 'Shortlist rate', 'Citation rate',
        ],
    )

    eligible_responses = (
        int(target_signal['EligibleResponses'])
        if target_signal is not None
        else int(competitive_view['EligibleResponses'].max())
        if not competitive_view.empty
        else 0
    )
    target_mention_rate = float(target_signal['MentionRate']) if target_signal is not None else 0.0
    target_first_rate = float(target_signal['FirstMentionedRate']) if target_signal is not None else 0.0
    target_shortlist_rate = float(target_signal['ShortlistRate']) if target_signal is not None else 0.0
    top_competitor_name = str(top_competitor['Entity']) if top_competitor is not None else 'No recognised competitor'
    top_competitor_rate = float(top_competitor['MentionRate']) if top_competitor is not None else 0.0
    competitor_gap = top_competitor_rate - target_mention_rate

    top_market = market_scores.iloc[0] if not market_scores.empty else None
    top_subject = subject_scores.iloc[0] if not subject_scores.empty else None
    weakest_segment = segments.iloc[0] if not segments.empty else None
    high_priority_count = int(recommendations['Priority'].eq('High').sum()) if not recommendations.empty else 0
    narrative_items = [
        (
            f'The selected {escape(mention_mode)} view contains {len(scored_df):,} responses across '
            f'{prompts:,} prompts. {escape(organisation_name)} appears in '
            f"{int(presence_metrics['Mentions']):,} responses ({float(presence_metrics['MentionRate']):.1f}%)."
        ),
        (
            f"Citation coverage is {float(presence_metrics['CitationRate']):.1f}% of responses. "
            f"When {escape(organisation_name)} is mentioned, it is recommended in "
            f"{float(presence_metrics['RecommendationRate']):.1f}% and shortlisted in "
            f"{float(presence_metrics['ShortlistRate']):.1f}% of those mentions."
        ),
    ]
    if top_market is not None and top_subject is not None:
        narrative_items.append(
            f"The strongest visibility slices in this view are {escape(str(top_market['Market']))} by market "
            f"({float(top_market['visibility_score']):.1f}/100) and {escape(str(top_subject['Subject']))} by topic "
            f"({float(top_subject['visibility_score']):.1f}/100)."
        )
    if target_signal is not None and top_competitor is not None:
        mention_gap = float(top_competitor['MentionRate']) - float(target_signal['MentionRate'])
        narrative_items.append(
            f"In organisation-neutral responses, {escape(str(top_competitor['Entity']))} is the most-mentioned "
            f"competitor at {float(top_competitor['MentionRate']):.1f}%, a {mention_gap:.1f}-point lead over "
            f"{escape(organisation_name)}."
        )
    if weakest_segment is not None:
        segment_name = ' × '.join(escape(str(weakest_segment[column])) for column in segment_columns)
        narrative_items.append(
            f"The highest-priority diagnostic segment is {segment_name}, classified as "
            f"{escape(str(weakest_segment['Diagnosis']))} with an opportunity score of "
            f"{float(weakest_segment['OpportunityScore']):.1f}/100."
        )
    narrative_items.append(
        f'The action plan contains {len(recommendations)} prioritised moves, including {high_priority_count} high-priority actions.'
    )
    executive_narrative = '<ul class="narrative">' + ''.join(f'<li>{item}</li>' for item in narrative_items) + '</ul>'

    html = f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>{escape(organisation_name)} · AI Reputation Intelligence Report</title>
  <style>
    :root {{
      --bg: #f4f2f7;
      --card: #ffffff;
      --ink: #272331;
      --muted: #6f697a;
      --brand: #5b2c83;
      --brand-2: #7f4ea8;
      --accent: #00ab8e;
      --border: #e6dfec;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: var(--bg); color: var(--ink); font-family: Inter, Segoe UI, Arial, sans-serif; }}
    .shell {{ max-width: 1240px; margin: 0 auto; padding: 24px; }}
    .hero {{
      background: linear-gradient(135deg, var(--brand), var(--brand-2));
      color: white;
      border-radius: 16px;
      padding: 24px 28px;
      box-shadow: 0 12px 34px rgba(48, 38, 56, 0.2);
    }}
    .hero h1 {{ margin: 0 0 8px; font-size: 30px; }}
    .hero p {{ margin: 4px 0; color: #e6dcf0; }}
    .filters {{ font-size: 13px; color: #efe8f8; margin-top: 10px; }}
    .grid {{ display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 12px; margin: 18px 0 24px; }}
    .kpi {{ background: var(--card); border: 1px solid var(--border); border-radius: 14px; padding: 14px; }}
    .kpi .label {{ color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: .04em; }}
    .kpi .value {{ font-size: 28px; font-weight: 700; margin-top: 6px; color: var(--brand); }}
    .kpi .value-text {{ font-size: 18px; line-height: 1.35; overflow-wrap: break-word; }}
    .section {{ background: var(--card); border: 1px solid var(--border); border-radius: 14px; padding: 18px; margin-bottom: 14px; }}
    .section h2 {{ margin: 0 0 12px; color: var(--brand); }}
    .section p {{ margin: 8px 0; color: var(--muted); }}
    .section-intro {{ max-width: 900px; line-height: 1.55; }}
    .narrative {{ margin: 0; padding-left: 22px; }}
    .narrative li {{ margin: 0 0 10px; line-height: 1.55; }}
    .chart-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }}
    .bar-group {{ border: 1px solid var(--border); border-radius: 12px; padding: 12px; }}
    .bar-group h3 {{ margin: 2px 0 10px; font-size: 16px; color: var(--ink); }}
    .bar-row {{ margin: 0 0 10px; }}
    .bar-label {{ display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px; }}
    .bar-track {{ width: 100%; height: 10px; background: #ece7f1; border-radius: 999px; overflow: hidden; }}
    .bar-fill {{ height: 100%; background: linear-gradient(90deg, var(--brand), var(--accent)); }}
    .table-wrap {{ width: 100%; overflow-x: auto; }}
    table {{ width: 100%; min-width: 720px; border-collapse: collapse; font-size: 13px; }}
    th, td {{
      border-bottom: 1px solid var(--border);
      text-align: left;
      padding: 8px 6px;
      vertical-align: top;
      white-space: normal;
      overflow-wrap: break-word;
      word-break: normal;
      line-height: 1.45;
    }}
    th {{ color: var(--muted); font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: .03em; }}
    .detail-list {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }}
    .detail-card {{ border: 1px solid var(--border); border-radius: 12px; padding: 16px; min-width: 0; }}
    .detail-card h3 {{ margin: 0 0 10px; color: var(--brand); font-size: 17px; line-height: 1.4; }}
    .detail-meta {{ display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px; }}
    .detail-meta span {{ background: #f1ecf5; border-radius: 999px; padding: 4px 8px; color: var(--muted); font-size: 12px; }}
    .detail-label {{ margin: 12px 0 4px; color: var(--muted); font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .04em; }}
    .detail-text {{ margin: 0; color: var(--ink); white-space: pre-wrap; overflow-wrap: break-word; word-break: normal; line-height: 1.55; }}
    footer {{ color: var(--muted); font-size: 12px; padding: 6px 4px 26px; }}
    @media (max-width: 1100px) {{
      .grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .chart-grid {{ grid-template-columns: 1fr; }}
    }}
    @media (max-width: 760px) {{
      .detail-list {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <div class=\"shell\">
    <header class=\"hero\">
      <h1>AI Reputation Intelligence Report</h1>
      <p><strong>Organisation:</strong> {escape(organisation_name)} ({escape(org_id)})</p>
      <p><strong>Generated:</strong> {generated_at}</p>
      <div class=\"filters\"><strong>Prompt-bank scope:</strong> {escape(prompt_scope)} | <strong>Prompt mention view:</strong> {escape(mention_mode)} | <strong>Other filters:</strong> {filter_text}</div>
    </header>

    <section class=\"grid\">
      <div class=\"kpi\"><div class=\"label\">Overall visibility</div><div class=\"value\">{visibility:.1f}/100</div></div>
      <div class=\"kpi\"><div class=\"label\">Reputation score</div><div class=\"value\">{reputation:.1f}/100</div></div>
      <div class=\"kpi\"><div class=\"label\">Prompts in view</div><div class=\"value\">{prompts}</div></div>
      <div class=\"kpi\"><div class=\"label\">Organisation mentions</div><div class=\"value\">{mentions}</div></div>
      <div class=\"kpi\"><div class=\"label\">Average rank</div><div class=\"value\">{avg_rank_text}</div></div>
    </section>

    <section class=\"section\">
      <h2>Executive summary</h2>
      <p class=\"section-intro\">This narrative uses the same selected view as the Executive dashboard, Visibility analysis, Topic and persona diagnostics, and Recommendations pages. Competitor findings use the app's separate organisation-neutral methodology.</p>
      {executive_narrative}
    </section>

    <section class=\"section\">
      <h2>Scope and measurement</h2>
      <p class=\"section-intro\">The headline cards use the selected <strong>{escape(mention_mode)}</strong> prompt mention view. The table keeps the other active filters but compares All, Organic, and Prompted/direct results side by side, matching the live visibility pages.</p>
      {scope_table}
      <p class=\"section-intro\"><strong>Metric definitions:</strong> visibility is the percentage of captured responses that mention the organisation. Reputation combines visibility (50%), placement or rank (30%), and citation presence (20%). Lower average rank is better. Recommendation, shortlist, and positive-association rates use organisation mentions as their denominator.</p>
    </section>

    <section class="section">
      <h2>Presence: Visibility Diagnostics</h2>
      <p class="section-intro">These signals and segment scores use the selected <strong>{escape(mention_mode)}</strong> view and the same formulas as Visibility analysis.</p>
      <section class="grid">
        <div class="kpi"><div class="label">Mention rate</div><div class="value">{float(presence_metrics['MentionRate']):.1f}%</div></div>
        <div class="kpi"><div class="label">Recommended when mentioned</div><div class="value">{float(presence_metrics['RecommendationRate']):.1f}%</div></div>
        <div class="kpi"><div class="label">Shortlisted when mentioned</div><div class="value">{float(presence_metrics['ShortlistRate']):.1f}%</div></div>
        <div class="kpi"><div class="label">Citation coverage</div><div class="value">{float(presence_metrics['CitationRate']):.1f}%</div></div>
        <div class="kpi"><div class="label">Positive association</div><div class="value">{float(presence_metrics['PositiveAssociationRate']):.1f}%</div></div>
      </section>
      <div class="chart-grid">
        {_render_bar_group(market_scores, 'Market', 'Visibility by market', max_value=100.0)}
        {_render_bar_group(subject_scores, 'Subject', 'Visibility by subject', max_value=100.0)}
      </div>
      <h3>Presence signals by model</h3>
      {model_presence_table}
    </section>

    <section class="section">
      <h2>Topic and persona diagnostics</h2>
      <p class="section-intro">Segments are ordered by opportunity score, matching the diagnostics page. A gap means the organisation is absent, weakly placed, poorly cited, or associated less positively in that segment.</p>
      {segment_table}
    </section>

    <section class="section">
      <h2>Competitive presence</h2>
      <p class="section-intro">Like the Competitor analysis page, this section excludes prompts that explicitly name the organisation or a configured competitor. It uses {eligible_responses:,} organisation-neutral responses and is not changed by the selected prompt mention view.</p>
      <section class="grid">
        <div class="kpi"><div class="label">{escape(organisation_name)} mention rate</div><div class="value">{target_mention_rate:.1f}%</div></div>
        <div class="kpi"><div class="label">First-mentioned share</div><div class="value">{target_first_rate:.1f}%</div></div>
        <div class="kpi"><div class="label">Shortlist share</div><div class="value">{target_shortlist_rate:.1f}%</div></div>
        <div class="kpi"><div class="label">Top competitor</div><div class="value value-text">{escape(top_competitor_name)}</div></div>
        <div class="kpi"><div class="label">Mention-rate gap</div><div class="value">{competitor_gap:.1f}pp</div></div>
      </section>
      {_render_bar_group(competitive_view, 'Entity', 'Organisation-neutral mention rate', value_column='MentionRate', max_value=100.0)}
      {competitive_table}
    </section>

    <section class="section">
      <h2>Priority moves: Recommendations</h2>
      <p class="section-intro">These actions are generated from the same selected response set as the Recommendations page. They are evidence-led hypotheses rather than guarantees about proprietary model behaviour. Calculated targets are measurement thresholds, not forecasts, and require matched reruns.</p>
      {recommendation_cards}
    </section>

    <section class="section">
      <h2>Evidence register</h2>
      <p class="section-intro">Full response-level strengths and gaps used to ground the diagnostics and action plan. Text is shown in full.</p>
      {evidence_cards}
    </section>

    <section class=\"section\">
      <h2>Run-over-run tracking</h2>
      <p class=\"section-intro\">Captured run dates are summarised using the same measures as the Recommendations page. Change columns compare each run with the preceding captured run.</p>
      {history_table}
    </section>

    <footer>
      Rendered microsite export generated by AI Reputation Intelligence Platform. This static package is read-only.
    </footer>
  </div>
</body>
</html>
"""
    return html


def _measurement_frame(frame: pd.DataFrame) -> pd.DataFrame:
    working = frame.copy()
    defaults: dict[str, object] = {
        'Mentioned': working['visible_bool'] if 'visible_bool' in working.columns else False,
        'Recommended': False,
        'Shortlisted': False,
        'CitationPresent': (
            working['citation_score_row'].fillna(0).gt(0)
            if 'citation_score_row' in working.columns
            else False
        ),
        'AssociationLabel': 'Not available',
        'ProminenceScore': working['rank_score_row'] if 'rank_score_row' in working.columns else 0,
    }
    for column, default in defaults.items():
        if column not in working.columns:
            working[column] = default
    for column in ['Mentioned', 'Recommended', 'Shortlisted', 'CitationPresent']:
        working[column] = working[column].fillna(False).astype(bool)
    working['AssociationLabel'] = working['AssociationLabel'].fillna('Not available').astype(str)
    working['ProminenceScore'] = pd.to_numeric(working['ProminenceScore'], errors='coerce').fillna(0)
    return working


def _presence_metrics(frame: pd.DataFrame) -> dict[str, float | int]:
    working = _measurement_frame(frame)
    responses = int(len(working))
    mentions = int(working['Mentioned'].sum())
    mention_denominator = max(mentions, 1)
    return {
        'Responses': responses,
        'Mentions': mentions,
        'MentionRate': mentions / responses * 100 if responses else 0.0,
        'RecommendationRate': float(working['Recommended'].sum()) / mention_denominator * 100,
        'ShortlistRate': float(working['Shortlisted'].sum()) / mention_denominator * 100,
        'CitationRate': float(working['CitationPresent'].sum()) / responses * 100 if responses else 0.0,
        'PositiveAssociationRate': (
            float(working.loc[working['Mentioned'], 'AssociationLabel'].eq('Positive').sum())
            / mention_denominator
            * 100
        ),
        'AverageProminence': float(working['ProminenceScore'].mean()) if responses else 0.0,
    }


def _presence_by_model(frame: pd.DataFrame) -> pd.DataFrame:
    columns = [
        'Model', 'Responses', 'Mentions', 'Mention rate', 'Average prominence',
        'Recommendation rate', 'Shortlist rate', 'Citation rate',
    ]
    if frame.empty or 'ModelName' not in frame.columns:
        return pd.DataFrame(columns=columns)

    rows = []
    for model_name, model_frame in frame.groupby('ModelName', dropna=False):
        metrics = _presence_metrics(model_frame)
        rows.append(
            {
                'Model': MODEL_LABELS.get(str(model_name), str(model_name)),
                'Responses': int(metrics['Responses']),
                'Mentions': int(metrics['Mentions']),
                'Mention rate': round(float(metrics['MentionRate']), 1),
                'Average prominence': round(float(metrics['AverageProminence']), 1),
                'Recommendation rate': round(float(metrics['RecommendationRate']), 1),
                'Shortlist rate': round(float(metrics['ShortlistRate']), 1),
                'Citation rate': round(float(metrics['CitationRate']), 1),
            }
        )
    return pd.DataFrame(rows, columns=columns).sort_values('Mention rate', ascending=False).reset_index(drop=True)


def _render_table(frame: pd.DataFrame, columns: list[str]) -> str:
    if frame.empty:
        return '<p>No records available for this filtered view.</p>'

    available_columns = [column for column in columns if column in frame.columns]
    if not available_columns:
        return '<p>No table columns are available for this section.</p>'

    view = frame[available_columns].copy()
    for column in view.columns:
        if pd.api.types.is_numeric_dtype(view[column]):
            view[column] = view[column].map(lambda value: f'{float(value):.1f}' if not pd.isna(value) else '-')
        else:
            view[column] = view[column].fillna('').astype(str)

    header = ''.join(f'<th>{escape(column)}</th>' for column in view.columns)
    rows = []
    for _, row in view.iterrows():
        cells = ''.join(f'<td>{escape(str(row[column]))}</td>' for column in view.columns)
        rows.append(f'<tr>{cells}</tr>')

    table = '<table><thead><tr>' + header + '</tr></thead><tbody>' + ''.join(rows) + '</tbody></table>'
    return f'<div class="table-wrap">{table}</div>'


def _html_text(value: object, *, fallback: str = '') -> str:
    if value is None or (not isinstance(value, (list, tuple, dict)) and pd.isna(value)):
        return escape(fallback)
    text = str(value).strip()
    return escape(text if text else fallback)


def _metadata_badges(row: pd.Series, columns: list[str]) -> str:
    badges = []
    for column in columns:
        value = _html_text(row.get(column))
        if value:
            badges.append(f'<span><strong>{escape(column)}:</strong> {value}</span>')
    return ''.join(badges)


def _render_evidence_cards(frame: pd.DataFrame) -> str:
    if frame.empty:
        return '<p>No evidence records are available for this filtered view.</p>'

    cards = []
    for _, row in frame.iterrows():
        outlier_type = _html_text(row.get('OutlierType'), fallback='Evidence')
        score = _html_text(row.get('OutlierScore'))
        score_suffix = f' · Score {score}' if score else ''
        reason = _html_text(row.get('OutlierReason'), fallback='No reason recorded.')
        response = _html_text(row.get('ResponseText'), fallback='No response text recorded.')
        metadata = _metadata_badges(row, ['PromptID', 'ModelName', 'Persona', 'Subject', 'Market'])
        cards.append(
            '<article class="detail-card">'
            f'<h3>{outlier_type}{score_suffix}</h3>'
            f'<div class="detail-meta">{metadata}</div>'
            '<div class="detail-label">Why this matters</div>'
            f'<p class="detail-text">{reason}</p>'
            '<div class="detail-label">Full response</div>'
            f'<p class="detail-text">{response}</p>'
            '</article>'
        )
    return f'<div class="detail-list">{"".join(cards)}</div>'


def _render_recommendation_cards(frame: pd.DataFrame) -> str:
    if frame.empty:
        return '<p>No recommendations are available for this filtered view.</p>'

    cards = []
    for _, row in frame.iterrows():
        action = _html_text(row.get('Action'), fallback='Recommended action')
        evidence = _html_text(row.get('Evidence'), fallback='No supporting evidence recorded.')
        objective = _html_text(row.get('Objective'), fallback='No objective recorded.')
        rationale = _html_text(row.get('Why this may matter'), fallback='No rationale recorded.')
        method_basis = _html_text(row.get('Method basis'), fallback='No method basis recorded.')
        target_calculation = _html_text(row.get('Target calculation'), fallback='No target calculation recorded.')
        validation_method = _html_text(row.get('Validation method'), fallback='No validation method recorded.')
        action_plan = _html_text(row.get('Action plan'), fallback='No action plan recorded.')
        metadata = _metadata_badges(
            row,
            ['Priority', 'Intervention level', 'Category', 'Scope', 'Affected signal', 'Evidence strength', 'Confidence', 'Owner', 'Timing'],
        )
        cards.append(
            '<article class="detail-card">'
            f'<h3>{action}</h3>'
            f'<div class="detail-meta">{metadata}</div>'
            '<div class="detail-label">Supporting evidence</div>'
            f'<p class="detail-text">{evidence}</p>'
            '<div class="detail-label">Objective</div>'
            f'<p class="detail-text">{objective}</p>'
            '<div class="detail-label">Why this may matter</div>'
            f'<p class="detail-text">{rationale}</p>'
            '<div class="detail-label">Method basis</div>'
            f'<p class="detail-text">{method_basis}</p>'
            '<div class="detail-label">Action plan</div>'
            f'<p class="detail-text">{action_plan}</p>'
            '<div class="detail-label">Target calculation</div>'
            f'<p class="detail-text">{target_calculation}</p>'
            '<div class="detail-label">Validation method</div>'
            f'<p class="detail-text">{validation_method}</p>'
            '</article>'
        )
    return f'<div class="detail-list">{"".join(cards)}</div>'


def _render_bar_group(
    frame: pd.DataFrame,
    label_column: str,
    title: str,
    *,
    value_column: str = 'visibility_score',
    max_value: float | None = None,
) -> str:
    if frame.empty or label_column not in frame.columns or value_column not in frame.columns:
        return f'<div class="bar-group"><h3>{escape(title)}</h3><p>No records available.</p></div>'

    values = pd.to_numeric(frame[value_column], errors='coerce').fillna(0)
    scale_max = max_value if max_value is not None else max(float(values.max()), 1.0)
    rows = []
    for _, row in frame.iterrows():
        label = escape(str(row.get(label_column, 'Unknown')))
        value = float(pd.to_numeric(row.get(value_column), errors='coerce') or 0)
        width = max(0.0, min(100.0, value / scale_max * 100.0))
        rows.append(
            '<div class="bar-row">'
            f'<div class="bar-label"><span>{label}</span><span>{value:.1f}</span></div>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{width:.1f}%"></div></div>'
            '</div>'
        )

    return f'<div class="bar-group"><h3>{escape(title)}</h3>{"".join(rows)}</div>'
