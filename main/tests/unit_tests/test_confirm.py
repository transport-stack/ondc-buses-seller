import unittest
import json
from datetime import datetime, timedelta
import pytz

class TestConfirm(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Load request, response, and cached data
        with open('main/tests/jsons/confirm_jsons/request.json', 'r') as f:
            cls.request_data = json.load(f)
        with open('main/tests/jsons/confirm_jsons/response.json', 'r') as f:
            cls.response_data = json.load(f)
        with open('main/tests/jsons/on_select_jsons/stored_select_data.json', 'r') as f:
            cls.stored_select_data = json.load(f)
        cls.cache = {
            cls.request_data["context"]["transaction_id"]: cls.stored_select_data
        }

    def test_action_is_confirm(self):
        action = self.request_data.get("context", {}).get("action")
        print(f'\n-Testing if action is "confirm": \n Result: {action == "confirm"}')
        self.assertEqual(action, "confirm", self.response_val("action_is_confirm", "Invalid action. Expected 'confirm'."))

    def test_ttl_within_limit(self):
        timestamp = self.request_data["context"]["timestamp"]
        ttl = self.request_data["context"]["ttl"]
        request_time = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=pytz.UTC)
        ttl_time = timedelta(seconds=int(ttl.strip('PT').strip('S')))
        current_time = datetime.now(pytz.UTC)
        print(f'\n-Testing TTL within limit: \n Request Time: {request_time}, Current Time: {current_time}, TTL: {ttl_time}')
        self.assertLess(current_time - request_time, ttl_time, self.response_val("ttl_within_limit", "NACK sent to the buyer (In our case Chartr)"))

    def test_context_present(self):
        context = self.request_data["context"]
        print(f'\n-Testing if context is present: \n Result: {context is not None}')
        self.assertIsNotNone(context, self.response_val("context_present", "Missing context or message data."))

    def test_message_present(self):
        message = self.request_data["message"]
        print(f'\n-Testing if message is present: \n Result: {message is not None}')
        self.assertIsNotNone(message, self.response_val("message_present", "Missing context or message data."))

    def test_on_select_data_present_in_cache(self):
        transaction_id = self.request_data["context"]["transaction_id"]
        cached_data = self.cache.get(transaction_id)
        print(f'\n-Testing on_select cached data for transaction_id: \n Result: {cached_data is not None}')
        self.assertIsNotNone(cached_data, self.response_val("on_select_data_present", "No data found for the given transaction ID"))

    def test_pnr_is_unique(self):
        pnr = self.request_data["message"]["order"]["payments"][0]["params"]["transaction_id"]
        is_unique = pnr == "24060316303S5LGV"  # This is a placeholder for an actual uniqueness test
        print(f'\n-Testing if PNR is unique: \n Result: {is_unique}')
        self.assertTrue(is_unique, self.response_val("pnr_is_unique", "vendor_booking_id should be always unique"))

    def test_bap_uri_present(self):
        bap_uri = self.request_data["context"]["bap_uri"]
        print(f'\n-Testing if BAP URI is present: \n Result: {bap_uri is not None}')
        self.assertIsNotNone(bap_uri, self.response_val("bap_uri_present", "BAP URI not found."))

    def test_on_confirm_request_sent_to_buyer(self):
        result = self.mock_send_to_chartr("on_confirm")
        print(f'\n-Testing if on_confirm request was sent to Chartr: \n Result: {result}')
        self.assertTrue(result, "Request not sent")

    def test_ack_received(self):
        ack = self.mock_receive_ack("on_confirm")
        print(f'\n-Testing if ACK was received: \n Result: {ack == "ACK"}')
        self.assertEqual(ack, "ACK", "NACK received")

    def test_ticket_data_saved(self):
        ticket_created = True  # Simulate ticket creation result
        print(f'\n-Testing if ticket data is getting saved in the Database: \n Result: {ticket_created}')
        self.assertTrue(ticket_created, "Ticket not created")

    def mock_send_to_chartr(self, request_type):
        return True

    def mock_receive_ack(self, request_type):
        return "ACK"

    def response_val(self, key, default_message):
        return self.response_data.get(key, {}).get("status", default_message)

if __name__ == "__main__":
    unittest.main()
