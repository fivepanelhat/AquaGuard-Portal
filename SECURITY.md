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
| Dependabot | Weekly dependency PRs - prioritise `security` / high CVEs |
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

## Fleet security principles

- **No silent exfiltration** of personal or tenant operational data
- Prefer **local-first** processing; third-party AI only with explicit operator configuration and UI/docs disclosure
- Report vulnerabilities via GitHub Security Advisories or the maintainer contact on the org profile
- High-stakes production changes require human approval (HITL)

## Data sales and third parties

- **We do not sell personal information or customer operational data to third parties.**
- Optional AI or cloud services run only when configured by the operator; processing must be disclosed (in-product and/or docs).
- Prefer local-first paths so third-party transfer is unnecessary by default.

## NZ Privacy Act and Te Mana Raraunga

- Design in accordance with the **Privacy Act 2020**.
- Operate in accordance with **Te Mana Raraunga** principles for Māori data sovereignty interests.
- Align AI features with **NZ AI safety** / responsible AI expectations (HITL, transparency, no silent training on private content).

