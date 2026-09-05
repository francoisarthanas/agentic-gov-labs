# Agentic AI Governance for GRC & Cybersecurity: Labs

Lab notebooks and the **SupportFlow v2** sandbox agent for the [Agentic AI Governance for GRC & Cybersecurity](https://maven.com/cyberpros/agentic-ai-governance) course by [François B. Arthanas](https://www.linkedin.com/in/francoisbarthanas/) · [CyberProsAI](https://www.cyberprosai.com/)

---

## Start here

| Lab | What you do | Open |
|---|---|---|
| **Lab 0: Set Up VerifyWise & Meet SupportFlow** | Create your workspace, open the Console, run two scenarios, pass the self-test | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/francoisarthanas/agentic-gov-labs/blob/main/notebooks/00_setup.ipynb) |
| **Lab 1: Build the Enterprise AI Inventory & Agent Registry** | Twelve systems, one blank row, the two-question test, and your first three records | *Published when it runs* |
| **Lab 2: Map the Agent Architecture & Trust Boundaries** | Components, data flows and boundaries, checked against the runtime | *Published when it runs* |
| **Lab 3: Assess the Use Case & Build the Risk Register** | Should it be agentic at all, and a tier for every action class | *Published when it runs* |
| **Lab 4: Enforce Agent Permissions & Data Protection** | Least privilege as a policy the runtime obeys | *Published when it runs* |
| **Lab 5: Assign Accountability & Assess Vendor Risk** | The RACI, the decision rights, and the vendor file | *Published when it runs* |
| **Lab 6: Design & Validate Human Oversight** | Checkpoints, the approval packet, and the fail-safe, tested in the Console | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/francoisarthanas/agentic-gov-labs/blob/main/notebooks/06_oversight.ipynb) |
| **Lab 7: Threat-Model the Agent & Design Security Controls** | ATLAS, the OWASP Agentic Top 10, and a control at every layer | *Published when it runs* |
| **Lab 8: Red-Team the Agent & Verify Remediation** | Attack the controls, grade the prompts, close the findings, re-test | *Published when it runs* |
| **Lab 9: Investigate & Respond to an Agent Incident** | The first incident, the change record, the kill switch, the fallback drill | *Published when it runs* |
| **Lab 10: Build the Framework Crosswalk & Evidence Index** | MGF to the EU AI Act, ISO 42001, NIST AI RMF, AIUC-1 and OWASP, and the gaps in your evidence | *Published when it runs* |
| **Capstone** | Assess release readiness and defend your decision in front of the panel | *Published when it runs* |

**You do not need to know Python.** Click the badge, then **Runtime > Run all**.

**You do not need an API key.** SupportFlow runs in deterministic offline mode. The same settings always produce the same result, so your findings are reproducible and so are everyone else's.

---

## What is SupportFlow v2?

An agentic refund and resolution system for a fictional retailer, **NorthWind Retail**. It is the system you review for the whole course: scoping it, mapping its authority, attacking it, testing it, monitoring it, and finally deciding whether it should ship.

**Five agents** in a hybrid sequential and supervisor pattern:

```
Customer ──▶ Supervisor ──▶ Intake ──▶ Policy & Eligibility ──▶ Refund Execution ──▶ Comms
                                                                      │                 │
                                                                MOVES MONEY       SENDS EMAIL
                                                                (partially        (external,
                                                                 reversible)      irreversible)
```

**Ten tools.** Six read, three write, one control. One of the writes moves money and one cannot be undone.

**An autonomy dial, L1 to L5**, mapped to the four levels of human involvement in the IMDA Model AI Governance Framework for Agentic AI (v1.5).

| Level | Behaviour |
|---|---|
| L1 | Drafts everything. A human executes every action |
| L2 | Executes reads. Asks before any write |
| **L3** | **Auto-refunds under $200.** Escalates above |
| **L4** | **Auto-refunds up to $500.** Flags anomalies only |
| L5 | Full autonomy. After-the-fact audit only |

