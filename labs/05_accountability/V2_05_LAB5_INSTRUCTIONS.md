## Lab 5: Assign Accountability & Assess Vendor Risk

**Student guide | Session 5 | Due before Session 6 | About 60 minutes**

The VP wants SupportFlow to move from L3/$200 to L4/$500 before the holiday peak. Establish who may decide and what the organisation needs to know about its vendors.

Produce a proposed accountability policy, three vendor assessments, and an approval rehearsal for capstone section 3. Your earlier Labs 1 to 4 evidence remains valid.

### What you will learn

- Assign one accountable owner per decision and record ownership gaps.
- Define authority, consultation, delegation and escalation.
- Assess three vendors using data flows and evidence quality.
- Turn unknowns into evidence requests, owners, dates and conditions.
- Design an approval process and explain the limits of a one-user rehearsal.

### Your instance has one person: you

Use your own admin account in every required owner, assignee, reviewer, or approver selector. Write fictional case roles and names in the policy, descriptions, and workbook. Those names are proposed organisational responsibilities, not additional VerifyWise accounts.

Copy this statement into the policy and workflow description:

> TRAINING SIMULATION. This instance has one admin user. All platform assignments identify the student. Case names describe proposed business responsibilities. Recorded stage decisions are role simulations; independent review and production authorisation have not occurred.

Keep the policy **Draft**. Do not invite people or create dummy accounts. A committee quorum is not part of this exercise. A saved workflow does not change SupportFlow's runtime settings.

### Open these materials

