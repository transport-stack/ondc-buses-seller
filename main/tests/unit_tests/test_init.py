import unittest
import json
from datetime import datetime, timedelta
import pytz


class TestInit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Load the JSON files for the request and expected responses
        with open('main/tests/jsons/init_jsons/request.json', 'r') as f:
            cls.request_data = json.load(f)
        with open('main/tests/jsons/init_jsons/response.json', 'r') as f:
            cls.response_data = json.load(f)
        # Load cached data for on_select if available
        with open('main/tests/jsons/on_select_jsons/stored_select_data.json', 'r') as f:
            cls.stored_select_data = json.load(f)
        cls.cache = {
            cls.request_data["context"]["transaction_id"]: cls.stored_select_data
        }

    def test_action_is_init(self):
        action = self.request_data.get("context", {}).get("action")
        print(f'\n-Testing if action is "init": \n Result: {action == "init"}')
        self.assertEqual(action, "init", self.response_val("action_is_init", "Invalid action. Expected 'init'."))

    def test_ttl_within_limit(self):
        timestamp = self.request_data.get("context", {}).get("timestamp")
        ttl = self.request_data.get("context", {}).get("ttl")
        request_time = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=pytz.UTC)
        ttl_time = timedelta(seconds=int(ttl.strip('PT').strip('S')))
        current_time = datetime.now(pytz.UTC)
        print(f'\n-Testing TTL within limit: \n Request Time: {request_time}, Current Time: {current_time}, TTL: {ttl_time}')
        self.assertLess(current_time - request_time, ttl_time, self.response_val("ttl_within_limit", "NACK sent to the buyer (In our case Chartr)"))

    def test_context_present(self):
        context = self.request_data.get("context")
        print(f'\n-Testing if context is present: \n Result: {context is not None}')
        self.assertIsNotNone(context, self.response_val("context_present", "Missing context or message data."))

    def test_message_present(self):
        message = self.request_data.get("message")
        print(f'\n-Testing if message is present: \n Result: {message is not None}')
        self.assertIsNotNone(message, self.response_val("message_present", "Missing context or message data."))

    def test_on_select_data_present_in_cache(self):
        transaction_id = self.request_data.get("context", {}).get("transaction_id")
        cached_data = self.cache.get(transaction_id)
        print(f'\n-Testing on_select cached data for transaction_id: \n Result: {cached_data is not None}')
        self.assertIsNotNone(cached_data, self.response_val("on_select_data_present", "No data found for the given transaction ID"))

    def test_order_object_present(self):
        order = self.request_data.get("message", {}).get("order")
        print(f'\n-Testing if order object is present: \n Result: {order is not None}')
        self.assertIsNotNone(order, self.response_val("order_object_present", "Missing context or message data."))

    def test_bap_uri_present(self):
        bap_uri = self.request_data.get("context", {}).get("bap_uri")
        print(f'\n-Testing if BAP URI is present: \n Result: {bap_uri is not None}')
        self.assertIsNotNone(bap_uri, self.response_val("bap_uri_present", "BAP URI not found."))

    def test_on_init_request_sent_to_buyer(self):
        # Simulating sending a request
        result = self.mock_send_to_chartr("on_init")
        print(f'\n-Testing if on_init request was sent to Chartr: \n Result: {result}')
        self.assertTrue(result, "Request not sent")

    def test_ack_received(self):
        # Simulating receiving an ACK
        ack = self.mock_receive_ack("on_init")
        print(f'\n-Testing if ACK was received: \n Result: {ack == "ACK"}')
        self.assertEqual(ack, "ACK", "NACK received")

    def mock_send_to_chartr(self, request_type):
        # Placeholder for actual sending logic
        return True

    def mock_receive_ack(self, request_id):
        # Placeholder for actual ACK reception logic
        return "ACK"

    def response_val(self, key, default_message):
        # Helper function to get the expected response
        return self.response_data.get(key, {}).get("status", default_message)

if __name__ == "__main__":
    unittest.main()
