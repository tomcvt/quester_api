import uuid

def generate_session_token() -> str:
    return str(uuid.uuid4()) + "-" + str(uuid.uuid4())

def generate_safe_api_key(password: str) -> str:
    #TODO: implement proper hashing and salting
    return "api_key_for_" + password