import hashlib

from pydantic import BaseModel
class Person(BaseModel):
    name: str
    email: str

    @property
    def identifier(self) -> str:
        sha256 = hashlib.sha256()
        sha256.update(self.email.encode('utf-8'))
        return sha256.hexdigest()

    def to_dict(self):
        return {
            "id": self.identifier,
            "name": self.name,
            "email": self.email
        }