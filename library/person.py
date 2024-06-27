import hashlib
class Person:
    def __init__(self, name, email):
        self.name = name
        self.email = email

    def identifier(self):
        sha256 = hashlib.sha256()
        sha256.update(self.email.encode('utf-8'))
        return sha256.hexdigest()

    def to_dict(self):
        return {
            "id": self.identifier(),
            "name": self.name,
            "email": self.email
        }