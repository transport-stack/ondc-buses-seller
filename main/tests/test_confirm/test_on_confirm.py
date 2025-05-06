import unittest
from unittest.mock import patch, MagicMock
from main.tasks.on_confirm import on_confirm
from django.core.cache import cache
import json
import requests
from datetime import datetime, timezone
import logging


class OnConfirmTaskTestCase(unittest.TestCase):

    def setUp(self):
        # Load the JSON data files for the test
        with open('main/tests/jsons/on_confirm_jsons/request.json', 'r') as file:
            self.on_confirm_request = json.load(file)

        with open('main/tests/jsons/on_select_jsons/stored_select_data.json',
                  'r') as file:
            self.stored_data = json.load(file)

        # Prepare the context and message data for easier access
        self.context_data = self.on_confirm_request['context']
        self.message_data = self.on_confirm_request['message']

        # Prepare cache keys
        self.cache_key_select = self.context_data['transaction_id'] + ':select'

        print("Cache_key==================",self.cache_key_select)
        # print("Stored_data==================",self.stored_data)

        # Set initial cache data from the stored select data
        cache.set(self.cache_key_select, self.stored_data)
        print("Cache_data==================" , cache.get(self.cache_key_select))

    @patch('requests.post')
    @patch('modules.fare_setup.main.FareCalculator.conn')
    @patch('modules.fare_setup.main.FareCalculator')
    def test_successful_execution(self, mock_fare_calculator, mock_conn, mock_post):
        # Arrange
        mock_conn.cursor.return_value.fetchall.return_value = [
            ('Stop A', 'STOPA', 1),
            ('Stop B', 'STOPB', 2)
        ]
        mock_post.return_value = MagicMock(status_code=200, json=lambda: {
            "data": {
                "booking": {
                    "total_fare": 100,
                    "amount_payable_by_user": 90,
                    "ticket": {
                        "ticket_id": "TICKET123",
                        "validTill": "2024-05-11T10:37:46.551345+00:00"
                    },
                    "busRegistrationNumber": "BUS123",
                    "route": "Route A",
                    "createdAt": "2024-05-11T10:37:46.551345+00:00",
                    "agency": "Agency A"
                }
            }
        })
        mock_fare_calculator.return_value = mock_fare_calculator
        mock_fare_calculator.conn = mock_conn

        # Act
        result = on_confirm(self.on_confirm_request)
        print("Result=========", result)

        # Assert
        self.assertEqual(result, True)
        mock_post.assert_called_once()
        cached_data = cache.get(self.context_data['transaction_id'] + ':confirm')
        self.assertIsNotNone(cached_data)

    @patch('requests.post')
    @patch('modules.fare_setup.main.FareCalculator.conn')
    def test_database_connection_failure(self, mock_conn, mock_post):
        # Arrange
        mock_conn.return_value = None  # Simulate database connection failure

        # Act
        result = on_confirm(self.on_confirm_request)

        # Assert
        self.assertEqual(result, False)
        self.assertLogs(level='ERROR')

    def test_missing_cached_data(self):
        # Arrange
        cache.delete(self.cache_key_select)  # Ensure the cache is empty

        # Act
        result = on_confirm(self.on_confirm_request)

        # Assert
        self.assertEqual(result, False)
        self.assertLogs(level='ERROR')

    @patch('requests.post')
    @patch('modules.fare_setup.main.FareCalculator.conn')
    def test_error_in_external_api_call(self, mock_conn, mock_post):
        # Arrange
        mock_conn.cursor.return_value.fetchall.return_value = [
            ('Stop A', 'STOPA', 1),
            ('Stop B', 'STOPB', 2)
        ]
        mock_post.return_value = MagicMock(status_code=500, json=lambda: {
            "error": "Internal Server Error"})

        # Act
        result = on_confirm(self.on_confirm_request)

        # Assert
        self.assertEqual(result, False)
        self.assertLogs(level='ERROR')

    @patch('requests.post')
    @patch('modules.fare_setup.main.FareCalculator.conn')
    def test_invalid_payment_status(self, mock_conn, mock_post):
        # Arrange
        invalid_payment_request = self.on_confirm_request.copy()
        invalid_payment_request['message']['order']['payments'][0][
            'status'] = "NOT-PAID"

        mock_conn.cursor.return_value.fetchall.return_value = [
            ('Stop A', 'STOPA', 1),
            ('Stop B', 'STOPB', 2)
        ]
        mock_post.return_value = MagicMock(status_code=200, json=lambda: {
            "data": {
                "booking": {
                    "total_fare": 100,
                    "amount_payable_by_user": 90,
                    "ticket": {
                        "ticket_id": "TICKET123",
                        "validTill": "2024-05-11T10:37:46.551345+00:00"
                    },
                    "busRegistrationNumber": "BUS123",
                    "route": "Route A",
                    "createdAt": "2024-05-11T10:37:46.551345+00:00",
                    "agency": "Agency A"
                }
            }
        })

        # Act
        result = on_confirm(invalid_payment_request)

        # Assert
        self.assertEqual(result, False)
        self.assertLogs(level='ERROR')


if __name__ == '__main__':
    unittest.main()
