import ast
import datetime
from typing import Union
from dateutil import parser as dateparser

from os import abort
import dotenv
import flask
from library.api_models import ApiResponse, AskResponse, BriefResponse, ScheduleResponse
from library.apisupport import APISupport
from library.briefing_support import BriefingSupport
import library.weaviate as weaviate
import warnings 
from api.reference import route as refs
from api.gsuite_retrieval import route as data
from fastapi import FastAPI
from pydantic import BaseModel

warnings.simplefilter("ignore", ResourceWarning)

app = FastAPI(title="Sofia API", description="API for intereacting with the Sofia agent", version="0.1")
app.include_router(refs)
app.include_router(data)

require = APISupport.require
tags = ["Main Interface"]

@app.get('/ask', tags=tags)
async def ask(query:str, n: Union[int,None] = None) -> ApiResponse[AskResponse]:
    """Ask Weaviate a question. Will leverage [email] for context."""
    response = APISupport.perform_ask(query, weaviate.WeaviateSchemas.EMAIL_TEXT, context_limit = n)
    return ApiResponse.create(response)

@app.get('/briefs', tags=tags)
async def briefs(email:str, start:datetime.datetime, end: Union[datetime.datetime, None] = None, certainty: Union[float,None] = None) -> ApiResponse[BriefResponse]:
    """Create briefings for a user."""
    if certainty is not None:
        if certainty < 0 or certainty > 100:
            flask.abort(400, "Confidence must be a percentage value between 0 and 100.")
        else:
            certainty = certainty / 100
    plus12 = start + datetime.timedelta(hours=12)
    if end is None:
        end = plus12
    elif end < start:
            flask.abort(400, "End time must be after the start time.")
    response =  BriefingSupport.create_briefings_for(email, start, end, certainty = certainty)
    return ApiResponse.create(response)

@app.get('/schedule', tags=tags)
async def schedule(email:str, start:datetime.datetime, end:datetime.datetime) -> ApiResponse[ScheduleResponse]:
    """Retrieves the schedule for a user."""
    response = APISupport.get_calendar_between(email, start, end)
    return ApiResponse.create(response)
