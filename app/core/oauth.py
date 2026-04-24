from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from dataclasses import dataclass

@dataclass
class OAuthClaims:
    sub: str        # stable unique ID
    email: str
    provider: str   # "google"

def verify_google_token(token: str, client_id: str) -> OAuthClaims:
    """
    Verifies the idToken signature against Google's public keys.
    Raises ValueError if the token is invalid, expired, or for wrong audience.
    
    client_id = your Google OAuth app's client ID
    This prevents tokens issued for other apps from being accepted.
    """
    claims = id_token.verify_oauth2_token(
        token,
        google_requests.Request(),
        client_id
    )
    # If we reach here, the signature is valid and token is not expired
    return OAuthClaims(
        sub=claims["sub"],
        email=claims["email"],
        provider="google"
    )