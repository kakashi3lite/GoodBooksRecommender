# 🗄️ Documentation Archive

**Everything in this folder is historical.** These are progress reports,
completion announcements, and design drafts written while the project was being
built — most of them by AI agents, most of them optimistic.

They are kept because they record *why* decisions were made and what was tried.
They are **not** a description of the current system, and they should never be
used as an implementation reference.

## What to read instead

| Question | Canonical document |
|---|---|
| What is deployed right now? | [`../LIVE_ARCHITECTURE_RUNBOOK.md`](../LIVE_ARCHITECTURE_RUNBOOK.md) |
| What actually works? | [`../PROJECT_STATUS.md`](../PROJECT_STATUS.md) |
| How do I start contributing? | [`../../HANDOFF.md`](../../HANDOFF.md) |
| How do I build/deploy/test? | [`../../AGENTS.md`](../../AGENTS.md), [`../../CONTRIBUTING.md`](../../CONTRIBUTING.md) |
| Where is the code? | [`../../CODEMAP.md`](../../CODEMAP.md) |
| How do customer accounts work? | [`../ACCOUNTS.md`](../ACCOUNTS.md) |
| Where is the API surface? | [`../API_REFERENCE.md`](../API_REFERENCE.md), [`../../API_CATALOG.md`](../../API_CATALOG.md) |
| Every document, organised | [`../../DOCUMENTATION_INDEX.md`](../../DOCUMENTATION_INDEX.md) |

## Rules

1. **Do not add new files here.** New work goes in `docs/` or is recorded in
   [`../../CHANGELOG.md`](../../CHANGELOG.md).
2. **Do not cite these files** as evidence of current behaviour.
3. If a document here becomes relevant again, move it back to `docs/`, update
   it against the code, and add it to the documentation index.
4. Relative links were rewritten when these files moved (e.g. `docs/X.md` →
   `../X.md`). Run `npm run docs:check` after touching any of them.

## What was archived (2026-11-17)

Progress reports and plans for work that is finished, superseded, or was never
deployed — including the aspirational `PROJECT_STATUS.md` that the current,
honest [`../PROJECT_STATUS.md`](../PROJECT_STATUS.md) replaced, the Kindle and
"futuristic dashboard" showcases, the false-news-detection roadmap, the
git-commit narratives, the "mission complete" reports, and the old ML-era `ROADMAP.md`.
