from rest_framework.test import APITestCase
from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework import status
from django.core.cache import cache
import json
from rest_framework.test import APIClient


class ConfirmAPITestCase(APITestCase):

    def setUp(self):
        self.client = APIClient()

        # Load the request payload from JSON file
        with open('main/tests/jsons/confirm_jsons/request.json', 'r') as file:
            self.request_payload = json.load(file)

        # Endpoint URL
        self.url = reverse('main:ondc_confirm-list')

    @patch('main.tasks.on_confirm.apply_async')
    def test_confirm_with_valid_data(self, mock_on_confirm):
        # Arrange
        mock_on_confirm.return_value = None  # Mock the delay function

        # Act
        response = self.client.post(self.url, data=self.request_payload, format='json')

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"ack": True})
        mock_on_confirm.assert_called_once_with(args=[self.request_payload])

    def test_confirm_missing_payment_info_in_message(self):
        # Arrange
        invalid_payload = self.request_payload.copy()
        del invalid_payload['message']['order']['payments']

        # Act
        response = self.client.post(self.url, data=invalid_payload, format='json')

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid order or payment key", response.json())

    def test_confirm_with_invalid_payment_structure(self):
        # Arrange
        invalid_payload = self.request_payload.copy()
        invalid_payload['message']['order'] = {"invalid_key": "invalid_value"}

        # Act
        response = self.client.post(self.url, data=invalid_payload, format='json')

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid order or payment key", response.json())

    def test_confirm_with_missing_payment_transaction_id(self):
        # Arrange
        invalid_payload = self.request_payload.copy()
        del invalid_payload['message']['order']['payments'][0]['params']['transaction_id']

        # Act
        response = self.client.post(self.url, data=invalid_payload, format='json')

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Missing payment transaction ID", response.json())

    def test_confirm_with_invalid_item_details_in_message(self):
        # Arrange
        invalid_payload = self.request_payload.copy()
        invalid_payload['message']['order'] = 'invalid_value'

        # Act
        response = self.client.post(self.url, data=invalid_payload, format='json')

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid order or payment key", response.json())

    def test_confirm_response_structure_on_success(self):
        # Act
        response = self.client.post(self.url, data=self.request_payload, format='json')
        print("Response===========", response.json())

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"ack": True})

