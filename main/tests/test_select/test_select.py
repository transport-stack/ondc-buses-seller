import json
import os

import redis
from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse


class SelectAPITestCase(APITestCase):
    def setUp(self):
        with open('main/tests/jsons/select_jsons/request.json', 'r') as file:
            self.request_payload = json.load(file)

        self.redis = redis.StrictRedis(host='localhost', port=6379, db=0)

    def test_select_api_missing_item_id(self):
        # Missing item ID in request
        payload_missing_item_id = self.request_payload.copy()
        del payload_missing_item_id['message']['order']['items']

        response = self.client.post(reverse("main:ondc_select-list"),
                                    data=payload_missing_item_id, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_provider_id(self):
        # Missing provider ID in request
        payload_missing_provider_id = self.request_payload.copy()
        del payload_missing_provider_id['message']['order'][
            'provider']

        response = self.client.post(reverse("main:ondc_select-list"),
                                    data=payload_missing_provider_id, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

