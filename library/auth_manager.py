from datetime import datetime, timedelta
from hashlib import md5
from typing import Any
from uuid import uuid4
from library.api_models import TokenResponse
from library.neo4j import Neo4j


class AuthManager:

    def __init__(self):
        self.datastore = Neo4j()

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
                return TokenResponse(email=record['person.email'], token=token, expiry=token_expiry)
        return self.update_user_token(record['person.email']) 
    
    def update_user_token(self, email: str) -> TokenResponse:     
        records: list[dict[str, Any]] = self.datastore.update_user_token(email)
        if len(records) == 0:
            return None
        
        record = records[0]
        token = record.get('person.token')
        token_expiry = record.get('person.token_expiry')   
        print("Updated token: ", token, " with expiry: ", token_expiry)
        ressult = TokenResponse(email=email, token=token, expiry=token_expiry)
        print("Auth result", ressult)
        return ressult

    def fail_login(self, email: str) -> TokenResponse:
        return TokenResponse(email = email, token = None, expiry = None)