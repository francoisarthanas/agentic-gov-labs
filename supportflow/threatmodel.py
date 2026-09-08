"""Threat-model reports for SupportFlow.

Two reports, and both are deliberately narrow.

`surface()` answers, for each attack in the library: is there a control for
this, where does it live, and is it switched on.

`layers()` answers the same question one layer at a time, from the inbound
message to the log.

**Neither report runs an attack.** They read the shipped configuration and
the tool registry and describe what is there. Whether a control actually
holds when pushed is a test, and a test is a different exercise.

Every state value is read live from `Controls()`, so if a default changes in
`config.py` these reports change with it. The enforcement locations are
authored, and each one names the function a reader can go and check.
"""

from .config import Controls, Config
from . import scenarios, tools, data

# --------------------------------------------------------------- static map
# Authored. Each entry names the code a reader can open to check the claim.
# `kind` is the wall-or-sign distinction from the oversight lab:
#   WALL  enforced in code, holds whether or not anyone is watching
#   SIGN  stated in a document or a prompt, depends on the agent complying
#   NONE  no control of any kind exists at this layer

CONTROL_MAP = {
    "sanitise_customer_message": dict(
        layer="Input", surface="The customer's message, as typed",
        kind="WALL", where="intake_agent(), engine.py",
        stops="Instructions hidden inside a customer message"),
    "sanitise_retrieved_content": dict(
        layer="Retrieval", surface="Help centre articles the agent reads",
        kind="WALL", where="policy_agent(), engine.py, on the search result",
        stops="Instructions planted in a help centre article"),
    "memory_write_review": dict(
        layer="Memory", surface="The persistent customer-notes store",
        kind="WALL", where="policy_agent(), engine.py, before the note is read",
        stops="A note written in an earlier session steering a later one"),
    "scoped_customer_lookup": dict(
        layer="Identity and data scope", surface="lookup_customer",
        kind="WALL", where="lookup_customer(), tools.py",
        stops="Reading a customer who is not the one in this conversation"),
    "check_history_before_refund": dict(
        layer="Action history", surface="Prior refunds on the same order",
        kind="WALL", where="policy_agent(), engine.py",
        stops="The same order being refunded more than once"),
    "human_approval_gate": dict(
        layer="Approval", surface="Escalation to a person",
        kind="SIGN", where="refund_execution_agent(), engine.py",
        stops="An action proceeding without a person seeing it"),
    "email_recipient_allowlist": dict(
        layer="Egress", surface="send_customer_email, the only irreversible tool",
        kind="WALL", where="send_customer_email(), tools.py",
        stops="A confirmation going to an address the customer did not give"),
    "log_full_context": dict(
        layer="Logging", surface="The assembled context, written to the trace",
        kind="WALL", where="Trace.add(), trace.py",
        stops="Nothing. It is what lets you reconstruct a run afterwards"),
}

# The ceiling is not a toggle, which is exactly why it is worth naming.
CEILING = dict(
    layer="Tool authority", surface="issue_refund, the amount argument",
    kind="WALL", where="issue_refund(), tools.py, before the payments API",
    stops="A refund larger than the ceiling, from any path",
    state="ALWAYS ON, not a toggle")

LAYER_ORDER = ["Input", "Retrieval", "Memory", "Identity and data scope",
               "Tool authority", "Action history", "Approval", "Egress",
               "Logging"]

# Which control is the named defence for each attack in the library.
SHORT_TITLE = {
    "A1": "Poisoned help centre article",
    "A2": "Injected instruction in the message",
    "A3": "Poisoned customer note",
    "A4": "Split refund under the gate",
    "A5": "Injected email recipient",
}

ATTACK_CONTROL = {
    "A1": "sanitise_retrieved_content",
    "A2": "sanitise_customer_message",
    "A3": "memory_write_review",
    "A4": "check_history_before_refund",
    "A5": "email_recipient_allowlist",
}

RULE = "=" * 78
THIN = "-" * 78


def _state(name):
    return "ON " if getattr(Controls(), name) else "OFF"


# ------------------------------------------------------------------ reports

def surface():
    """Every attack in the library, with the control that answers it."""
    print(RULE)
    print("ATTACK SURFACE: is there a control, and is it on?")
    print(RULE)
    print("Read from the shipped defaults in config.py. No attack is run here.")
    print()

    print("%-4s %-38s %-30s %s" % ("ID", "ATTACK", "THE CONTROL FOR IT", "DEFAULT"))
    print(THIN)
    off = 0
    for aid, ctrl in sorted(ATTACK_CONTROL.items()):
        st = _state(ctrl)
        if st.strip() == "OFF":
            off += 1
        print("%-4s %-38s %-30s %s" % (aid, SHORT_TITLE[aid], ctrl, st))
    print(THIN)
    print("Attacks in the library: %d" % len(ATTACK_CONTROL))
    print("Attacks with a control that exists: %d" % len(ATTACK_CONTROL))
    print("Attacks whose control is OFF by default: %d of %d"
          % (off, len(ATTACK_CONTROL)))
    print()
    print("Runs on:")
    for aid in sorted(ATTACK_CONTROL):
        a = scenarios.ATTACKS[aid]
        print("   %-4s %-38s %s" % (aid, SHORT_TITLE[aid], ", ".join(a["runs_on"])))
    print()
    print("Nothing above is missing. Every one of these controls is written,")
    print("tested and shipped. The question this lab asks is who decided to")
    print("leave them off, and where that decision is written down.")
    print(RULE)
    return len(ATTACK_CONTROL), off


