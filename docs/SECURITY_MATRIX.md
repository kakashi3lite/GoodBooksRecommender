
# Security Controls Matrix

## OWASP Top 10 vs Security Tools Coverage

| OWASP Category | SAST Tools | DAST Tools | Container | IaC | Manual Testing |
|----------------|------------|------------|-----------|-----|----------------|
| **A01: Broken Access Control** | ✅ Semgrep<br/>✅ CodeQL | ✅ OWASP ZAP<br/>✅ Custom Tests | ⚪ Limited | ⚪ Limited | ✅ Auth Testing |
| **A02: Cryptographic Failures** | ✅ Bandit<br/>✅ Semgrep | ✅ SSL Labs<br/>✅ Custom Tests | ✅ Trivy | ✅ tfsec | ✅ Crypto Review |
| **A03: Injection** | ✅ Bandit<br/>✅ CodeQL | ✅ OWASP ZAP<br/>✅ SQLMap | ⚪ Limited | ⚪ Limited | ✅ Injection Tests |
| **A04: Insecure Design** | ⚪ Limited | ⚪ Limited | ⚪ Limited | ⚪ Limited | ✅ Architecture Review |
| **A05: Security Misconfiguration** | ✅ Semgrep | ✅ OWASP ZAP | ✅ Trivy<br/>✅ Hadolint | ✅ tfsec<br/>✅ Checkov | ✅ Config Review |
| **A06: Vulnerable Components** | ✅ Safety<br/>✅ Snyk | ⚪ Limited | ✅ Trivy | ✅ Checkov | ✅ SCA Review |
| **A07: ID & Auth Failures** | ✅ Semgrep<br/>✅ CodeQL | ✅ OWASP ZAP<br/>✅ Custom Tests | ⚪ Limited | ⚪ Limited | ✅ Auth Testing |
| **A08: Data Integrity Failures** | ✅ CodeQL | ⚪ Limited | ✅ Supply Chain | ✅ IaC Integrity | ✅ Pipeline Security |
| **A09: Logging Failures** | ✅ Semgrep | ✅ Log Analysis | ✅ Container Logs | ✅ Logging Config | ✅ Log Review |
| **A10: SSRF** | ✅ Semgrep<br/>✅ CodeQL | ✅ OWASP ZAP | ⚪ Limited | ⚪ Limited | ✅ SSRF Testing |

**Legend:**
- ✅ = Full Coverage
- ⚪ = Partial Coverage
- ❌ = No Coverage

## Security Tool Configuration Matrix

| Tool | Type | Language | Severity | Config File | Pipeline Stage |
|------|------|----------|----------|-------------|----------------|
| **Bandit** | SAST | Python | HIGH/MEDIUM | bandit.yml | SAST Scan |
| **Safety** | SCA | Python | ALL | safety.json | SAST Scan |
| **Semgrep** | SAST | Multi | ERROR/WARNING | semgrep.yml | SAST Scan |
| **CodeQL** | SAST | Multi | HIGH/MEDIUM | codeql.yml | SAST Scan |
| **ESLint** | SAST | JavaScript | ERROR/WARNING | eslintrc.json | Code Quality |
| **Trivy** | Container | All | HIGH/CRITICAL | trivy.yaml | Container Scan |
| **OWASP ZAP** | DAST | Web Apps | HIGH/MEDIUM | zap-config.yml | DAST Scan |
| **tfsec** | IaC | Terraform | HIGH/MEDIUM | tfsec.yml | Infrastructure |
| **Checkov** | IaC | Multi | HIGH/MEDIUM | checkov.yml | Infrastructure |

## Compliance Mapping

### GDPR Article Compliance

| GDPR Article | Requirement | Technical Control | Validation Method |
|--------------|-------------|-------------------|-------------------|
| **Art. 25** | Data Protection by Design | Privacy-by-design architecture | Architecture review |
| **Art. 32** | Security of Processing | Encryption, access controls | Security testing |
| **Art. 33** | Breach Notification | Incident response procedures | IR testing |
| **Art. 35** | Data Protection Impact Assessment | DPIA documentation | Compliance audit |
| **Art. 17** | Right to Erasure | Data deletion endpoints | Functional testing |
| **Art. 20** | Data Portability | Data export functionality | API testing |

### Security Framework Alignment

| Framework | Standard | Implementation | Assessment |
|-----------|----------|----------------|------------|
| **NIST CSF** | Cybersecurity Framework | Complete security controls | Annual assessment |
| **ISO 27001** | Information Security | ISMS implementation | Certification audit |
| **SOC 2 Type II** | Service Organization Controls | Operational controls | Third-party audit |
| **PCI DSS** | Payment Card Industry | If handling payments | Quarterly scan |
| **HIPAA** | Healthcare Privacy | If handling health data | Risk assessment |
