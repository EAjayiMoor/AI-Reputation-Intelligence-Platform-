from __future__ import annotations

import streamlit as st

MOORHOUSE_PURPLE = '#3c1053'
MOORHOUSE_PURPLE_SCALE = [
    '#f5f3f6',
    '#ebe4ef',
    '#ded1e5',
    '#cfb9d9',
    '#bd9aca',
    '#a879ba',
    '#8e55a8',
    '#733397',
    '#5c068c',
    '#3c1053',
]

METRIC_DEFINITIONS = {
    'visibility': (
        'The percentage of captured model responses that mention the University of Southampton. '
        'It is scored from 0 to 100 and includes every captured response in the current filters.'
    ),
    'reputation': (
        'A score out of 100 combining visibility (50%), placement or rank (30%) and citation presence (20%). '
        'It is a directional benchmark for this captured prompt set, not a general reputation survey.'
    ),
    'average_rank': (
        'The mean explicit list position when Southampton is mentioned and a position can be extracted. '
        'Lower is better; 1 is the top position. Unranked mentions and absent responses are excluded.'
    ),
    'total_prompts': (
        'The number of unique prompts in the current v2 prompt bank, regardless of how many models answered each prompt.'
    ),
    'prompts_in_view': (
        'The number of unique prompts remaining after the prompt mention mode and sidebar filters are applied.'
    ),
    'mentions': (
        'The number of captured model responses in the current filters that mention the University of Southampton.'
    ),
    'rank_score': (
        'A placement score out of 100: rank 1 = 100, 2 = 90, 3 = 80, 4–5 = 70, 6–10 = 50, '
        'an unranked visible mention = 40, and no mention = 0.'
    ),
    'citation_score': (
        'The percentage of captured responses with at least one extracted citation or source, scored from 0 to 100.'
    ),
}


