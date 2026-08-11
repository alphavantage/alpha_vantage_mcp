"""Verify the Cowork confidential DCR OAuth lifecycle end to end over real HTTP.

Drives ``/register``, ``/authorize``, and ``/token`` with an actual HTTP client so routing,
headers, and redirects match how Microsoft's Cowork token store will exercise them.

With no ``--base-url`` the script starts ``mcp/local_http_server.py`` on a free port with
throwaway signing keys, registers a confidential DCR client, runs every check, and tears the
server down. Given a ``--base-url`` it runs the same checks against that deployment.

    uv run --project mcp python -m av_mcp.cowork_connector.verify_oauth
    uv run --project mcp python -m av_mcp.cowork_connector.verify_oauth \
        --base-url https://mcp.alphavantage.co
"""

from __future__ import annotations

import argparse
import base64
import contextlib
import hashlib
import os
import secrets
import socket
import subprocess
import sys
import tempfile
import time
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional, Sequence

import httpx
from cryptography.fernet import Fernet

from av_mcp.oauth import (
    CONFIDENTIAL_CLIENT_ID_PREFIX,
    COWORK_REDIRECT_URI,
    derive_client_secret,
)

MCP_ROOT = Path(__file__).resolve().parents[3]
LOCAL_SERVER = MCP_ROOT / "local_http_server.py"

# Redirects used for public registration and legacy token-path regression checks.
GENERIC_REDIRECT_URI = "https://claude.ai/api/mcp/auth_callback"
PUBLIC_REDIRECT_URI = "http://127.0.0.1:8765/callback"
# Synthetic legacy public client_id for the public token path.
LEGACY_PUBLIC_CLIENT_ID = "mcp-client-verification"

# Environment the managed local server must not inherit: real OAuth keys or anything that
# would make it talk to AWS.
SCRUBBED_ENV = (
    "JWT_SECRET_KEY",
    "AV_APIKEY_ENC_KEY",
    "DOMAIN_NAME",
    "S3_INGEST_URL",
    "S3_INGEST_SECRET",
    "ANALYTICS_LOGS_BUCKET",
)


@dataclass
class Result:
    name: str
    status: str
    detail: str


@dataclass
class RegisteredClient:
    client_id: str
    client_secret: str


def pkce_pair() -> tuple[str, str]:
    """Return a (code_verifier, S256 code_challenge) pair."""
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return verifier, base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def basic_header(client_id: str, client_secret: str) -> dict[str, str]:
    raw = f"{client_id}:{client_secret}".encode()
    return {"Authorization": f"Basic {base64.b64encode(raw).decode()}"}


def _json(response: httpx.Response) -> dict:
    try:
        payload = response.json()
    except ValueError:
        return {}
    return payload if isinstance(payload, dict) else {}


