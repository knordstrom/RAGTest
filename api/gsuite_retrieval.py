import datetime
from typing import Any, List, Union
import dotenv
from pydantic import EmailStr

from library.apisupport import APISupport
from library.enums.data_sources import DataSources
from library.gsuite import GSuite
from googleapiclient.errors import HttpError
import os
from fastapi import APIRouter

from library.models.message import Message

route = APIRouter(tags=["Data Acquisition"])

dotenv.load_dotenv()

root_path = os.path.dirname(os.path.realpath(__file__))

creds = root_path + '/../' + os.getenv('GSUITE_CREDS_FILE', 'resources/gmail_creds.json')

@route.get('/data/gsuite/email')
async def email(email: EmailStr, n: Union[int, None] = None) -> List[Message]:
    """Get the last n emails from the specified user's gsuite account. Response is a pass-through of the Gmail API response."""
    mapped: list[Message] = APISupport.read_last_emails(email, creds, count = n)
    APISupport.write_emails_to_kafka(mapped, DataSources.GOOGLE) 
    return mapped

@route.get('/data/gsuite/calendar')
async def calendar(email: EmailStr, n: int) -> List[dict]:
    """Get the next n events from the specified user's gsuite calendar. Response is a pass-through of the Calendar API response."""
    try:
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        print("Getting the upcoming " + str(n) + " events")
        print("Creds " + creds)
        events = GSuite(email, creds).events(now, n)
        APISupport.write_cal_to_kafka(events, DataSources.GOOGLE) 
        return events

    except HttpError as error:
        print(f"An error occurred: {error}")
        APISupport.error_response(400, f"An HTTP error occurred '{error}'")

@route.get('/data/gsuite/documents')
async def documents(email: EmailStr) -> dict[str, Any]:
    """Get the documents from the specified user's gsuite account. Response is a pass-through of the Drive API response."""
    try:
        # now = datetime.datetime.now(datetime.UTC).isoformat()
        print("Getting your documents")
        print("Creds " + creds)
        temp_folder = create_temporary_folder()
        doc_info: dict[str, any] = GSuite(email, creds, temp_folder).get_doc_info()
        print("doc_info: ", doc_info.keys())
        APISupport.write_docs_to_kafka([x for x in doc_info.values()], DataSources.GOOGLE) 
        return doc_info

    except HttpError as error:
        print(f"An error occurred: {error}")
        APISupport.error_response(400, f"An HTTP error occurred '{error}'")     

def create_temporary_folder():
    temp_folder = os.path.join(root_path, 'temp', 'gsuite')
    os.makedirs(temp_folder, exist_ok=True)
    return temp_folder