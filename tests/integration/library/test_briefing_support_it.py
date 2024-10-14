from copyreg import pickle
from datetime import datetime, tzinfo
from hashlib import md5
import json
import math
import os
import random
import dateutil
import dateutil.tz
from groq import Groq
import pytest
import requests
from globals import Globals
from library.data.external.gsuite import GSuite
from library.data.local import weaviate as w
from library.data.local.neo4j import Neo4j
from library.enums.data_sources import DataSources
from library.llms.promptmanager import PromptRetriever
from library.managers.auth_manager import AuthManager
from library.managers.briefing_summarizer import BriefingSummarizer
from library.managers.briefing_support import BriefingSupport
import library.managers.handlers as h
from requests.exceptions import ConnectionError

from library.models.api_models import OAuthCreds, TokenResponse
from library.models.employee import Employee, User
from library.utils import Utils
from library.models.weaviate_schemas import Email, EmailParticipant, SlackMessage, WeaviateSchema, WeaviateSchemas
from tests.integration.library.integration_test_base import IntegrationTestBase, MultiReadyResponse, ReadyResponse
from weaviate.collections.collection import Collection
from weaviate.collections.classes.internal import Object
from weaviate.collections.classes.types import Properties, References
from google.oauth2.credentials import Credentials

class BriefingSummarizerStub(BriefingSummarizer):
    def summarize(self, prompt_name: str, context: dict[str, str]) -> str:
        return md5((prompt_name + json.dumps(context)).encode()).hexdigest()

    def summarize_with_prompt(self, prompt: str, context: dict[str, str]) -> str:
        return md5((prompt + json.dumps(context)).encode()).hexdigest()
    
class PromptRetrieverStub(PromptRetriever):
    def get_prompt(self, prompt_name: str) -> str:
        return Globals().prompt(prompt_name)
    
