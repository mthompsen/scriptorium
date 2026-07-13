# ADR-0001: Record architecture decisions

- **Status:** Accepted
- **Date:** 2026-07-13

## Context

Scriptorium is built milestone by milestone against `docs/DESIGN.md` by an AI
coding agent under human review. The design document intentionally leaves some
downstream decisions open (Section 0, Section 18) and requires that any choice
made where the spec is silent be recorded rather than silently invented. A
reviewer cloning this repository must be able to reconstruct not just what was
built but why each non-obvious choice was made.

## Decision

We will record every architecturally significant decision as an Architecture
Decision Record in `docs/adr/`, numbered sequentially, using the format in
`0000-template.md` (status, context, decision, consequences). An ADR is written
the moment the decision is made, in the same change set that implements it.
Decisions that warrant an ADR include: choices between real alternatives the
spec leaves open (e.g. which migration tool owns the Postgres schema,
per-tenant vs shared OpenSearch indexes), any major-version deviation from the
technology baseline in DESIGN.md Section 5, and any scope interpretation made
under the Section 3 design goals.

## Consequences

The decision log lives in the repository and travels with every clone; review
and interviews can trace rationale directly. Writing ADRs adds a small,
constant documentation cost per decision, which we accept. Superseded
decisions are never deleted — their status is updated to point at the ADR
that replaces them, preserving history.
