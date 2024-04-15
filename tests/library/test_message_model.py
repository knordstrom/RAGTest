import ast
from library import models    
from library.gmail import GmailLogic, GmailServiceProvider
import pytest
import unittest
import os

class TestMessage(unittest.TestCase):

    resource = os.path.dirname(__file__) + "/../resources/sample_email.json"
    def test_message_structure(self):
        if os.path.exists(self.resource):
            with open(self.resource, "r") as email_json:
                msg = email_json.readline()
                #first messagee
                message = ast.literal_eval(msg)
                email_obj = models.Message.extract_data(message)
                assert email_obj['email_id'] == '18ea11b72cb9b7e5'
                assert email_obj['history_id'] == '8009515'
                assert email_obj['thread_id'] == '18ea11b72cb9b7e5'
                assert email_obj['labels'] == ['UNREAD', 'CATEGORY_UPDATES', 'INBOX']
                assert email_obj['to'] == [{'email': 'soandso@youremail.com', 'name': None}]
                assert email_obj['cc'] == []
                assert email_obj['bcc'] == []
                assert email_obj['subject'] == 'Latest News from My Portfolios'
                assert email_obj['from'] == {'email': 'fool@motley.fool.com', 'name': 'The Motley Fool'}
                assert email_obj['date'] == '2024-04-02 17:18:34'
                assert str(email_obj['body'])[0:35:1] == 'Daily Update        The Motley Fool'

                msg = email_json.readline()
                #second messagee
                message = ast.literal_eval(msg)
                email_obj = models.Message.extract_data(message)
                assert email_obj['email_id'] == '18eb9e11501a6c78'
                assert email_obj['history_id'] == '8022615'
                assert email_obj['thread_id'] == '18eb9e11501a6c78'
                assert email_obj['labels'] == ['UNREAD', 'CATEGORY_UPDATES', 'INBOX']
                assert email_obj['to'] == [{'email': 'soandso@youremail.com', 'name': None}]
                assert email_obj['cc'] == []
                assert email_obj['bcc'] == []
                assert email_obj['subject'] == 'The French Whisperer just shared: "Ghost Ships, WITH Wave Sounds"'
                assert email_obj['from'] == {'email': 'bingo@patreon.com', 'name': 'Patreon'}
                assert email_obj['date'] == '2024-04-07 12:45:19'
                assert str(email_obj['body'])[0:33:1] == 'The French Whisperer just shared:'

                msg = email_json.readline()
                #third messagee
                message = ast.literal_eval(msg)
                email_obj = models.Message.extract_data(message)
                assert email_obj['email_id'] == '18eba138f3178250'
                assert email_obj['history_id'] == '8022873'
                assert email_obj['thread_id'] == '18eba138f3178250'
                assert email_obj['labels'] == ['UNREAD', 'IMPORTANT', 'CATEGORY_UPDATES', 'INBOX']
                assert email_obj['to'] == [{'email': 'soandso@youremail.com', 'name': 'Keith'}]
                assert email_obj['cc'] == []
                assert email_obj['bcc'] == []
                assert email_obj['subject'] == 'Appointment reminder for Tuesday, April 9th'
                assert email_obj['from'] == {'email': 'yourprovider@simplepractice.com', 'name': 'Doctor Appointment'}
                assert email_obj['date'] == '2024-04-07 13:40:26'
                assert str(email_obj['body']) == ''
        else:
            print("File " +  + " not found")
            assert False