from datetime import datetime
from math import exp
import os
from typing import List, Optional, Union, TypeVar, Generic

import dotenv
from pydantic import BaseModel

from globals import Globals
from library.models.api_models import DocumentEntry, DocumentOwner, DocumentResponse, EmailConversationEntry, EmailMessage, EmailThreadResponse, MeetingAttendee, MeetingContext, SlackConversationEntry, SlackMessage, SlackThreadResponse
from library.models.employee import Employee
from library.data.local.neo4j import Neo4j
from library.data.local.weaviate import Weaviate


T = TypeVar('T')

class ImportanceServiceException(Exception):
    pass

class ImportanceService:

    _graph: Neo4j = None
    @property
    def graph(self) -> Neo4j:
        if self._graph is None:
            self._graph = Neo4j()
        return self._graph
    
    _vector: Weaviate = None
    @property
    def vector(self) -> Weaviate:
        if self._vector is None:
            self._vector = Weaviate()
        return self._vector
    
    def __init__(self):
        dotenv.load_dotenv(dotenv_path=Globals().root_resource('.env'))
        self.decay_document_days = float(os.getenv('DECAY_DOC_DAYS', '7'))
        self.decay_email_days = float(os.getenv('DECAY_EMAIL_DAYS', '7'))
        self.decay_slack_days = float(os.getenv('DECAY_SLACK_DAYS', '7'))

    decay_email_days: float = 7
    decay_slack_days: float = 7
    decay_document_days: float = 7

    def add_importance_to_meeting(self, meeting: MeetingContext) -> None:
        full_org = self.graph.get_employee_with_full_org_chart(meeting.person.email)
        if full_org is None:
            raise ImportanceServiceException(f"Employee {meeting.person.email} not found in the organization chart")

        for item in meeting.support.docs:
            document: DocumentResponse = self.vector.get_document_by_id(item.document_id)
            owners: list[DocumentOwner] = document.metadata.owners
            item.importance = self.decay_importance(ImportanceService._importance_document(full_org, owners), item.metadata.last_response, self.decay_document_days)

        for item in meeting.support.email:
            emails: list[EmailMessage] = self.vector.get_email_metadatas_in_thread(item.thread_id)
            item.importance = self.decay_importance(ImportanceService._importance_email(full_org, emails), item.last_response, self.decay_email_days)

        for item in meeting.support.slack:
            slack_messages: list[SlackMessage] = self.vector.get_slack_thread_messages_by_id(item.thread_id).messages
            item.importance = self.decay_importance(ImportanceService._importance_slack(full_org, slack_messages), item.last_response, self.decay_slack_days)
    
    def decay_importance(self, importance: float, last_response: datetime, decay_days: float) -> float:
        delta = datetime.now().astimezone() - last_response
        return importance * exp(-delta.days/decay_days)
    
    @staticmethod
    def _identity_importance(org: Employee, email: str) -> int:
        distance = org.distance_to(email)
        importance = 0
        if distance is None or distance == 0:
            return 0
        
        if distance == 1 or distance == -1:
            importance = 100
        elif distance > 0:
            importance = min(100, 25*distance)
        else: # distance < 0
            importance = max(0, 100 - 25*abs(distance))
        return importance

    @staticmethod
    def _importance_email(org: Employee, emails: list[EmailMessage]) -> int:    
        importance = 0
        for email in emails:
            importance = max(importance, ImportanceService._identity_importance(org, email.sender))

        return importance
    
    @staticmethod
    def _importance_slack(org: Employee, slack_messages: list[SlackMessage]) -> int: 
        importance = 0
        for message in slack_messages:
            importance = max(importance, ImportanceService._identity_importance(org, message.sender))

        return importance
    
    @staticmethod
    def _importance_document(org: Employee, owners: list[DocumentOwner]) -> int:
        importance = 0

        for owner in owners:
            if owner.emailAddress is not None:
                importance = max(importance, ImportanceService._identity_importance(org, owner.emailAddress))

        return importance