class TestBriefingSupportIt(IntegrationTestBase):
    
    def is_responsive(self, url):
        try:
            print("Checking if service is responsive at ", url, " ... ")
            response = requests.get(url)
            if response.status_code == 200:
                print("Service is responsive")
                return True
        except ConnectionError:
            return False

    @pytest.fixture(scope="session")
    def service(self, docker_ip, docker_services) -> MultiReadyResponse:
        # """Ensure that service is up and responsive."""

        weaviate_config = self.get_config(docker_ip, docker_services, "weaviate", 8081)
        neo4j_config = self.get_config(docker_ip, docker_services, "neo4j", int(os.getenv("NEO4J_BOLT_PORT","7688")))
        return MultiReadyResponse(weaviate = weaviate_config, neo4j = neo4j_config)
    
    def get_config(self, docker_ip, docker_services, service_name: str,default_port: int) -> ReadyResponse:
        port = docker_services.port_for(service_name, default_port)
        url = "http://{}:{}".format(docker_ip, port)
        print("port for service ", service_name, " is ", port)
        docker_services.wait_until_responsive(
            timeout=60.0, pause=0.1, check=lambda: self.is_responsive(url)
        )
        return ReadyResponse(url = url,host = docker_ip,port = str(port))
    
    def test_summary_for_email(self, service):
        weaviate = w.Weaviate()
        neo4j = Neo4j()
        sum = BriefingSummarizerStub()
        prompt_retriever = PromptRetrieverStub()
        auth = AuthManager(neo4j)
        token: TokenResponse = auth.datastore.create_new_user("someone@somewhere.idk", "password")
        user: User = auth.get_user_by_token(token.access_token)

        emails_before_save = list(weaviate.collection(WeaviateSchemas.EMAIL).iterator())
        emailtexts_before_save = list(weaviate.collection(WeaviateSchemas.EMAIL_TEXT).iterator())

        support: BriefingSupport = BriefingSupport(sum, user, weaviate, prompt_retriever)

        handler = h.Handlers(weaviate, Groq())

        participant1 = EmailParticipant(email=user.email, name=user.email)
        participant2 = EmailParticipant(email="another@somewhere.idk", name="Another Person")

        email1 = self.create_email(to = [participant1], sender=participant2, sent=datetime(2024,9,1,3,45,46), 
                                   txt="Hi Joe, how are things?")
        email2 = self.create_email(to = [participant2], sender=participant1, sent=datetime(2024,9,1,3,48,46),
                                      txt="Sue! They're great. Did you get your work done?",
                                      thread_id = email1['thread_id'])

        handler.handle_email(email1)
        handler.handle_email(email2)

        emails_after_save = list(weaviate.collection(WeaviateSchemas.EMAIL).iterator())
        emailtexts_after_save = list(weaviate.collection(WeaviateSchemas.EMAIL_TEXT).iterator())
        
        assert len(emails_after_save) == len(emails_before_save) + 2
        assert len(emailtexts_after_save) == len(emailtexts_before_save) + 2

        summary_and_convo = support.get_or_save_summary(email1['thread_id'], WeaviateSchemas.EMAIL_THREAD_SUMMARY, 'thread_id')
        print(summary_and_convo.conversation)
        assert summary_and_convo.conversation == """
Another Person: Hi Joe, how are things?
someone@somewhere.idk: Sue! They're great. Did you get your work done?"""
        assert summary_and_convo.summary.summary_date == datetime(2024,9,1,3,48,46, tzinfo=dateutil.tz.tzutc())
        assert summary_and_convo.summary.thread_id == email1['thread_id']

        emailsummaries_after_save = weaviate.get_by_ids(WeaviateSchemas.EMAIL_THREAD_SUMMARY, "thread_id", [email1["thread_id"]])
        print(emailsummaries_after_save)
        assert len(emailsummaries_after_save) == 1  
        assert emailsummaries_after_save[0].properties['text'] == summary_and_convo.summary.text
        assert emailsummaries_after_save[0].properties['thread_id'] == summary_and_convo.summary.thread_id

        email3 = self.create_email(to = [participant1], sender=participant2, sent=datetime(2024,9,1,3,52,46, tzinfo=dateutil.tz.tzutc()),
                                      txt="Most of it. You?",
                                      thread_id = email1['thread_id'])
        handler.handle_email(email3)
        
        summary_and_convo_new = support.get_or_save_summary(email1['thread_id'], WeaviateSchemas.EMAIL_THREAD_SUMMARY, 'thread_id')
        print(summary_and_convo_new)
        assert summary_and_convo_new.conversation == """
Another Person: Hi Joe, how are things?
someone@somewhere.idk: Sue! They're great. Did you get your work done?
Another Person: Most of it. You?"""
        assert summary_and_convo_new.summary.summary_date == datetime(2024,9,1,3,52,46, tzinfo=dateutil.tz.tzutc())
        assert summary_and_convo_new.summary.thread_id == email1['thread_id']

        emailsummaries_after_save_new = weaviate.get_by_ids(WeaviateSchemas.EMAIL_THREAD_SUMMARY, "thread_id", [email1["thread_id"]])
        print(emailsummaries_after_save_new)
        assert len(emailsummaries_after_save_new) == 1  
        assert emailsummaries_after_save_new[0].properties['text'] != summary_and_convo.summary.text
        assert emailsummaries_after_save_new[0].properties['thread_id'] == summary_and_convo.summary.thread_id

    def test_summary_for_slack(self, service):
        weaviate = w.Weaviate()
        neo4j = Neo4j()
        sum = BriefingSummarizerStub()
        prompt_retriever = PromptRetrieverStub()
        auth = AuthManager(neo4j)
        token: TokenResponse = auth.datastore.create_new_user("someone@somewhere.idk", "password")
        user: User = auth.get_user_by_token(token.access_token)

        slacks_before_save = list(weaviate.collection(WeaviateSchemas.SLACK_MESSAGE).iterator())
        slacktexts_before_save = list(weaviate.collection(WeaviateSchemas.SLACK_MESSAGE_TEXT).iterator())

        support: BriefingSupport = BriefingSupport(sum, user, weaviate, prompt_retriever)

        handler = h.Handlers(weaviate, Groq())

        participant1 = EmailParticipant(email=user.email, name=user.email)
        participant2 = EmailParticipant(email="another@somewhere.idk", name="Another Person")

        slack1 = self.create_slack_message(to = [participant1], sender=participant2, sent=datetime(2024,9,1,3,45,46))
        slack2 = self.create_slack_message(to = [participant2], sender=participant1, sent=datetime(2024,9,1,3,48,46),
                                      thread_id = slack1['thread_id'])
        
        weaviate.upsert({
            'thread_id': slack1['thread_id'],
            'channel_id': "whatever",
        }, WeaviateSchemas.SLACK_THREAD, 'thread_id')

        handler.handle_slack_message(slack1, {
            'message_id': slack1['message_id'],
            'thread_id': slack1['thread_id'],
            'text': "Hi Joe, how are things?",
            'ordinal': 1
        })
        
        handler.handle_slack_message(slack2, {
            'message_id': slack2['message_id'],
            'thread_id': slack2['thread_id'],
            'text': "Sue! They're great. Did you get your work done?",
            'ordinal': 2 
        })

        slacks_after_save = list(weaviate.collection(WeaviateSchemas.SLACK_MESSAGE).iterator())
        slacktexts_after_save = list(weaviate.collection(WeaviateSchemas.SLACK_MESSAGE_TEXT).iterator())
        
        assert len(slacks_after_save) == len(slacks_before_save) + 2
        assert len(slacktexts_after_save) == len(slacktexts_before_save) + 2

        summary_and_convo = support.get_or_save_summary(slack1['thread_id'], WeaviateSchemas.SLACK_THREAD_SUMMARY, 'thread_id')
        print(summary_and_convo.conversation)
        assert summary_and_convo.conversation == """
another@somewhere.idk: Hi Joe, how are things?
someone@somewhere.idk: Sue! They're great. Did you get your work done?"""
        assert summary_and_convo.summary.summary_date == datetime(2024,9,1,3,48,46, tzinfo=dateutil.tz.tzutc())
        assert summary_and_convo.summary.thread_id == slack1['thread_id']

        slackummaries_after_save = weaviate.get_by_ids(WeaviateSchemas.SLACK_THREAD_SUMMARY, "thread_id", [slack1["thread_id"]])
        print(slackummaries_after_save)
        assert len(slackummaries_after_save) == 1  
        assert slackummaries_after_save[0].properties['text'] == summary_and_convo.summary.text
        assert slackummaries_after_save[0].properties['thread_id'] == summary_and_convo.summary.thread_id

        slack3 = self.create_slack_message(to = [participant1], sender=participant2, sent=datetime(2024,9,1,3,52,46, tzinfo=dateutil.tz.tzutc()),
                                      thread_id = slack1['thread_id'])
        handler.handle_slack_message(slack3, {
            'message_id': slack3['message_id'],
            'thread_id': slack3['thread_id'],
            'text': "Most of it. You?",
            'ordinal': 3,
        })
        
        summary_and_convo_new = support.get_or_save_summary(slack1['thread_id'], WeaviateSchemas.SLACK_THREAD_SUMMARY, 'thread_id')
        print(summary_and_convo_new)
        assert summary_and_convo_new.conversation == """
another@somewhere.idk: Hi Joe, how are things?
someone@somewhere.idk: Sue! They're great. Did you get your work done?
another@somewhere.idk: Most of it. You?"""
        assert summary_and_convo_new.summary.summary_date == datetime(2024,9,1,3,52,46, tzinfo=dateutil.tz.tzutc())
        assert summary_and_convo_new.summary.thread_id == slack1['thread_id']

        slacksummaries_after_save_new = weaviate.get_by_ids(WeaviateSchemas.SLACK_THREAD_SUMMARY, "thread_id", [slack1["thread_id"]])
        print(slacksummaries_after_save_new)
        assert len(slacksummaries_after_save_new) == 1  
        assert slacksummaries_after_save_new[0].properties['text'] != summary_and_convo.summary.text
        assert slacksummaries_after_save_new[0].properties['thread_id'] == summary_and_convo.summary.thread_id

    def test_summary_for_transcript(self, service):
        weaviate = w.Weaviate()
        neo4j = Neo4j()
        sum = BriefingSummarizerStub()
        prompt_retriever = PromptRetrieverStub()
        auth = AuthManager(neo4j)
        token: TokenResponse = auth.datastore.create_new_user("someone@somewhere.idk", "password")
        user: User = auth.get_user_by_token(token.access_token)

        transcripts_before_save = list(weaviate.collection(WeaviateSchemas.TRANSCRIPT).iterator())
        transcripttexts_before_save = list(weaviate.collection(WeaviateSchemas.TRANSCRIPT_ENTRY).iterator())

        support: BriefingSupport = BriefingSupport(sum, user, weaviate, prompt_retriever)

        handler = h.Handlers(weaviate, Groq())

        participant1 = EmailParticipant(email=user.email, name=user.email)
        participant2 = EmailParticipant(email="another@somewhere.idk", name="Another Person")

        transcript1 = self.create_transcript_entry(to = [participant1], sender=participant2, sent=datetime(2024,9,1,3,45,46), 
                                   txt="Hi Joe, how are things?")
        transcript2 = self.create_transcript_entry(to = [participant2], sender=participant1, sent=datetime(2024,9,1,3,48,46),
                                      txt="Sue! They're great. Did you get your work done?",
                                      thread_id = transcript1['meeting_code'])
        
        weaviate.upsert({
            'document_id': 'docid',
            'meeting_code': transcript1['meeting_code'],
            'title': "some meeting we had",
            'provider': 'Google',
            'attendee_names': [participant1.email, participant2.email],
        }, WeaviateSchemas.TRANSCRIPT, 'meeting_code')


        handler.handle_transcript_entry(transcript1, transcript1['text'])
        handler.handle_transcript_entry(transcript2, transcript2['text'])

        transcripts_after_save = list(weaviate.collection(WeaviateSchemas.TRANSCRIPT).iterator())
        transcripttexts_after_save = list(weaviate.collection(WeaviateSchemas.TRANSCRIPT_ENTRY).iterator())
        
        assert len(transcripts_after_save) == len(transcripts_before_save) + 1
        assert len(transcripttexts_after_save) == len(transcripttexts_before_save) + 2

        summary_and_convo = support.get_or_save_summary(transcript1['meeting_code'], WeaviateSchemas.TRANSCRIPT_SUMMARY, 'meeting_code')
        print(summary_and_convo.conversation)
        assert summary_and_convo.conversation == """
another@somewhere.idk: Hi Joe, how are things?
someone@somewhere.idk: Sue! They're great. Did you get your work done?"""
        assert summary_and_convo.summary.thread_id == transcript1['meeting_code']

        transcriptsummaries_after_save = weaviate.get_by_ids(WeaviateSchemas.TRANSCRIPT_SUMMARY, "meeting_code", [transcript1["meeting_code"]])
        print(transcriptsummaries_after_save)
        assert len(transcriptsummaries_after_save) == 1  
        assert transcriptsummaries_after_save[0].properties['text'] == summary_and_convo.summary.text
        assert transcriptsummaries_after_save[0].properties['meeting_code'] == summary_and_convo.summary.thread_id

        transcript3 = self.create_transcript_entry(to = [participant1], sender=participant2, sent=datetime(2024,9,1,3,52,46, tzinfo=dateutil.tz.tzutc()),
                                      txt="Most of it. You?",
                                      thread_id = transcript1['meeting_code'])
        handler.handle_transcript_entry(transcript3, transcript3['text'])

        summary_and_convo_new = support.get_or_save_summary(transcript1['meeting_code'], WeaviateSchemas.TRANSCRIPT_SUMMARY, 'meeting_code')
        print(summary_and_convo_new)
        assert summary_and_convo_new.conversation == """
another@somewhere.idk: Hi Joe, how are things?
someone@somewhere.idk: Sue! They're great. Did you get your work done?
another@somewhere.idk: Most of it. You?"""
        assert summary_and_convo_new.summary.thread_id == transcript1['meeting_code']

        transcriptsummaries_after_save_new = weaviate.get_by_ids(WeaviateSchemas.TRANSCRIPT_SUMMARY, "meeting_code", [transcript1["meeting_code"]])
        print(transcriptsummaries_after_save_new)
        assert len(transcriptsummaries_after_save_new) == 1  
        assert transcriptsummaries_after_save_new[0].properties['text'] != summary_and_convo.summary.text
        assert transcriptsummaries_after_save_new[0].properties['meeting_code'] == summary_and_convo.summary.thread_id


    def create_email(self, to: list[EmailParticipant], sender: EmailParticipant, sent: datetime, txt: str, thread_id: str = None) -> dict[str, any]:
        id = f"${math.floor(random.random() * 1000000)}"
        e = Email(
            email_id = id,
            thread_id = id if thread_id is None else thread_id,
            labels= list(),
            to= to,
            cc=list(),
            bcc=list(),
            subject = "random subject",
            sender = sender,
            date = sent,
            provider = "GOOGLE",
            person_id = "a",
        ).model_dump()
        e['body'] = txt
        return e
    
    def create_slack_message(self, to: list[EmailParticipant], sender: EmailParticipant, sent: datetime, thread_id: str = None) -> dict[str, any]:
        id = f"${math.floor(random.random() * 1000000)}"

        e = {
            'message_id': id,
            'sender': sender.email,
            'type' :"message",
            'subtype' :"message",
            'ts': sent,
            'thread_id': id if thread_id is None else thread_id,
        }
        return e

    def create_transcript_entry(self, to: list[EmailParticipant], sender: EmailParticipant, sent: datetime, txt: str, thread_id: str = None, ordinal: int = 0) -> dict[str, any]:
        id = f"${math.floor(random.random() * 1000000)}"

        e = {
            'meeting_code': id if thread_id is None else thread_id,
            'speaker': sender.email,
            'text': txt,
            'ordinal': ordinal,
        }
        return e