def apply_moorhouse_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
            --mh-brand: #3c1053;
            --mh-brand-contrast: #ffffff;
            --mh-brand-accent: #00ab8e;
            --mh-brand-purple: #5c068c;
            --mh-brand-muted: #bdb6b9;
            --mh-brand-orange: #e48949;
            --mh-brand-ocean: #186e7e;
            --mh-background: #fbfafb;
            --mh-foreground: #181018;
            --mh-surface: #ffffff;
            --mh-surface-muted: #f5f3f6;
            --mh-border: rgba(60, 16, 83, 0.12);
            --mh-border-strong: rgba(60, 16, 83, 0.20);
            --mh-text-muted: #71717a;
            --mh-focus: #00ab8e;
            --mh-radius-sm: 4px;
            --mh-radius-md: 6px;
            --mh-radius-lg: 8px;
        }

        html, body, [class*="css"] {
            font-family: 'Poppins', 'Segoe UI', sans-serif;
            color: var(--mh-foreground);
            background: var(--mh-background);
        }

        .stApp {
            background: var(--mh-background);
        }

        .block-container {
            max-width: 1280px;
            padding-top: 1.5rem;
            padding-bottom: 2rem;
        }

        h1 {
            color: var(--mh-brand);
            letter-spacing: -0.01em;
            font-weight: 600;
            font-size: 28px;
            line-height: 1.15;
            margin-bottom: 0.25rem;
        }

        h2, h3 {
            color: var(--mh-brand);
            letter-spacing: -0.005em;
            font-weight: 600;
        }

        h2 {
            font-size: 20px;
            line-height: 1.2;
        }

        h3 {
            font-size: 18px;
            line-height: 1.25;
            letter-spacing: 0;
        }

        .mh-page-header {
            background: var(--mh-surface);
            border: 1px solid var(--mh-border);
            border-radius: var(--mh-radius-lg);
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 1px 0 rgba(0, 0, 0, 0.03);
            width: 100%;
            max-width: 100%;
        }

        .mh-title-row {
            display: flex;
            align-items: center;
            gap: 0.6rem;
        }

        .mh-icon-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 2rem;
            height: 2rem;
            padding: 0 0.35rem;
            border-radius: 9999px;
            background: rgba(0, 171, 142, 0.12);
            color: var(--mh-brand-accent);
            font-size: 1rem;
            line-height: 1;
        }

        .mh-eyebrow {
            font-size: 11px;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: var(--mh-brand-accent);
            margin-bottom: 4px;
            font-weight: 600;
        }

        .mh-subtitle {
            color: var(--mh-text-muted);
            font-size: 13px;
            margin-top: 2px;
        }

        .mh-callout {
            background: var(--mh-surface);
            border: 1px solid var(--mh-border);
            border-left: 4px solid var(--mh-brand-accent);
            border-radius: var(--mh-radius-sm);
            padding: 12px 14px;
            color: var(--mh-foreground);
            margin: 0 0 1rem 0;
        }

        .mh-callout p,
        .mh-callout li,
        .mh-callout strong {
            color: var(--mh-foreground);
        }

        a, a:visited {
            color: var(--mh-brand);
            text-decoration: none;
        }

        a:hover {
            color: var(--mh-brand-purple);
        }

        div[data-testid="stStatusWidget"] {
            background: var(--mh-surface);
            border: 1px solid var(--mh-border);
            border-left: 4px solid var(--mh-brand-accent);
            color: var(--mh-foreground);
        }

        div[data-testid="stStatusWidget"] p {
            color: var(--mh-foreground);
        }

        div[data-testid="stMetric"] {
            background: var(--mh-surface);
            border: 1px solid var(--mh-border);
            border-radius: var(--mh-radius-sm);
            padding: 10px 12px;
            box-shadow: none;
        }

        div[data-testid="stMetricLabel"] {
            color: var(--mh-text-muted);
            font-weight: 500;
        }

        div[data-testid="stMetricValue"] {
            color: var(--mh-brand);
            font-weight: 600;
        }

        .stDataFrame, .stPlotlyChart {
            background: var(--mh-surface);
            border: 1px solid var(--mh-border);
            border-radius: var(--mh-radius-sm);
            padding: 6px;
        }

        .stButton > button, .stDownloadButton > button {
            background: var(--mh-brand);
            color: var(--mh-brand-contrast);
            border-radius: var(--mh-radius-sm);
            border: 1px solid var(--mh-brand);
            font-weight: 600;
            padding: 0.4rem 0.8rem;
        }

        .stButton > button:hover, .stDownloadButton > button:hover {
            background: var(--mh-brand-purple);
            border-color: var(--mh-brand-purple);
            color: var(--mh-brand-contrast);
        }

        .stButton > button:focus, .stDownloadButton > button:focus,
        .stSelectbox div[data-baseweb="select"]:focus-within,
        .stTextInput input:focus,
        .stNumberInput input:focus,
        .stDateInput input:focus {
            outline: 2px solid var(--mh-focus) !important;
            outline-offset: 2px;
        }

        .stTabs [role="tablist"] button {
            color: var(--mh-foreground);
            border-radius: var(--mh-radius-sm);
        }

        .stTabs [role="tablist"] .st-emotion-cache-1t0v0g2[aria-selected="true"] {
            color: var(--mh-brand);
            border-bottom: 2px solid var(--mh-brand-accent);
        }

        [data-testid="stSidebar"] {
            background: var(--mh-surface-muted);
            border-right: 1px solid var(--mh-border);
        }

        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {
            color: var(--mh-brand);
        }

        [data-testid="stSidebar"] [data-testid="stSidebarNav"] a {
            color: var(--mh-foreground);
            border-radius: var(--mh-radius-sm);
            padding: 0.35rem 0.55rem;
            text-decoration: none;
            font-weight: 500;
        }

        [data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover {
            background: rgba(60, 16, 83, 0.08);
            color: var(--mh-brand);
        }

        [data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] {
            background: rgba(0, 171, 142, 0.12);
            color: var(--mh-brand);
            font-weight: 600;
        }

        [data-testid="stSidebar"] .stSelectbox > div {
            border: 1px solid var(--mh-border-strong);
            border-radius: var(--mh-radius-sm);
        }

        .stAlert {
            border-radius: var(--mh-radius-sm);
            border: 1px solid var(--mh-border);
        }

        .stCaption {
            color: var(--mh-text-muted);
        }

        .stDataFrame [data-testid="stBaseButton-secondary"] {
            border-radius: var(--mh-radius-sm);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(
    title: str,
    subtitle: str,
    eyebrow: str = 'Moorhouse analytics',
    icon: str = '',
) -> None:
    title_block = f"<div class='mh-title-row'><span class='mh-icon-badge'>{icon}</span><h1>{title}</h1></div>" if icon else f'<h1>{title}</h1>'
    st.markdown(
        f"""
        <div class='mh-page-header'>
            <div class='mh-eyebrow'>{eyebrow}</div>
            {title_block}
            <div class='mh-subtitle'>{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_definitions(*, include_components: bool = False) -> None:
    """Render a consistent, plain-English explanation of scorecard metrics."""
    with st.expander('How these metrics are calculated', icon=':material/info:'):
        st.markdown(f"**Overall visibility score**  \n{METRIC_DEFINITIONS['visibility']}")
        st.markdown(f"**Reputation score**  \n{METRIC_DEFINITIONS['reputation']}")
        st.markdown(f"**Average rank**  \n{METRIC_DEFINITIONS['average_rank']}")
        st.markdown(f"**Prompts in view**  \n{METRIC_DEFINITIONS['prompts_in_view']}")
        st.markdown(f"**Southampton mentions**  \n{METRIC_DEFINITIONS['mentions']}")
        if include_components:
            st.markdown(f"**Rank score**  \n{METRIC_DEFINITIONS['rank_score']}")
            st.markdown(f"**Citation score**  \n{METRIC_DEFINITIONS['citation_score']}")
