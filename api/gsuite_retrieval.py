import datetime
from typing import Any, List, Union
import dotenv
from pydantic import EmailStr
from pydantic import EmailStr

from globals import Globals
from library.models.api_models import ConferenceCall, ConferenceTranscript
from library.managers.api_support import APISupport
from library.enums.data_sources import DataSources
from library.data.external.gsuite import GSuite
from googleapiclient.errors import HttpError
from google.api_core import exceptions as exceptions
from google.apps.meet_v2.types import ConferenceRecord
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
async def calendar(email: EmailStr, n: int) -> List[dict[str, Any]]:
    """Get the next n events from the specified user's gsuite calendar. Response is a pass-through of the Calendar API response."""
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    print("Getting the upcoming " + str(n) + " events")
    print("Creds " + creds)
    events = GSuite(email, creds).events(now, n)
    APISupport.write_cal_to_kafka(events, DataSources.GOOGLE) 
    return events

@route.get('/data/gsuite/documents')
async def documents(email: EmailStr) -> dict[str, Any]:
    """Get the documents from the specified user's gsuite account. Response is a pass-through of the Drive API response."""
    # now = datetime.datetime.now(datetime.UTC).isoformat()
    print("Getting your documents")
    print("Creds " + creds)
    temp_folder = create_temporary_folder()
    doc_info: dict[str, any] = GSuite(email, creds).get_doc_info()
    print("doc_info: ", doc_info.keys())
    APISupport.write_docs_to_kafka([x for x in doc_info.values()], DataSources.GOOGLE) 
    return doc_info

@route.get('/data/gsuite/conferences')
async def list_conferences(email: EmailStr) -> List[ConferenceCall]:
    """Get the meetings from the specified user's gsuite account. Response is a pass-through of the Calendar API response."""

    try:
        print("Getting your conferences")
        print("Creds " + creds)
        events: list[ConferenceCall] = await GSuite(email, creds).list_meetings()

        transcript_ids: dict[str, str] = {}
        meeting_codes: dict[str, str] = {}
        for call in events:
            print(call)          
            transcript: ConferenceTranscript
            for transcript in call.transcripts:
                meeting_codes[transcript.document] = call.space.meeting_code
                print("Visit ",transcript.export_uri)
                transcript_ids[transcript.document] = transcript.document
        
        transcript_content = GSuite(email, creds).get_gdocs_content(transcript_ids)
        for doc_id in transcript_content:
            transcript_content[doc_id]['meeting_code'] = meeting_codes[doc_id]
        APISupport.write_transcripts_to_kafka(transcript_content, DataSources.GOOGLE)
        APISupport.write_conferences_to_kafka(events, DataSources.GOOGLE) 
    except exceptions.PermissionDenied as error:
        print(error)
        return APISupport.error_response(403, "Google message: " + error.message)
    
    print(events)
    return events

def create_temporary_folder():
    temp_folder = Globals().api_temp_resource('gsuite')
    os.makedirs(temp_folder, exist_ok=True)
    return temp_folder