## Summary

<!-- What does this PR change? Link the feature spec: specs/NNNN-slug.md -->

## Spec-driven checklist

- [ ] Feature spec exists (`specs/NNNN-slug.md`) and has status `approved`
- [ ] Tests written before implementation (TDD), failing first
- [ ] API responses covered by synthetic fixtures (no live API in unit tests)
- [ ] Live tests stay behind the `live` marker
- [ ] `ruff check .`, `ruff format --check .`, `mypy`, `pytest -m "not live"` pass
- [ ] Skeptic review completed: verdict `APPROVED` (or `NITS` only)
- [ ] No secrets committed (credentials, password hashes); placeholders only
- [ ] Logs never contain credentials or the password hash

## Commit style

Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `chore:`, `refactor:`).
