from dagster import Definitions, load_assets_from_modules

from jobs.dags.refresh_slack_tokens import slack_refresh_all_near_expired, slack_refresh_job, slack_refresh_schedule

defs = Definitions(
    jobs=[slack_refresh_job],
    schedules=[slack_refresh_schedule],
    assets=[slack_refresh_all_near_expired]
)
