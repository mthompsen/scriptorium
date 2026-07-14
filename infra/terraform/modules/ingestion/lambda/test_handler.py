"""Unit test for the ingestion-trigger Lambda. SQS is mocked with moto; no
cloud, no LocalStack needed. Run: pip install moto boto3 pytest && pytest."""

import importlib
import json
import os

import boto3
import pytest
from moto import mock_aws


@pytest.fixture
def queue_and_handler(monkeypatch):
    with mock_aws():
        sqs = boto3.client("sqs", region_name="us-east-1")
        queue_url = sqs.create_queue(QueueName="test-ingestion")["QueueUrl"]
        monkeypatch.setenv("INGESTION_QUEUE_URL", queue_url)
        monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
        import handler

        importlib.reload(handler)  # rebind module-level sqs client + QUEUE_URL
        yield sqs, queue_url, handler


def _s3_event(key: str, size: int = 42) -> dict:
    return {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": "raw-uploads"},
                    "object": {"key": key, "size": size},
                }
            }
        ]
    }


def test_object_created_enqueues_a_job(queue_and_handler):
    sqs, queue_url, handler = queue_and_handler

    result = handler.handler(
        _s3_event("11111111-1111-4111-8111-111111111111/doc-1/handbook.md"), None
    )

    assert result["enqueued"] == 1
    messages = sqs.receive_message(QueueUrl=queue_url).get("Messages", [])
    body = json.loads(messages[0]["Body"])
    assert body["tenant_id"] == "11111111-1111-4111-8111-111111111111"
    assert body["document_id"] == "doc-1"
    assert body["key"].endswith("handbook.md")


def test_url_encoded_keys_are_decoded(queue_and_handler):
    sqs, queue_url, handler = queue_and_handler

    handler.handler(_s3_event("tenant/doc/my+file%20name.pdf"), None)

    body = json.loads(sqs.receive_message(QueueUrl=queue_url)["Messages"][0]["Body"])
    assert body["key"] == "tenant/doc/my file name.pdf"


def test_records_without_bucket_or_key_are_skipped(queue_and_handler):
    _, _, handler = queue_and_handler

    result = handler.handler({"Records": [{"s3": {"object": {}}}]}, None)

    assert result["enqueued"] == 0


def test_multiple_records_enqueue_each(queue_and_handler):
    sqs, queue_url, handler = queue_and_handler
    event = {"Records": _s3_event("t/d/a.md")["Records"] + _s3_event("t/d/b.md")["Records"]}

    result = handler.handler(event, None)

    assert result["enqueued"] == 2
    assert int(
        sqs.get_queue_attributes(
            QueueUrl=queue_url, AttributeNames=["ApproximateNumberOfMessages"]
        )["Attributes"]["ApproximateNumberOfMessages"]
    ) == 2
