from modules.fare_setup.main import FareCalculator

print(
    FareCalculator().get_fare_given_route_id__start_stop_code__end_stop_code('2', 0, 1))
# # print(FareCalculator().get_routes_given_start_stop_code__end_stop_code("D_BLOCK_MANGOL_PURI_T",
# #                                                                        "POLICE_STATION_BEGUMPUR"))

print(FareCalculator().get_routes_given_start_stop_code__end_stop_code(
    "ROHINI_SEC_22_TERMINAL",
    "AVANTIKA_XING"))
