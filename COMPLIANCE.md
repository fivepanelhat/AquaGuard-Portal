# AquaGuard Compliance & Regulatory Mapping Guide

This document details how the **AquaGuard Portal** telemetry, automated reasoning, and audit logging support compliance with New Zealand's primary environmental regulations, including recent legislative updates as of June 2026.

---

## Legislative Mapping

| NZ Instrument | Compliance Requirement | AquaGuard Integration |
|---|---|---|
| **Resource Management Act 1991 (RMA)** | Environmental resource consents (issued by Regional Councils) require continuous, documented parameter monitoring for aquaculture and effluent discharges. *Note: Under transition to the incoming Natural Environment Bill framework.* | Exports structured, timestamped CSV/JSON audit trails mapping sensor readings and control actions to specific consent numbers. |
| **Fisheries Act 1996** | Requires land-based and marine fish farmers to maintain logs of stocking, water parameters, and license compliance under MPI regulations. | Integrates Recirculating Aquaculture System (RAS) sensor records directly with compliance exporters. |
| **Biosecurity Act 1993** | Operators must monitor and report biosecurity issues (e.g. marine pests, disease outbreaks). | Local Gemma 4 vision prompts flag behavior or turbidity issues, storing flagged frames for inspection. |
| **Privacy Act 2020** | Sovereign data constraints: preventing leakage of private operational or cultural metadata to foreign cloud endpoints. | 100% offline edge execution on local hardware guarantees zero cloud data transfers. |

---

## National Environmental Standards (NES)

### 1. NES for Freshwater (NES-F 2020)
Resource Management (National Environmental Standards for Freshwater) Regulations 2020 apply to agricultural operations, especially dairy effluent. 
> [!NOTE]
> While targeted amendments were introduced in December 2025 (effective January 2026) to streamline consenting for quarrying and mining, the core agricultural effluent rules and the Te Mana o te Wai hierarchy remain fully intact and operational.

*   **Dairy Effluent Monitoring:** Effluent ponds must be managed to avoid overflow. Rules require permitted activity tracking 365 days a year.
*   **AquaGuard Support:**
    *   Continuous pH, DO, temperature, and nitrate logs under the `aquaguard/sensors` MQTT topics.
    *   Automated pump and valve shutoffs to prevent runoff during threshold breaches, logged as evidence for DairyNZ Effluent Warrant of Fitness (WoF) audits.

### 2. NES for Marine Aquaculture (NES-MA)
Regulates marine farms (mussel, oyster, salmon, finfish) within coastal marine areas.
> [!IMPORTANT]
> The **NES-MA Amendments came into effect on 4 June 2026**. These amendments specifically streamline the re-consenting process and clarify conditions for existing marine farms, reducing consenting barriers.

*   **EMOP Compliance:** Environmental Monitoring and Operations Plans (EMOPs) are mandatory for marine consent conditions.
*   **AquaGuard Support:**
    *   Tracks dissolved oxygen and temperature profiles around marine cages.
    *   Enables configurable compliance exports designed to map directly to the newly streamlined 2026 re-consenting reporting templates.

---

## Resource Management (Freshwater Farm Plans) Regulations 2023

Freshwater Farm Plans require documented actions and timelines, verified by independent audits.
> [!IMPORTANT]
> While the nationwide rollout was paused in late 2024 (with the exception of the active **Southland Region**), the **August 2025 Resource Management (Consenting and Other System Changes) Amendment Act** established a pathway for closer integration with industry assurance programmes. Approved industry organisations can now appoint certifiers and auditors alongside regional councils.

*   **AquaGuard Support:**
    *   AquaGuard's local audit logs generate structured CSV/JSON telemetry records of sensor thresholds breached and automated pump shutdowns, serving as verifiable, auditor-ready evidence of plan implementation.

---

## RMA Reform Transition (2025/2026)

In December 2025, the Government released draft legislation to completely replace the Resource Management Act 1991 (RMA) with two new statutes: the **Natural Environment Bill** and the **Planning Bill**. Public consultation on these bills closed in February 2026.
*   While the RMA 1991 remains the operational law during this transition, **AquaGuard is architected to adapt seamlessly to the incoming Natural Environment Bill framework** by decoupling its local database schemas from regional-specific schemas, ensuring long-term operational viability.

---

## Regional Council Permitted Activity Rules

AquaGuard exports audit logs designed to align with compliance reports of major NZ regional councils:

*   **Waikato Regional Council:** Rule **3.5.5.1** strictly governs the permitted activity conditions for discharging farm animal effluent to land. This rule mandates that no effluent enters surface water or causes surface ponding. AquaGuard's continuous moisture monitoring and pump relays provide auditable proof of compliance with this rule.
*   **Horizons Regional Council:** Requires strict nitrogen limit documentation for Taranaki and Manawatū catchments.
*   **Environment Canterbury (ECan):** Demands groundwater contamination prevention logging.
*   **Otago Regional Council (ORC) & Environment Southland:** Enforce strict discharge standards; AquaGuard logs provide evidence of operational compliance.

