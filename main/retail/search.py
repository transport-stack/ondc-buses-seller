# TODO: this is my views

# from flask import g, request
# from flask_expects_json import expects_json
# from flask_restx import Namespace, Resource, reqparse
from jsonschema import validate

from main import constant
from main.service import send_message_to_queue_for_given_request
from main.service.common import dump_request_payload
from ondc_protocol.models import ONDCDomain
from ondc_protocol.repository.responses import get_ack_response


# TODO: replace with serializers
# from main.utils.schema_utils import get_json_schema_for_given_path, get_json_schema_for_response

# search_namespace = Namespace('search', description='Search Namespace')


# @search_namespace.route("/v1/search")
class SearchCatalogues(Resource):
    path_schema = get_json_schema_for_given_path('/search')

    # @expects_json(path_schema)
    def post(self):
        response_schema = get_json_schema_for_response('/search')
        resp = get_ack_response(ack=True)
        payload = request.get_json()
        dump_request_payload(payload, domain=ONDCDomain.RETAIL.value)
        message = {
            "request_type": f"{ONDCDomain.RETAIL.value}_search",
            "message_ids": {
                "search": payload[constant.CONTEXT]["message_id"]
            }
        }
        send_message_to_queue_for_given_request(message)
        validate(resp, response_schema)
        return resp


@search_namespace.route("/v1/on_search")
class OnSearch(Resource):
    path_schema = get_json_schema_for_given_path('/on_search')

    # @expects_json(path_schema)
    def post(self):
        response_schema = get_json_schema_for_response('/on_search')
        resp = get_ack_response(ack=True)
        payload = request.get_json()
        dump_request_payload(payload, domain=ONDCDomain.RETAIL.value)
        message = {
            "request_type": f"{ONDCDomain.RETAIL.value}_on_search",
            "message_ids": {
                "on_search": payload[constant.CONTEXT]["message_id"]
            }
        }
        send_message_to_queue_for_given_request(message)
        validate(resp, response_schema)
        return resp
