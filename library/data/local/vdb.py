from library.models.employee import User
from library.models.weaviate_schemas import EmailText, EmailTextWithFrom, WeaviateSchemas


class VDB:
    @property
    def client(self):
        pass

    def create_schema(self, schema_object: dict[str,any]) -> None:
        pass
    
    def upsert(self, text:str) -> bool:
        pass
    
    def count(self) -> object:
        pass

    def split(self, text:str) -> list:
        pass

    def search(self, user: User, query:str, key: WeaviateSchemas, limit: int = 5, certainty: float = .7, threshold: float = None, use_hyde: bool = False) -> list[object]:
        pass
    
    def close(self):
        pass

    def get_thread_email_messages_by_id(self, thread: str) -> list[EmailText]:
        pass

    def get_thread_email_messages_by_id(self, thread_id: str) -> list[EmailTextWithFrom]:
        pass