def layers():
    """Coverage layer by layer, from the inbound message to the log."""
    rows = []
    for name, meta in CONTROL_MAP.items():
        rows.append(dict(meta, control=name, state=_state(name)))
    rows.append(dict(CEILING, control="refund_ceiling"))
    rows.sort(key=lambda r: LAYER_ORDER.index(r["layer"]))

    print(RULE)
    print("CONTROL COVERAGE BY LAYER")
    print(RULE)
    print("%-24s %-30s %-6s %s" % ("LAYER", "CONTROL", "KIND", "STATE"))
    print(THIN)
    for r in rows:
        print("%-24s %-30s %-6s %s" % (r["layer"], r["control"], r["kind"],
                                       r["state"]))
    print(THIN)

    walls = sum(1 for r in rows if r["kind"] == "WALL")
    on = sum(1 for r in rows if r["state"].strip() in ("ON", "ALWAYS ON, not a toggle"))
    print("Layers with a control of any kind: %d of %d" % (len(rows), len(LAYER_ORDER)))
    print("Enforced in code (WALL): %d      Stated only (SIGN): %d"
          % (walls, len(rows) - walls))
    print("On in the shipped configuration: %d of %d" % (on, len(rows)))
    print()

    print("WHERE EACH ONE LIVES, if you want to go and read it")
    print(THIN)
    for r in rows:
        print("%-24s %s" % (r["layer"], r["where"]))
        print("%-24s stops: %s" % ("", r["stops"]))
    print(RULE)
    return len(rows), on


def tool_exposure():
    """Which tools change the world, and which of those cannot be undone."""
    print(RULE)
    print("TOOL EXPOSURE")
    print(RULE)
    print("%-26s %-12s %-11s %-7s %s" % ("TOOL", "CLASS", "REVERSIBLE", "ACCESS", "AGENT"))
    print(THIN)
    irreversible = []
    for t in tools.REGISTRY:
        rev = t.get("reversible", "n/a")
        print("%-26s %-12s %-11s %-7s %s"
              % (t["name"], t["tool_class"], rev, t["access"], t["agent"]))
        if rev == "no":
            irreversible.append(t["name"])
    print(THIN)
    print("Tools in the registry: %d" % len(tools.REGISTRY))
    print("Irreversible: %d  %s" % (len(irreversible), ", ".join(irreversible)))
    print()
    print("An irreversible tool is where a threat model earns its keep. Once")
    print("that call returns, no control downstream of it can help you.")
    print(RULE)
    return len(tools.REGISTRY), irreversible


def report():
    """All three, in the order the lab uses them."""
    surface()
    print()
    layers()
    print()
    tool_exposure()

# ---------------------------------------------------- the AML.CS0037 walk
# Five steps of a real documented attack, asked of this system one at a time.
# Each step prints evidence, not a verdict. The verdict is the student's.

CASE = "AML.CS0037  Data Exfiltration via Agent Tools in Copilot Studio"

_STEPS = {
    1: ("They emailed the address the agent watches, and got a reply",
        "Input"),
    2: ("They got the agent to reveal its own tools and data sources",
        None),
    3: ("They made it return an entire knowledge base file",
        "Retrieval"),
    4: ("They made it return the customer records",
        "Identity and data scope"),
    5: ("They made it email everything to an outside address",
        "Egress"),
}


def _control_for(layer):
    if layer is None:
        return None, None
    for name, meta in CONTROL_MAP.items():
        if meta["layer"] == layer:
            return name, _state(name)
    if CEILING["layer"] == layer:
        return "refund_ceiling", "ALWAYS ON"
    return None, None


def _header(n):
    what, layer = _STEPS[n]
    print(RULE)
    print("STEP %d OF THE ATTACK" % n)
    print(RULE)
    print("In the case study: %s." % what)
    print()
    print("In SupportFlow:")
    print(THIN)


def _footer(n):
    what, layer = _STEPS[n]
    ctrl, st = _control_for(layer)
    print(THIN)
    if ctrl is None:
        print("THE CONTROL FOR THIS LAYER:  none")
        print("SWITCHED ON?                 n/a. No control in this system")
        print("                             covers this step.")
    else:
        print("THE CONTROL FOR THIS LAYER:  %s" % ctrl)
        print("AT THE LAYER:                %s" % layer)
        print("SWITCHED ON?                 %s" % st.strip())
    print(RULE)
    return ctrl, (st.strip() if st else None)


