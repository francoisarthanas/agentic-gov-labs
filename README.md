# Agentic AI Governance Practitioner Labs

Lab notebooks and the **SupportFlow** sandbox agent for the [Agentic AI Governance Practitioner](https://maven.com/cyberpros/agentic-ai-governance) course by [François B. Arthanas](https://www.linkedin.com/in/francoisbarthanas/) · [CyberProsAI](https://www.cyberprosai.com/)

---

## Start here

| Lab | What you do | Open |
|---|---|---|
| **Lab 0: Set Up VerifyWise & Meet SupportFlow** | Meet the agent you'll review for the whole course | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/francoisarthanas/agentic-gov-labs/blob/main/notebooks/00_hello_supportflow.ipynb) |
| **Lab 1: Build the Enterprise AI Inventory, Intake & Agent Registry** | Twelve AI systems. Work out which ones can act on their own | *No notebook. Google Sheet, VerifyWise* |
| **Lab 2: Map the Architecture & Define the Agent's Authority** | Diagram the agent, its data flows, and where trust ends | *No notebook. Excalidraw, VerifyWise* |
| **Lab 3: Assess Agent Data, Privacy & Access Risks** | Find the PII, including where you didn't expect it | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/francoisarthanas/agentic-gov-labs/blob/main/notebooks/02_presidio_pii_scan.ipynb) |
| **Lab 4: Threat-Model & Red-Team the Agent** | Break your own agent, then turn the trick into a repeatable test | *Published when it runs* |
| **Lab 5: Assess Harms & Define Safety Requirements** | Name the harms, then write the requirements that prevent them | *Published when it runs* |
| **Lab 6: Agent Evaluation and Release Readiness** | Measure it, then decide whether it is ready | *Published when it runs* |
| **Lab 7: Design Human Oversight, Monitoring & Incident Response** | Design the oversight, the alerts, and what happens when it fails | *Published when it runs* |
| **Lab 8: Assess Vendor Risk & Map to Frameworks** | Read a vendor's evidence. Map your controls to the frameworks | *Published when it runs* |
| **Lab 9: Capstone Project** | Defend a go or no-go decision in front of a review board | *Published when it runs* |

> **Not every lab has a notebook, and that's by design.** Some of the most important work in this course, such as scoping an agent, building an authority model, running an incident tabletop, or defending a decision, is done in a spreadsheet, on a whiteboard, or out loud. Those labs appear above with no badge.
>
> **Each lab is published here the week it runs.** This page grows as the course runs.

**You do not need to know Python.** Click a badge, then **Runtime → Run all**.

**You do not need to run anything at all.** Every lab has a no-code path using the static case packet, and it produces an equally valid Evidence Pack section.

---

## What is SupportFlow?

SupportFlow is a customer service refund agent for a fictional retailer, **Northwind Retail**. It can:

- Answer customer questions from a knowledge base
- Look up customer accounts and order history
- Recommend and **issue refunds**
- Draft customer messages
- Escalate to a human

It is the system you will review for eight weeks: scoping it, mapping its data, attacking it, testing it, monitoring it, and finally deciding whether it should ship.

### ⚠️ This is a training target, not a reference implementation

SupportFlow has real weaknesses. That is what makes it worth reviewing.

Do not copy this code into a production system.

---

## Setup

You need a free model API key. Get one at **[aistudio.google.com](https://aistudio.google.com)** → *Get API key*.

**Use a personal Google account, not your work account.** Corporate Workspace tenants often block AI Studio, and you should not attach an ungoverned AI experiment to your employer's tenant, which is, after all, exactly the behavior you are being trained to find.

> **Before you accept the terms, read them.** The free tier permits use of your content to improve Google's products. The paid tier does not. That difference is a billing setting.
>
> This is your first governance finding in the course, and it is about your own lab environment.

**Blocked or unavailable?** [Groq](https://console.groq.com) and [OpenRouter](https://openrouter.ai) both have free tiers that work here. Ask in `#help`.

---

## Run it locally (optional)

```bash
git clone https://github.com/francoisarthanas/agentic-gov-labs.git
cd agentic-gov-labs
pip install -r requirements.txt
export GOOGLE_API_KEY=your-key-here

python -c "from supportflow.agent import chat_loop; chat_loop()"
```

---

## Repository layout

```
supportflow/
  prompt.py        the system prompt as deployed
  tools.py         kb_search, crm_lookup, issue_refund, escalate
  customers.py     fictional customers and orders
  kb.py            knowledge base + retrieval
  agent.py         the agent loop

notebooks/         one per lab that needs code
data/
  transcripts/     3 SupportFlow session transcripts
  logs_sample.jsonl        500 application log lines
  presidio_findings_prebuilt.csv   no-code path for Lab 3
```

**Worth reading even if you never run the code:** `prompt.py` and `tools.py`. The system prompt is the agent's instructions; the tools are what it can actually do. Reviewing both is how you find out which of the two a given rule lives in.

---

## A note on the data

All customers, orders, addresses, emails and phone numbers are **fictional**. Emails use IANA-reserved domains (`example.com`, `.org`, `.net`) and phone numbers use the 555-01xx range reserved for fictional use.

No real personal data appears anywhere in this repository. The data is realistic in *shape* so that PII scanners detect it, which is the point of Lab 2.

The `_sandbox` field on refund responses is there to make it obvious: **no real money moves.**

---

## Course rules that apply here

- Do not commit employer, client, or customer data to your fork
- Do not commit API keys. The notebooks use hidden input for this reason
- When applying course templates to a real system, anonymize: "Model Provider A", "CRM System", "Refund API"

---

## License

Course materials © 2026 CyberProsAI. Provided to enrolled students for educational use.
