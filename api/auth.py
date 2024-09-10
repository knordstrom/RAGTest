from datetime import datetime
import json
from typing import Optional
from globals import Globals
from library.models.api_models import ApiResponse, LoginRequest, TokenResponse
from fastapi import APIRouter

from library.managers.auth_manager import AuthManager

route = APIRouter(tags=["Auth"])

@route.post('/auth/login')
async def authenticate(form: LoginRequest) -> ApiResponse[TokenResponse]:  
    """Perform login for a user"""
    result: TokenResponse = AuthManager().authenticate(form.email, form.password)
    return ApiResponse.create(result)
    
@route.post('/auth/creds')
async def credentials(target: str, token: str, refresh_token: str, expiry: datetime, client_id: Optional[str] = None, 
                      client_secret: Optional[str] = None, scopes: Optional[str]= None) -> ApiResponse[str]:
    """Store credentials for a user"""
    with open(Globals().root_resource(target + ".json"), "w") as f:
        f.write(json.dumps({"token": token, "refresh_token": refresh_token, "expiry": expiry.isoformat(), 
                            "client_id": client_id, "client_secret": client_secret, "scopes": scopes.split(",")}))
    return ApiResponse.create("True")