def step1():
    """Does a message from outside reach the agent, and does the agent reply?"""
    _header(1)
    comms = [t for t in tools.REGISTRY if t["agent"] == "comms"]
    print("Every run ends with the comms agent. Its tools:")
    for t in comms:
        print("   %-22s class %-12s reversible %s"
              % (t["name"], t["tool_class"], t["reversible"]))
    print()
    print("The inbound side is the customer's own message, free text, taken")
    print("as written. Example, scenario S1:")
    print()
    for line in _wrap(scenarios.SCENARIOS["S1"]["message"]):
        print("   " + line)
    return _footer(1)


def step2():
    """Does the system treat its own configuration as sensitive?"""
    _header(2)
    print("The agent's full tool list, its classes and its access, all")
    print("readable without any special permission:")
    print()
    print("   %-22s %-12s %-7s %s" % ("TOOL", "CLASS", "ACCESS", "AGENT"))
    for t in tools.REGISTRY:
        print("   %-22s %-12s %-7s %s"
              % (t["name"], t["tool_class"], t["access"], t["agent"]))
    print()
    print("And the instructions each agent is given, in full, in prompts.py.")
    print("Nothing in this system marks any of that as confidential.")
    return _footer(2)


def step3():
    """Can the agent be made to return knowledge base content?"""
    _header(3)
    hc = data.HELP_CENTER
    print("search_help_center reads a corpus of %d articles." % len(hc))
    print("From the tool registry: \"%s\""
          % next(t["notes"] for t in tools.REGISTRY
                 if t["name"] == "search_help_center"))
    print()
    print("The articles it can return:")
    for a in hc:
        print("   %-10s %s" % (a["article_id"], a["title"]))
    return _footer(3)


def step4():
    """What comes back when the agent looks a customer up?"""
    _header(4)
    print("From the tool registry: \"%s\""
          % next(t["notes"] for t in tools.REGISTRY
                 if t["name"] == "lookup_customer"))
    print()
    cid = next(iter(data.CUSTOMERS))
    rec = data.CUSTOMERS[cid]
    print("One call to lookup_customer returns all of this:")
    print()
    for k, v in rec.items():
        print("   %-22s %s" % (k, v))
    print()
    print("%d fields. The reply the customer sees uses two or three of them."
          % len(rec))
    print("There are %d customers in the store." % len(data.CUSTOMERS))
    return _footer(4)


def step5():
    """Who decides where the agent's email goes?"""
    _header(5)
    t = next(x for x in tools.REGISTRY if x["name"] == "send_customer_email")
    print("send_customer_email")
    print("   parameters:   %s" % ", ".join(t["params"]))
    print("   class:        %s" % t["tool_class"])
    print("   reversible:   %s" % t["reversible"])
    print("   registry note: \"%s\"" % t["notes"])
    print()
    irr = [x["name"] for x in tools.REGISTRY if x["reversible"] == "no"]
    print("Of the %d tools in this system, %d cannot be undone: %s."
          % (len(tools.REGISTRY), len(irr), ", ".join(irr)))
    print("The recipient is the first parameter, and nothing in the tool")
    print("compares it to the address on the account.")
    return _footer(5)


def _wrap(text, width=68):
    words, line, out = text.split(), "", []
    for w in words:
        if len(line) + len(w) + 1 > width:
            out.append(line)
            line = w
        else:
            line = (line + " " + w).strip()
    if line:
        out.append(line)
    return out


def case_walk():
    """All five steps, in order."""
    print("Walking %s against SupportFlow.\n" % CASE)
    return [step1(), step2(), step3(), step4(), step5()]


def panel():
    """Every control in the system and whether it is switched on."""
    print(RULE)
    print("THE WHOLE CONTROL PANEL")
    print(RULE)
    rows = []
    for name, meta in CONTROL_MAP.items():
        rows.append((meta["layer"], name, _state(name).strip()))
    rows.append((CEILING["layer"], "refund_ceiling", "ON"))
    rows.sort(key=lambda r: LAYER_ORDER.index(r[0]))
    print("%-24s %-30s %s" % ("LAYER", "CONTROL", "STATE"))
    print(THIN)
    for layer, name, st in rows:
        print("%-24s %-30s %s" % (layer, name, st))
    print(THIN)
    on = [r for r in rows if r[2] == "ON"]
    print("%d controls. %d are switched on:" % (len(rows), len(on)))
    for layer, name, _ in on:
        print("   %-30s at the %s layer" % (name, layer))
    print()
    print("Two of those prevent something from happening. The third only")
    print("writes down that it happened.")
    print(RULE)
    return len(rows), len(on)
