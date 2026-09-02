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

CONTROL_HELP = {
    "human_approval_gate": "Refunds above the ceiling require a human to approve",
    "refund_ceiling": "Hard cap enforced in the tool wrapper",
    "check_history_before_refund": "Look at prior refunds before issuing another",
    "sanitise_retrieved_content": "Strip instruction-like text from help centre results",
    "sanitise_customer_message": "Strip instruction-like text from the customer's message",
    "memory_write_review": "Review a note before it is written to persistent memory",
    "email_recipient_allowlist": "Restrict outbound email to the address on the account",
    "scoped_customer_lookup": "Restrict lookups to the customer in this conversation",
    "log_full_context": "Write the assembled context to the trace",
}

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
    head = "SECOND CONTACT — refund ledger carried over\n\n" if second_contact else ""
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
            "NorthWind Retail · agentic refund and resolution · **live in three "
            "regions**\n\n"
            "*Everything here is a dropdown, a slider, a checkbox or a button. "
            "Nothing requires code.*"
        )

        with gr.Tab("Console"):
            with gr.Row():
                scn = gr.Dropdown(scen_choices, value="S1", label="Scenario",
                                  scale=3)
                atk = gr.Dropdown(atk_choices, value="none", label="Attack",
                                  scale=3)
            with gr.Row():
                lvl = gr.Dropdown(auto_choices, value="L3",
                                  label="Autonomy level", scale=3)
                ceil = gr.Slider(0, 1000, value=200, step=50,
                                 label="Refund ceiling ($) — enforced in tool code",
                                 scale=3)

            gr.Markdown("### Controls")
            boxes = []
            defaults = Controls().as_dict()
            keys = list(defaults)
            for i in range(0, len(keys), 2):
                with gr.Row():
                    for k in keys[i:i + 2]:
                        boxes.append(gr.Checkbox(
                            value=defaults[k], label=k,
                            info=CONTROL_HELP.get(k, "")))

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


def launch(share=False, height=900, **kwargs):
    """Launch the best available console.

    Gradio if it is installed, ipywidgets otherwise. Both drive the same
    engine, so the results and the config_hash are identical either way.

    In Colab the app renders in an inline frame. `height` matters: the
    console has six tabs and a trace table, and Gradio's default frame is
    too short to show them without scrolling inside a scroll.
    """
    try:
        import gradio  # noqa: F401
    except ImportError:
        from . import console
        print("Gradio is not installed, using the widget console instead.\n"
              "Same engine, same results. To get the full console:\n"
              "    pip install 'gradio>=6.0,<7.0'")
        return console.launch()

    demo = build()
    opts = dict(share=share, inline=True, height=height,
                quiet=False, debug=False)
    opts.update(kwargs)
    try:
        demo.launch(**opts)
    except TypeError:
        # Older Gradio does not accept every option above.
        demo.launch(share=share, inline=True)
    return demo
