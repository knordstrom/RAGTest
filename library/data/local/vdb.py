from datetime import datetime
from pydantic import BaseModel
from library.models.api_models import SlackThreadResponse, TranscriptConversation
from library.models.employee import User
from library.models.weaviate_schemas import CommunicationSummary, EmailText, EmailTextWithFrom, WeaviateSchemas
from weaviate.collections.collection import Collection
from weaviate.collections.classes.types import Properties, References

class VDB:
    @property
    def client(self):
        pass
    
    def collection(self, key: WeaviateSchemas) -> Collection[Properties, References]:
        pass

    def get_summary_by_id(self, collection: WeaviateSchemas, id_prop: str, id: str) -> CommunicationSummary:
        pass

    def get_conversation_for_summary(self, thread_collection: WeaviateSchemas, thread_id: str) -> list[BaseModel]:
        pass

    def save_summary(self, collection: WeaviateSchemas, id_prop: str, id: str, summary: str, timestamp: datetime) -> None:
        pass

    def create_schema(self, schema_object: dict[str,any]) -> bool:
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

    def get_thread_email_messages_by_id(self,  thread_id: str) -> list[EmailText]:
        pass

    def get_thread_email_messages_by_id(self, thread_id: str) -> list[EmailTextWithFrom]:
        pass

    def get_slack_thread_messages_by_id(self,  thread_id: str) -> SlackThreadResponse:
        pass

    def get_transcript_conversation_by_meeting_code(self, meeting_code: str) -> TranscriptConversation:
        pass