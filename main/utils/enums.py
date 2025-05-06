from enum import Enum
from datetime import timedelta


class ActionTTL(Enum):
    ON_SEARCH = 30
    ON_SELECT = 30
    ON_INIT = 180


def get_ttl_delta(action_name):
    # Use getattr to dynamically access enum values
    action_value = getattr(ActionTTL, action_name, None)
    if action_value is None:
        raise ValueError(f"No such action '{action_name}' in ActionTTL enum")
    return timedelta(seconds=action_value.value)
