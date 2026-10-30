"""Saved runs offered as demo entry points on Start."""

DEMO_RUNS = (
    {
        'label': 'Demo Careers',
        'scenario': 'careers',
        'description': 'Explore careers and employability across markets, subjects and student personas.',
        'org_id': 'southampton',
        'run_id': '20261029T213634_06a312c914f94a929b4a32c94e12e1dd',
    },
    {
        'label': 'Demo Research',
        'scenario': 'research',
        'description': 'Explore research reputation and partnerships across the nine Southampton subject areas.',
        'org_id': 'southampton',
        'run_id': '20261029T213634_daaaee1c60dd4bc6ac2d5f274f7e74e8',
    },
)


def demo_for_run(org_id, run_id):
    return next((demo for demo in DEMO_RUNS
                 if demo['org_id'] == org_id and demo['run_id'] == run_id), None)
