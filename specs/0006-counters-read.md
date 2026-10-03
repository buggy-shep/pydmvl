# 0006 — Counters (read)

- **Status:** implemented
- **Scope:** `pydmvl` parsing of meter counters and readings from the account
  snapshot

## Summary

The account snapshot includes the account's meters and their readings. This
spec defines a read-only counter model. It was deferred from the 0.1.0 scope and
is implemented as of 0.3.0.

## Motivation

Meter readings are useful for Home Assistant, but the 0.1.0 scope is limited to
authentication, documents, and payments. This spec adds the read-only model
without committing to writing readings.

## Requirements

- R1 (MUST) Parse `counters[]` into `Counter(name, serial, service, checked,
  readings)`.
  - `name` — display name (`sch_name`); `serial` — identifier (`sch_id`); no
    real value is committed to the repository.
  - `service` — `st_name`; `checked` — verification date (`sch_date_c`).
- R2 (MUST) Parse `values[]` into `CounterReading(period_start, period_end,
  reading, volume, kind, is_actual)` from `sp_date_b`, `sp_date_e`, `sp_pok`,
  `sp_val`, `sp_type`, `isActual`.
- R3 (MUST) `Counter.current_reading` returns the reading whose `is_actual` is
  true, or `None`.
- R4 (MUST) Reading is strictly read-only; submitting or deleting a reading
  (`addcounter`/`delcounter`) is out of scope.
- R5 (SHOULD) Missing reading values degrade to zero or `None` rather than
  failing the snapshot, consistent with spec 0002 R7.

## Design

- Parsing is pure and lives in `models.py`; `Session` exposes `counters:
  tuple[Counter, ...]`.
- `AccountInfo.counters` stays the array length (spec 0007 R2); it is derived
  from the parsed counters, so the two never disagree.

## API

```python
@dataclass(frozen=True)
class CounterReading:
    period_start: str | None
    period_end: str | None
    reading: Decimal
    volume: Decimal
    kind: str | None
    is_actual: bool


@dataclass(frozen=True)
class Counter:
    name: str
    serial: str
    service: str | None
    checked: str | None
    readings: tuple[CounterReading, ...]

    @property
    def current_reading(self) -> CounterReading | None: ...
```

## Test plan

- Fixture-driven parsing of `counters[]`; `current_reading` selects the actual
  reading and returns `None` when none is marked.
- Missing values degrade to zero or `None`.

## Acceptance criteria

- Unit tests green; the model is read-only.

## Out of scope

- Submitting and deleting readings (writing actions).
- Reading-window validation rules.

## Status

`implemented` (2026-10-03) — `Session.counters: tuple[Counter, ...]` with
`Counter`/`CounterReading` exported from the package; `Counter.current_reading`
selects the actual reading; missing values degrade to zero/`None`; version
0.3.0.
