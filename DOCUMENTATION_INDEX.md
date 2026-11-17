# 📚 Documentation Index

Single map of the repository's documentation. **Verified 2026-11-17** against the
live deployment (`https://books.dalecabra.com`).

> Rule: if a document disagrees with the code or the live API, the document is
> wrong — fix it in the same change. Historical reports live in
> [`docs/archive/`](docs/archive/README.md) and are never authoritative.

---

## ⭐ Start here

| Audience | Document | Why |
|---|---|---|
| Humans joining the project | [**HANDOFF.md**](HANDOFF.md) | Current state, architecture in one diagram, first tasks, landmines |
| AI agents / contributors | [**AGENTS.md**](AGENTS.md) | Golden rules, commands, change recipes, testing expectations |
| Anyone touching production | [**docs/LIVE_ARCHITECTURE_RUNBOOK.md**](docs/LIVE_ARCHITECTURE_RUNBOOK.md) | Deploy runbook, endpoint tables, verification logs |
| Anyone asking "does it work?" | [**docs/PROJECT_STATUS.md**](docs/PROJECT_STATUS.md) | Honest status: live vs partial vs legacy |
| Customer accounts / data | [**docs/ACCOUNTS.md**](docs/ACCOUNTS.md) | D1 contract, security model, upgrade context, dead ends |

---

## 🎯 By task

| I want to… | Read |
|---|---|
| Run the app locally | [HANDOFF.md § In 5 minutes](HANDOFF.md), [docs/DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md) |
| Deploy | [docs/LIVE_ARCHITECTURE_RUNBOOK.md](docs/LIVE_ARCHITECTURE_RUNBOOK.md), [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) |
| Understand the API | [API_CATALOG.md](API_CATALOG.md) (live), [docs/ACCOUNTS.md](docs/ACCOUNTS.md), [docs/API_REFERENCE.md](docs/API_REFERENCE.md) (legacy FastAPI) |
| Change accounts or the D1 schema | [docs/ACCOUNTS.md](docs/ACCOUNTS.md), [AGENTS.md § Recipes](AGENTS.md) |
| Understand the data layer | [docs/DATA_LAYER.md](docs/DATA_LAYER.md) |
| Change the recommender | [docs/DATA_LAYER.md](docs/DATA_LAYER.md), [ARCHITECTURE.md § 4](ARCHITECTURE.md) |
| Find a file | [CODEMAP.md](CODEMAP.md) |
| Write tests | [docs/TESTING_GUIDE.md](docs/TESTING_GUIDE.md), [TEST_MATRIX.md](TEST_MATRIX.md) |
| Ship a change safely | [AGENTS.md § Recipes](AGENTS.md), [CONTRIBUTING.md](CONTRIBUTING.md) |
| Understand security controls | [SECURITY.md](SECURITY.md), [docs/SECURITY_GUIDE.md](docs/SECURITY_GUIDE.md) |
| See what changed | [CHANGELOG.md](CHANGELOG.md) |
| Find the old "mission complete" reports / roadmap | [docs/archive/](docs/archive/README.md) |

---

## 🟢 Living documents (authoritative)

| Document | Covers | Verified |
|---|---|---|
| [HANDOFF.md](HANDOFF.md) | Human onboarding, current state, landmines | 2026-11-17 |
| [AGENTS.md](AGENTS.md) | Agent handbook: rules, commands, recipes | 2026-11-17 |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Deployed topology, state model, security boundaries | 2026-11-17 |
| [CODEMAP.md](CODEMAP.md) | What every directory is and whether it deploys | 2026-11-17 |
| [docs/LIVE_ARCHITECTURE_RUNBOOK.md](docs/LIVE_ARCHITECTURE_RUNBOOK.md) | Operations, endpoints, incidents, verification logs | 2026-11-17 |
| [docs/ACCOUNTS.md](docs/ACCOUNTS.md) | Accounts on D1: API, schema, client, upgrade context | 2026-11-17 |
| [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md) | Honest status by dimension | 2026-11-17 |
| [docs/DATA_LAYER.md](docs/DATA_LAYER.md) | Data flow, recommender rationale, catalog sync | 2026-11-17 |
| [API_CATALOG.md](API_CATALOG.md) | Short endpoint catalogue | 2026-08 |
| [CHANGELOG.md](CHANGELOG.md) | Release notes (Keep a Changelog) | per release |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution workflow | 2026-08 |
| [SECURITY.md](SECURITY.md) | Security policy + controls | 2026-08 |
| [PROJECT_BRIEF.md](PROJECT_BRIEF.md) | One-page product brief | 2026-08 |
| [DATA_MODEL.md](DATA_MODEL.md) | Book/user data shapes | 2026-08 |
| [TEST_MATRIX.md](TEST_MATRIX.md) | Test coverage by area | 2026-08 |
| [BENCHMARKS.md](BENCHMARKS.md) | Performance targets | 2026-08 |
| [REPOSITORY_GOVERNANCE.md](REPOSITORY_GOVERNANCE.md) | Repo conventions | 2026-08 |

