from datetime import datetime
import json
from typing import Annotated, Optional

from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from globals import Globals
from library.models.api_models import ApiResponse, LoginRequest, TokenResponse
from fastapi import APIRouter, Depends, HTTPException

from library.managers.auth_manager import AuthManager
from library.models.employee import User

route = APIRouter(tags=["Auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login/openapi")

def _perform_login(form: LoginRequest) -> TokenResponse:
    response: TokenResponse = AuthManager().authenticate(form.email, form.password)
    if not response.token:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return response

@route.post("/auth/login/openapi")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> TokenResponse:
    return _perform_login(LoginRequest(email=form_data.username, password=form_data.password)) 

@route.post('/auth/login')
async def authenticate(form: LoginRequest) -> ApiResponse[TokenResponse]:  
    """Perform login for a user"""
    return ApiResponse.create(_perform_login(form))
    
@route.post('/auth/creds')
async def credentials(me: Annotated[User, Depends(AuthManager.get_user_dependency(oauth2_scheme))],
                      target: str, token: str, expiry: datetime, refresh_token:  Optional[str] = None, client_id: Optional[str] = None, 
                      client_secret: Optional[str] = None, token_uri:  Optional[str] = None, scopes: Optional[str]= None) -> ApiResponse[str]:
    """Store credentials for a user"""
    scopes = scopes or ""
    AuthManager().write_remote_credentials(me, target, token, refresh_token, expiry, client_id, client_secret, token_uri, scopes.split(","))
    return ApiResponse.create("True")