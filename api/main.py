import datetime
from typing import Union

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
from fastapi import FastAPI

warnings.simplefilter("ignore", ResourceWarning)

app = FastAPI(title="Sofia API", description="API for intereacting with the Sofia agent", version="0.1")
app.include_router(refs)
app.include_router(data)
app.include_router(slack)
app.include_router(auth)
app.include_router(script)
app.include_router(employees)

tags = ["Main Interface"]

@app.get('/ask', tags=tags)
async def ask(query:str, n: Union[int,None] = None) -> ApiResponse[AskResponse]:
    """Ask Weaviate a question. Will leverage [email] for context."""
    response = APISupport.perform_ask(query, weaviate.WeaviateSchemas.EMAIL_TEXT, context_limit = n)
    return ApiResponse.create(response)

@app.get('/briefs', tags=tags)
async def briefs(email:str, start:datetime.datetime, end: Union[datetime.datetime, None] = None, certainty: Union[float,None] = None, threshold: Union[float,None] = None) -> ApiResponse[BriefResponse]:
    """Create briefings for a user."""
    if certainty is not None:
        if certainty < 0 or certainty > 100:
            APISupport.error_response(400, "Confidence must be a percentage value between 0 and 100.")
        else:
            certainty = certainty / 100
    if threshold is not None:
        if threshold < 0 or threshold > 100:
            APISupport.error_response(400, "Threshold must be a percentage value between 0 and 100.")
        else:
            threshold = threshold / 100
    plus12 = start + datetime.timedelta(hours=12)
    if end is None:
        end = plus12
    elif end < start:
        APISupport.error_response(400, "End time must be after the start time.")
    support = BriefingSupport(GroqBriefingSummarizer())
    response =  support.create_briefings_for(email = email, start_time=start, end_time= end, certainty = certainty, threshold = threshold)
    return ApiResponse.create(response)

@app.get('/schedule', tags=tags)
async def schedule(email:str, start:datetime.datetime, end:datetime.datetime) -> ApiResponse[ScheduleResponse]:
    """Retrieves the schedule for a user."""
    response = APISupport.get_calendar_between(email, start, end)
    return ApiResponse.create(response)
