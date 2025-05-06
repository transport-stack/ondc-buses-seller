import unittest
import json
import logging
from datetime import datetime, timedelta
import pytz

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TestSelect(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Loading request and response data
        with open('main/tests/jsons/select_jsons/request.json', 'r') as f:
            cls.request_data = json.load(f)
        with open('main/tests/jsons/select_jsons/response.json', 'r') as f:
            cls.response_data = json.load(f)
        # Loading cached on_search data
        with open('main/tests/jsons/on_search_jsons/stored_search_data.json', 'r') as f:
            cls.stored_search_data = json.load(f)
        # Setting up a cache with on_search data keyed by transaction_id
        cls.cache = {
            cls.request_data["context"]["transaction_id"]: cls.stored_search_data
        }

    def test_action_is_select(self):
        action = self.request_data.get("context", {}).get("action")
        print("\nTesting action is 'select':", action)
        self.assertEqual(action, "select", self.response_val("action_is_select", "Invalid action"))

    def test_ttl_within_limit(self):
        timestamp = self.request_data.get("context", {}).get("timestamp")
        ttl = self.request_data.get("context", {}).get("ttl")
        request_time = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=pytz.UTC)
        ttl_time = timedelta(seconds=int(ttl.strip('PT').strip('S')))
        current_time = datetime.now(pytz.UTC)
        print("\nTesting TTL within limit:", "Request Time:", request_time, "Current Time:", current_time, "TTL:", ttl_time)
        self.assertLess(current_time - request_time, ttl_time, self.response_val("ttl_within_limit", "NACK sent to the buyer (In our case Chartr)"))

    def test_context_present(self):
        context = self.request_data.get("context")
        print("\nTesting if context is present:", context)
        self.assertIsNotNone(context, self.response_val("context_present", "Missing required fields in the request data."))

    def test_transaction_cache_data_found(self):
        transaction_id = self.request_data.get("context", {}).get("transaction_id")
        cache_data = self.cache.get(transaction_id)
        print("\nTesting transaction cache data found for ID:", transaction_id)
        self.assertIsNotNone(cache_data, self.response_val("transaction_cache_dated_found", "No data found for the given transaction ID"))

    def test_item_id_present(self):
        item_id = self.request_data.get("message", {}).get("order", {}).get("items")[0].get("id")
        print("\nTesting if item ID is present:", item_id)
        self.assertIsNotNone(item_id, self.response_val("item_id_present", "Invalid request format, Missing key: item_id/provider_id"))

    def test_provider_id_present(self):
        provider_id = self.request_data.get("message", {}).get("order", {}).get("provider", {}).get("id")
        print("\nTesting if provider ID is present:", provider_id)
        self.assertIsNotNone(provider_id, self.response_val("provider_id_present", "Invalid request format, Missing key: item_id/provider an_id"))

    def test_selected_item_present_in_cache(self):
        transaction_id = self.request_data.get("context", {}).get("transaction_id")
        cached_data = self.cache.get(transaction_id)
        item_id = self.request_data.get("message", {}).get("order", {}).get("items")[0].get("id")
        cached_item_ids = [item["id"] for provider in cached_data["message"]["catalog"]["providers"] for item in provider["items"]]
        print("\nTesting selected item present in cache:", "Item ID:", item_id, "Cached Item IDs:", cached_item_ids)
        self.assertIn(item_id, cached_item_ids, self.response_val("selected_item_present_in_cache", "Selected item or provider not found in the stored data"))

    def test_bap_uri_present(self):
        bap_uri = self.request_data.get("context", {}).get("bap_uri")
        print("\nTesting if BAP URI is present:", bap_uri)
        self.assertIsNotNone(bap_uri, self.response_val("bap_uri_present", "BAP URI not found."))

    def test_request_sent_to_chartr_on_select(self):
        # Simulating sending of a request
        result = self.mock_send_to_chartr("on_select")
        print("\nTesting if request was sent to Chartr on select:", result)
        self.assertTrue(result, "Request not sent")

    def test_ack_received_for_on_select(self):
        # Simulating ACK reception
        ack = self.mock_receive_ack("on_select")
        print("\nTesting if ACK was received for on_select:", ack)
        self.assertEqual(ack, "ACK", "NACK received")

    def mock_send_to_chartr(self, request_type):
        # Placeholder for actual request sending logic
        return True

    def mock_receive_ack(self, request_type):
        # Placeholder for actual ACK reception logic
        return "ACK"

    def response_val(self, key, default_message):
        # Handle missing keys gracefully
        return self.response_data.get(key, {}).get("status", default_message)

if __name__ == "__main__":
    unittest.main()
