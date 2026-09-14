from __future__ import annotations

import json

from streamlit.testing.v1 import AppTest


def _load_dashboard(org_id: str = 'southampton') -> AppTest:
    app = AppTest.from_file('pages/04_Executive_Dashboard.py')
    app.run(timeout=30)
    app.session_state['active_org_id'] = org_id
    return app.run(timeout=60)


def test_executive_dashboard_renders_without_errors_and_resolves_top_competitor() -> None:
    app = _load_dashboard()

    assert not app.exception
    assert not app.error

    metrics = {metric.label: metric.value for metric in app.metric}
    assert metrics['Most-mentioned competitor'] != '-'
    assert metrics['Competitor lead (index points)'] != '-'


def test_executive_competitor_chart_uses_one_explicit_order_for_bars_and_labels() -> None:
    app = _load_dashboard()
    layered_specs = [
        json.loads(chart.proto.spec)
        for chart in app.get('vega_lite_chart')
        if '"layer"' in chart.proto.spec
    ]

    assert len(layered_specs) == 1
    spec = layered_specs[0]
    bar_order = spec['layer'][0]['encoding']['y']['sort']
    label_order = spec['layer'][1]['encoding']['y']['sort']
    assert bar_order == label_order
    assert isinstance(bar_order, list)
    assert bar_order
    assert spec['layer'][0]['encoding']['x']['scale']['domain'] == [0, 110]
