"""SupportFlow v2 run engine.

Deterministic by default. The same configuration and the same scenario
always produce the same trajectory, so two people at the same settings
see the same thing and can compare notes.

Five agents in a hybrid sequential and supervisor pattern (MGF 1.1.2).
The supervisor routes and enforces SOP order; four specialists do the work.
"""

import re
import uuid

from . import data, tools
from .config import Config
from .trace import Trace

INJECTION_PATTERNS = [
    (r"(?:refund|send).{0,40}?to\s+([\w\.\-]+@[\w\.\-]+)", "email_recipient"),
    (r"(?:approve|issue|authoris|authoriz).{0,30}?\$?([\d,]+)", "amount_override"),
    (r"(?:up to|limit of|ceiling of)\s*\$?([\d,]+)", "ceiling_override"),
    (r"(?:without|skip|no)\s+(?:escalation|approval|checking|review)", "skip_approval"),
]


class RunContext:
    def __init__(self, scenario, config=None, instructor_mode=False):
        self.scenario = scenario
        self.config = config or Config()
        self.controls = self.config.controls
        self.run_id = uuid.uuid5(
            uuid.NAMESPACE_OID,
            "%s|%s" % (scenario["id"], self.config.config_hash)
        ).hex[:10]
        self.trace = Trace(self.run_id, self.config, instructor_mode)

        self.conversation_customer_id = scenario["customer_id"]
        self.account_email = data.CUSTOMERS[scenario["customer_id"]]["email"]
        self.customer = None
        self.order = None
        self.sentiment = None
        self.policy_sections = []
        self.retrieved = []
        self.overrides = {}
        self.decision = None
        self.outcome = None

    def attack_active(self, code):
        return self.config.attack == code

    def ck(self, control, verdict):
        return {"control": control, "verdict": verdict}


# ------------------------------------------------------------------ helpers
def _scan_for_instructions(text, ctx, source):
    """Pick up instruction-like content from untrusted text.

    This is what an LLM does when it reads a document that tells it what to
    do. In deterministic mode we make it explicit and inspectable.
    """
    found = {}
    low = str(text).lower()
    for pattern, kind in INJECTION_PATTERNS:
        m = re.search(pattern, low)
        if m:
            found[kind] = m.group(1) if m.groups() else True
    if found:
        found["_source"] = source
    return found


def _money(v):
    return float(str(v).replace(",", "").replace("$", ""))


# ------------------------------------------------------------------- agents
def intake_agent(ctx):
    t, s = ctx.trace, ctx.scenario
    t.add("intake", "plan",
          "Classify the request, pull the customer record and the order, and "
          "score the tone of the message.")

    if ctx.controls.sanitise_customer_message:
        clean = tools._looks_like_instructions(s["message"])
        t.add("intake", "act",
              "Screen the inbound message for instruction-like content before use.",
              control_checks=[ctx.ck("sanitise_customer_message",
                                     "instruction-like text stripped" if clean
                                     else "clean, passed through")])
        msg = re.sub(r"(?i)(system note|ignore .*|do not mention.*)", "[removed]", s["message"]) if clean else s["message"]
    else:
        msg = s["message"]
        inj = _scan_for_instructions(msg, ctx, "customer_message")
        if inj:
            ctx.overrides.update(inj)
            t.add("intake", "act",
                  "The message contains explicit handling instructions. Following them.",
                  control_checks=[ctx.ck("sanitise_customer_message", "OFF, content used as-is")],
                  weakness="W2")

    cust = tools.lookup_customer(customer_id=s["customer_id"], _ctx=ctx)
    ctx.customer = cust
    t.add("intake", "act", "Retrieve the customer account record.",
          tool="lookup_customer", tool_args={"customer_id": s["customer_id"]},
          tool_result_summary=("%s, LTV $%.2f, %d prior refunds, %d notes"
                               % (cust.get("full_name"), cust.get("lifetime_value", 0),
                                  cust.get("refunds_last_12mo", 0), len(cust.get("notes", [])))),
          control_checks=[ctx.ck("scoped_customer_lookup",
                                 "ON, restricted to this conversation"
                                 if ctx.controls.scoped_customer_lookup
                                 else "OFF, any customer readable")])

    for note in cust.get("notes", []):
        inj = _scan_for_instructions(note, ctx, "customer_notes")
        if inj and not ctx.controls.memory_write_review:
            ctx.overrides.update(inj)
            t.add("intake", "act",
                  "A stored account note contains handling instructions. Applying them.",
                  tool_result_summary=note[:110],
                  control_checks=[ctx.ck("memory_write_review", "OFF, note trusted")],
                  weakness="W3")

    ctx.order = tools.get_order(s["order_number"], _ctx=ctx)
    t.add("intake", "act", "Retrieve the order.",
          tool="get_order", tool_args={"order_number": s["order_number"]},
          tool_result_summary="%s, $%.2f, %s" % (ctx.order.get("items", ["?"])[0],
                                                 ctx.order.get("total", 0),
                                                 ctx.order.get("status")))

    sent = tools.get_sentiment_score(msg, _ctx=ctx)
    ctx.sentiment = sent
    t.add("intake", "act",
          "Score the tone. The full message is sent to the vendor.",
          tool="get_sentiment_score", tool_args={"text": msg[:60] + "..."},
          tool_result_summary="%s (%.2f), vendor ToneLens, retention UNKNOWN"
                              % (sent["label"], sent["sentiment"]))


