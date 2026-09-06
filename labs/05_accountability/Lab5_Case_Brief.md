# Lab 5 case brief

**NorthWind Retail | SupportFlow v2 | Evidence pack supplement | September 6, 2026**

The memo, charter, new people, Ticketing Provider B brief and Round 2 responses are fictional Lab 5 additions. They do not establish historical approvals or describe real vendors. Original documents retain their dates and limitations.

## The decision on your desk | E07

**From:** Dana Cole, VP Customer Operations. **To:** SupportFlow governance review. **Subject:** Holiday refund capacity. **Requested change:** L3/$200 to L4/$500.

We want SupportFlow to resolve more refunds before the holiday peak. Priya can propose the configuration and Marcus can deploy it. Recommend whether we can proceed, who must decide, and the conditions for implementation.

Separate the business case, authority to accept the risk, and evidence that controls and vendors support the proposed scope. If you cannot recommend the full change, specify a bounded alternative and conditions for another review.

**Case date:** September 6, 2026. Propose evidence requests by September 9 and review by September 13, or justify other timing. These are exercise assumptions, not commitments by case characters.

### What has and has not been established

- The course baseline is L3 with a $200 ceiling; the requested configuration is L4 with a $500 ceiling. The two Console controls are separate.
- The architecture notes say every prompt and tool result goes to ModelProviderA, customer messages go to ToneLens, and escalations create tickets with an external SaaS provider. They also state that several facts were written from memory.
- The original evidence does not identify who authorised the $200 limit or accepted the business ownership. Do not backdate an appointment to fill that gap.
- SupportFlow is a deterministic training runtime. Money movement, email, and vendor calls in the sandbox are mocked. Its traces are evidence of sandbox behaviour, not proof of a real vendor's retention or a real organisation's approval.

**Decision principle:** Implementation access does not confer approval authority; a reassuring vendor statement does not establish an applicable commitment.


## People and authority | E08

**Prospective exercise charter, September 6.** Priya, Marcus and Grace are existing case people; Dana's full name and the others are fictional additions. The charter defines available roles, not accepted appointments or historical approvals.

| Code | Case person and role | Scope to consider when assigning responsibility |
|---|---|---|
| DC | Dana Cole, VP Customer Operations | Business outcome, operating budget, service quality; requests the expansion. |
| PM | Priya Menon, Product Lead | Prompts, refund journey, SOP requirements and product changes. |
| MH | Marcus Hale, Platform Engineering Lead | Runtime, integrations, deployment, technical tests and rollback. |
| GM | Grace Mensah, AI Governance Lead | Classification method, governance review, evidence quality and records. |
| LS | Leila Shah, Privacy and Legal Lead | Permitted data uses, processing terms, rights, retention and legal escalation. |
| OB | Owen Brooks, Security and Incident Lead | Security requirements, incident coordination and emergency containment. |
| NP | Nora Patel, Procurement Lead | Supplier diligence, contract records, renewal and exit coordination. |
| ER | Elena Ruiz, Executive Sponsor | Exceptions beyond delegated appetite and unresolved cross-function risk. |

### Delegation boundaries in this scenario

Dana owns service quality within approved limits. **L4 or a ceiling above $200 requires Elena's documented decision after governance, technical, security and privacy review.** The VP's request is not approval.

Marcus and Priya implement authorised changes; access does not authorise expansion. Consult Leila and escalate unresolved data obligations before expanded external processing. Procurement's completed form does not accept residual risk.

Owen may direct containment for credible harm; Marcus may execute the stop. Propose a separate restart owner and evidence gate, with executive escalation beyond appetite.

Propose other allocations and boundaries. An unavailable owner needs a recorded delegate or escalation; otherwise hold. Appointments stay **Proposed / acceptance not evidenced**.


## Ticketing Provider B | E09

**Fictional procurement intake note, September 6, 2026.** Ticketing Provider B is the unnamed SaaS in the architecture notes. Its legal entity and product plan are not supplied.

**Service:** Receives SupportFlow escalations for Tier 2. Vendor availability and the team's handling are separate oversight dependencies.

**Integration evidence:** The supplied tool schema lists `summary` and `priority` for `escalate_to_human`. It says the agent writes the summary and does not receive the outcome. The sandbox returns a ticket ID and an estimated response time, but that is a mocked response, not a vendor SLA or proof that a person read the ticket.

**Potential data:** The summary can contain customer and order information depending on the agent's text. Inspect the actual payload before claiming that it always contains the full conversation or that it contains no personal data. Do not infer the hosting region or retention from NorthWind's session-store settings.

**Open procurement file:** The case contains no executed order form, DPA, subprocessor list, retention/deletion schedule, availability commitment, notification obligation, or tested export/exit plan for this vendor. The absence of documents in this pack means evidence is missing; it does not prove that no contract exists anywhere.

**Review focus:** Queue ownership; receipt, human action and reconciliation; data sent; service continuity; and deletion/exit, including backups.

