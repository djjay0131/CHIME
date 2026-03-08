# Architectural Decisions

## ADR-001: Mirror the Proposal Project's Documentation Layout

Status: accepted

Context:
The user wanted a `construction/` and `memory-bank/` setup similar to `construction-ai-proposal`.

Decision:
Create the same top-level workflow concepts, but adapt the content for code comprehension and repository stewardship instead of proposal polishing.

Consequences:

- documentation work now has a predictable home
- future sessions have a continuity layer
- the structure is familiar across the user's projects

## ADR-002: Center Initial Code Documentation on One Figure Script

Status: accepted

Context:
Documenting the full artifact at once would be broad and slow.

Decision:
Use `exp/fig_03a.py` as the representative experiment walkthrough for the first pass.

Consequences:

- the docs become useful immediately
- the explanation covers the main orchestration pattern
- more figure scripts can be added incrementally
