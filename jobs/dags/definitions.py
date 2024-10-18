from dagster import Definitions, load_assets_from_modules

from . import refresh_slack_tokens
from .refresh_slack_tokens import assets, slack_refresh_job, slack_refresh_schedule

all_assets = load_assets_from_modules([refresh_slack_tokens])

defs = Definitions(
    assets=assets,
    jobs=[slack_refresh_job],
    schedules=[slack_refresh_schedule],
)
