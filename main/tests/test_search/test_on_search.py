from django.test import TestCase
import json
import os
from unittest.mock import patch, Mock, ANY
from main.tasks.on_search import on_search


class TestOnSearch(TestCase):
    def setUp(self):
        with open('main/tests/jsons/on_search_jsons/request.json', 'r') as file:
            self.request_payload = json.load(file)
        with open('main/tests/jsons/on_search_jsons/response.json', 'r') as file:
            self.response_payload = json.load(file)
        with open('main/tests/jsons/on_search_jsons/search_transformer_response.json', 'r') as file:
            self.search_transformer_response = json.load(file)

    @patch('main.transformers.search_transformer.SearchTransformer.ondc_to_chartr_v2')
    @patch('modules.fare_setup.main.FareCalculator.get_stop_name_from_code')
    @patch('requests.post')
    @patch('django.core.cache.cache.set')
    def test_on_search_success(self, mock_cache_set, mock_post, mock_get_stop_name_from_code, mock_ondc_to_chartr_v2):
        # Mock environment variables setup
        os.environ['BPP_ID'] = '123'
        os.environ['BPP_URL'] = 'https://bpp.example.com'

        # Setup mocks
        mock_ondc_to_chartr_v2.return_value = self.search_transformer_response
        mock_get_stop_name_from_code.side_effect = lambda code: "Station Name for " + code

        mock_response = Mock()
        mock_response.json.return_value = {'success': True}
        mock_post.return_value = mock_response

        # Call the function using apply to run it synchronously
        result = on_search.apply(args=[self.request_payload]).get()

        # Assertions
        mock_ondc_to_chartr_v2.assert_called_once_with(self.request_payload)
        self.assertEqual(mock_get_stop_name_from_code.call_count, 20)
        print("mock_post===========", mock_post.call_args)
        # Verify response handling
        self.assertTrue(mock_response.json.called)
