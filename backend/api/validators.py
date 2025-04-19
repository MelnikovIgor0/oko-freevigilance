import re
from typing import Any, Dict, List, Optional, Union
from datetime import datetime


def validate_username(username: str) -> bool:
    if len(username) < 6 or len(username) > 80:
        return False
    pattern = re.compile("^[a-zA-Z0-9-_]*")
    return pattern.match(username)


def validate_email(email: str) -> bool:
    if len(email) < 5 or len(email) > 255:
        return False
    pattern = re.compile(
        "^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
    )
    return pattern.match(email)


def validate_password(password: str) -> bool:
    if len(password) < 8 or len(password) > 50:
        return False
    pattern = re.compile("^[a-zA-Z0-9-,.;:?]*")
    return pattern.match(password)


def validate_uuid(uuid: str) -> bool:
    pattern = re.compile(
        "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    )
    return pattern.match(uuid)


def validate_url(url: str) -> bool:
    # TODO: найти нормальную регулярку на url
    return True


def validate_name(name: str) -> bool:
    return 0 <= len(name) <= 255


def validate_description(descripiton: str) -> bool:
    return 0 <= len(descripiton) <= 1024


def validate_keywords(keywords: List[str]) -> bool:
    if len(keywords) > 100:
        return False
    for keyword in keywords:
        if len(keyword) > 255:
            return False
    return True


def validate_interval(interval: Dict[str, str]) -> bool:
    if type(interval) != dict:
        return False
    for data_type in ["minutes", "hours", "days", "months", "day_of_week"]:
        if data_type not in interval:
            return False
        if type(interval[data_type]) != str:
            return False
        try:
            value = int(interval[data_type])
            if value < 0:
                return False
            continue
        except:
            pass
        if interval[data_type] == "*":
            continue
        parts = interval[data_type].split(" ")
        if len(parts) != 3:
            return False
        if parts[0] != "*":
            return False
        if parts[1] != "/":
            return False
        try:
            value = int(parts[2])
            if value < 0:
                return False
            continue
        except:
            pass
        return False
    return True


def get_interval(interval: Dict[str, str]) -> str:
    return (
        interval["minutes"].replace(" ", "")
        + " "
        + interval["hours"].replace(" ", "")
        + " "
        + interval["days"].replace(" ", "")
        + " "
        + interval["months"].replace(" ", "")
        + " "
        + interval["day_of_week"].replace(" ", "")
    )


def validate_polygon(polygon: Dict[str, Any]) -> bool:
    if "sensitivity" not in polygon:
        return False
    try:
        sensitivity = float(polygon["sensitivity"])
        if sensitivity < 0 or sensitivity > 100:
            return False
    except:
        return False
    for area_param in ["x", "y", "width", "height"]:
        if area_param not in polygon:
            return False
        try:
            area_param = float(polygon[area_param])
            if area_param < 0:
                return False
        except:
            return False
    return True


def validate_monitoring_event_status(status: str) -> bool:
    return status in ["CREATED", "NOTIFIED", "WATCHED", "REACTED"]


def validate_date_time(date_input: Union[str, int]) -> Optional[datetime]:
    try:
        if isinstance(date_input, int):
            return datetime.fromtimestamp(date_input)
        else:
            return None
    except:
        return None