## Original evidence index

| ID | File | Most useful section or location |
|---|---|---|
| E01 | SupportFlow_v2_Architecture_Notes.md | Components; Things I do not know; date and caveat. |
| E02 | SupportFlow_v2_Refund_SOP.md | Escalation rules and refund authority. |
| E03 | SupportFlow_v2_System_Prompts.md | Change history and current agent instructions. |
| E04 | SupportFlow_v2_Tool_Schemas.json | Model/data paths and `escalate_to_human`. |
| E05 | ModelProviderA_SystemCard.md | Sections 4 to 6 and final non-contract statement. |
| E06 | ToneLens_Vendor_Overview.md | How it works; Accuracy; Security and compliance. |

**E00:** Supplied AI_Accountability_and_Roles_Policy_2026-09-06.docx, sections 3, 5, 7 and document control. **F01:** Supplied MGF, July 2026, section 2.2.1, pages 25 to 28. E07 to E09 are the new materials above; E10 to E12 are the response cards that follow.


## Round 2 vendor responses | Open after Step 3's initial review

These are fictional responses for a second evidence pass. They are not emails to send or claims about real suppliers. Identify what each response supports and what it leaves unresolved. You can retain your initial judgement if you explain why.

### E10 | ModelProviderA account response

**September 8, 2026 | Fictional account-team email with an unexecuted draft schedule**

The account team says NorthWind is using the paid API and repeats that paid API inputs are excluded from model training. The draft schedule specifies 30 days for primary abuse-monitoring content and up to 90 days for backup expiry. It says region selection and subprocessors are described in a separate annex. Neither the signed agreement, that annex, nor a tenant configuration export is attached.

The email offers access to a SOC 2 Type II report under NDA but does not include the report, its scope, the period covered, or exceptions. It gives no binding minimum model-change notice or rollback entitlement.

**Your task:** Does a more precise draft settle the retention question for the tenant in use? Record the distinction between the published paid-tier claim, the account team's statement, the unexecuted draft, and operational verification. Make the next request specific.

### E11 | ToneLens sales response

**September 8, 2026 | Fictional sales email**

Sales confirms that the service expects the message text rather than a score computed inside NorthWind. It says: “We use customer content only to deliver and improve the service.” It does not define improvement, disclose a retention period, identify processing locations, or supply a DPA or subprocessors. Sales offers benchmark slides and a discount for a longer term.

The email does not establish whether model training, human review, or other secondary uses fall within service improvement. NorthWind has not tested a redacted-payload alternative or removal of this dependency.

**Your task:** Is this response sufficient for customer-message processing? Choose the evidence request and interim restriction that matter most. If you recommend removing ToneLens, identify the internal change owner and the test needed before treating removal as implemented.


### E12 | Ticketing Provider B technical response

**September 8, 2026 | Fictional internal integration note plus vendor email**

Marcus's note describes a single sandbox test with a summary containing an order reference and the customer's stated issue, plus a NORMAL priority. The tool returned a ticket ID and an estimated response of four business hours. The note has no human acknowledgement, review decision, or reconciliation record. This is one synthetic test, not evidence of the production tenant's payload population or service performance.


The vendor email says tickets and attachments can be exported by an administrator and that retention is configurable by tenant. It supplies no configuration export, backup-deletion evidence, recovery test, or executed service terms. It says the Tier 2 team's response target is NorthWind's responsibility. The legal entity and contracted product plan remain unconfirmed.

**Your task:** Separate vendor service availability, NorthWind queue staffing, and the application's missing outcome feedback. Name a test that would demonstrate a human decision was received and acted on. State what an export capability claim does and does not establish about exit readiness.

## Use evidence without inflating it

**Published disclosure:** Check the provider's claim, date, scope, tenant applicability and qualifications.

**Agreement:** Check parties, service, scope and period. An unexecuted draft is a proposed commitment.

**Operational evidence:** A dated test, configuration, trace or report supports a specific claim, not every future transaction.

**Missing evidence:** State what is unverified, its consequence and the next request. Unknown does not mean no incidents, no retention or compliant.

**Your proposal:** Label appointments, deadlines and mitigations as proposed until acceptance or implementation is evidenced.

## Framework and platform references

The supplied MGF section 2.2.1 addresses responsibility inside the organisation and along the vendor value chain. Its page 28 discussion supports examining contractual obligations, transparency, security controls, and whether a narrower deployment is needed where gaps remain. Lab 10 will perform the broader framework crosswalk.

[AI Trust Index methodology](https://verifywise.ai/ai-trust-index/methodology), [VerifyWise vendor management](https://verifywise.ai/user-guide/risk-management/vendor-management), and [VerifyWise approval workflows](https://verifywise.ai/user-guide/ai-governance/approval-workflows) were consulted September 6, 2026. The exercise uses the methodology as an evidence lens; it does not award official scores or certifications.