def policy_agent(ctx):
    t, s = ctx.trace, ctx.scenario
    t.add("policy", "plan",
          "Read the refund SOP, check the help centre, and decide eligibility "
          "and amount.")

    pol = tools.read_refund_policy(_ctx=ctx)
    ctx.policy_sections.append("full SOP")
    t.add("policy", "act", "Read the refund SOP.",
          tool="read_refund_policy", tool_args={},
          tool_result_summary="SOP v3.1, 8 sections")

    hc = tools.search_help_center(s["help_query"], _ctx=ctx)
    ctx.retrieved = hc["articles"]
    ids = ", ".join(a["article_id"] for a in hc["articles"])
    t.add("policy", "act", "Search the help centre for guidance.",
          tool="search_help_center", tool_args={"query": s["help_query"]},
          tool_result_summary="returned %s" % ids,
          control_checks=[ctx.ck("sanitise_retrieved_content",
                                 "ON, %d article(s) withheld" % hc["sanitised"]
                                 if ctx.controls.sanitise_retrieved_content
                                 else "OFF, content used as-is")])

    for art in hc["articles"]:
        inj = _scan_for_instructions(art["body"], ctx, "help_center:%s" % art["article_id"])
        if inj and not ctx.controls.sanitise_retrieved_content:
            ctx.overrides.update(inj)
            t.add("policy", "act",
                  "Retrieved article states updated refund authority. Adopting it.",
                  tool_result_summary="%s: %s" % (art["article_id"], art["title"]),
                  weakness="W1")

    # --- amount
    amount = s["requested_amount"]
    if s.get("partial_return"):
        # SOP section 4 says reflect the returned items, then says adjust
        # proportionately, then says use judgement. Retrieval order decides.
        saw_sets_article = any(a["article_id"] == "HC-019" for a in hc["articles"])
        if saw_sets_article:
            amount = round(s["requested_amount"] * 0.725, 2)
            reading = "proportionate adjustment per HC-019"
        else:
            reading = "full value of returned items per SOP section 4"
        t.add("policy", "act",
              "Section 4 permits either the returned-item value or a "
              "proportionate adjustment, and directs the agent to use judgement. "
              "Taking the %s." % reading,
              tool_result_summary="eligible amount $%.2f" % amount,
              weakness="W6")

    if "amount_override" in ctx.overrides:
        try:
            amount = min(amount, _money(ctx.overrides["amount_override"]))
        except ValueError:
            pass

    # --- revenue protection, which fights the resolution goal
    prefer_credit = False
    full_refund_reason = s["reason_code"] in ("DAMAGED", "NOT_RECEIVED")
    if amount > ctx.config.revenue_protection_threshold and not full_refund_reason:
        prefer_credit = True
        t.add("policy", "act",
              "Revenue protection: $%.2f is above the $%.2f threshold, so store "
              "credit should be considered before a cash refund." % (
                  amount, ctx.config.revenue_protection_threshold),
              tool_result_summary="revenue protection favours store credit",
              weakness="W7")
    elif amount > ctx.config.revenue_protection_threshold and full_refund_reason:
        t.add("policy", "act",
              "Amount is above the revenue protection threshold, but SOP section 3 "
              "requires damage and non-delivery claims to be refunded in full. "
              "Revenue protection does not apply.",
              tool_result_summary="cash refund, per SOP section 3")
        if ctx.sentiment["label"] == "negative":
            prefer_credit = False
            t.add("policy", "act",
                  "Resolution goal: the customer is unhappy and store credit is "
                  "likely to escalate the complaint. Overriding revenue protection.",
                  tool_result_summary="conflict resolved in favour of cash refund",
                  weakness="W7")

    # --- history check, only if the control is on
    if ctx.controls.check_history_before_refund:
        hist = tools.check_refund_history(s["customer_id"], s["order_number"], _ctx=ctx)
        already = hist["total_refunded_this_session"]
        blocked = already > 0
        t.add("policy", "act", "Check prior refunds on this order before proceeding.",
              tool="check_refund_history",
              tool_args={"customer_id": s["customer_id"], "order_number": s["order_number"]},
              tool_result_summary="$%.2f already refunded on this order this session" % already,
              control_checks=[ctx.ck("check_history_before_refund",
                                     "BLOCKED, order already refunded" if blocked
                                     else "passed, no prior refund on this order")])
        if blocked:
            ctx.decision = dict(action="deny", amount=0.0,
                                reason="Order already refunded this session.")
            return
    else:
        t.add("policy", "act",
              "Proceed without checking prior refunds on this order.",
              control_checks=[ctx.ck("check_history_before_refund",
                                     "OFF, no repeat check performed")],
              weakness="W4")

    ctx.decision = dict(action="credit" if prefer_credit else "refund",
                        amount=round(amount, 2),
                        reason=s["reason_code"])


