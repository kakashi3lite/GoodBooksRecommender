# Security Notes

## ASVS L2 Checklist
| Control | Status | Notes |
|---------|--------|-------|
| Authentication requires JWT with RBAC | Pass | See `src/auth/security.py` |
| Refresh tokens stored server-side | Pass | Redis blacklisting in `src/auth/security.py` |
| Session timeout and revocation | Pass | Tokens carry `exp` claims |
| Passwords hashed with bcrypt | Pass | `src/auth/security.py` lines 34-35 |
| Input validation on API models | Pass | Pydantic models in `src/api/main.py` |
| Output encoding for templates | N/A | No server-side rendering |
| Error handling avoids leaks | Pass | Central handler in `src/api/main.py` |
| Security headers set | Gap | No explicit `SecurityMiddleware` |
| HTTPS enforcement | Gap | Handled by reverse proxy not shown |
| Logging with request IDs | Pass | `src/core/enhanced_logging.py` |
| Dependency scanning | Gap | No automated vulnerability scan in CI |
| CSRF protection | N/A | Pure API with JWT |
| Deserialization security | Pass | Only Pydantic parsing |
| SSRF protections for external calls | Gap | External requests not validated |
| Secrets management | Gap | `.env.example` recommends manual entry |
| Rate limiting | Gap | No rate limit middleware |

## Secret Handling
- Do not commit real credentials; use `.env.example` as template.
- Rotate JWT signing key and database passwords regularly.

## Dependency Risks
- Review `requirements.txt` and `package.json` for outdated packages.
