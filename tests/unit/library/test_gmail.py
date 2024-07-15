#import and create pytest tests for the GmailLogic class in library
from library import models    
from library.gsuite import GmailLogic, GSuiteServiceProvider
import pytest
import unittest


class TestGmail(GSuiteServiceProvider):
    __test__ = False
    def __init__(self, totalMessages = 1000):
        self.totalMessages = totalMessages
    
    def service(self):
        pass
    
    def list_emails(self, userId='me', pageToken=None, maxResults = None):
        messages = []
        if not maxResults:
            maxResults = 100
        elif maxResults > 500:
            maxResults = 500

        if pageToken is not None:
            tokenLimit = int(pageToken)
        else:
            tokenLimit = 0

        maxResults = min(maxResults, self.totalMessages)

        counter = 0
        for i in range(tokenLimit, min(maxResults + tokenLimit, self.totalMessages)):
            counter += 1
            messages.append({'id': str(i), 'historyId': str(i), 'threadId': str(i), 'labelIds': ['INBOX'], 'internalDate': str(i)})
        return {'messages': messages, 'nextPageToken': str(counter) if maxResults + tokenLimit < self.totalMessages else None}
    
    def get_email(self, id, userId='me', format='full'):
        return {'payload': {'parts': [{'mimeType': 'text/plain', 'body': {'data': 'dGV4dC1wbGFpbg=='}}]}}
    
    def close(self):
        pass

class TestGmailLogic(unittest.TestCase):

    def test_stub_sanity(self):
        tm = TestGmail(5)
        assert tm.totalMessages == 5
        assert len(tm.list_emails(maxResults=10)['messages']) == 5
        assert tm.list_emails(maxResults=10)['nextPageToken'] is None

        #request these in pieces now
        assert len(tm.list_emails(maxResults=3)['messages']) == 3
        assert tm.list_emails(maxResults=3)['nextPageToken'] is not None

        prev_token = tm.list_emails(maxResults=3)['nextPageToken']
        print("Prev token: " + prev_token)
        assert len(tm.list_emails(maxResults=3, pageToken = prev_token)['messages']) == 2
        assert tm.list_emails(maxResults=3, pageToken = prev_token)['nextPageToken'] is None


    def test_get_emails_returns_as_many_as_asked_for_below_limit(self):
        tm = TestGmail(1000)
        gmail = GmailLogic(tm)
        emails = gmail.get_emails(10)
        assert len(emails) == 10

        emails = gmail.get_emails(899)
        assert len(emails) == 899

        emails = gmail.get_emails(1199)
        assert len(emails) == 1000

