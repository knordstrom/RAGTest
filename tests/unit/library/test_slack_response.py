import unittest
import os
import json

class TestSlackResponse(unittest.TestCase):

    def test_example(self):
        # Assuming the JSON file is in the same directory as the test file
        json_file_path = os.path.join(os.path.dirname(__file__), '../../resources', 'slack_response.json')

        # Load the JSON data into a dictionary
        with open(json_file_path) as json_file:
            channels = json.load(json_file)

        print(len(channels))
        print(channels[0].keys())



        print([channel['name'] for channel in channels])


if __name__ == '__main__':
    unittest.main()