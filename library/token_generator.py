
from datetime import datetime, timedelta
from hashlib import md5
from uuid import uuid4


class TokenGenerator:
    @staticmethod
    def generate_token() -> tuple[str, datetime]:
        token = str(md5(uuid4().hex.encode()).hexdigest())
        token_expiry = (datetime.now()+ timedelta(hours=9))
        print("Generated token: ", token, " with expiry: ", token_expiry)
        return (token, token_expiry)