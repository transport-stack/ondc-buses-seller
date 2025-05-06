import logging

from main.models.request import Fulfilment, Item
from main.transformers.base import RequestBodyTransformer
from modules.fare_setup.main import FareCalculator


# def profile_task(func):
#     def wrapper(*args, **kwargs):
#         profiler = cProfile.Profile()
#         profiler.enable()
#         result = func(*args, **kwargs)
#         profiler.disable()
#         s = io.StringIO()
#         sortby = 'cumulative'
#         ps = pstats.Stats(profiler, stream=s).sort_stats(sortby)
#         ps.print_stats()
#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#         filename = f'profiles/{func.__name__}_celery_profiling_stats_{timestamp}.prof'
#         profiler.dump_stats(filename)
#
#         # with open(f'profiles/{func.__name__}_celery_profiling_stats_{timestamp}.txt', 'a') as f:
#         #     f.write(s.getvalue())
#         return result
#
#     return wrapper

class SearchTransformer(RequestBodyTransformer):

    def chartr_to_ondc(self, route, vehicle, *args, context=None, **kwargs):
        fulfilment, _ = Fulfilment.objects.get_or_create(
            type="ROUTE",
            stops=route,
            vehicle=dict(vehicle)
        )
        item = Item.objects.create(
            fulfillment=fulfilment,
        )
        item.save()
        return {
            "context": context,
            "message": {
                "catalog": {
                    "descriptor": {
                        "name": "Delhi Metro",
                        "images": [
                            {
                                "url": "string"
                            }
                        ]
                    },
                    "providers": [
                        {
                            "id": "P1",  # provider id
                            "descriptor": {
                                "name": "Delhi Metro Rail Limited",
                            },
                            "fulfillments": [
                                fulfilment.__dict__
                            ],
                            "items": [
                                {
                                    "id": str(item.id),
                                }
                            ]
                        }
                    ]
                }
            }
        }

    # @profile_task
    def ondc_to_chartr_v2(self, request_data):
        try:
            if len(request_data.get('stops', [])) != 2 or 'vehicle' not in request_data:
                raise ValueError("Stops or vehicle is missing.")

            start_stop = next(filter(lambda x: x.get('type') == 'START',
                                     request_data.get('stops', [])), None)
            end_stop = next(
                filter(lambda x: x.get('type') == 'END', request_data.get('stops', [])),
                None)

            if not start_stop or not end_stop:
                raise ValueError("Start or end stop is missing.")

            start_code = start_stop['location']['descriptor']['code']
            end_code = end_stop['location']['descriptor']['code']
            variant = request_data.get('vehicle', {}).get('variant', None)
            is_ac = False if variant and variant.upper() == 'NAC' else True if variant and variant.upper() == 'AC' else None
            calculator = FareCalculator()
            combined_data, sequence_dict = calculator.get_combined_route_and_fare_details(start_code, end_code, is_ac)
            if not combined_data or not sequence_dict:
                return f"No matching route found for provided stops. {start_code} to {end_code} with is_ac = {is_ac}"
            else:
                logging.info(f"{request_data['context']['transaction_id']} had {len(combined_data)} results/")
                logging.info(f"Fetched routes data for {request_data['context']['transaction_id']}======={combined_data}")
                return combined_data, sequence_dict

        except Exception as ex:
            logging.error(f"Unhandled error : {ex}")