class Verifier:
    """Runs the confidential-DCR checks against one base URL."""

    def __init__(
        self,
        client: httpx.Client,
        base_url: str,
        api_key: str,
        *,
        local: bool = False,
    ) -> None:
        self.client = client
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.local = local
        self.results: list[Result] = []
        self.registered: Optional[RegisteredClient] = None

    # --- result recording -------------------------------------------------

    def expect(
        self,
        name: str,
        response: httpx.Response,
        status: int,
        *,
        error: Optional[str] = None,
        require: Sequence[tuple[str, bool]] = (),
    ) -> bool:
        problems = []
        if response.status_code != status:
            problems.append(f"expected HTTP {status}, got {response.status_code}")
        if error is not None:
            actual = _json(response).get("error")
            if actual != error:
                problems.append(f"expected error={error!r}, got {actual!r}")
        problems.extend(message for message, ok in require if not ok)
        self.results.append(
            Result(
                name,
                "FAIL" if problems else "PASS",
                "; ".join(problems) or f"HTTP {response.status_code}",
            )
        )
        return not problems

    def skip(self, name: str, reason: str) -> None:
        self.results.append(Result(name, "SKIP", reason))

    # --- request helpers --------------------------------------------------

    def authorize_params(
        self, client_id: str, redirect_uri: str, challenge: str
    ) -> dict[str, str]:
        return {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "state": "verify-state",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        }

    def mint_code(
        self, name: str, client_id: str, redirect_uri: str
    ) -> tuple[Optional[str], str]:
        """Complete the consent form and return the (authorization code, code_verifier)."""
        verifier, challenge = pkce_pair()
        response = self.client.post(
            f"{self.base_url}/authorize",
            params=self.authorize_params(client_id, redirect_uri, challenge),
            data={"api_key": self.api_key},
        )
        location = response.headers.get("Location", "")
        query = urllib.parse.parse_qs(urllib.parse.urlparse(location).query)
        code = (query.get("code") or [""])[0]
        self.expect(
            name,
            response,
            302,
            require=[
                (
                    f"redirect must target {redirect_uri}",
                    location.startswith(redirect_uri),
                ),
                ("redirect must carry an authorization code", bool(code)),
                ("redirect must echo state", query.get("state") == ["verify-state"]),
            ],
        )
        return (code or None), verifier

    def token(
        self, data: dict[str, str], *, basic: Optional[tuple[str, str]] = None
    ) -> httpx.Response:
        headers = basic_header(*basic) if basic else {}
        return self.client.post(f"{self.base_url}/token", data=data, headers=headers)

    def code_exchange(
        self,
        code: str,
        verifier: str,
        redirect_uri: str,
        *,
        extra: Optional[dict[str, str]] = None,
        basic: Optional[tuple[str, str]] = None,
    ) -> httpx.Response:
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "code_verifier": verifier,
        }
        data.update(extra or {})
        return self.token(data, basic=basic)

    # --- checks -----------------------------------------------------------

    def check_metadata(self) -> None:
        response = self.client.get(
            f"{self.base_url}/.well-known/oauth-authorization-server"
        )
        payload = _json(response)
        methods = payload.get("token_endpoint_auth_methods_supported", [])
        registration = payload.get("registration_endpoint", "")
        self.expect(
            "metadata-advertises-client-secret-methods",
            response,
            200,
            require=[
                (
                    f"token_endpoint_auth_methods_supported must offer both secret methods, got {methods}",
                    {"client_secret_basic", "client_secret_post"} <= set(methods),
                ),
                ("public clients must keep the 'none' method", "none" in methods),
                (
                    "metadata must advertise a registration_endpoint",
                    bool(registration) and registration.endswith("/register"),
                ),
            ],
        )

    def check_registration(self) -> Optional[RegisteredClient]:
        """DCR must issue a confidential client (with secret) and accept the Cowork callback."""
        cowork = self.client.post(
            f"{self.base_url}/register",
            json={"redirect_uris": [COWORK_REDIRECT_URI]},
        )
        payload = _json(cowork)
        client_id = payload.get("client_id") or ""
        client_secret = payload.get("client_secret") or ""
        requires: list[tuple[str, bool]] = [
            (
                "registration must return a confidential client_id prefix",
                bool(client_id) and client_id.startswith(CONFIDENTIAL_CLIENT_ID_PREFIX),
            ),
            ("registration must return a client_secret", bool(client_secret)),
            (
                "client_secret_expires_at must be 0 (no expiry)",
                payload.get("client_secret_expires_at") == 0,
            ),
            (
                "token_endpoint_auth_method must be secret-based",
                payload.get("token_endpoint_auth_method")
                in ("client_secret_basic", "client_secret_post"),
            ),
            (
                "registered redirect_uris must include the Cowork callback",
                COWORK_REDIRECT_URI in (payload.get("redirect_uris") or []),
            ),
        ]
        # HMAC derivation check only in local mode, where this process shares JWT_SECRET_KEY
        # with the managed server. Remote mode must not use the operator's env secret as a
        # proxy — that would spuriously FAIL against a deployment with a different key.
        if self.local and client_id and client_secret:
            try:
                expected_secret = derive_client_secret(client_id)
                requires.append(
                    (
                        "issued client_secret must match HMAC derivation",
                        secrets.compare_digest(client_secret, expected_secret),
                    )
                )
            except Exception as error:  # noqa: BLE001 - surface as a failed require
                requires.append((f"derive_client_secret failed: {error}", False))

        ok = self.expect(
            "register-issues-confidential-dcr-client",
            cowork,
            201,
            require=requires,
        )

        # Every non-Cowork registration keeps the legacy public response shape.
        generic = self.client.post(
            f"{self.base_url}/register",
            json={"redirect_uris": [GENERIC_REDIRECT_URI]},
        )
        generic_payload = _json(generic)
        self.expect(
            "register-generic-remains-public-secretless",
            generic,
            201,
            require=[
                (
                    "generic registration must issue the legacy mcp-client- prefix",
                    str(generic_payload.get("client_id", "")).startswith("mcp-client-"),
                ),
                (
                    "generic registration must not issue a client_secret",
                    "client_secret" not in generic_payload,
                ),
                (
                    "generic registration must not issue client_secret_expires_at",
                    "client_secret_expires_at" not in generic_payload,
                ),
                (
                    "generic registration must remain a public client",
                    generic_payload.get("token_endpoint_auth_method") == "none",
                ),
            ],
        )

        mixed = self.client.post(
            f"{self.base_url}/register",
            json={"redirect_uris": [COWORK_REDIRECT_URI, GENERIC_REDIRECT_URI]},
        )
        self.expect(
            "register-mixed-cowork-callback-rejected",
            mixed,
            400,
            error="invalid_redirect_uri",
        )

        if not ok:
            return None
        self.registered = RegisteredClient(
            client_id=client_id, client_secret=client_secret
        )
        return self.registered

    def check_authorize_reservation(
        self, registered: Optional[RegisteredClient]
    ) -> None:
        """The Cowork callback is available only to confidential-DCR client IDs."""
        _, challenge = pkce_pair()
        if registered:
            configured = self.client.get(
                f"{self.base_url}/authorize",
                params=self.authorize_params(
                    registered.client_id, COWORK_REDIRECT_URI, challenge
                ),
            )
            self.expect(
                "authorize-cowork-redirect-confidential-client",
                configured,
                200,
                require=[
                    (
                        "confidential client must reach the consent form",
                        "api_key" in configured.text,
                    )
                ],
            )
        else:
            self.skip(
                "authorize-cowork-redirect-confidential-client",
                "no confidential client was registered",
            )

        other = self.client.get(
            f"{self.base_url}/authorize",
            params=self.authorize_params(
                LEGACY_PUBLIC_CLIENT_ID,
                COWORK_REDIRECT_URI,
                challenge,
            ),
        )
        self.expect(
            "authorize-cowork-redirect-public-client-rejected",
            other,
            400,
            error="invalid_request",
        )

    def check_code_exchange(self, registered: Optional[RegisteredClient]) -> None:
        if not registered:
            self.skip("token-*", "no confidential client was registered")
            return

        code, verifier = self.mint_code(
            "authorize-mints-code-for-cowork-redirect",
            registered.client_id,
            COWORK_REDIRECT_URI,
        )
        if not code:
            self.skip("token-*", "no authorization code was minted")
            return

        post = self.code_exchange(
            code,
            verifier,
            COWORK_REDIRECT_URI,
            extra={
                "client_id": registered.client_id,
                "client_secret": registered.client_secret,
            },
        )
        payload = _json(post)
        self.expect(
            "token-code-client-secret-post",
            post,
            200,
            require=[
                (
                    "response must carry an access_token",
                    bool(payload.get("access_token")),
                ),
                (
                    "response must carry a refresh_token",
                    bool(payload.get("refresh_token")),
                ),
            ],
        )

        code, verifier = self.mint_code(
            "authorize-mints-code-for-basic-exchange",
            registered.client_id,
            COWORK_REDIRECT_URI,
        )
        if code:
            basic = self.code_exchange(
                code,
                verifier,
                COWORK_REDIRECT_URI,
                extra={"client_id": registered.client_id},
                basic=(registered.client_id, registered.client_secret),
            )
            self.expect(
                "token-code-client-secret-basic",
                basic,
                200,
                require=[
                    (
                        "response must carry an access_token",
                        bool(_json(basic).get("access_token")),
                    )
                ],
            )

        code, verifier = self.mint_code(
            "authorize-mints-code-for-bad-secret",
            registered.client_id,
            COWORK_REDIRECT_URI,
        )
        if code:
            wrong_post = self.code_exchange(
                code,
                verifier,
                COWORK_REDIRECT_URI,
                extra={
                    "client_id": registered.client_id,
                    "client_secret": "wrong-secret",
                },
            )
            self.expect(
                "token-code-wrong-secret-post-rejected",
                wrong_post,
                401,
                error="invalid_client",
            )

            wrong_basic = self.code_exchange(
                code,
                verifier,
                COWORK_REDIRECT_URI,
                basic=(registered.client_id, "wrong-secret"),
            )
            self.expect(
                "token-code-wrong-secret-basic-rejected",
                wrong_basic,
                401,
                error="invalid_client",
            )

            missing = self.code_exchange(
                code,
                verifier,
                COWORK_REDIRECT_URI,
                extra={"client_id": registered.client_id},
            )
            self.expect(
                "token-code-missing-secret-rejected",
                missing,
                401,
                error="invalid_client",
            )

    def confidential_refresh_token(
        self, registered: Optional[RegisteredClient]
    ) -> Optional[str]:
        """Mint a refresh token for the confidential DCR client."""
        if not registered:
            return None
        code, verifier = self.mint_code(
            "authorize-mints-code-for-refresh",
            registered.client_id,
            COWORK_REDIRECT_URI,
        )
        if not code:
            return None
        response = self.code_exchange(
            code,
            verifier,
            COWORK_REDIRECT_URI,
            extra={
                "client_id": registered.client_id,
                "client_secret": registered.client_secret,
            },
        )
        return _json(response).get("refresh_token")

    def check_refresh(self, registered: RegisteredClient, refresh_token: str) -> None:
        post = self.token(
            {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": registered.client_id,
                "client_secret": registered.client_secret,
            }
        )
        rotated = _json(post).get("refresh_token")
        self.expect(
            "refresh-client-secret-post",
            post,
            200,
            require=[
                (
                    "response must carry an access_token",
                    bool(_json(post).get("access_token")),
                ),
                ("response must rotate the refresh_token", bool(rotated)),
            ],
        )

        basic = self.token(
            {"grant_type": "refresh_token", "refresh_token": refresh_token},
            basic=(registered.client_id, registered.client_secret),
        )
        self.expect(
            "refresh-client-secret-basic",
            basic,
            200,
            require=[
                (
                    "response must carry an access_token",
                    bool(_json(basic).get("access_token")),
                )
            ],
        )

        anonymous = self.token(
            {"grant_type": "refresh_token", "refresh_token": refresh_token}
        )
        self.expect(
            "refresh-without-client-auth-rejected",
            anonymous,
            401,
            error="invalid_client",
        )

        wrong = self.token(
            {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": registered.client_id,
                "client_secret": "wrong-secret",
            }
        )
        self.expect("refresh-wrong-secret-rejected", wrong, 401, error="invalid_client")

        if rotated:
            shed = self.token({"grant_type": "refresh_token", "refresh_token": rotated})
            self.expect(
                "refresh-rotation-keeps-client-binding",
                shed,
                401,
                error="invalid_client",
            )

    def check_public_client(self) -> None:
        """Legacy public clients (non-confidential ID class) keep working with no client auth."""
        code, verifier = self.mint_code(
            "authorize-mints-code-for-public-client",
            LEGACY_PUBLIC_CLIENT_ID,
            PUBLIC_REDIRECT_URI,
        )
        if not code:
            return
        exchange = self.code_exchange(
            code,
            verifier,
            PUBLIC_REDIRECT_URI,
            extra={"client_id": LEGACY_PUBLIC_CLIENT_ID},
        )
        refresh_token = _json(exchange).get("refresh_token")
        self.expect(
            "token-code-public-client-no-secret",
            exchange,
            200,
            require=[("response must carry a refresh_token", bool(refresh_token))],
        )
        if refresh_token:
            response = self.token(
                {"grant_type": "refresh_token", "refresh_token": refresh_token}
            )
            self.expect(
                "refresh-public-client-no-client-auth",
                response,
                200,
                require=[
                    (
                        "response must carry an access_token",
                        bool(_json(response).get("access_token")),
                    )
                ],
            )


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@contextlib.contextmanager
def local_server(jwt_secret: str, enc_key: str) -> Iterator[str]:
    """Run ``mcp/local_http_server.py`` with throwaway OAuth configuration."""
    port = free_port()
    env = {k: v for k, v in os.environ.items() if k not in SCRUBBED_ENV}
    env["JWT_SECRET_KEY"] = jwt_secret
    env["AV_APIKEY_ENC_KEY"] = enc_key
    base_url = f"http://127.0.0.1:{port}"
    with tempfile.TemporaryFile("w+") as log:
        process = subprocess.Popen(
            [sys.executable, str(LOCAL_SERVER), "--port", str(port)],
            cwd=MCP_ROOT,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        try:
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    log.seek(0)
                    raise SystemExit(f"local server exited early:\n{log.read()}")
                try:
                    httpx.get(
                        f"{base_url}/.well-known/oauth-authorization-server", timeout=1
                    )
                    break
                except httpx.HTTPError:
                    time.sleep(0.2)
            else:
                raise SystemExit(f"local server did not become ready on port {port}")
            yield base_url
        finally:
            process.terminate()
            with contextlib.suppress(subprocess.TimeoutExpired):
                process.wait(timeout=10)


def run_checks(verifier: Verifier) -> None:
    """Run the full confidential-DCR lifecycle plus legacy public-client regression."""
    verifier.check_metadata()
    registered = verifier.check_registration()
    verifier.check_authorize_reservation(registered)
    verifier.check_code_exchange(registered)
    refresh_token = verifier.confidential_refresh_token(registered)
    if registered and refresh_token:
        verifier.check_refresh(registered, refresh_token)
    else:
        verifier.skip("refresh-*", "no confidential refresh token was minted")
    verifier.check_public_client()


def report(results: list[Result]) -> int:
    width = max((len(result.name) for result in results), default=0)
    for result in results:
        print(f"{result.status:<4}  {result.name:<{width}}  {result.detail}")
    counts = {
        status: sum(1 for r in results if r.status == status)
        for status in ("PASS", "FAIL", "SKIP")
    }
    print(
        f"\n{counts['PASS']} passed, {counts['FAIL']} failed, {counts['SKIP']} skipped"
    )
    return 1 if counts["FAIL"] else 0


def verify_remote(base_url: str, api_key: str) -> list[Result]:
    with httpx.Client(timeout=30, follow_redirects=False) as client:
        verifier = Verifier(client, base_url, api_key, local=False)
        run_checks(verifier)
        return verifier.results


def verify_local(api_key: str) -> list[Result]:
    """Register via DCR against a managed local server and run every check."""
    jwt_secret = secrets.token_urlsafe(32)
    enc_key = Fernet.generate_key().decode()

    with httpx.Client(timeout=30, follow_redirects=False) as client:
        with local_server(jwt_secret, enc_key) as base_url:
            # derive_client_secret reads JWT_SECRET_KEY from the environment of this process
            # (not the child server). Point it at the same throwaway secret the server uses.
            os.environ["JWT_SECRET_KEY"] = jwt_secret
            os.environ["AV_APIKEY_ENC_KEY"] = enc_key
            verifier = Verifier(client, base_url, api_key, local=True)
            run_checks(verifier)
            return verifier.results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify the Cowork confidential DCR OAuth lifecycle over HTTP"
    )
    parser.add_argument(
        "--base-url",
        help="Deployment to verify; omit to start a local server with throwaway credentials",
    )
    parser.add_argument(
        "--api-key",
        default="verification-only-apikey",
        help="Alpha Vantage API key submitted on the consent form",
    )
    args = parser.parse_args()

    if args.base_url:
        results = verify_remote(args.base_url, args.api_key)
    else:
        results = verify_local(args.api_key)

    raise SystemExit(report(results))


if __name__ == "__main__":
    main()
