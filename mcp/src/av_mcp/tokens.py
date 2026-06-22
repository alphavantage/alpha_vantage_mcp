"""Stateless encrypted OAuth tokens.

Modeled on the org's PyJWT auth pattern (project-alpha ``api/src/api/auth.py``):
**PyJWT HS256** with ``JWT_SECRET_KEY`` for the token envelope (``exp`` / ``client_id`` /
``scope`` / ``typ`` / signature). Because our tokens must carry the upstream Alpha Vantage
**apikey** (itself a secret), a signed-only JWT would leave the apikey base64-readable in the
payload. So the apikey claim is additionally field-encrypted with **Fernet**
(``cryptography.fernet``) using ``AV_APIKEY_ENC_KEY`` — it is never base64-readable.

Fully stateless: minting is pure encrypt, validation is pure ``jwt.decode`` (signature + ``exp``)
plus Fernet decrypt. Nothing is persisted server-side — no DynamoDB, no token store.

Keys are configuration (Lambda env vars sourced from SSM/KMS), not per-token state. They are read
lazily so cold-start ordering and local-dev env fallback both work.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from cryptography.fernet import Fernet, InvalidToken

JWT_ALGORITHM = "HS256"

# Token lifetimes.
ACCESS_TOKEN_TTL = timedelta(hours=1)
REFRESH_TOKEN_TTL = timedelta(days=30)
AUTH_CODE_TTL = timedelta(seconds=60)


class TokenError(Exception):
    """Raised when a token is malformed, expired, tampered, or undecryptable."""


class TokenConfigError(TokenError):
    """Raised when the OAuth signing/encryption keys are not configured (server misconfig).

    Distinct from a bad/expired token: this is an operator error (unset ``JWT_SECRET_KEY`` or
    ``AV_APIKEY_ENC_KEY``) that should surface as a 500, not masquerade as a 401 auth failure.
    """


def _jwt_secret() -> str:
    secret = os.environ.get("JWT_SECRET_KEY", "")
    if not secret:
        raise TokenConfigError("JWT_SECRET_KEY is not configured")
    return secret


def _fernet() -> Fernet:
    key = os.environ.get("AV_APIKEY_ENC_KEY", "")
    if not key:
        raise TokenConfigError("AV_APIKEY_ENC_KEY is not configured")
    return Fernet(key)


def encrypt_apikey(api_key: str) -> str:
    """Field-encrypt the AV apikey with Fernet. Result is opaque ciphertext."""
    return _fernet().encrypt(api_key.encode()).decode()


def decrypt_apikey(enc_apikey: str) -> str:
    """Decrypt a Fernet-encrypted apikey claim. Raises ``TokenError`` if invalid."""
    try:
        return _fernet().decrypt(enc_apikey.encode()).decode()
    except InvalidToken as exc:
        raise TokenError("apikey decryption failed") from exc


def encode_token(claims: dict[str, Any], ttl: timedelta) -> str:
    """Sign a JWT envelope (HS256) carrying ``claims`` plus an ``exp`` ``ttl`` from now."""
    payload = dict(claims)
    payload["exp"] = datetime.now(timezone.utc) + ttl
    return jwt.encode(payload, _jwt_secret(), algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """Verify signature + ``exp`` and return the claims.

    Raises ``jwt.ExpiredSignatureError`` for expired tokens and ``jwt.InvalidTokenError``
    (its superclass) for anything else malformed/tampered, mirroring the org pattern.
    """
    return jwt.decode(token, _jwt_secret(), algorithms=[JWT_ALGORITHM])


def decode_access_token(token: str) -> str | None:
    """Validate a Bearer access token and return the decrypted apikey, or ``None``.

    Convenience for the request path: ``jwt.decode`` (signature + ``exp``) then Fernet-decrypt
    the ``enc_apikey`` claim. Returns ``None`` on any token-level failure (expired, tampered,
    wrong ``typ``, missing/undecryptable apikey) so the caller can answer 401 uniformly.

    ``TokenConfigError`` (unset keys) is NOT swallowed: it propagates so the caller can answer
    500 rather than mask a server misconfiguration as an auth failure.
    """
    try:
        claims = decode_token(token)
    except jwt.InvalidTokenError:
        return None
    if claims.get("typ") != "access":
        return None
    enc_apikey = claims.get("enc_apikey")
    if not enc_apikey:
        return None
    try:
        return decrypt_apikey(enc_apikey)
    except TokenConfigError:
        raise
    except TokenError:
        return None
