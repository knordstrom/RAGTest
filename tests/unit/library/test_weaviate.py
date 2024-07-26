import unittest

from library.weaviate import Weaviate
from weaviate.collections.classes.internal import Object

from library.weaviate_schemas import EmailParticipant, EmailTextWithFrom


class TestWeavviate(unittest.TestCase):

    def test_collate(self):

        metadata = [
            Object(properties= {'email_id': '1','text': "B", "thread_id": "1", "ordinal": 1}, uuid = "0000", metadata = {}, references = {}, vector = {}, collection = 'x'),
            Object(properties= {'email_id': '1','text': "A", "thread_id": "1", "ordinal": 0}, uuid = "0000", metadata = {}, references = {}, vector = {}, collection = 'x'),
            Object(properties= {'email_id': '1','text': "C", "thread_id": "1", "ordinal": 2}, uuid = "0000", metadata = {}, references = {}, vector = {}, collection = 'x'),

            Object(properties= {'email_id': '2','text': "A", "thread_id": "1", "ordinal": 0}, uuid = "0000", metadata = {}, references = {}, vector = {}, collection = 'x'),
            Object(properties= {'email_id': '2','text': "B", "thread_id": "1", "ordinal": 1}, uuid = "0000", metadata = {}, references = {}, vector = {}, collection = 'x'),
            Object(properties= {'email_id': '2','text': "D", "thread_id": "1", "ordinal": 2}, uuid = "0000", metadata = {}, references = {}, vector = {}, collection = 'x'),
            Object(properties= {'email_id': '2','text': "C", "thread_id": "1", "ordinal": 3}, uuid = "0000", metadata = {}, references = {}, vector = {}, collection = 'x'),

            Object(properties= {'email_id': '3','text': "A", "thread_id": "1", "ordinal": 4}, uuid = "0000", metadata = {}, references = {}, vector = {}, collection = 'x'),
            Object(properties= {'email_id': '3','text': "A", "thread_id": "1", "ordinal": 3}, uuid = "0000", metadata = {}, references = {}, vector = {}, collection = 'x'),
            Object(properties= {'email_id': '3','text': "A", "thread_id": "1", "ordinal": 2}, uuid = "0000", metadata = {}, references = {}, vector = {}, collection = 'x'),    
            Object(properties= {'email_id': '3','text': "A", "thread_id": "1", "ordinal": 1}, uuid = "0000", metadata = {}, references = {}, vector = {}, collection = 'x')
        ]

        froms = {
            '1': {'email': 'a@b.c', 'name': 'a'},
            '2': {'email': 'b@c.d', 'name': 'b'},
            '3': {'email': 'c@d.e', 'name': 'c'}
        }
        results = Weaviate._collate_emails(metadata, froms)

        assert results == [
            EmailTextWithFrom(text="ABC", email_id="1", thread_id="1", ordinal=1, from_=EmailParticipant(email="a@b.c", name="a")),
            EmailTextWithFrom(text="ABDC", email_id="2", thread_id="1", ordinal=0, from_=EmailParticipant(email="b@c.d", name="b")),
            EmailTextWithFrom(text="AAAA", email_id="3", thread_id="1", ordinal=4, from_=EmailParticipant(email="c@d.e", name="c")),
        ]