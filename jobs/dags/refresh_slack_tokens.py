import json
import os
import dotenv
from pydantic import BaseModel
import requests

from dagster import (
    AssetExecutionContext,
    AssetKey,
    AssetSelection,
    AssetsDefinition,
    Config,
    DefaultScheduleStatus,
    Definitions,
    JsonMetadataValue,
    MaterializeResult,
    MetadataValue,
    OpExecutionContext,
    ScheduleDefinition,
    asset,
    define_asset_job,
    graph,
    graph_asset,
    materialize,
    op,
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

def report(context: OpExecutionContext, text: str):
    context.log.info(text)
    print(text)

class CredentialsResult(BaseModel):
    num_records: int
    credentials: list[OAuthCreds]
    refreshed_credentials: list[OAuthCreds] = []
    num_refreshed: int = 0
    num_failed: int = 0

@op
def find_expiring_creds(context: OpExecutionContext) -> CredentialsResult:
    neo = Neo4j()
    creds = neo.read_all_credentials_to_refresh(DataSources.SLACK)
    
    report(context, f"Found {len(creds)} expiring credentials")
    for cred in creds:
        report(context, "     Expiring credential: {cred}")

    return CredentialsResult(
            num_records = len(creds), 
            credentials = creds
    )
    
@op
def refresh_creds(context: OpExecutionContext, creds: CredentialsResult) -> CredentialsResult:
    for c in creds.credentials:
        report(context, f"Refreshing with {c}")
        old_token = c.token
        credentials = Slack.refresh_token(c)
        if credentials.token != old_token:
            creds.refreshed_credentials.append(credentials)

    creds.num_refreshed = len(creds.refreshed_credentials)
    creds.num_failed = creds.num_records - creds.num_refreshed
    report(context, f"Refreshed {creds.num_refreshed} expiring credentials")
    return creds

@op
def write_refreshed_creds(context: OpExecutionContext, creds: CredentialsResult) -> CredentialsResult:
    neo = Neo4j()
    user_map: dict[str, User] = {}
    for c in creds.refreshed_credentials:
        report(context, f"C WAS {c}")
        user = user_map.get(c.email)
        if not user:
            user = neo.get_user_by_email(c.email)
            user_map[c.email] = user
        neo.write_remote_credentials(user, c)
    return creds

@op
def create_metadata(context: OpExecutionContext, creds: CredentialsResult) -> MaterializeResult:
    return MaterializeResult(
        metadata={
            "num_records": MetadataValue.int(creds.num_records),
            "num_refreshed": MetadataValue.int(creds.num_refreshed),
            "num_failed": MetadataValue.int(creds.num_failed),
            "credentials": JsonMetadataValue([creds_to_json(c) for c in creds.credentials]),
            "refreshed_credentials": JsonMetadataValue([creds_to_json(c) for c in creds.refreshed_credentials]),
        }
    )

@graph_asset
def slack_refresh_all_near_expired() -> MaterializeResult:
    return create_metadata(write_refreshed_creds(refresh_creds(find_expiring_creds())))

slack_refresh_job = define_asset_job(
    "slack_refresh_job", [slack_refresh_all_near_expired]
)

# schedule = os.getenv("DAGSTER_SLACK_REFRESH_TOKEN_SCHEDULE")
slack_refresh_schedule = ScheduleDefinition(
    job=slack_refresh_job,
    cron_schedule="* * * * *",
    default_status=DefaultScheduleStatus.RUNNING,
)



