from django.test import TestCase
from django.core.cache import cache
from main.tasks.on_select import on_select
from unittest.mock import patch, ANY
import json
import requests
import logging


class TestOnSelect(TestCase):

    def setUp(self):
        # Load the JSON data files for the test
        with open('main/tests/jsons/on_search_jsons/stored_search_data.json', 'r') as file:
            self.stored_search_data = json.load(file)
        with open('main/tests/jsons/on_select_jsons/request.json', 'r') as file:
            self.request_payload = json.load(file)

        # Set the transaction ID and cache key based on the request data
        self.transaction_id = self.request_payload['context']['transaction_id']
        self.cache_key = f'{self.transaction_id}:search'

        # Set initial cache data from the stored search data
        cache.set(self.cache_key, self.stored_search_data)
        self.on_select_request = self.request_payload

    @patch('requests.post')
    def test_successful_execution(self, mock_post):
        # Arrange
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"ack": True}

        # Act
        result = on_select.apply_async(args=[self.on_select_request])

        # Log the result and cached data for debugging
        cached_data = cache.get(f'{self.transaction_id}:search')

        # Assert
        self.assertTrue(result)
        self.assertIsNotNone(cached_data)
        response = requests.post(
            self.on_select_request['context']['bap_uri'] + '/on_select',
            json=ANY
        )
        self.assertEqual(response.status_code, 200)

    def test_missing_cached_data(self):
        # Arrange
        cache.delete(self.cache_key)

        # Act
        result = on_select(self.on_select_request)

        # Assert
        self.assertFalse(result)

    def test_item_or_provider_not_found(self):
        # Arrange
        self.on_select_request['item'] = ''
        self.on_select_request['provider'] = ''

        # Act
        result = on_select(self.on_select_request)

        # Log the result for debugging
        logging.debug(f'Result: {result}')

        # Assert
        self.assertFalse(result)
