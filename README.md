# multi-tenant-trip-agent

A minimal, dependency-free skeleton of a **multi-tenant conversational trip-planning agent** — the architecture I use for production LLM agents, reduced to code you can read in ten minutes. Clean-room, synthetic data, no LLM key required.

## Design
- **Typed state machine** (`state.py`) — `collecting → confirming → searching → done`; illegal transitions and searching with missing slots raise.
- **Provenance rule** — an inferred value never overwrites something the user actually said.
- **Consensus intent extraction** (`intent.py`) — two extractors run on every turn; slots they disagree on are *dropped and re-asked*, never guessed. Plug an LLM extractor in as the second one.
- **Shared tool registry, tenant-scoped execution** (`tools.py`) — the registry is shared *code*, not shared *state*. Every call carries a `TenantContext`; tools can only read that tenant's data, and per-tenant allow-lists decide which tools exist for a brand.
- **Per-tenant config** — brand-specific behaviour (e.g. markup) lives in config, not forks of the code.

## Run
```bash
pip install -r requirements.txt
pytest -q
```
Tests cover the full conversation flow, cross-tenant isolation, consensus conflicts, illegal transitions and the provenance rule.

MIT licensed.
