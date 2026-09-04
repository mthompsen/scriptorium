# ADR-0003: Upload path (synchronous ingest to Mongo) and JWT transport

- **Status:** Accepted
- **Date:** 2026-07-13

## Context

The walking skeleton needs a document upload that stores a file and creates a
`documents` row, but the queue (SQS / local) and the transactional outbox
belong to the real ingestion pipeline that comes later, and the local compose
stack has no object store. That leaves two things to settle now: where raw
bytes live in the meantime, and how the demo frontend carries the JWT.
Section 4 already routes BFF → ingestion and makes MongoDB the home of raw
document content.

## Decision

**Upload path.** For now the BFF accepts the multipart upload, creates the
`documents` row (status `uploaded`), and synchronously calls the ingestion
service's internal `POST /ingest`; ingestion stores the raw bytes in MongoDB
(`raw_documents` collection) and advances the row to `stored`. This follows
the Section 4 arrows exactly (BFF→ING, ING→MG, ING→PG), so the queue + outbox
can replace the synchronous call later without moving any data ownership.

**JWT transport.** The BFF issues the JWT both in the JSON response and as an
`HttpOnly` cookie. The browser flow relies on the cookie (no token readable
by page script; `localhost:3000` and `localhost:3001` are same-site, so the
cookie travels with `credentials: 'include'` under CORS); non-browser clients
use the `Authorization: Bearer` header. The auth guard accepts either.

## Consequences

Uploads are synchronous and bounded by request size limits; large-corpus
throughput is deferred to the event-driven path, which supersedes the direct
call (and with it this ADR's upload section). Storing raw bytes in Mongo keeps
laptop mode dependency-free; S3 becomes the raw source in cloud mode, with
Mongo retaining extracted content per Section 8.2. Cookie + bearer dual transport adds a small amount of guard code
but keeps the demo secure-by-default in browsers and scriptable from CLIs.
