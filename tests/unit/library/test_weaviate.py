from datetime import datetime, timedelta
import unittest

from library.data.local.weaviate import Weaviate
from weaviate.collections.classes.internal import Object

from library.models.weaviate_schemas import EmailParticipant, EmailTextWithFrom


class TestWeavviate(unittest.TestCase):

    def test_collate(self):

        now: datetime = datetime.now()
        metadata = [
            Object(properties= {'email_id': '1','text': "B", "thread_id": "1", "sender": {'email': 'a@b.c', 'name': 'a'}, "ordinal": 1, "date": now + timedelta(seconds = -4678)}, uuid = "0000", metadata = {}, references = {}, vector = {}, collection = 'x'),
            Object(properties= {'email_id': '1','text': "A", "thread_id": "1", "sender": {'email': 'a@b.c', 'name': 'a'}, "ordinal": 0, "date": now + timedelta(seconds = -4678)}, uuid = "0000", metadata = {}, references = {}, vector = {}, collection = 'x'),
            Object(properties= {'email_id': '1','text': "C", "thread_id": "1", "sender": {'email': 'a@b.c', 'name': 'a'}, "ordinal": 2, "date": now + timedelta(seconds = -4678)}, uuid = "0000", metadata = {}, references = {}, vector = {}, collection = 'x'),

            Object(properties= {'email_id': '2','text': "A", "thread_id": "1", "sender": {'email': 'b@c.d', 'name': 'b'}, "ordinal": 0, "date": now + timedelta(seconds = -3002)}, uuid = "0000", metadata = {}, references = {}, vector = {}, collection = 'x'),
            Object(properties= {'email_id': '2','text': "B", "thread_id": "1", "sender": {'email': 'b@c.d', 'name': 'b'}, "ordinal": 1, "date": now + timedelta(seconds = -3002)}, uuid = "0000", metadata = {}, references = {}, vector = {}, collection = 'x'),
            Object(properties= {'email_id': '2','text': "D", "thread_id": "1", "sender": {'email': 'b@c.d', 'name': 'b'}, "ordinal": 2, "date": now + timedelta(seconds = -3002)}, uuid = "0000", metadata = {}, references = {}, vector = {}, collection = 'x'),
            Object(properties= {'email_id': '2','text': "C", "thread_id": "1", "sender": {'email': 'b@c.d', 'name': 'b'}, "ordinal": 3, "date": now + timedelta(seconds = -3002)}, uuid = "0000", metadata = {}, references = {}, vector = {}, collection = 'x'),

            Object(properties= {'email_id': '3','text': "A", "thread_id": "1", "ordinal": 4, "sender": {'email': 'c@d.e', 'name': 'c'}, "date": now + timedelta(seconds = -2134)}, uuid = "0000", metadata = {}, references = {}, vector = {}, collection = 'x'),
            Object(properties= {'email_id': '3','text': "A", "thread_id": "1", "ordinal": 3, "sender": {'email': 'c@d.e', 'name': 'c'}, "date": now + timedelta(seconds = -2134)}, uuid = "0000", metadata = {}, references = {}, vector = {}, collection = 'x'),
            Object(properties= {'email_id': '3','text': "A", "thread_id": "1", "ordinal": 2, "sender": {'email': 'c@d.e', 'name': 'c'}, "date": now + timedelta(seconds = -2134)}, uuid = "0000", metadata = {}, references = {}, vector = {}, collection = 'x'),    
            Object(properties= {'email_id': '3','text': "A", "thread_id": "1", "ordinal": 1, "sender": {'email': 'c@d.e', 'name': 'c'}, "date": now + timedelta(seconds = -2134)}, uuid = "0000", metadata = {}, references = {}, vector = {}, collection = 'x')
        ]

        results = Weaviate._collate_emails(metadata)

        assert results == [
            EmailTextWithFrom(text="ABC", email_id="1", thread_id="1", ordinal=1, sender=EmailParticipant(email="a@b.c", name="a"), date = now + timedelta(seconds = -4678)),
            EmailTextWithFrom(text="ABDC", email_id="2", thread_id="1", ordinal=0, sender=EmailParticipant(email="b@c.d", name="b"), date = now + timedelta(seconds = -3002)),
            EmailTextWithFrom(text="AAAA", email_id="3", thread_id="1", ordinal=4, sender=EmailParticipant(email="c@d.e", name="c"), date = now + timedelta(seconds = -2134)),
        ]