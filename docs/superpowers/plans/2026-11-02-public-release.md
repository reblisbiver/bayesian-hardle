# Bayesian Hardle Public Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prepare Bayesian Hardle as a clean, truthful, reproducible portfolio repository without publishing it yet.

**Architecture:** Preserve the solver and experiment code on the latest completed technical branch. Change only repository presentation, release metadata, internal-control artifacts, and vocabulary distribution strategy; verify behavior with the existing test suite.

**Tech Stack:** Python 3.9+, unittest, NumPy, setuptools

**Spec:** `docs/superpowers/specs/2026-11-02-public-release.md`

## Global Constraints
- Solver semantics and existing benchmark claims must not change.
- All existing tests must remain green.
- No secrets, personal paths, or internal project-control language in public-facing content.
- Do not push or publish in this plan.

## Review Focus
- Vocabulary preparation works from a clean checkout without silently changing hashes.
- README commands match actual CLI/scripts and current branch behavior.
- Removing project-control does not break imports/tests/scripts.
- Package metadata and LICENSE agree.
- Secret/path scan includes git-tracked public branch content.

---

### Task 1: Release-surface cleanup
**Files:** Modify `README.md`, `pyproject.toml`, `.gitignore`; create `LICENSE`; remove `project-control/` from public-prep branch.
- [ ] Replace internal executor/supervisor/ISSUE framing with a portfolio/research README describing problem, architecture, algorithms, verification, experiments, limitations, and provenance.
- [ ] Add a real MIT LICENSE and align package author/project metadata.
- [ ] Remove internal project-control artifacts from this branch and ensure no public docs link to them.
- [ ] Run the full unittest suite and require PASS.
- [ ] Commit.

### Task 2: Vocabulary redistribution boundary
**Files:** Modify `data/wordlists/`, `scripts/`, README/tests as needed.
- [ ] Verify upstream licensing/provenance for both vocabulary sources.
- [ ] If redistribution is not clearly licensed, stop vendoring those lists and provide a deterministic preparation script pinned to the recorded source revisions/hashes.
- [ ] Add a test that validates prepared counts and hashes/expected additions.
- [ ] Run targeted test then full suite and require PASS.
- [ ] Commit.

### Task 3: Public artifacts and final audit
**Files:** `docs/figures/`, README, release docs as needed.
- [ ] Select useful architecture figures and exclude redundant source/render artifacts where they add noise.
- [ ] Add one architecture image to README if it renders cleanly.
- [ ] Run tests, package/build smoke checks, tracked secret/path scan, and repository status audit.
- [ ] Record any unresolved publication blockers without pushing.
- [ ] Commit only if all changes are internally consistent.
