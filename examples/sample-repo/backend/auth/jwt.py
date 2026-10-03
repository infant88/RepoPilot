import json
import base64
import hmac
import hashlib
import time
from typing import Optional, Dict, Any
from backend.config.settings import settings

def create_access_token(data: dict, expires_delta: Optional[int] = None) -> str:
    """Generate a signed HMAC-SHA256 JWT access token."""
    to_encode = data.copy()
    expire = time.time() + (expires_delta or (settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60))
    to_encode.update({"exp": expire, "iat": time.time()})
    
    header = {"alg": settings.JWT_ALGORITHM, "typ": "JWT"}
    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    payload_b64 = base64.urlsafe_b64encode(json.dumps(to_encode).encode()).decode().rstrip("=")
    
    signature = hmac.new(
        settings.JWT_SECRET.encode(),
        f"{header_b64}.{payload_b64}".encode(),
        hashlib.sha256
    ).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")
    
    return f"{header_b64}.{payload_b64}.{sig_b64}"

def verify_jwt_token(token: str, secret: str) -> Dict[str, Any]:
    """
    Decodes and validates JWT token signature and expiration.
    Throws ValueError if expired or signature is invalid.
    """
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid token format")
        
    header_b64, payload_b64, sig_b64 = parts
    
    # Re-calculate signature
    expected_sig = hmac.new(
        secret.encode(),
        f"{header_b64}.{payload_b64}".encode(),
        hashlib.sha256
    ).digest()
    
    # Decode signature with padding correction
    padded_sig = sig_b64 + "=" * (-len(sig_b64) % 4)
    given_sig = base64.urlsafe_b64decode(padded_sig.encode())
    
    if not hmac.compare_digest(expected_sig, given_sig):
        raise ValueError("Signature verification failed: invalid key or tampered token")
        
    # Decode payload
    padded_payload = payload_b64 + "=" * (-len(payload_b64) % 4)
    payload = json.loads(base64.urlsafe_b64decode(padded_payload.encode()).decode())
    
    if payload.get("exp", 0) < time.time():
        raise ValueError("Token has expired")
        
    return payload