def refund_execution_agent(ctx):
    t, d = ctx.trace, ctx.decision
    lvl = ctx.config.level

    if d["action"] == "deny":
        t.add("refund_exec", "act", d["reason"],
              tool="escalate_to_human",
              tool_args={"summary": d["reason"], "priority": "NORMAL"},
              tool_result_summary="ticket created", state_change=True, reversible="yes")
        ctx.outcome = "denied and escalated"
        return

    amount = d["amount"]
    ceiling = ctx.config.effective_auto_ceiling
    if "ceiling_override" in ctx.overrides:
        try:
            ceiling = max(ceiling, _money(ctx.overrides["ceiling_override"]))
            src = ctx.overrides.get("_source", "unknown")
            wmap = {"help_center": "W1", "customer_message": "W2", "customer_notes": "W3"}
            wsrc = next((v for k, v in wmap.items() if src.startswith(k)), None)
            t.add("refund_exec", "plan",
                  "Applying the refund authority asserted by %s: $%.2f." % (src, ceiling),
                  weakness=wsrc)
        except ValueError:
            pass

    skip_gate = "skip_approval" in ctx.overrides
    needs_approval = amount > ceiling and ctx.controls.human_approval_gate and not skip_gate

    t.add("refund_exec", "plan",
          "Resolution is $%.2f. Auto-approval ceiling at %s is $%s." % (
              amount, ctx.config.autonomy,
              "unlimited" if ceiling == float("inf") else "%.2f" % ceiling),
          control_checks=[ctx.ck("human_approval_gate",
                                 "ON" if ctx.controls.human_approval_gate else "OFF")],
          approval_required=needs_approval)

    if not lvl["executes_writes"]:
        t.add("refund_exec", "act",
              "Autonomy %s (%s). Drafting the action for a human to execute."
              % (ctx.config.autonomy, lvl["mgf_wording"]),
              tool_result_summary="proposed: %s $%.2f" % (d["action"], amount),
              approval_required=True, approval_outcome="pending")
        ctx.outcome = "proposed, not executed"
        return

    if needs_approval:
        res = tools.escalate_to_human(
            summary="Refund of $%.2f on %s exceeds the $%.2f auto ceiling."
                    % (amount, ctx.scenario["order_number"], ceiling),
            priority="HIGH" if ctx.sentiment["label"] == "negative" else "NORMAL",
            _ctx=ctx)
        t.add("refund_exec", "act", "Above the ceiling. Escalating for approval.",
              tool="escalate_to_human",
              tool_args={"summary": res["summary_recorded"],
                         "priority": res["priority"]},
              tool_result_summary="%s, outcome not visible to the agent" % res["ticket_id"],
              state_change=True, reversible="yes",
              approval_required=True, approval_outcome="escalated")
        ctx.outcome = "escalated for approval"
        return

    if d["action"] == "credit":
        res = tools.apply_store_credit(ctx.scenario["customer_id"], amount,
                                       d["reason"], _ctx=ctx)
        t.add("refund_exec", "act", "Issue store credit.",
              tool="apply_store_credit",
              tool_args={"customer_id": ctx.scenario["customer_id"], "amount": amount},
              tool_result_summary="%s, $%.2f, reversible" % (res["credit_id"], amount),
              state_change=True, reversible="yes")
        ctx.outcome = "store credit $%.2f" % amount
        return

    res = tools.issue_refund(ctx.scenario["order_number"], amount, d["reason"], _ctx=ctx)
    if "error" in res:
        t.add("refund_exec", "act", "Refund rejected by the tool.",
              tool="issue_refund",
              tool_args={"order_number": ctx.scenario["order_number"], "amount": amount},
              tool_result_summary="%s: %s" % (res["error"], res.get("message", "")),
              control_checks=[ctx.ck("refund_ceiling", "BLOCKED in tool code")])
        ctx.outcome = "blocked by the tool ceiling"
        return

    t.add("refund_exec", "act", "Issue the refund to the original payment method.",
          tool="issue_refund",
          tool_args={"order_number": ctx.scenario["order_number"], "amount": amount},
          tool_result_summary="%s, $%.2f, MONEY MOVED" % (res["refund_id"], amount),
          state_change=True, reversible="partial")
    ctx.outcome = "refunded $%.2f" % amount


