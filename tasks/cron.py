"""Manage configured user and root crontab entries.

Configuration uses host.data["cron_jobs"], a list of jobs with a stable
name, command, scope ("user" or "root"), and a cron schedule. User-scoped
jobs are installed in the configured deployment user's crontab; root-scoped
jobs are installed in root's crontab. pyinfra's crontab operation handles
drift detection and updates entries by their stable cron_name.
"""

from pyinfra import host
from pyinfra.operations import crontab


SCHEDULE_FIELDS = (
    "minute",
    "hour",
    "month",
    "day_of_week",
    "day_of_month",
    "special_time",
)
ALLOWED_FIELDS = {"name", "command", "scope", "present", *SCHEDULE_FIELDS}


jobs = host.data.get("cron_jobs", [])

if not isinstance(jobs, list):
    raise ValueError("cron_jobs must be a list")

seen_jobs = set()

for job in jobs:
    if not isinstance(job, dict):
        raise ValueError("Each cron job must be a dictionary")

    unknown_fields = set(job) - ALLOWED_FIELDS
    if unknown_fields:
        raise ValueError(
            f"Unsupported cron job fields: {', '.join(sorted(unknown_fields))}"
        )

    name = job.get("name")
    command = job.get("command")
    scope = job.get("scope", "user")
    present = job.get("present", True)

    if not isinstance(name, str) or not name.strip() or any(
        character in name for character in ("\\n", "\\r")
    ):
        raise ValueError("Every cron job requires a single-line name")

    if not isinstance(command, str) or not command.strip() or any(
        character in command for character in ("\\n", "\\r")
    ):
        raise ValueError(f"Cron job {name!r} requires a single-line command")

    if scope not in ("user", "root"):
        raise ValueError(f"Invalid cron scope for {name}: {scope}")

    if not isinstance(present, bool):
        raise ValueError(f"Cron job present must be a boolean: {name}")

    target_user = "root" if scope == "root" else host.data.get("username")
    if not isinstance(target_user, str) or not target_user.strip():
        raise ValueError(
            f"Cron job {name!r} uses user scope but username is not configured"
        )

    identity = (target_user, name)
    if identity in seen_jobs:
        raise ValueError(f"Duplicate cron job name for {target_user}: {name}")
    seen_jobs.add(identity)

    schedule = {
        field: job[field]
        for field in SCHEDULE_FIELDS
        if field in job
    }

    if "special_time" in schedule and len(schedule) > 1:
        raise ValueError(
            f"Cron job {name!r} cannot combine special_time with a field schedule"
        )

    for field, value in schedule.items():
        values = value if isinstance(value, list) else [value]
        if not values or any(
            isinstance(item, bool)
            or not isinstance(item, (str, int))
            or (isinstance(item, str) and any(
                character in item for character in ("\\n", "\\r")
            ))
            for item in values
        ):
            raise ValueError(f"Invalid cron schedule value for {name}: {field}")

    crontab.crontab(
        name=f"Manage cron job: {name}",
        cron_name=name,
        command=command,
        present=present,
        user=target_user,
        _sudo=True,
        **schedule,
    )
