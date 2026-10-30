from src.ui.run_dates import dated_run_name, format_run_timestamp, run_timing_caption


def test_run_dates_convert_utc_to_gmt_and_bst():
    assert format_run_timestamp('2026-10-29T21:36:34+00:00') == '29 Oct 2026, 21:36:34 GMT'
    assert format_run_timestamp('2026-07-01T23:30:00Z') == '02 Jul 2026, 00:30:00 BST'


def test_missing_legacy_dates_do_not_break_run_labels():
    assert format_run_timestamp(None) == '—'
    assert format_run_timestamp('invalid') == 'Unknown date'
    assert format_run_timestamp('2026-10-29T21:36:34') == '29 Oct 2026, 21:36:34 GMT'
    run = {'name': 'Test', 'created_at': '2026-10-29T21:36:34Z'}
    assert dated_run_name(run) == 'Test · 29 Oct 2026, 21:36:34 GMT'
    assert run_timing_caption(run) == 'Created 29 Oct 2026, 21:36:34 GMT'
