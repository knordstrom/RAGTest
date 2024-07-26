import os
import unittest
# import groq
import sys

from library.weaviate_schemas import EmailTextWithFrom
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))
import library.briefing_support as bs
import json
import pickle


class BriefingSupportTest(unittest.TestCase):
    # this doesn't test anything but that the result the original code spit out is the same as what the new code will spit out

    def test_group_messages_by_thread_id(self):
        pass
    #     b_s = bs.BriefingSupport()
    #     threads = os.path.join(os.path.dirname(__file__), '../../resources', 'sample_thread.json')
    #     with open(threads) as f:
    #         thread_data = json.load(f)
    #     actual_grouped_messages = os.path.join(os.path.dirname(__file__), '../../resources', 'grouped_messages.pkl')
    #     with open(actual_grouped_messages, 'rb') as f:
    #         actual_grouped_messages_data = pickle.load(f)
    #     grouped_messages = b_s.group_messages_by_thread_id(thread_data)
    #     assert grouped_messages == actual_grouped_messages_data


if __name__ == '__main__':
    unittest.main()