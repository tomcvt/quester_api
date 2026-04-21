import uuid
from passlib.context import CryptContext

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)

def generate_session_token() -> str:
    return str(uuid.uuid4()) + "-" + str(uuid.uuid4())

def generate_safe_api_key(password: str) -> str:
    #TODO: implement proper hashing and salting
    return "api_key_for_" + password