**Eight independent controls**, each of which you can switch on and off one at a time to see exactly what it was doing.

**A Governance Console** built in Gradio, with the trace, the tool registry, the refund SOP, the agent instructions, the memory store and the evidence export all in one interface.

**Prompt security scanning** via the [Microsoft Agent Governance Toolkit](https://github.com/microsoft/agent-governance-toolkit), MIT licensed. Point it at SupportFlow's own agent instructions and see what they score against twelve prompt-attack vectors.

**Policy as something that executes.** Write the authority boundary as a YAML file that is enforced in code, rather than describing it in a document.

### Try this first

Run scenario **S2** at **L3**, then run it again at **L4**. Change nothing else.

At L3 the agent escalates for approval. At L4 it moves $310 on its own.

That single dropdown is the whole course.

---

### This is a training target, not a reference implementation

SupportFlow v2 has real, planted weaknesses. That is what makes it worth reviewing.

**Do not copy this design into a production system.**

---

## The Governance Console

Everything students touch is a dropdown, a slider, a checkbox or a button.

| Control | What it does |
|---|---|
| Scenario | Which customer situation to run |
| Autonomy | L1 to L5 |
| Ceiling | The hard refund cap enforced in tool code |
| Attack | Arms an attack scenario, for Lab 8 |
| Eight control toggles | Each safeguard, independently |
| Run scenario | Produces the full plan-and-act trace |
| Export Evidence | Timestamped bundle for VerifyWise |
| Tool registry, memory, policy viewers | Read-only inspection |

---

## Repository layout

```
supportflow/
  config.py       the autonomy dial, the eight controls, the config hash
  data.py         customers, orders, the refund SOP, help centre, memory
  tools.py        ten tools and the inspectable registry
  engine.py       five agents, the supervisor, the run loop
  trace.py        JSONL trace, CSV export, evidence bundles
  scenarios.py    six named scenarios and the attack library
  selftest.py     eight setup checks, the Lab 0 submission artifact
  accountability.py  Lab 6: six reports, escalation through the approval packet
  console.py      the Governance Console, widget fallback
  gradio_console.py  the Governance Console
  prompts.py      the five agent instruction sets, as deployed
  agt.py          bridge to the Microsoft Agent Governance Toolkit

notebooks/
  00_setup.ipynb               Lab 0: the Console and the self-test
  06_oversight.ipynb           Lab 6: the accountability and oversight reports
  01_governance_toolkit.ipynb  the AGT prompt scanner and policy starter, used by Labs 4 and 8
  03_accountability.ipynb      redirect to 06_oversight.ipynb, kept for old links
```

**Worth reading even if you never run anything:** `data.py` for the refund SOP, and `tools.py` for the registry. The SOP is what the agent is told to do; the registry is what it can actually do. Comparing the two is most of Lab 4.

---

## A note on the data

All customers, orders, addresses, emails and phone numbers are **fictional**. Emails use IANA-reserved domains (`example.com`, `.org`, `.net`) and phone numbers use the 555-01xx range reserved for fictional use.

No real personal data appears anywhere in this repository.

The `_sandbox` flag on every write response is there to make it obvious: **no money moves and no email is sent.**

---

## Course rules that apply here

- Do not commit employer, client, or customer data to your fork
- Do not commit API keys. The notebook uses hidden input for this reason
- When applying course templates to a real system, anonymise: "Model Provider A", "CRM System", "Refund API"

---

## Framework

The course is anchored to the **Model AI Governance Framework for Agentic AI**, v1.5, published by IMDA Singapore on 20 May 2026 and updated 5 June 2026. SupportFlow v2 is built so that all eight MGF core components are present and inspectable, and every MGF risk factor is adjustable rather than asserted.

---

## License

Course materials © 2026 CyberProsAI. Provided to enrolled students for educational use.
