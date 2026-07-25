from datetime import datetime, timedelta, timezone
from io import BytesIO

import compactor
from compactor import compact_hour


class FakeS3Client:
    def __init__(self, objects=None):
        self.objects = dict(objects or {})
        self.put_calls = []
        self.delete_calls = []

    def get_paginator(self, operation_name):
        assert operation_name == "list_objects_v2"
        return self

    def paginate(self, Bucket, Prefix):
        keys = sorted(k for k in self.objects if k.startswith(Prefix))
        yield {"Contents": [{"Key": key} for key in keys]}

    def get_object(self, Bucket, Key):
        return {"Body": BytesIO(self.objects[Key])}

    def put_object(self, Bucket, Key, Body, ContentType):
        self.put_calls.append(Key)
        self.objects[Key] = Body

    def delete_object(self, Bucket, Key):
        self.delete_calls.append(Key)
        del self.objects[Key]


def test_single_object_hour_is_still_compacted():
    prefix = "jsonl/2026/06/16/15/"
    client = FakeS3Client({f"{prefix}20260616_150117_555943.jsonl": b'{"a": 1}\n'})

    compacted = compact_hour("bucket", prefix, client)

    assert compacted == 1
    assert client.put_calls == [f"{prefix}compacted.jsonl"]
    assert client.objects == {f"{prefix}compacted.jsonl": b'{"a": 1}\n'.strip()}


def test_already_compacted_hour_is_a_noop():
    prefix = "jsonl/2026/06/16/14/"
    client = FakeS3Client({f"{prefix}compacted.jsonl": b'{"a": 1}\n'})

    compacted = compact_hour("bucket", prefix, client)

    assert compacted == 0
    assert client.put_calls == []
    assert client.delete_calls == []


def test_empty_prefix_is_a_noop():
    client = FakeS3Client()

    compacted = compact_hour("bucket", "jsonl/2026/06/16/16/", client)

    assert compacted == 0
    assert client.put_calls == []
    assert client.delete_calls == []


def test_multiple_objects_are_merged_and_originals_deleted():
    prefix = "jsonl/2026/06/16/17/"
    client = FakeS3Client(
        {
            f"{prefix}a.jsonl": b'{"a": 1}',
            f"{prefix}b.jsonl": b'{"a": 2}',
        }
    )

    compacted = compact_hour("bucket", prefix, client)

    assert compacted == 2
    assert set(client.delete_calls) == {f"{prefix}a.jsonl", f"{prefix}b.jsonl"}
    assert client.objects == {f"{prefix}compacted.jsonl": b'{"a": 1}\n{"a": 2}'}


def test_lookback_sweep_self_heals_a_missed_hour(monkeypatch):
    stale_target = datetime.now(timezone.utc) - timedelta(hours=5)
    stale_prefix = (
        f"jsonl/{stale_target.year}/{stale_target.month:02d}/"
        f"{stale_target.day:02d}/{stale_target.hour:02d}/"
    )
    client = FakeS3Client(
        {
            f"{stale_prefix}a.jsonl": b'{"a": 1}',
            f"{stale_prefix}b.jsonl": b'{"a": 2}',
        }
    )

    monkeypatch.setattr(compactor, "s3_client", client)
    monkeypatch.setenv("S3_BUCKET", "bucket")

    result = compactor.lambda_handler({}, None)

    assert result["hours"][stale_prefix] == 2
    assert client.objects == {f"{stale_prefix}compacted.jsonl": b'{"a": 1}\n{"a": 2}'}
