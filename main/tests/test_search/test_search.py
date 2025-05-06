import json
import os
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class SearchAPITestCase(APITestCase):

    def setUp(self):
        with open('main/tests/jsons/search_jsons/request.json', 'r') as file:
            self.request_payload = json.load(file)
        with open('main/tests/jsons/search_jsons/response.json', 'r') as file:
            self.response_payload = json.load(file)

    def test_successful_search(self):
        response = self.client.post(
            reverse("main:ondc_search-list"), data=self.request_payload,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_api_with_invalid_json_format(self):
        response = self.client.post(reverse("main:ondc_search-list"),
                                    data='{"invalidJson": true',
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_search_api_with_empty_payload(self):
        response = self.client.post(reverse("main:ondc_search-list"),
                                    data={}, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_search_api_with_unexpected_action_value(self):
        modified_payload = self.request_payload.copy()
        modified_payload['context']['action'] = 'invalid_action'
        response = self.client.post(reverse("main:ondc_search-list"),
                                    data=json.dumps(modified_payload),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_search_api_missing_transaction_id(self):
        modified_payload = self.request_payload.copy()
        del modified_payload['context']['transaction_id']
        response = self.client.post(reverse("main:ondc_search-list"),
                                    data=json.dumps(modified_payload),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_search_api_with_nonexistent_start_stop_code(self):
        modified_payload = self.request_payload.copy()
        modified_payload['message']['intent']['fulfillment']['stops'][0] = ''
        response = self.client.post(reverse("main:ondc_search-list"),
                                    data=json.dumps(modified_payload),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_search_api_with_nonexistent_end_stop_code(self):
        modified_payload = self.request_payload.copy()
        modified_payload['message']['intent']['fulfillment']['stops'][1] = ''
        response = self.client.post(reverse("main:ondc_search-list"),
                                    data=json.dumps(modified_payload),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_search_api_with_invalid_vehicle_category(self):
        modified_payload = self.request_payload.copy()
        modified_payload['message']['intent']['fulfillment'] = 'INVALID_CATEGORY'
        response = self.client.post(reverse("main:ondc_search-list"),
                                    data=json.dumps(modified_payload),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_search_api_without_intent_in_message(self):
        modified_payload = self.request_payload.copy()
        del modified_payload['message']['intent']
        response = self.client.post(reverse("main:ondc_search-list"),
                                    data=json.dumps(modified_payload),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)
    def test_search_api_with_invalid_method_get_instead_of_post(self):
        response = self.client.get(reverse("main:ondc_search-list"),
                                   data=self.request_payload,
                                   content_type='application/json')
        self.assertEqual(response.status_code, 405)

    def test_search_api_with_missing_context_data(self):
        modified_payload = self.request_payload.copy()
        del modified_payload['context']
        response = self.client.post(reverse("main:ondc_search-list"),
                                    data=json.dumps(modified_payload),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)
