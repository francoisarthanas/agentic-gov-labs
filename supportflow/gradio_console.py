"""The SupportFlow v2 Governance Console, Gradio edition.

Same engine, same determinism, same config_hash. The difference is that this
looks like the production system a governance lead would be handed, rather
than a stack of notebook widgets.

Falls back to the ipywidgets console if Gradio is unavailable:

    import supportflow as sf
    sf.launch()          # picks the best available interface
"""

from . import config as _config
from . import data, scenarios, tools
from .config import AUTONOMY, LEVELS, Config, Controls
from .engine import run as _run

CONTROL_KEYS = list(Controls().as_dict().keys())

# Readable label first, because the audience is governance, not engineering.
# The identifier stays in the help line: students need it for the control
# audit sheet and for policy.yaml, and it has to match exactly.
CONTROL_LABELS = {
    "human_approval_gate": "Human approval gate",
    "check_history_before_refund": "Check refund history first",
    "sanitise_retrieved_content": "Sanitise retrieved content",
    "sanitise_customer_message": "Sanitise customer message",
    "memory_write_review": "Review memory writes",
    "email_recipient_allowlist": "Email recipient allowlist",
    "scoped_customer_lookup": "Scoped customer lookup",
    "log_full_context": "Log full context",
}

CONTROL_HELP = {
    "human_approval_gate": "Refunds above the ceiling require a human to approve",
    "check_history_before_refund": "Look at prior refunds before issuing another",
    "sanitise_retrieved_content": "Strip instruction-like text from help centre results",
    "sanitise_customer_message": "Strip instruction-like text from the customer's message",
    "memory_write_review": "Review a note before it is written to persistent memory",
    "email_recipient_allowlist": "Restrict outbound email to the address on the account",
    "scoped_customer_lookup": "Restrict lookups to the customer in this conversation",
    "log_full_context": "Write the assembled context to the trace",
}


def _control_label(key):
    return CONTROL_LABELS.get(key, key.replace("_", " ").capitalize())


def _control_info(key):
    return f"{CONTROL_HELP.get(key, '')}  ·  {key}"

_TRACE_HEADERS = ["#", "agent", "phase", "tool", "changed state?",
                  "reversible", "reasoning"]


class _State:
    """Holds the last run so the viewers and the export can see it."""
    last = None
    cfg = None


def _build_config(level, ceiling, attack, toggles):
    return Config(autonomy=level,
                  refund_ceiling=float(ceiling),
                  attack=attack,
                  controls=Controls(**dict(zip(CONTROL_KEYS, toggles))))


def _trace_rows(ctx):
    rows = []
    for r in ctx.trace.rows:
        rows.append([
            r["step"],
            r["agent"],
            r["phase"],
            r.get("tool") or "",
            "YES" if r.get("state_change") else "",
            r.get("reversible") or "",
            r["reasoning"],
        ])
    return rows


def _summary(ctx, cfg, second_contact=False):
    t = ctx.trace
    lvl = AUTONOMY[cfg.autonomy]
    head = ("SECOND CONTACT: refund ledger carried over from the previous run\n\n"
            if second_contact else "")
    return (
        f"{head}OUTCOME    {ctx.outcome}\n"
        f"{'-' * 62}\n"
        f"Autonomy   {cfg.autonomy}  (MGF level {lvl['mgf_level']}: {lvl['mgf_wording']})\n"
        f"Ceiling    ${cfg.refund_ceiling:,.0f}\n"
        f"Steps {len(t.rows)}   Tools called {len(t.tools_called)}   "
        f"Actions that changed state {len(t.action_flows)}   "
        f"Irreversible {len(t.irreversible_actions)}\n"
        f"config_hash  {cfg.config_hash}"
    )


def _controls_line(cfg):
    on = [k for k, v in cfg.controls.as_dict().items() if v]
    off = [k for k, v in cfg.controls.as_dict().items() if not v]
    return (f"**{len(on)} of {len(CONTROL_KEYS)} controls are ON.**\n\n"
            f"ON: {', '.join(on) or 'none'}\n\n"
            f"OFF: {', '.join(off) or 'none'}")


# --------------------------------------------------------------- handlers
# Module level on purpose: the Console and the instructor verification suite
# call exactly the same code, so what a student sees is what gets checked.

def go(scenario, level, ceiling, attack, *toggles):
    """Run scenario. Clears the refund ledger first."""
    cfg = _build_config(level, ceiling, attack, toggles)
    tools.reset_ledger()
    ctx = _run(scenarios.get(scenario, attack), cfg, reset=True)
    _State.last, _State.cfg = ctx, cfg
    return _summary(ctx, cfg), _controls_line(cfg), _trace_rows(ctx)


def again(scenario, level, ceiling, attack, *toggles):
    """Run again without clearing the ledger, as if the customer came back."""
    cfg = _build_config(level, ceiling, attack, toggles)
    ctx = _run(scenarios.get(scenario, attack), cfg, reset=False)
    _State.last, _State.cfg = ctx, cfg
    return (_summary(ctx, cfg, second_contact=True),
            _controls_line(cfg), _trace_rows(ctx))


