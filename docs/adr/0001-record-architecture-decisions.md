# ADR-0001: Record architecture decisions

- **Status:** Accepted
- **Date:** 2026-07-13

## Context

Scriptorium is built in phases against `docs/ARCHITECTURE.md`. The design
document deliberately leaves some downstream decisions open (Section 0,
Section 17), and those choices are worth writing down: six months later the
code shows what was built but not which alternatives were weighed, or why the
one that shipped won.

## Decision

We will record every architecturally significant decision as an Architecture
Decision Record in `docs/adr/`, numbered sequentially, using the format in
`0000-template.md` (status, context, decision, consequences). An ADR is written
the moment the decision is made, in the same change set that implements it.
Decisions that warrant an ADR include: choices between real alternatives the
design document leaves open (e.g. which migration tool owns the Postgres
schema, per-tenant vs shared OpenSearch indexes), any major-version deviation from the
technology baseline in ARCHITECTURE.md Section 5, and any scope interpretation made
under the Section 3 design goals.

## Consequences

The decision log lives in the repository and travels with every clone, so the
rationale is one directory away from the code it explains. Writing ADRs adds a small,
constant documentation cost per decision, which we accept. Superseded
decisions are never deleted — their status is updated to point at the ADR
that replaces them, preserving history.
