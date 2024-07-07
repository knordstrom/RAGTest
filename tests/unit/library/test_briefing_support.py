import os
import unittest
# import groq
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))
import library.briefing_support as bs
import json
import pickle


class BriefingSupportTest(unittest.TestCase):
    def test_group_messages_by_thread_id(self):
        b_s = bs.BriefingSupport()
        threads = os.path.join(os.path.dirname(__file__), '../../resources', 'sample_thread.json')
        with open(threads) as f:
            thread_data = json.load(f)
        actual_grouped_messages = os.path.join(os.path.dirname(__file__), '../../resources', 'grouped_messages.pkl')
        with open(actual_grouped_messages, 'rb') as f:
            actual_grouped_messages_data = pickle.load(f)
        grouped_messages = b_s.group_messages_by_thread_id(thread_data)
        assert grouped_messages == actual_grouped_messages_data


if __name__ == '__main__':
    unittest.main()