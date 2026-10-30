"""Readable UK-local run dates; persisted timestamps remain in UTC."""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


def format_run_timestamp(value):
    if not value:
        return '—'
    try:
        instant = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    except ValueError:
        return 'Unknown date'
    if instant.tzinfo is None:
        instant = instant.replace(tzinfo=timezone.utc)
    return instant.astimezone(ZoneInfo('Europe/London')).strftime('%d %b %Y, %H:%M:%S %Z')


def dated_run_name(run):
    return f"{run['name']} · {format_run_timestamp(run.get('created_at'))}"


def run_timing_caption(run):
    parts = [f"Created {format_run_timestamp(run.get('created_at'))}"]
    for field, label in (('started_at', 'Started'), ('finished_at', 'Last execution finished')):
        if run.get(field):
            parts.append(f"{label} {format_run_timestamp(run[field])}")
    return ' · '.join(parts)