def briefing(scenario):
    """The ticket, as a support agent would receive it.

    A scenario is one customer contacting support once. This is what the
    agent is given before it does anything.
    """
    s = scenarios.SCENARIOS[scenario]
    cust = data.CUSTOMERS.get(s["customer_id"], {})
    order = data.ORDERS.get(s["order_number"], {})
    name = cust.get("full_name", s["customer_id"])
    total = order.get("total")
    return (
        f"### Incoming ticket · {s['id']}\n\n"
        f"**{name}** · order `{s['order_number']}`"
        + (f" · order value **${total:,.2f}**" if total else "") + "\n\n"
        f"> {s['message']}\n\n"
        f"**They are asking for ${s['requested_amount']:,.2f}.** "
        f"Reason code recorded as `{s['reason_code']}`.\n\n"
        f"Press **Run scenario** and watch what the agent does with it."
    )


def memory(scenario, attack):
    """Persistent customer notes for the scenario's customer."""
    cid = scenarios.SCENARIOS[scenario]["customer_id"]
    notes = list(data.CUSTOMER_NOTES.get(cid, []))
    if attack == "A3":
        poisoned = data.CUSTOMER_NOTES_POISONED.get(cid)
        if poisoned:
            notes.append(poisoned)
    body = "\n".join("  " + n for n in notes) or "  (no notes)"
    return f"PERSISTENT CUSTOMER NOTES: {cid}\n{'-' * 62}\n{body}"


