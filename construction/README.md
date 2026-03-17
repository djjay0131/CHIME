# Construction Folder - CHIME Codebase Stewardship

## Purpose

This folder tracks active understanding and documentation work for the CHIME repository. Use it to organize code-reading tasks, documentation goals, and short sprints that improve maintainability.

## Project Context

**Project:** CHIME  
**Goal:** Understand, maintain, and document the SOSP'24 artifact codebase and experiment pipeline  
**Status:** CloudLab reproduction in progress — pre-CloudLab prep done; experiment params patched for 10-node (9 CN); Day 1 automation (runbook + day1-dry-run.sh) ready

## Structure

### `design/`
Design notes and code-reading guides for the repository.

### `requirements/`
Documentation quality targets and acceptance checks.

### `sprints/`
Short execution plans for documentation and onboarding work.

### `spec_builder.md`
Lightweight prompt template for turning vague documentation requests into a concrete write-up plan.

## Workflow

1. Start in `memory-bank/activeContext.md` to see the current focus.
2. Use `design/codebase-guide.md` when reading or explaining the code.
3. Check `requirements/documentation-acceptance.md` before expanding docs.
4. Record the current status in `sprints/` and `memory-bank/progress.md`.

## Initial Focus

- Explain the top-level architecture and build knobs.
- Map the experiment scripts to the C++ binaries they drive.
- Document `exp/fig_03a.py` as a representative experiment flow.
