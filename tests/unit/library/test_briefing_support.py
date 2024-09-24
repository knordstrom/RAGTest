from hashlib import md5
import os
import unittest
# import groq
import sys

from globals import Globals
from library.models.api_models import EmailConversationEntry
from library.managers.briefing_summarizer import BriefingSummarizer
from library.models.employee import User
from library.models.weaviate_schemas import EmailTextWithFrom
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))
import library.managers.briefing_support as bs
import json
import pickle

class BriefingSummarizerStub(BriefingSummarizer):
    def summarize(self, prompt_name: str, context: dict[str, str]) -> str:
        return md5(pickle.dumps(context)).hexdigest()

    def summarize_with_prompt(self, prompt: str, context: dict[str, str]) -> str:
        return md5(pickle.dumps(context)).hexdigest()

class BriefingSupportTest(unittest.TestCase):
    # this doesn't test anything but that the result the original code spit out is the same as what the new code will spit out

    def test_group_messages_by_thread_id(self):
        threads = Globals().test_resource('sample_thread.json')
        
        with open(threads) as f:
            thread_data: dict[str,list[EmailTextWithFrom]] = self.thread_data_becomes_objects(json.load(f))
        
        print(thread_data)
        sum_email: dict[str, list[EmailTextWithFrom]] = {}

        sum = BriefingSummarizerStub()
        grouped_messages: list[EmailConversationEntry] = bs.BriefingSupport(sum, user=User(id="1234", email="keith@cognimate.ai")).process_email_context(thread_data)
        print()
        [print("Grouped", m) for m in grouped_messages]

        assert len(grouped_messages) == 2
        assert grouped_messages[0].thread_id == '18fda76d210fb708'
        assert grouped_messages[0].text[0:27] == '\nKeith: Thanks Pradeep.\nDid'
        assert grouped_messages[0].text[-31:-1] == 'GDrive and see how bad it gets'
        assert grouped_messages[0].summary == sum.summarize_with_prompt('test',  {'Conversation': grouped_messages[0].text})

        assert grouped_messages[1].thread_id == '1905c06b129ea57d'
        assert grouped_messages[1].text == '\nKeith: Invitation: Mithali:Keith @ Thu Jun 27, 2024 4:30pm - 5:30pm (PDT) (mithali@cognimate.ai)'
        assert grouped_messages[1].summary == sum.summarize_with_prompt('test',  {'Conversation': grouped_messages[1].text})

    def thread_data_becomes_objects(self, thread_data: dict[str, list[dict[str,any]]]) ->  dict[str,list[EmailTextWithFrom]]:
        response: dict[str,list[EmailTextWithFrom]] = {}
        for thread, text_list in thread_data.items():
            response[thread] = [EmailTextWithFrom(**message) for message in text_list]
        return response

if __name__ == '__main__':
    unittest.main()