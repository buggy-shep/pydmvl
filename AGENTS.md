# AGENTS.md — pydmvl

Working agreement for humans and AI agents contributing to this repository.

## 1. Role in the group

This repository is part of a group of projects that build a self-hosted
control stack for a residential utility account ("Domovladelets" / homeowner):

| Repository | Role | Visibility | Language |
|---|---|---|---|
| `pydmvl` (this repo) | Python client for a homeowner account API | public | English |
| `dmvl-ha-integration` | Home Assistant custom integration, consumes `pydmvl` from PyPI | public | English |

`pydmvl` is the producer: it encapsulates authentication and the account data
models. The Home Assistant integration depends on `pydmvl` as an external
package, does not duplicate client logic, and performs no authentication of its
own. Group identity: code name `dmvl`, package/import `pydmvl`, Home Assistant
domain `dmvl`.

## 2. Language

All repository text is English: code, comments, docstrings, documentation,
commit messages, and review notes. The only exception is runtime translation
of user-facing strings (e.g. `translations/ru.json`) in the consumer
integration, not in this library.

## 3. Stack and commands

- Python >= 3.11, hatchling, src-layout (`src/pydmvl/`), plain top-level
  package (no PEP 420 namespace).
- Runtime dependency: `httpx>=0.27`; dev tools: pytest, pytest-asyncio, ruff,
  mypy (strict for `src/`).

```bash
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/mypy
.venv/bin/pytest -m "not live"
```

Live tests (real account, real credentials) carry the `live` marker and are run
manually only: `.venv/bin/pytest -m live`. Credentials come from the
environment: `DMVL_USERNAME`, `DMVL_PASSWORD`.

## 4. Spec-driven development (SDD)

- Every feature starts with a spec in `specs/NNNN-slug.md` (zero-padded number,
  short slug). Status lifecycle: `draft → approved → implemented →
  superseded`.
- Implementation without an `approved` spec is forbidden. Specs marked
  "implementation pending research" must not be implemented until they move to
  `approved`.
- Spec template: Summary / Motivation / Requirements (MUST/SHOULD) / Design /
  API / Test plan / Acceptance criteria / Out of scope / Status.
- Moving a spec from `draft` to `approved` is a reviewable change (PR or a
  recorded decision in the conversation).

## 5. Test-driven development (TDD)

- Tests are written first and must fail before the implementation exists.
- API responses are covered by synthetic fixtures via an httpx mock transport;
  unit tests never touch the real API.
- A merge requires a fully green run of all gate commands (§3).

## 6. Git process

- Default branch: `master`. Direct commits to `master` are forbidden (the
  initial scaffold import is the only exception).
- One feature = one branch `feat/NNNN-slug` containing the spec, the tests, and
  the implementation together.
- Commit messages follow Conventional Commits (`feat:`, `fix:`, `docs:`,
  `test:`, `chore:`, `refactor:`).
- Merge into `master` only after the review gate (§7), squash-merge, then delete
  the feature branch.

## 7. Review gate (mandatory)

A feature branch may merge into `master` only when both hold:

1. A full local run is green (§3/§5).
2. A skeptic review returns no `BLOCKING` findings. Invoke the skeptic agent
   (Task tool, definition in `.kilo/agent/skeptic.md`) with a prompt such as:

   > Review branch `feat/NNNN-slug` against its spec `specs/NNNN-slug.md`
   > (diff base: `master`). Follow the checklist in `.kilo/agent/skeptic.md`
   > and answer in the verdict format (`BLOCKING: ...` / `NITS: ...` /
   > `APPROVED`).

`BLOCKING` findings forbid the merge; fix and re-review.

## 8. Secrets and safety

- Account credentials and account data are confidential: never include them in
  this public repository — in code, docs, examples, fixtures, or commit
  history. This covers logins, passwords, tokens (including the password hash
  sent by the API), full names, addresses, personal account numbers, object and
  payment identifiers, and receipt links. Use synthetic placeholders
  (`<account>`, `<password>`); real values live only in environment variables
  or gitignored `*.local.json` files.
- Authentication material is sent as request query parameters (an observed
  property of the API). Never log request URLs, credentials, or the password
  hash. The library installs a redaction filter on the `httpx` logger so
  dependency-emitted request-URL records have `login` and `hash` replaced; do
  not remove it.

## 9. Publication policy (public repository)

- Do not copy text or material from non-public sources into this repo.
- Public documentation is an English description of observed API behavior.
  Cite only this repository's own specs; do not name non-public or third-party
  sources, and do not state or claim how the API was determined.
- Keep the disclaimers in place (unofficial, not affiliated with the service
  operator, own account only).

## 10. Release runbook (new versions)

Ship a release only from a green `master`:

1. Bump the version in one change: `pyproject.toml` `[project].version` and
   `src/pydmvl/__init__.py` `__version__`. A test enforces that they match; no
   other source or test file pins the version. SemVer; `0.x` while the API is
   unstable.
2. Feature branch `feat/NNNN-slug` (spec + tests + code **and the version
   bump**), gate (§3), skeptic (§7), squash-merge into `master`.
3. Push `master`.
4. Create a GitHub Release with tag `vX.Y.Z` equal to the version. Publishing
   the release triggers `publish.yml`, which builds and uploads to PyPI via
   Trusted Publishing. A plain tag push does **not** publish.
5. Run the `testpypi.yml` dry run for every packaging/metadata change, and
   always before the first production release.
6. Never reuse a published version; if a release is wrong, bump the patch
   version and repeat. Verify with `pip install pydmvl==X.Y.Z`.
7. Keep the runtime dependency floor compatible with Home Assistant's pinned
   `httpx`.

## 11. References

- Specs: `specs/` (0001 authentication is the first deliverable).
- Public API surface catalogue: `specs/0005-api-surface.md`.
- Versioning: SemVer, `0.x` while the API is unstable.
