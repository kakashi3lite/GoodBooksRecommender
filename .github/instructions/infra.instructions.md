---
applyTo: "terraform/**"
---
- Format with `terraform fmt` before commit.
- Validate with `terraform validate`.
- Keep secrets in variables and `.tfvars`, never commit real credentials.
