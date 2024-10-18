import json
import os
import dotenv
import requests

from dagster import (
    AssetExecutionContext,
    AssetKey,
    AssetSelection,
    Config,
    DefaultScheduleStatus,
    Definitions,
    JsonMetadataValue,
    MaterializeResult,
    MetadataValue,
    ScheduleDefinition,
    asset,
    define_asset_job,
    materialize,
)
from library.data.external.slack import Slack
from library.data.local.neo4j import Neo4j

from globals import Globals
from library.enums.data_sources import DataSources
from library.models.api_models import OAuthCreds
from library.models.employee import User

# dotenv.load_dotenv(dotenv_path=Globals().root_resource(".env"))

def creds_to_json(creds: OAuthCreds) -> dict[str, any]:
    obj = creds.model_dump()
    obj["expiry"] = obj["expiry"].isoformat()
    obj["remote_target"] = obj["remote_target"].value
    return obj

@asset(group_name="slack_refresh")
def find_expiring_creds(context: AssetExecutionContext) -> MaterializeResult:
    neo = Neo4j()
    creds = neo.read_all_expiring_credentials(DataSources.SLACK)
    
    context.log.info(f"Found {len(creds)} expiring credentials")
    result = []
    for cred in creds:
        result.append(creds_to_json(cred))
        context.log.info(f"     Expiring credential: {cred}")

    return MaterializeResult(
        asset_key="find_expiring_creds",
        metadata={
            "num_records": len(creds), 
            "credentials": MetadataValue.json(result),
        }
    )

@asset(deps=[find_expiring_creds], group_name="slack_refresh")
def refresh_creds(context: AssetExecutionContext) -> MaterializeResult:
    mat = context.instance.get_latest_materialization_event(AssetKey("find_expiring_creds"))
    value: JsonMetadataValue = mat.dagster_event.event_specific_data.materialization.metadata['credentials']
    print(value.data)
    value.data
    result = []

    for r in value.data:
        r["remote_target"] = DataSources(r["remote_target"].lower())
        c = OAuthCreds(**r)
        print("Refreshing with ", c)
        credentials = Slack.refresh_token(c)
        print("Refreshed credentials: ", credentials)
        if credentials:
            context.log.info(f"Refreshed credentials for {c.remote_target}")
            result.append(creds_to_json(credentials))

    return MaterializeResult(
        
        metadata={
            "num_records": len(result), 
            "refreshed": MetadataValue.json(result),
        }
    )

@asset(deps=[refresh_creds], group_name="slack_refresh")
def write_refrehed_creds(context: AssetExecutionContext) -> MaterializeResult:
    mat = context.instance.get_latest_materialization_event(AssetKey("refresh_creds"))
    value: JsonMetadataValue = mat.dagster_event.event_specific_data.materialization.metadata['refreshed']

    neo = Neo4j()
    user_map: dict[str, User] = {}
    for r in value.data:
        print("R WAS ", r)
        r["remote_target"] = DataSources(r["remote_target"].lower())
        c = OAuthCreds(**r)
        user = user_map.get(c.email)
        if not user:
            user = neo.get_user_by_email(c.email)
            user_map[c.email] = user
        neo.write_remote_credentials(user, c)

assets = [find_expiring_creds, refresh_creds, write_refrehed_creds]
if not os.getenv("IS_TEST"):

    materialize(assets)

    slack_refresh_job = define_asset_job(
        "slack_refresh_job", AssetSelection.groups("slack_refresh")
    )

    # schedule = os.getenv("DAGSTER_SLACK_REFRESH_TOKEN_SCHEDULE")
    slack_refresh_schedule = ScheduleDefinition(
        job=slack_refresh_job,
        cron_schedule="*/5 * * * *",
        # os.getenv("DAGSTER_SLACK_REFRESH_TOKEN_SCHEDULE", "* * * * *"),
        default_status=DefaultScheduleStatus.RUNNING,
    )



