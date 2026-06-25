import contextlib

import av_api.client as client


def test_default_path_uses_per_request_client(monkeypatch):
    """With AV_HTTP_POOL unset (default/Lambda), each call builds a fresh,
    real httpx.Client context manager (closed per request)."""
    monkeypatch.delenv("AV_HTTP_POOL", raising=False)
    monkeypatch.setattr(client, "_shared_http_client", None)

    created = []

    class FakeClient:
        def __init__(self, *args, **kwargs):
            created.append(self)

    monkeypatch.setattr(client.httpx, "Client", FakeClient)

    first = client._get_request_client()
    second = client._get_request_client()

    # Real per-request clients: two distinct instances, shared client untouched.
    assert isinstance(first, FakeClient)
    assert isinstance(second, FakeClient)
    assert first is not second
    assert client._shared_http_client is None


def test_pool_path_reuses_shared_client(monkeypatch):
    """With AV_HTTP_POOL='1' (docker), calls reuse one lazily built shared
    client, wrapped in nullcontext so it is yielded but never closed."""
    monkeypatch.setenv("AV_HTTP_POOL", "1")
    monkeypatch.setattr(client, "_shared_http_client", None)

    created = []

    class FakeClient:
        def __init__(self, *args, **kwargs):
            created.append(self)

    monkeypatch.setattr(client.httpx, "Client", FakeClient)

    first = client._get_request_client()
    second = client._get_request_client()

    # nullcontext yields the same shared instance both times; only one built.
    assert isinstance(first, contextlib.nullcontext)
    assert isinstance(second, contextlib.nullcontext)
    with first as a, second as b:
        assert a is b
        assert a is client._shared_http_client
    assert len(created) == 1
