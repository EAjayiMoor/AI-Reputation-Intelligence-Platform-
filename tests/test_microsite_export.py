from __future__ import annotations

import re
from pathlib import Path
from zipfile import ZipFile

import pandas as pd
from streamlit.testing.v1 import AppTest

from src.export import build_microsite_archive, build_rendered_microsite_archive, missing_microsite_assets


def test_microsite_export_page_keeps_prompt_scope_as_text() -> None:
    app = AppTest.from_file('pages/11_Microsite_Export.py')
    app.run(timeout=30)
    app.session_state['active_org_id'] = 'southampton'
    app.run(timeout=60)

    assert not app.exception
    assert not app.error


def test_microsite_archive_builds_with_expected_entries(tmp_path: Path) -> None:
    docs = tmp_path / 'docs'
    snapshots = docs / 'app_snapshots'
    snapshots.mkdir(parents=True)

    (docs / 'static_app_replica.html').write_text('<html><body>ok</body></html>', encoding='utf-8')
    (snapshots / '01_dashboard.png').write_bytes(b'png-a')
    (snapshots / '02_recommendations.png').write_bytes(b'png-b')

    archive_bytes = build_microsite_archive(tmp_path)

    archive_path = tmp_path / 'microsite.zip'
    archive_path.write_bytes(archive_bytes)
    with ZipFile(archive_path, mode='r') as archive:
        names = set(archive.namelist())

    assert 'microsite/index.html' in names
    assert 'microsite/assets/01_dashboard.png' in names
    assert 'microsite/assets/02_recommendations.png' in names


def test_missing_assets_reports_paths(tmp_path: Path) -> None:
    missing = missing_microsite_assets(tmp_path)
    assert any('static_app_replica.html' in item for item in missing)
    assert any('app_snapshots' in item for item in missing)


def test_rendered_microsite_archive_contains_report_sections(tmp_path: Path) -> None:
    long_response = (
        'Southampton is recommended and shortlisted. '
        + 'This supporting explanation remains readable in the exported report. ' * 8
        + 'END-OF-FULL-RESPONSE'
    )
    frame = pd.DataFrame(
        [
            {
                'PromptID': 'P1',
                'Market': 'UK',
                'Subject': 'Engineering',
                'ModelName': 'model-a',
                'PromptMentionType': 'Organic',
                'CompetitorPromptEligible': True,
                'CompetitorsMentioned': 'Comp One; Comp Two',
                'CitationSources': 'https://example.com',
                'ResponseText': long_response,
                'visible_bool': True,
                'rank_float': 2,
                'visibility_score_row': 100,
                'rank_score_row': 90,
                'citation_score_row': 100,
                'reputation_score_row': 97,
            },
            {
                'PromptID': 'P2',
                'Market': 'US',
                'Subject': 'Business',
                'ModelName': 'model-a',
                'PromptMentionType': 'Organic',
                'CompetitorPromptEligible': True,
                'CompetitorsMentioned': 'Comp One',
                'CitationSources': '',
                'ResponseText': 'No mention in this response.',
                'visible_bool': False,
                'rank_float': None,
                'visibility_score_row': 0,
                'rank_score_row': 0,
                'citation_score_row': 0,
                'reputation_score_row': 0,
            },
        ]
    )

    archive_bytes = build_rendered_microsite_archive(
        scored_df=frame,
        scope_df=pd.concat(
            [
                frame,
                frame.iloc[[1]].assign(
                    PromptID='P3',
                    PromptMentionType='Prompted/direct',
                ),
            ],
            ignore_index=True,
        ),
        organisation_name='University of Southampton',
        org_id='southampton',
        prompt_scope='Combined',
        mention_mode='Organic',
        filters={'Market': 'All'},
    )
    archive_path = tmp_path / 'rendered_microsite.zip'
    archive_path.write_bytes(archive_bytes)

    with ZipFile(archive_path, mode='r') as archive:
        html = archive.read('microsite/index.html').decode('utf-8')

    assert 'AI Reputation Intelligence Report' in html
    assert 'Visibility Diagnostics' in html
    assert 'Recommendations' in html
    assert 'Leader evidence matrix' in html
    assert 'END-OF-FULL-RESPONSE' in html
    assert '<div class="detail-list">' in html
    assert '<div class="table-wrap">' in html
    assert 'Prompt mention view:</strong> Organic' in html
    assert 'The selected Organic view contains 2 responses across 2 prompts.' in html
    assert re.search(r'<td>Prompted/direct</td><td>1\.0</td>', html)
    assert 'Topic and persona diagnostics' in html
    assert 'Competitive presence' in html
    assert 'Run-over-run tracking' in html
