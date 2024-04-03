import ast
from library import models    
from library.gmail import GmailLogic, GmailServiceProvider
import pytest
import unittest
import os



class TestMessage(unittest.TestCase):

    resource = os.path.dirname(__file__) + "/../resources/sample_email.json"
    def test_messagee_structure(self):
        if os.path.exists(self.resource):
            with open(self.resource, "r") as email_json:
                msg = email_json.read()
                message = ast.literal_eval(msg)
                email_obj = models.Message.extract_data(message)
                assert email_obj['id'] == '18ea11b72cb9b7e5'
                assert email_obj['history_id'] == '8009515'
                assert email_obj['thread_id'] == '18ea11b72cb9b7e5'
                assert email_obj['labels'] == ['UNREAD', 'CATEGORY_UPDATES', 'INBOX']
                assert email_obj['to'] == [{'email': 'keith@madsync.com', 'name': None}]
                assert email_obj['cc'] == []
                assert email_obj['bcc'] == []
                assert email_obj['subject'] == 'Latest News from My Portfolios'
                assert email_obj['from'] == 'fool@motley.fool.com'
                assert email_obj['from_name'] == 'The Motley Fool'
                assert email_obj['date'] == '2024-04-02 17:18:34'
                assert str(email_obj['body'])[0:35:1] == 'Daily Update        The Motley Fool'

        else:
            print("File " +  + " not found")
            assert False