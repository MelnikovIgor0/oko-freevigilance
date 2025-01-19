import re

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
