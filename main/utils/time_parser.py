from datetime import datetime, timezone


def get_current_utc_timestamp():
    current_utc_datetime = datetime.now(timezone.utc)
    formatted_current_utc = current_utc_datetime.strftime('%Y-%m-%dT%H:%M:%S.%f')[
                            :-3] + 'Z'
    return formatted_current_utc