def export(folder="evidence"):
    """Write the last run's evidence bundle to disk."""
    import os
    if _State.last is None:
        return "Run a scenario first."
    os.makedirs(folder, exist_ok=True)
    written = []
    for name, body in _State.last.trace.evidence_bundle().items():
        path = os.path.join(folder, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(body)
        written.append(f"  {path}  ({len(body):,} bytes)")
    return ("EVIDENCE BUNDLE WRITTEN\n" + "-" * 62 + "\n"
            + "\n".join(written)
            + f"\n\nconfig_hash {_State.cfg.config_hash}"
            + "\nAttach these to your VerifyWise record.")


def build(share=False):
    """Construct the Gradio Blocks app. Returns the demo without launching."""
    import gradio as gr

    scen_choices = [(f"{s['id']}  {s['title']}", s["id"])
                    for s in scenarios.SCENARIOS.values()]
    atk_choices = [(f"{a['id']}  {a['title']}", a["id"])
                   for a in scenarios.ATTACKS.values()]
    auto_choices = [(f"{l}  {AUTONOMY[l]['mgf_wording']}", l) for l in LEVELS]

    with gr.Blocks(title="SupportFlow v2 Governance Console") as demo:

        gr.Markdown(
            "# SupportFlow v2 · Governance Console\n"
            "NorthWind Retail · agentic refund and resolution · **live in "
            "three regions, handling 61% of refund tickets**\n\n"
            "### You are the governance lead reviewing this system.\n"
            "The case packet tells you what SupportFlow is **supposed** to do. "
            "**This console is how you find out whether that is true.**"
        )

        with gr.Accordion("What am I looking for?", open=False):
            gr.Markdown(
                "Your job is not to admire the system. It is to test the "
                "claims made about it.\n\n"
                "The case packet is full of statements like these. Each one "
                "sounds like a control. **Only some of them are.**\n\n"
                "| The packet says | How you check it here |\n"
                "| :---- | :---- |\n"
                "| *\"Refunds above the ceiling must be escalated.\"* | Raise "
                "the autonomy level and leave the ceiling alone. Did anything "
                "change? |\n"
                "| *\"Do not split a resolution into multiple smaller "
                "actions.\"* | Run a scenario, then press **Run again (same "
                "day)** and add up what was paid. |\n"
                "| *\"Only discuss the account belonging to the person you "
                "are speaking with.\"* | Look at the tool registry. What "
                "would stop it reading another record? |\n\n"
                "A control you can switch off and watch fail is **enforced**. "
                "A control that is only written down is a **request**. "
                "Telling those apart is the whole job, and it is what the "
                "next six weeks are for.\n\n"
                "*Nothing here is real. No money moves and no email is sent.*"
            )

        with gr.Tab("Console"):
            gr.Markdown(
                "**A scenario is one customer contacting support once.** "
                "Pick one, set how much freedom the agent has, then press "
                "**Run scenario** and read what it did.")
            scn = gr.Dropdown(scen_choices, value="S1", label="Scenario")
            brief = gr.Markdown(briefing("S1"))
            with gr.Row():
                lvl = gr.Dropdown(auto_choices, value="L3",
                                  label="Autonomy level", scale=3)
                ceil = gr.Slider(0, 1000, value=200, step=50,
                                 label="Refund ceiling ($), enforced in tool code",
                                 scale=3)

            gr.Markdown(
                "### Controls\n"
                "*Eight safeguards, each independent. Switch one off, run "
                "again, and see whether the outcome changes. If it does not, "
                "ask what that control was doing.*")
            boxes = []
            defaults = Controls().as_dict()
            keys = list(defaults)
            for i in range(0, len(keys), 2):
                with gr.Row():
                    for k in keys[i:i + 2]:
                        boxes.append(gr.Checkbox(
                            value=defaults[k], label=_control_label(k),
                            info=_control_info(k)))

            with gr.Accordion("Attack simulation · used in Week 4",
                              open=False):
                gr.Markdown(
                    "Arms an adversarial scenario. **Leave this on "
                    "'No attack' until Week 4.** It is here so you can see "
                    "the whole control surface, not because you need it yet.")
                atk = gr.Dropdown(atk_choices, value="none", label="Attack")

            with gr.Row():
                run_btn = gr.Button("Run scenario", variant="primary", scale=2)
                again_btn = gr.Button("Run again (same day)", scale=2)
                gr.Markdown("*Run again keeps the refund ledger, as if the "
                            "customer came back a second time.*")

            outcome = gr.Textbox(label="Outcome", lines=7)
            ctrl_md = gr.Markdown()
            trace = gr.Dataframe(headers=_TRACE_HEADERS, label="Trace",
                                 wrap=True, row_count=(1, "dynamic"))

        with gr.Tab("Tool registry"):
            gr.Markdown("**Nine tools, plus the control tool.** Note the "
                        "`ACCESS` and `REVERSIBLE` columns.")
            gr.Code(tools.registry_table(), language=None)

        with gr.Tab("Refund SOP"):
            gr.Markdown("The written policy the agents are told to follow.")
            gr.Code(data.REFUND_SOP, language=None)

        with gr.Tab("Agent instructions"):
            gr.Markdown("What each of the five agents is told to do.")
            prompts_md = gr.Markdown(_prompts_markdown())

        with gr.Tab("Memory"):
            gr.Markdown("What the agent remembers about people between "
                        "conversations.")
            mem_btn = gr.Button("Show notes for the selected scenario")
            mem_out = gr.Code(label="Persistent customer notes", language=None)

        with gr.Tab("Evidence"):
            gr.Markdown("Export a timestamped bundle of the last run: the "
                        "JSONL trace, the CSV, the config and the summary.")
            exp_btn = gr.Button("Export evidence bundle", variant="primary")
            exp_out = gr.Textbox(label="Export", lines=8)

        # ------------------------------------------------------------ wiring
        inputs = [scn, lvl, ceil, atk] + boxes
        outputs = [outcome, ctrl_md, trace]
        run_btn.click(go, inputs, outputs)
        again_btn.click(again, inputs, outputs)
        mem_btn.click(memory, [scn, atk], mem_out)
        exp_btn.click(lambda: export(), None, exp_out)
        scn.change(briefing, scn, brief)

    return demo


def _prompts_markdown():
    """Render the five agent prompts, read from the running package."""
    try:
        from . import prompts_text
        return prompts_text.MARKDOWN
    except Exception:
        return ("The agent instructions live in the case packet document "
                "`SupportFlow_v2_System_Prompts`. Open it alongside this "
                "console.")


def in_colab():
    try:
        import google.colab  # noqa: F401
        return True
    except ImportError:
        return False


def launch(share=None, height=900, **kwargs):
    """Open the Governance Console.

    Gradio if it is installed, ipywidgets otherwise. Both drive the same
    engine, so the results and the config_hash are identical either way.

    In Colab this defaults to `share=True`. Gradio's inline proxy renders
    an empty frame often enough that a shared link is the reliable path,
    and everything in this app is fictional and ephemeral.

    Returns None on purpose. Returning the Blocks object makes Jupyter
    print its repr, which buries the console under a wall of component
    addresses.
    """
    try:
        import gradio  # noqa: F401
    except ImportError:
        from . import console
        print("Gradio is not installed, using the widget console instead.\n"
              "Same engine, same results. To get the full console:\n"
              "    pip install 'gradio>=6.0,<7.0'")
        console.launch()
        return None

    if share is None:
        share = in_colab()

    demo = build()
    opts = dict(share=share, inline=True, height=height,
                quiet=False, debug=False, show_error=True)
    opts.update(kwargs)

    try:
        demo.launch(**opts)
    except TypeError:
        demo.launch(share=share, inline=True)
    except Exception as exc:                       # tunnel blocked, etc.
        print(f"\nCould not open a shared link ({type(exc).__name__}). "
              f"Trying the inline frame instead.")
        try:
            demo.launch(share=False, inline=True, height=height, quiet=False)
        except Exception:
            from . import console
            print("Gradio could not start. Using the widget console.\n"
                  "Same engine, same results.")
            console.launch()
    return None
