import datetime
from typing import Annotated, Union

from fastapi.security import OAuth2PasswordBearer

from library.managers.auth_manager import AuthManager
from library.models.api_models import ApiResponse, AskResponse, BriefResponse, ScheduleResponse
from library.managers.api_support import APISupport
from library.managers.briefing_support import BriefingSupport
from library.managers.briefing_summarizer import GroqBriefingSummarizer
import library.data.local.weaviate as weaviate
import warnings 

from api.reference import route as refs
from api.gsuite_retrieval import route as data
from api.slack_retrieval import route as slack
from api.auth import route as auth
from api.script import route as script
from api.employees import route as employees
from fastapi import Depends, FastAPI

from library.models.employee import User

warnings.simplefilter("ignore", ResourceWarning)

app = FastAPI(title="Sofia API", description="API for intereacting with the Sofia agent", version="0.1")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login/openapi")

app.include_router(refs)
app.include_router(data)
app.include_router(slack)
app.include_router(auth)
app.include_router(script)
app.include_router(employees)

tags = ["Main Interface"]

def _check_float(value: Union[float,None], field_name: str) -> Union[float,None]:
    if value is not None:
        if value < 0 or value > 100:
            APISupport.error_response(400, f"Value for {field_name} must be a percentage value between 0 and 100.")
        else:
            value = value / 100
    return value

@app.get("/status")
def get_status():
    return {"status": "ok"}

@app.get('/ask', tags=tags)
async def ask(me: Annotated[User, Depends(AuthManager.get_user_dependency(oauth2_scheme))],
              query:str, n: Union[int,None] = None, 
                 certainty: Union[float,None] = None, threshold: Union[float,None] = None, use_hyde: bool = False) -> ApiResponse[AskResponse]:
    """Ask Weaviate a question. Will leverage [email] for context."""
    response = APISupport.perform_ask(me, query, weaviate.WeaviateSchemas.EMAIL_TEXT, context_limit = n, certainty = certainty, threshold = threshold, use_hyde = use_hyde)
    return ApiResponse.create(response)

@app.get('/briefs', tags=tags)
async def briefs(me: Annotated[User, Depends(AuthManager.get_user_dependency(oauth2_scheme))],
                 email:str, start:datetime.datetime, end: Union[datetime.datetime, None] = None, 
                 certainty: Union[float,None] = None, threshold: Union[float,None] = None, use_hyde: bool = False) -> ApiResponse[BriefResponse]:
    """Create briefings for a user. Toggle [use_hyde] to use the GroqBriefingSummarizer to perform a HYpothetical Document Embeddings search."""
    AuthManager.assert_authorization_email(me, email)
    if not email:
        APISupport.error_response(400, "Email is required.")
    if not start:
        APISupport.error_responsen(400, "Start time is required.")
    certainty  = _check_float(certainty, "certainty")
    threshold = _check_float(threshold, "threshold")
    plus12 = start + datetime.timedelta(hours=12)
    if end is None:
        end = plus12
    elif end < start:
        APISupport.error_response(400, "End time must be after the start time.")
    support = BriefingSupport(GroqBriefingSummarizer(), me)

    response =  support.create_briefings_for(start_time=start, end_time= end, certainty = certainty, threshold = threshold, use_hyde = use_hyde)
    return ApiResponse.create(response)

@app.get('/schedule', tags=tags)
async def schedule(me: Annotated[User, Depends(AuthManager.get_user_dependency(oauth2_scheme))],
                   email:str, start:datetime.datetime, end:datetime.datetime) -> ApiResponse[ScheduleResponse]:
    """Retrieves the schedule for a user."""
    AuthManager.assert_authorization_email(me, email)
    response = APISupport.get_calendar_between(email, start, end)
    return ApiResponse.create(response)
