from datetime import datetime, timedelta
from hashlib import md5
from typing import Annotated, Any, Optional
from uuid import uuid4

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from library.enums.data_sources import DataSources
from library.models.api_models import OAuthCreds, TokenResponse
from library.data.local.neo4j import Neo4j
from library.models.employee import Employee, User


class AuthManager:

    def __init__(self, datastoree: Neo4j = None) -> None:
        self.datastore = datastoree if datastoree else Neo4j()

    @staticmethod
    def assert_authorization_email(me: User, emails: str | list[str]) -> None:
        if isinstance(emails, str):
            emails = [emails]
        if not me:
            raise HTTPException(status_code=401, detail="You are not authenticated.")
        if me.email not in emails:
            raise HTTPException(status_code=403, detail="You are not authorized to access this email account.")

    @staticmethod
    def get_user_dependency(oauth2: OAuth2PasswordBearer) -> callable:
        async def get_current_user(token: Annotated[str, Depends(oauth2)]) -> User:
            return AuthManager().get_user_by_token(token)
        return get_current_user

    def get_user_by_token(self, token: str) -> User:
        record: User = self.datastore.get_user_by_token(token)
        return record

    def authenticate(self, email: str, password: str) -> TokenResponse:
        records: list[dict[str, any]] = self.datastore.authenticate(email, password)
            
        if len(records) == 0:
            self.datastore.create_new_user(email, password)
        else :
            record = records[0]
            if record.get('person.password') is None:
                return self.datastore.create_login(email, password)
            elif record.get('person.password') == str(md5(password.encode()).hexdigest()):
                return self.handle_authenticated_user(record)
            return self.fail_login(email)
    
    def handle_authenticated_user(self, record: dict[str, any]) -> TokenResponse:
        print("Handling authenticated user", record)
        token = record.get('person.token')
        token_expiry = record.get('person.token_expiry')
        print("Token is: ", token, " with expiry: ", token_expiry)
        if token is not None and token_expiry is not None and datetime.now() < datetime.fromisoformat(token_expiry):
                return TokenResponse(email=record['person.email'], name=record['person.name'], token=token, expiry=token_expiry)
        return self.update_user_token(record['person.email'], record.get('person.name')) 
    
    def update_user_token(self, email: str, name: Optional[str] = None) -> TokenResponse:     
        records: list[dict[str, Any]] = self.datastore.update_user_token(email)
        if len(records) == 0:
            return None
        
        record = records[0]
        token = record.get('person.token')
        token_expiry = record.get('person.token_expiry')   
        print("Updated token: ", token, " with expiry: ", token_expiry)
        result = TokenResponse(email=email, name = name, token=token, expiry=token_expiry)
        print("Auth result", result)
        return result

    def fail_login(self, email: str) -> TokenResponse:
        return TokenResponse(email = email, name = None, token = None, expiry = None)
    
    def write_remote_credentials(self, user: User, target: str, token: str, refresh_token: str, expiry: datetime, client_id: str, 
                                 client_secret: str, token_uri: str, scopes: list[str]) -> None:
        provider: DataSources = DataSources.__members__.get(target)
        if not provider:
            raise HTTPException(status_code=400, detail="Invalid target")

        creds = OAuthCreds(
            remote_target=provider, 
            token=token, 
            refresh_token=refresh_token, 
            expiry=expiry, 
            client_id=client_id, 
            client_secret=client_secret, 
            token_uri=token_uri,
            scopes=scopes)
        self.datastore.write_remote_credentials(user, creds)
    
    def write_remote_credentials_object(self, user: User, provider: OAuthCreds) -> OAuthCreds:
        return self.datastore.write_remote_credentials(user, provider) if provider else None

    def read_remote_credentials(self, user: User, provider: DataSources) -> OAuthCreds:
        return self.datastore.read_remote_credentials(user, provider)
    
    def read_all_remote_credentials(self, user: User) -> list[OAuthCreds]:
        return self.datastore.read_all_remote_credentials(user)