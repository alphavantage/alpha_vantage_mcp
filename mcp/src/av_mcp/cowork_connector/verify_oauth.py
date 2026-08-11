"""Verify the Cowork confidential OAuth client end to end over real HTTP.

Layer-1 self-test for the Microsoft 365 static OAuth contract: it drives ``/authorize``,
``/token``, and ``/register`` with an actual HTTP client instead of calling the handlers
in-process, so routing, headers, and redirects are exercised the way Microsoft's token
store will exercise them.

With no ``--base-url`` the script starts ``mcp/local_http_server.py`` on a free port with
throwaway credentials, runs every check, and tears the server down. Given a ``--base-url``
it runs the same checks against that deployment (production, once the Microsoft client is
configured), which is the run that also proves CloudFront forwards ``Authorization`` to
``/token``. The client-rotation checks need control of the server's own configuration and
are reported as skipped in that mode.

    uv run --project mcp python -m av_mcp.cowork_connector.verify_oauth
    uv run --project mcp python -m av_mcp.cowork_connector.verify_oauth \
        --base-url https://mcp.alphavantage.co --client-id <id> --client-secret <secret>
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

from av_mcp.oauth import MICROSOFT_REDIRECT_URI

MCP_ROOT = Path(__file__).resolve().parents[3]
LOCAL_SERVER = MCP_ROOT / "local_http_server.py"

# Loopback redirect used for the public-client (DCR) regression checks.
PUBLIC_REDIRECT_URI = "http://127.0.0.1:8765/callback"

# Environment the managed local server must not inherit: real OAuth keys, real Microsoft
# client credentials, and anything that would make it talk to AWS.
SCRUBBED_ENV = (
    "JWT_SECRET_KEY",
    "AV_APIKEY_ENC_KEY",
    "MICROSOFT_OAUTH_CLIENT_ID",
    "MICROSOFT_OAUTH_CLIENT_SECRET",
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
    """Runs the confidential-client checks against one base URL."""

    def __init__(
        self,
        client: httpx.Client,
        base_url: str,
        client_id: str,
        client_secret: str,
        api_key: str,
    ) -> None:
        self.client = client
        self.base_url = base_url.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret
        self.api_key = api_key
        self.results: list[Result] = []

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
        methods = _json(response).get("token_endpoint_auth_methods_supported", [])
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
            ],
        )

    def check_registration(self) -> Optional[str]:
        """DCR must still refuse the Teams callback and stay public-client only."""
        teams = self.client.post(
            f"{self.base_url}/register",
            json={"redirect_uris": [MICROSOFT_REDIRECT_URI]},
        )
        self.expect(
            "register-rejects-teams-redirect", teams, 400, error="invalid_redirect_uri"
        )

        public = self.client.post(
            f"{self.base_url}/register", json={"redirect_uris": [PUBLIC_REDIRECT_URI]}
        )
        payload = _json(public)
        self.expect(
            "register-issues-public-client-only",
            public,
            201,
            require=[
                (
                    "registration must return a client_id",
                    bool(payload.get("client_id")),
                ),
                (
                    "registration must not issue a client_secret",
                    "client_secret" not in payload,
                ),
                (
                    "registered client must be token_endpoint_auth_method=none",
                    payload.get("token_endpoint_auth_method") == "none",
                ),
            ],
        )
        return payload.get("client_id")

    def check_authorize_reservation(self, public_client_id: Optional[str]) -> None:
        """The Teams callback is available to the configured client and nobody else."""
        _, challenge = pkce_pair()
        configured = self.client.get(
            f"{self.base_url}/authorize",
            params=self.authorize_params(
                self.client_id, MICROSOFT_REDIRECT_URI, challenge
            ),
        )
        self.expect(
            "authorize-teams-redirect-configured-client",
            configured,
            200,
            require=[
                (
                    "configured client must reach the consent form",
                    "api_key" in configured.text,
                )
            ],
        )

        other = self.client.get(
            f"{self.base_url}/authorize",
            params=self.authorize_params(
                public_client_id or "mcp-client-unregistered",
                MICROSOFT_REDIRECT_URI,
                challenge,
            ),
        )
        self.expect(
            "authorize-teams-redirect-public-client-rejected",
            other,
            400,
            error="invalid_request",
        )

    def check_code_exchange(self) -> None:
        code, verifier = self.mint_code(
            "authorize-mints-code-for-teams-redirect",
            self.client_id,
            MICROSOFT_REDIRECT_URI,
        )
        if not code:
            self.skip("token-*", "no authorization code was minted")
            return

        post = self.code_exchange(
            code,
            verifier,
            MICROSOFT_REDIRECT_URI,
            extra={"client_id": self.client_id, "client_secret": self.client_secret},
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
            self.client_id,
            MICROSOFT_REDIRECT_URI,
        )
        if code:
            basic = self.code_exchange(
                code,
                verifier,
                MICROSOFT_REDIRECT_URI,
                extra={"client_id": self.client_id},
                basic=(self.client_id, self.client_secret),
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
            self.client_id,
            MICROSOFT_REDIRECT_URI,
        )
        if code:
            wrong_post = self.code_exchange(
                code,
                verifier,
                MICROSOFT_REDIRECT_URI,
                extra={"client_id": self.client_id, "client_secret": "wrong-secret"},
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
                MICROSOFT_REDIRECT_URI,
                basic=(self.client_id, "wrong-secret"),
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
                MICROSOFT_REDIRECT_URI,
                extra={"client_id": self.client_id},
            )
            self.expect(
                "token-code-missing-secret-rejected",
                missing,
                401,
                error="invalid_client",
            )

    def confidential_refresh_token(self) -> Optional[str]:
        """Mint a refresh token for the configured confidential client."""
        code, verifier = self.mint_code(
            "authorize-mints-code-for-refresh", self.client_id, MICROSOFT_REDIRECT_URI
        )
        if not code:
            return None
        response = self.code_exchange(
            code,
            verifier,
            MICROSOFT_REDIRECT_URI,
            extra={"client_id": self.client_id, "client_secret": self.client_secret},
        )
        return _json(response).get("refresh_token")

    def check_refresh(self, refresh_token: str) -> None:
        post = self.token(
            {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
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
            basic=(self.client_id, self.client_secret),
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
                "client_id": self.client_id,
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

    def check_public_client(self, public_client_id: Optional[str]) -> None:
        """Public (DCR) clients keep working with no client authentication."""
        client_id = public_client_id or "mcp-client-verification"
        code, verifier = self.mint_code(
            "authorize-mints-code-for-public-client", client_id, PUBLIC_REDIRECT_URI
        )
        if not code:
            return
        exchange = self.code_exchange(
            code, verifier, PUBLIC_REDIRECT_URI, extra={"client_id": client_id}
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

    def check_rotated_config(self, name: str, refresh_token: str) -> None:
        """An old confidential refresh token must not survive a config change as public."""
        anonymous = self.token(
            {"grant_type": "refresh_token", "refresh_token": refresh_token}
        )
        self.expect(
            f"{name}-anonymous-rejected", anonymous, 401, error="invalid_client"
        )

    def check_rotated_credentials(
        self, refresh_token: str, client_id: str, client_secret: str
    ) -> None:
        response = self.token(
            {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": client_id,
                "client_secret": client_secret,
            }
        )
        self.expect(
            "rotated-client-id-new-credentials-rejected",
            response,
            401,
            error="invalid_client",
        )


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@contextlib.contextmanager
def local_server(
    client_id: str, client_secret: str, jwt_secret: str, enc_key: str
) -> Iterator[str]:
    """Run ``mcp/local_http_server.py`` with throwaway OAuth configuration."""
    port = free_port()
    env = {k: v for k, v in os.environ.items() if k not in SCRUBBED_ENV}
    env["JWT_SECRET_KEY"] = jwt_secret
    env["AV_APIKEY_ENC_KEY"] = enc_key
    if client_id:
        env["MICROSOFT_OAUTH_CLIENT_ID"] = client_id
        env["MICROSOFT_OAUTH_CLIENT_SECRET"] = client_secret

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


def run_shared_checks(verifier: Verifier) -> Optional[str]:
    """Every check that only needs HTTP access; returns a confidential refresh token."""
    verifier.check_metadata()
    public_client_id = verifier.check_registration()
    verifier.check_authorize_reservation(public_client_id)
    verifier.check_code_exchange()
    refresh_token = verifier.confidential_refresh_token()
    if refresh_token:
        verifier.check_refresh(refresh_token)
    else:
        verifier.skip("refresh-*", "no confidential refresh token was minted")
    verifier.check_public_client(public_client_id)
    return refresh_token


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


def verify_remote(
    base_url: str, client_id: str, client_secret: str, api_key: str
) -> list[Result]:
    with httpx.Client(timeout=30, follow_redirects=False) as client:
        verifier = Verifier(client, base_url, client_id, client_secret, api_key)
        run_shared_checks(verifier)
        verifier.skip(
            "cleared-client-config-anonymous-rejected",
            "requires server-side configuration control (local mode only)",
        )
        verifier.skip(
            "rotated-client-id-anonymous-rejected",
            "requires server-side configuration control (local mode only)",
        )
        verifier.skip(
            "rotated-client-id-new-credentials-rejected",
            "requires server-side configuration control (local mode only)",
        )
        return verifier.results


def verify_local(api_key: str) -> list[Result]:
    """Run every check, including the ones that need the server's configuration changed."""
    client_id = "verify-microsoft-client"
    client_secret = secrets.token_urlsafe(24)
    # Shared across restarts so tokens minted before a rotation stay decodable.
    jwt_secret = secrets.token_urlsafe(32)
    enc_key = Fernet.generate_key().decode()

    with httpx.Client(timeout=30, follow_redirects=False) as client:
        with local_server(client_id, client_secret, jwt_secret, enc_key) as base_url:
            verifier = Verifier(client, base_url, client_id, client_secret, api_key)
            refresh_token = run_shared_checks(verifier)

        if not refresh_token:
            verifier.skip(
                "cleared-client-config-anonymous-rejected",
                "no confidential refresh token",
            )
            verifier.skip("rotated-client-id-*", "no confidential refresh token")
            return verifier.results

        # Configuration removed: the token must become unredeemable, not public.
        with local_server("", "", jwt_secret, enc_key) as base_url:
            verifier.base_url = base_url
            verifier.check_rotated_config("cleared-client-config", refresh_token)

        # Client ID rotated: neither anonymous nor the new client may redeem it.
        rotated_id = "verify-microsoft-client-rotated"
        rotated_secret = secrets.token_urlsafe(24)
        with local_server(rotated_id, rotated_secret, jwt_secret, enc_key) as base_url:
            verifier.base_url = base_url
            verifier.check_rotated_config("rotated-client-id", refresh_token)
            verifier.check_rotated_credentials(
                refresh_token, rotated_id, rotated_secret
            )

        return verifier.results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify the Cowork confidential OAuth client over HTTP"
    )
    parser.add_argument(
        "--base-url",
        help="Deployment to verify; omit to start a local server with throwaway credentials",
    )
    parser.add_argument(
        "--client-id", help="Configured confidential client ID (--base-url mode)"
    )
    parser.add_argument(
        "--client-secret",
        help="Configured confidential client secret (--base-url mode)",
    )
    parser.add_argument(
        "--api-key",
        default="verification-only-apikey",
        help="Alpha Vantage API key submitted on the consent form",
    )
    args = parser.parse_args()

    if args.base_url:
        if not args.client_id or not args.client_secret:
            raise SystemExit("--base-url requires --client-id and --client-secret")
        results = verify_remote(
            args.base_url, args.client_id, args.client_secret, args.api_key
        )
    else:
        results = verify_local(args.api_key)

    raise SystemExit(report(results))


if __name__ == "__main__":
    main()
