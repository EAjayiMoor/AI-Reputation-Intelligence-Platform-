from __future__ import annotations

from pathlib import Path


def test_recommendations_page_exposes_evidence_and_target_methodology() -> None:
    source = Path('pages/09_Recommendations.py').read_text(encoding='utf-8')

    assert 'Expected lift score' not in source
    assert 'Why this may matter' in source
    assert 'Target calculation' in source
    assert 'Evidence strength' in source
    assert 'Method basis' in source
    assert 'measurement threshold, not a forecast' in source


def test_microsite_export_includes_intervention_logic() -> None:
    source = Path('src/export/rendered_microsite.py').read_text(encoding='utf-8')

    assert "row.get('Why this may matter')" in source
    assert "row.get('Method basis')" in source
    assert "row.get('Target calculation')" in source
    assert "row.get('Validation method')" in source