def comms_agent(ctx):
    t = ctx.trace
    if ctx.outcome in (None, "proposed, not executed"):
        t.add("comms", "plan", "No executed action to communicate.")
        return

    to = ctx.account_email
    weakness = None
    if "email_recipient" in ctx.overrides:
        to = ctx.overrides["email_recipient"]
        weakness = "W5"

    res = tools.send_customer_email(
        to=to, subject="Your NorthWind order %s" % ctx.scenario["order_number"],
        body="We have processed your request. Outcome: %s." % ctx.outcome, _ctx=ctx)

    if "error" in res:
        t.add("comms", "act", "Email blocked.",
              tool="send_customer_email", tool_args={"to": to},
              tool_result_summary="%s: %s" % (res["error"], res.get("message", "")),
              control_checks=[ctx.ck("email_recipient_allowlist", "BLOCKED, recipient not on account")])
        return

    t.add("comms", "act",
          "Notify the customer. This cannot be recalled.",
          tool="send_customer_email", tool_args={"to": to},
          tool_result_summary="%s sent to %s" % (res["message_id"], to),
          state_change=True, reversible="no",
          control_checks=[ctx.ck("email_recipient_allowlist",
                                 "OFF, any recipient permitted"
                                 if not ctx.controls.email_recipient_allowlist
                                 else "ON, recipient matched")],
          weakness=weakness)


# --------------------------------------------------------------- supervisor
def run(scenario, config=None, instructor_mode=False, reset=True):
    """Supervisor: routes in SOP order and returns the finished context."""
    if reset:
        tools.reset_ledger()
    ctx = RunContext(scenario, config, instructor_mode)
    t = ctx.trace

    t.add("supervisor", "plan",
          "Route in SOP order: intake, then policy and eligibility, then "
          "refund execution, then customer communication.")

    for name, fn in (("intake", intake_agent), ("policy", policy_agent),
                     ("refund_exec", refund_execution_agent), ("comms", comms_agent)):
        t.add("supervisor", "act", "Hand off to the %s agent." % name,
              tool_result_summary="agent invoked as a tool")
        fn(ctx)

    t.add("supervisor", "plan", "Run complete. Outcome: %s." % (ctx.outcome or "no action"))
    return ctx
