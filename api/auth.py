from library import neo4j
from library.api_models import ApiResponse, LoginRequest, TokenResponse
from fastapi import APIRouter

from library.auth_manager import AuthManager

route = APIRouter(tags=["Auth"])

@route.post('/auth/login')
async def authenticate(form: LoginRequest) -> ApiResponse[TokenResponse]:  
    """Perform login for a user"""
    result: TokenResponse = AuthManager().authenticate(form.email, form.password)
    return ApiResponse.create(result)
    