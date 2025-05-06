import os

import uuid

from locust import HttpUser, TaskSet, task, between

from main.utils.time_parser import get_current_utc_timestamp


class UserBehavior(TaskSet):
    @task
    def search(self):
        formatted_current_utc = get_current_utc_timestamp()
        payload = {
              "context": {
                "location": {
                  "country": {
                    "code": "IND"
                  },
                  "city": {
                    "code": "std:011"
                  }
                },
                "domain": "ONDC:TRV11",
                "timestamp": formatted_current_utc,
                "bap_id": "dev-ondc-buyer-api.chartr.in",
                "transaction_id": "57b96718-ba4b-420f-a6ad-417aa43489dc",
                "message_id": "eb7a8bee-33a4-4154-b14a-fda1f4390e69",
                "version": "2.0.0",
                "action": "search",
                "bap_uri": "http://192.168.31.163:8001/api/v1/ondc/buyer",
                "ttl": "PT30S"
              },
              "message": {
                "intent": {
                  "fulfillment": {
                    "stops": [
                      {
                        "type": "START",
                        "location": {
                          "descriptor": {
                            "code": "ZAKHIRA_FLYOVER"
                          }
                        }
                      },
                      {
                        "type": "END",
                        "location": {
                          "descriptor": {
                            "code": "DB_GUPTA_MARKET"
                          }
                        }
                      }
                    ],
                    "vehicle": {
                      "category": "BUS",
                      "variant": "AC",
                      "registration": "DL1PD5604"
                    }
                  },
                  "payment": {
                    "tags": [
                      {
                        "descriptor": {
                          "code": "BUYER_FINDER_FEES"
                        },
                        "display": False,
                        "list": [
                          {
                            "descriptor": {
                              "code": "BUYER_FINDER_FEES_PERCENTAGE"
                            },
                            "value": "0"
                          },
                          {
                            "descriptor": {
                              "code": "BUYER_FINDER_FEES_TYPE"
                            },
                            "value": "percent-annualized"
                          }
                        ]
                      },
                      {
                        "descriptor": {
                          "code": "SETTLEMENT_TERMS"
                        },
                        "display": False,
                        "list": [
                          {
                            "descriptor": {
                              "code": "DELAY_INTEREST"
                            },
                            "value": "0.0"
                          },
                          {
                            "descriptor": {
                              "code": "STATIC_TERMS"
                            },
                            "value": "https://api.example-bap.com/booking/terms"
                          }
                        ]
                      }
                    ]
                  }
                }
              }
            }
        self.client.post("/search", json=payload)


class WebsiteUser(HttpUser):
    tasks = [UserBehavior]
    wait_time = between(1, 1.5)

