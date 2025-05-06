import unittest
from unittest.mock import patch, MagicMock, ANY
from main.tasks.on_init import on_init
from django.core.cache import cache
import json


class OnInitTaskTestCase(unittest.TestCase):

    def setUp(self):
        # Load the JSON data files for the test
        with open('main/tests/jsons/on_init_jsons/request.json', 'r') as file:
            self.on_init_request = json.load(file)

        with open('main/tests/jsons/on_select_jsons/stored_select_data.json', 'r') as file:
            self.stored_data = json.load(file)

        # Prepare the context and message data for easier access
        self.context_data = self.on_init_request['context']
        self.message_data = self.on_init_request['message']

        # Prepare cache keys
        self.cache_key_select = self.context_data['transaction_id'] + ':select'
        self.cache_key_init = self.context_data['transaction_id'] + ':init'

        # Set initial cache data from the stored select data
        cache.set(self.cache_key_select, self.stored_data)

    @patch('requests.post')
    def test_successful_execution(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200, json=lambda: {"ack": True})

        result = on_init(self.on_init_request)

        cached_data = cache.get(self.cache_key_init)
        self.assertIsNotNone(cached_data)
        self.assertEqual(cached_data['context']['transaction_id'],
                         self.context_data['transaction_id'])
        self.assertEqual(cached_data['message']['order']['items'][0]['id'],
                         self.message_data['order']['items'][0]['id'])

        self.assertEqual(result, True)

        mock_post.assert_called_once_with(self.context_data['bap_uri'] + '/on_init', json=ANY)

    def test_missing_cached_data(self):
        cache.delete(self.cache_key_select)

        result = on_init(self.on_init_request)

        self.assertEqual(result, False)

    def test_missing_order_data(self):
        incomplete_message_data = {
            "order": {}
        }

        incomplete_on_init_request = {
            "context": self.context_data,
            "message": incomplete_message_data
        }

        result = on_init(incomplete_on_init_request)

        self.assertEqual(result, False)


if __name__ == '__main__':
    unittest.main()
