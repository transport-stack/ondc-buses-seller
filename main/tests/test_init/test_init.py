from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from unittest.mock import patch
import json


class InitAPITestCase(TestCase):

    def setUp(self):
        self.client = APIClient()

        # Load the JSON data files for the test
        with open('main/tests/jsons/init_jsons/request.json', 'r') as file:
            self.request_payload = json.load(file)
        self.response_payload = {"ack": True}

        self.url = reverse('main:ondc_init-list')
        # Make sure to replace 'main:ondc_init-list' with the actual endpoint name

    def test_invalid_action(self):
        # Arrange
        invalid_request_payload = self.request_payload.copy()
        invalid_request_payload['context']['action'] = 'invalid_action'

        # Act
        response = self.client.post(self.url, data=invalid_request_payload, format='json')

        # Assert
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, "Invalid action. Expected 'init'.")

    def test_missing_context_or_message_data(self):
        # Arrange
        missing_context_request_payload = self.request_payload.copy()
        del missing_context_request_payload['context']

        missing_message_request_payload = self.request_payload.copy()
        del missing_message_request_payload['message']

        # Act
        response_context = self.client.post(self.url, data=missing_context_request_payload, format='json')
        response_message = self.client.post(self.url, data=missing_message_request_payload, format='json')

        # Assert
        self.assertEqual(response_context.status_code, 400)
        self.assertEqual(response_message.status_code, 400)
