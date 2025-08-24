# Test Matrix

| Area | Framework | Location | Coverage | Gaps |
|------|-----------|----------|----------|------|
| Frontend components | Vitest | `tests/frontend` | ~60% (estimate) | Missing tests for complex animations and 3D scenes |
| Backend API | pytest | `tests/backend`, `test_api.py` | ~70% | Limited error-path and auth failure tests |
| News engine | pytest | `tests/news` | moderate | No load tests for expansion endpoints |
| E2E dashboard | (none) | N/A | 0% | No Cypress tests configured |
| Terraform modules | terraform validate | `terraform/` | manual | No automated plan test |

## Recommended Additions
- Smoke test hitting `/health` and `/news/health`
- Integration test for cache behavior in `/recommendations`
- Frontend test for store persistence
- Security test for auth role restrictions
- Terraform unit tests with `terraform validate` in CI