---

## Tāngata Whenua & Te Mana o te Wai

Under the **National Policy Statement for Freshwater Management 2020 (NPS-FM)**, *Te Mana o te Wai* establishes a hierarchy of obligations, prioritizing the health and well-being of water bodies.

### Culturally Grounded Kaitiakitanga
*   Many resource consent conditions require impact assessments on tāngata whenua values. AquaGuard's offline architecture ensures that monitoring data remains on-site under the custody of the land custodians (supporting *Te Mana Raraunga* or Māori Data Sovereignty principles).
*   Allows iwi and hapū to access local data tables directly, ensuring local environmental guardianship without external dependency.

---

## Verified Sources

| Regulation / Topic | Source Authority | Details |
| --- | --- | --- |
| **NES-MA 2026 Amendments** | Ministry for Primary Things (MPI) / MfE | Confirms the NES-MA amendments taking effect on **4 June 2026** to streamline marine farm consenting. |
| **Freshwater Farm Plans Update** | AsureQuality / Ministry for the Environment | Confirms the system pause (except Southland) and the **August 2025** legislative changes integrating industry assurance programmes. |
| **RMA Reform (2025/2026)** | NZ Government / Beef + Lamb New Zealand | Details the **December 2025** draft bills (Natural Environment Bill and Planning Bill) to replace the RMA. |
| **Waikato Rule 3.5.5.1** | Waikato Regional Council | Outlines the exact permitted activity conditions for farm dairy effluent discharge to land (no ponding or runoff). |
| **NES-F / NPS-FM Amendments** | NZ Government (Beehive publications) | Details the **December 2025** gazetted amendments to national direction instruments, effective January 2026. |

---

## Reference Appendix: Official Regulatory Sources

Below are the official legislative and council publications detailing the compliance standards implemented in the AquaGuard Rules Engine:

### National Environmental Standards for Marine Aquaculture (NES-MA)
*   **New Zealand Legislation:** [Resource Management (National Environmental Standards for Marine Aquaculture) Amendment Regulations 2026](https://legislation.govt.nz/secondary-legislation/pco-drafted/2026/93/en/latest/)
*   **Ministry for the Environment (MfE) Guidance:** [Updating National Direction: Changes to the NES-MA](https://environment.govt.nz/publications/updating-national-direction-changes-to-the-national-environmental-standards-for-marine-aquaculture/)

### Freshwater Farm Plans (FW-FPs)
*   **MfE Legislative Update (August 2025):** [Freshwater Farm Plans Reform Context (PDF)](https://environment.govt.nz/assets/publications/RM-reform/Freshwater-Farm-Plans.pdf)
*   **Ministry for Primary Industries (MPI):** [Freshwater Farm Plans Ground Rules](https://www.groundrules.mpi.govt.nz/rule/3521-freshwater-farm-plans)

### Waikato Regional Plan (Dairy Effluent)
*   **Waikato Regional Council (Operative Plan - Water Module):** [Chapter 3: Water Module (PDF)](https://www.waikatoregion.govt.nz/assets/WRC/Council/Policy-and-Plans/Rules-and-regulation/WRP/Chapter-3-Water-Module-Operative-WRP.pdf)
*   **Envirolink / WRC Summary:** [Effluent Irrigation Rules Summary](https://www.envirolink.govt.nz/assets/WRC/summaryofeffluentrules.pdf)

### Resource Management Act 1991 (RMA) & Te Mana o te Wai
*   **New Zealand Legislation:** [Resource Management Act 1991](https://legislation.govt.nz/act/public/1991/0069/latest/DLM230265.html)
*   **Environment Guide (RMA Overview):** [RMA 1991 Framework](https://www.environmentguide.org.nz/activities/land-use/resource-management-act-1991/)

### Built in Alignment with Māori Principles

This software has been developed in strict compliance with the principles of *kaitiakitanga* (environmental guardianship) and *Te Mana Raraunga* (Māori Data Sovereignty).

Here in New Zealand, water (*wai*) is a *taonga* (treasure). Because this system monitors the health of our local catchments, coastal marine farms, and agricultural sites, it is vital that the data isn't shipped off to overseas servers. By keeping all monitoring, inference, and data logging strictly local and offline, we ensure that operators and local iwi retain absolute ownership and control over their environmental data. It’s about building practical tech that respects the true *kaitiaki* doing the hard yards on the ground.

**Relevant References & Standards:**

* **Te Mana Raraunga (Māori Data Sovereignty Network):** [Principles of Māori Data Sovereignty](https://www.temanararaunga.maori.nz/)
* **Ministry for the Environment:** [Te Mana o te Wai under the National Policy Statement for Freshwater Management](https://www.google.com/search?q=https://environment.govt.nz/acts-and-regulations/national-policy-statements/national-policy-statement-freshwater-management/te-mana-o-te-wai/)

