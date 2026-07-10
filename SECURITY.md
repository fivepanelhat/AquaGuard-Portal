# Security Policy for AquaGuard-Portal

## Supported Versions
Only the `main` branch is actively supported with security updates.

## Reporting a Vulnerability
Coastal Alpine Tech Limited takes the security of our Sovereign Edge networks seriously. 
If you discover a vulnerability in the AquaGuard-Portal, please DO NOT open a public issue. 
Instead, report it directly to the Chief Architect. All critical hardware-layer and edge-network 
vulnerabilities will be addressed within 48 hours.

## Security Notifications

| Channel | Response |
| ------- | -------- |
| Dependabot | Weekly dependency PRs — prioritise `security` / high CVEs |
| Code scanning / SecOps / Red team | Fix-forward on `main`; never weaken actuator guards |
| Coastal-Alpine-Core advisories | Bump core pin; re-run portal tests |
| Org threat register | See coastal-alpine-stack `SECURITY.md` / `SECURITY_POSTURE_REPORT.md` |

## Active threat patches (2026-07)

| ID / finding | Mitigation |
| ------------ | ---------- |
| GHSA-f4xh-w4cj-qxq8 langsmith | Floor `>=0.8.18` via stack/Weaver pins |
| GHSA-4xgf-cpjx-pc3j pydantic-settings | Floor `>=2.14.2` |
| GHSA-f4j7-r4q5-qw2c chromadb | Local-only vector DB; no public bind |
| Prompt injection | Core `SecurityGuard` on all LLM prompts |
| GITHUB_TOKEN | CI workflows use `permissions: contents: read` |

## Quality gates

- Portal CI + SecOps (Bandit/Gitleaks) + red-team schedules.
- Actuator / irrigation / crop actions must remain fail-closed on guard failure.