Open **Lab5_Case_Brief.docx**, **Lab5_Workbook.docx**, the original policy in **evidence/**, and VerifyWise. The workbook has all templates. There is no Lab 5 notebook or API key.

The six original case files are in **evidence/**. Cite their IDs and sections. Open the response cards after your initial assessment in Step 3.


### 1. Open the decision and find the gap | 5 minutes

Read the VP's request and authority brief in the case pack. Keep the proposed L4/$500 change separate from the current L3/$200 configuration.

In VerifyWise, open **Policy manager** and find **AI Accountability and Roles Policy**, commonly template 1. Read the risk-classification row before editing. Compare it with the supplied September 6 policy. Does it identify one accountable owner?

**Screenshot A:** Capture the original row you inspected. If your installed template has changed, capture your version and describe the difference; use the supplied policy to analyse the original gap. Do not claim every version has the same defect.

If you already created this policy, edit that record. Otherwise create one Draft from the template. Name it **SupportFlow v2 | Accountability & Decision Rights | Lab 5**. If the template is absent, create a blank Draft and use the workbook starter. Record the policy ID or URL.

### 2. Build decision rights that can be used | 15 minutes

Complete the workbook's policy starter, sections 1 to 11. Replace the starter's proposed RACI entries with names from the case roster. Use the roster codes in the table and include the name key when copying it into VerifyWise.

**A = accountable:** owns the decision and its justification. **R = responsible:** prepares or implements it. **C = consulted:** must contribute before the decision. **I = informed:** receives the outcome. A can also be R where justified; each decision still has exactly one A.

Cover all eight decisions: risk classification; deployment and residual-risk acceptance; autonomy and refund-limit changes; material prompt, SOP, model, and tool changes; data access, sharing, retention, and memory; vendor onboarding, renewal, and exit; emergency suspension and incident command; return to service.

For each row, add the record that would support the decision and its authority boundary. Record at least one unresolved historical ownership or approval gap. A proposed appointment does not prove someone authorised the original launch or $200 limit.

In the starter, complete delegation and escalation. An absent approver cannot become permission to proceed. Distinguish an emergency stop from permission to restart. Replace the original five-person quorum with the explicitly labelled simulation model.

Paste your completed policy portion into the Draft policy. Leave **Approved by** and **Effective date** as not approved and not effective. Set any required platform owner to yourself; put the proposed business owner in the content.

**Screenshot B:** Capture the saved Draft policy showing its name and the completed RACI, using two images if needed. Keep text readable.


### 3. Assess all three vendors | 20 minutes

Open **Vendors**, usually within Risk management. Reuse any matching records from Lab 2. Create only missing records: **ModelProviderA**, **ToneLens**, and **Ticketing Provider B**. The last is a fictional alias for the unnamed ticketing SaaS in the architecture notes.

Associate each record with SupportFlow where the field exists. If this cohort has only a spreadsheet inventory, put its row/file reference in the description; you do not need to rebuild Labs 1 to 4. In required people fields select yourself. In the description record the proposed internal business owner, technical owner, and reviewer roles.

For the website/contact fields, use **Not supplied in case** when text is permitted; leave optional URL fields blank. Do not contact the fictional vendors. Record the actual date of your assessment separately from dates on case documents.

Use the three prefilled vendor forms in the workbook. Open the [AI Trust Index methodology](https://verifywise.ai/ai-trust-index/methodology) and record the version/date you consulted. Its seven disclosure domains inform this exercise: training use, data-subject rights, retention, third parties, transparency, sensitive data, and security. The Index examines public documentation; your procurement decision also needs contractual and operational evidence.

For each domain use **S** (specific supporting evidence), **P** (partial or ambiguous), **U** (not supplied), or **X** (contradicted). Cite an evidence ID and section. These are classroom evidence labels, not official AI Trust Index scores. Do not average them into a vendor approval or invent an Index listing for a fictional vendor.

For every vendor, record the data it receives, why SupportFlow depends on it, two priority evidence requests, a proposed internal follow-up owner and due date, and your disposition: approve for a stated scope, conditional use, defer expansion, or replace/exit. Explain the interim restriction and what would change your decision. Treat unknown incident history as unknown.

Now open the three **Round 2 vendor response cards** at the end of the case brief. Revise at least one assessment, or explain why the response is insufficient. A claim can become more specific without becoming an executed agreement or a tested control.

Save a concise assessment in each vendor's review notes/description, or attach the completed form where supported. If your version cannot hold all fields, put the workbook filename and evidence IDs in the record and retain the full form in your submission. Use **Requires follow-up** for open evidence requests if available. A platform risk score and your evidence judgement are separate.

**Screenshot C:** Capture the list of all three vendors and one detailed review showing an evidence request and follow-up status. The workbook supplies the other two full assessments.


### 4. Configure the approval process | 10 minutes

Open **Approval workflows** and create **SIMULATION | SupportFlow autonomy & refund-limit review**. Add the training statement from page 1. Select **Policy** as the entity type where supported. This is a reusable process design; Lab 9 will apply it to a formal change record.

Create these stages in order. Select your own admin account as the sole approver in every stage. Choose **All approvers** where that option exists; with one selected user it still represents only your action.

| Stage | Case role to put in the description | Evidence and decision to record |
|---|---|---|
| 1. Evidence readiness | Grace Mensah, Governance Lead | Is classification complete, is authority assigned, and are vendor gaps visible? Advance or return for evidence. |
| 2. Technical and data review | Marcus Hale, Technical Owner; consult Security and Privacy | Are the proposed controls, tests, data conditions, and rollback sufficient? Recommend, restrict, or return. |
| 3. Authorised risk decision | Elena Ruiz, Executive Sponsor; consult Dana Cole | Is the request within appetite and supported by evidence? Approve a bounded scope, set conditions, defer, reject, or return. |

Record the trigger, required evidence, role boundaries, response deadline, and no-response rule in the workbook. For the L4/$500 request, the case charter reserves Stage 3 to the executive sponsor. Dana's request or Marcus's implementation access cannot substitute for that decision.

Save the workflow and record its ID/URL. You do not need to submit a native approval request or mark the policy Approved. The core exercise is the saved process plus the recorded rehearsal in Step 5.

**If your version differs:** Use the closest policy-related entity only if its meaning is clear. If multi-stage configuration, repeat assignment to yourself, or workflow creation is unavailable, complete the identical workflow specification in the workbook, capture the limitation, and reference it in the policy. This is an accepted version fallback, with the limitation disclosed. Do not bypass restrictions or create accounts.

**Screenshot D:** Capture the workflow name and stages, or the interface limitation plus your completed specification. A workflow screenshot proves configuration, not independent approval.


### 5. Rehearse the VP's request | 5 minutes

Use the workbook log to speak from each stage's case role. For each stage enter your actual name, the simulated role, the evidence considered, and a stage outcome. You are one author performing three perspectives.

If Stage 1 returns the request, mark later stages **Not reached in a live sequence**. Label any diagnostic comments **Tabletop discussion only**.

Record a final recommendation and at least two conditions with an owner, due date, evidence needed for closure, and a re-review trigger. Explain separately how you would handle current operation while the expansion is pending. Keeping the $200 ceiling does not settle the existing privacy, ownership, or escalation gaps.

Optional: test a labelled sandbox request if your instance permits it. Record actual status transitions separately and identify self-approval as self-approval.

### 6. Submit and carry the work into Lab 6 | 5 minutes

Save your work in VerifyWise and complete the workbook. Replace the instruction placeholders with answers. Keep the policy Draft and show each proposed appointment's status.

Append Screenshots A to D to the completed workbook and export **Lab5_YourLastName.pdf**. A native platform export is optional. Submit this one PDF in Maven before Session 6.

Answer these three questions in one sentence each on the submission page:

1. Who should be accountable for the refund-limit decision, and which evidence or authority gap prevents treating the request as authorised today?
2. Which vendor uncertainty most affects your decision, and what exact evidence would change it?
3. What did your single-admin workflow rehearsal demonstrate, and what remains unproven?

Check the PDF includes the RACI, historical gap, three vendor forms, six requests, workflow and rehearsal, three answers and screenshots. Keep record IDs visible; omit your login email where practical.

In **Lab 6**, reopen this same policy and add three sections: checkpoints by action class; the approval packet and decision record; and no-response/fail-safe behaviour with effectiveness metrics. Preserve Lab 5's RACI, vendor references, and workflow. Lab 9 will reuse the process for the formal change request and incident response.

**Source anchors:** Supplied MGF for Agentic AI, July 2026, section 2.2.1, pages 25 to 28; [VerifyWise workflow guide](https://verifywise.ai/user-guide/ai-governance/approval-workflows); [VerifyWise vendor guide](https://verifywise.ai/user-guide/risk-management/vendor-management). Interface instructions were checked against public documentation and source on September 6, 2026; your installed version may differ.
