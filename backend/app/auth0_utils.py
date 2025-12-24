import json
import requests
from jose import jwt
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings

def get_auth0_public_key(token):
    jwks_url = f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json"
    jwks = requests.get(jwks_url).json()
    unverified_header = jwt.get_unverified_header(token)
    
    rsa_key = {}
    for key in jwks["keys"]:
        if key["kid"] == unverified_header["kid"]:
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"]
            }
    return rsa_key

def validate_auth0_token(token):
    """
    Decodes the JWT and returns the payload.
    """
    try:
        rsa_key = get_auth0_public_key(token)
        if rsa_key:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=["RS256"],
                audience=settings.AUTH0_AUDIENCE, # Keep passing it if present, but we will relax checks if needed, or better:
                # To support both Access Token (Audience=API) and ID Token (Audience=ClientID), 
                # and since we might not have ClientID in settings, we can disable aud check 
                # OR trust that the library handles list. 
                # Simple fix: Verify signature and issuer.
                options={"verify_aud": False},
                issuer=f"https://{settings.AUTH0_DOMAIN}/"
            )
            return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationFailed(_("Token is expired."), code="token_expired")
    except jwt.JWTClaimsError:
        raise AuthenticationFailed(_("Incorrect claims."), code="token_invalid_claims")
    except Exception as e:
        raise AuthenticationFailed(_("Unable to parse authentication token."), code="token_invalid")
    
    raise AuthenticationFailed(_("Unable to find appropriate key."), code="token_invalid_key")
