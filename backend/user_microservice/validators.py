import re
from typing import Any, Dict, List

def validate_username(username: str) -> bool:
    if len(username) < 6 or len(username) > 80:
        return False
    pattern = re.compile("^[a-zA-Z0-9-_]*")
    return pattern.match(username)

def validate_email(email: str) -> bool:
    if len(email) < 5 or len(email) > 255:
        return False
    pattern = re.compile("^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$")
    return pattern.match(email)

def validate_password(password: str) -> bool:
    if len(password) < 8 or len(password) > 50:
        return False
    pattern = re.compile("^[a-zA-Z0-9-,.;:?]*")
    return pattern.match(password)

def validate_uuid(uuid: str) -> bool:
    pattern = re.compile("^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
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

def validate_interval(interval: str) -> bool:
    # TODO: договориться о формате и научиться валидировать крон-выражения
    return True

def validate_polygon(polygon: Dict[str, Any]) -> bool:
    if 'sensitivity' not in polygon:
        return False
    try:
        sensitivity = float(polygon['sensitivity'])
        if sensitivity < 0 or sensitivity > 100:
            print('here1')
            return False
    except:
        return False
    for area_param in ['x', 'y', 'width', 'height']:
        if area_param not in polygon:
            print('here2', area_param)
            return False
        try:
            area_param = float(polygon[area_param])
            if area_param < 0:
                print('here3', area_param)
                return False
        except:
            return False
    return True
