import datetime
import json
from typing import Union

from library.managers.auth_manager import AuthManager
from library.models.api_models import ApiResponse, AskResponse, BriefResponse, LoginRequest, ScheduleResponse, TokenResponse
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
from globals import Globals

warnings.simplefilter("ignore", ResourceWarning)

app = FastAPI(title="Sofia Faked API", description="Faked API for developing UI for Sofia", version="0.1")
app.include_router(auth)

@app.get('/briefs', tags=["Main Interface"])
async def briefs(email:str, start:datetime.datetime, end: Union[datetime.datetime, None] = None, certainty: Union[float,None] = None) -> ApiResponse[BriefResponse]:
    email = email.replace("@", "%40")
    start = start.strftime("%Y-%m-%d")
    end = end.strftime("%Y-%m-%d") if end else ""
    certainty = int(certainty)
    base: str = f"http-::127.0.0.1-5010:briefs?email={email}&start={start}&end={end}&certainty={certainty}"
    file: str = Globals().resource(f"api_stubs/{base}")
    try:
       with open(file, 'r') as f:
            response = json.loads(f.read())
    except FileNotFoundError:
        APISupport.error_response(404, f"File {file} not found")
    return ApiResponse.create(BriefResponse(**response["response"]))

@app.post('/auth/login')
async def authenticate(form: LoginRequest) -> ApiResponse[TokenResponse]:  
    """Perform login for a user"""
    result: TokenResponse = AuthManager().authenticate(form.email, form.password)
    return ApiResponse.create(result)
    