## 🟡 Guides for the optional/legacy stack

These describe the Python/ML infrastructure that is **not** in the deploy path.
Read them only if you are reviving that stack.

[docs/API_REFERENCE.md](docs/API_REFERENCE.md) ·
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) ·
[docs/TECHNICAL_ARCHITECTURE.md](docs/TECHNICAL_ARCHITECTURE.md) ·
[docs/PIPELINE_ARCHITECTURE.md](docs/PIPELINE_ARCHITECTURE.md) ·
[docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) ·
[docs/DEPLOYMENT_PLAN.md](docs/DEPLOYMENT_PLAN.md) ·
[docs/DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md) ·
[docs/TESTING_GUIDE.md](docs/TESTING_GUIDE.md) ·
[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) ·
[docs/SECURITY_GUIDE.md](docs/SECURITY_GUIDE.md) ·
[docs/SECURITY_MATRIX.md](docs/SECURITY_MATRIX.md) ·
[docs/SECURITY_PIPELINE_CHECKLIST.md](docs/SECURITY_PIPELINE_CHECKLIST.md) ·
[docs/LOAD_BALANCER_GUIDE.md](docs/LOAD_BALANCER_GUIDE.md) ·
[docs/REDIS_CLUSTER_GUIDE.md](docs/REDIS_CLUSTER_GUIDE.md) ·
[docs/ML_PIPELINE_ENHANCEMENTS.md](docs/ML_PIPELINE_ENHANCEMENTS.md) ·
[docs/CICD_PIPELINE_GUIDE.md](docs/CICD_PIPELINE_GUIDE.md) ·
[docs/TYPESCRIPT_ARCHITECTURE.md](docs/TYPESCRIPT_ARCHITECTURE.md) ·
[docs/IMPLEMENTATION_GUIDE.md](docs/IMPLEMENTATION_GUIDE.md) ·
[docs/USER_GUIDE.md](docs/USER_GUIDE.md) ·
[docs/USER_GROWTH.md](docs/USER_GROWTH.md) ·
[docs/SOCIAL_LAUNCH.md](docs/SOCIAL_LAUNCH.md) ·
[docs/UX_PREMIUM_UPGRADE.md](docs/UX_PREMIUM_UPGRADE.md) ·
[docs/NEWSLETTER_ARCHITECTURE.md](docs/NEWSLETTER_ARCHITECTURE.md) ·
[docs/NEWS_EXPANSION_ARCHITECTURE.md](docs/NEWS_EXPANSION_ARCHITECTURE.md) ·
[docs/ENHANCED_FEATURES_GUIDE.md](docs/ENHANCED_FEATURES_GUIDE.md) ·
[docs/KINDLE_DASHBOARD_GUIDE.md](docs/KINDLE_DASHBOARD_GUIDE.md) ·
[docs/AI_NEWS_ENGINE_ARCHITECTURE.md](docs/AI_NEWS_ENGINE_ARCHITECTURE.md) ·
[docs/AI_NEWS_ENGINE_IMPLEMENTATION.md](docs/AI_NEWS_ENGINE_IMPLEMENTATION.md) ·
[docs/AI_NEWS_ENGINE_WIREFRAMES.md](docs/AI_NEWS_ENGINE_WIREFRAMES.md) ·
[docs/FALSE_NEWS_DETECTION_SYSTEM.md](docs/FALSE_NEWS_DETECTION_SYSTEM.md) ·
[docs/FALSE_NEWS_DETECTION_PLAN.md](docs/FALSE_NEWS_DETECTION_PLAN.md) ·
[docs/FALSE_NEWS_DETECTION_TASKS.md](docs/FALSE_NEWS_DETECTION_TASKS.md) ·
[docs/FALSE_NEWS_DETECTION_QUICKSTART.md](docs/FALSE_NEWS_DETECTION_QUICKSTART.md) ·
[docs/FALSE_NEWS_DETECTION_INTEGRATION_EXAMPLE.md](docs/FALSE_NEWS_DETECTION_INTEGRATION_EXAMPLE.md)

## 🗄️ Historical

[docs/archive/](docs/archive/README.md) — progress reports, "mission complete"
announcements, wireframes and plans that are finished, superseded, or were never
deployed. **Never cite them as current behaviour.**

---

## 🧹 Documentation rules

1. **One canonical file per topic.** If two documents describe the same thing,
   merge them and leave a pointer.
2. **No new root-level reports.** Progress goes in [CHANGELOG.md](CHANGELOG.md);
   living docs go in `docs/`; history goes to `docs/archive/`.
3. **Update this index** whenever a document is added, moved, or retired.
4. **Links must resolve** — run `npm run docs:check` (CI-friendly, exits 1 on a
   broken relative link).
5. **State the verification date** in any document that describes production.
