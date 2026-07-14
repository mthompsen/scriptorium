"""S3 -> Lambda -> SQS ingestion trigger (ARCHITECTURE.md Sections 9.1, 14.5).

An object landing in the raw-uploads bucket fires this Lambda, which enqueues
one ingestion job per object onto the SQS queue the ingestion worker
consumes. Keeping the Lambda thin (translate event -> job message) means the
heavy pipeline stays in the ingestion service; the Lambda is just the
event-driven front door that replaces the M1 synchronous call (ADR-0003).
"""

import json
import os
import urllib.parse

import boto3

sqs = boto3.client("sqs")
QUEUE_URL = os.environ["INGESTION_QUEUE_URL"]


def handler(event, context):
    records = event.get("Records", [])
    enqueued = 0
    for record in records:
        s3 = record.get("s3", {})
        bucket = s3.get("bucket", {}).get("name")
        # S3 keys arrive URL-encoded in event notifications.
        key = urllib.parse.unquote_plus(s3.get("object", {}).get("key", ""))
        if not (bucket and key):
            continue
        # Key convention: <tenant_id>/<document_id>/<filename>
        parts = key.split("/", 2)
        job = {
            "bucket": bucket,
            "key": key,
            "tenant_id": parts[0] if len(parts) > 0 else None,
            "document_id": parts[1] if len(parts) > 1 else None,
            "size": s3.get("object", {}).get("size"),
        }
        sqs.send_message(QueueUrl=QUEUE_URL, MessageBody=json.dumps(job))
        enqueued += 1
    return {"enqueued": enqueued}
