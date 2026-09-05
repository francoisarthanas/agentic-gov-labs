"""The Governance Console.

The only interface a student touches. Dropdowns, sliders, toggles and two
buttons. No Python is written or edited by a student at any point.

Falls back to a text menu if ipywidgets is unavailable, so the package is
usable in any environment.
"""

import json
import os

from .config import Config, Controls, AUTONOMY, LEVELS
from . import scenarios, tools, data
from .engine import run as _run

CONTROL_LABELS = {
    "human_approval_gate": "Human approval gate",
    "check_history_before_refund": "Check refund history before refunding",
    "sanitise_retrieved_content": "Sanitise retrieved help centre content",
    "sanitise_customer_message": "Sanitise the inbound customer message",
    "memory_write_review": "Review notes before writing to memory",
    "email_recipient_allowlist": "Restrict email recipients to the account",
    "scoped_customer_lookup": "Scope customer lookup to this conversation",
    "log_full_context": "Log customer identifiers in the trace",
}


class Console:
    """Programmatic form of the Console. The widget UI drives this."""

    def __init__(self):
        self.config = Config()
        self.scenario_id = "S1"
        self.last = None

    # ------------------------------------------------------------- settings
    def set_autonomy(self, level):
        self.config.autonomy = level
        return self

    def set_ceiling(self, amount):
        self.config.refund_ceiling = float(amount)
        return self

    def set_control(self, name, value):
        setattr(self.config.controls, name, bool(value))
        return self

    def set_scenario(self, sid):
        self.scenario_id = sid
        return self

    def set_attack(self, code):
        self.config.attack = code
        return self

    # ----------------------------------------------------------------- run
    def run(self, reset=True, show=True):
        s = scenarios.get(self.scenario_id, self.config.attack)
        self.last = _run(s, self.config, instructor_mode=False, reset=reset)
        if show:
            print(self.header())
            print(self.last.trace.render())
            print()
            print(self.footer())
        return self.last

    def header(self):
        s = scenarios.SCENARIOS[self.scenario_id]
        lvl = self.config.level
        on = [k for k, v in self.config.controls.as_dict().items() if v]
        return (
            "SUPPORTFLOW v2\n"
            + "=" * 74 + "\n"
            "Scenario   %s  %s\n"
            "Autonomy   %s  (MGF level %d: %s)\n"
            "Ceiling    $%.2f tool cap   auto-approve up to $%s\n"
            "Attack     %s\n"
            "Controls   %d of 8 on: %s\n"
            "Config     %s\n"
            % (s["id"], s["title"], self.config.autonomy, lvl["mgf_level"],
               lvl["mgf_wording"], self.config.refund_ceiling,
               "unlimited" if self.config.effective_auto_ceiling == float("inf")
               else "%.2f" % self.config.effective_auto_ceiling,
               self.config.attack,
               len(on), ", ".join(on) or "none",
               self.config.config_hash)
            + "=" * 74)

    def footer(self):
        t = self.last.trace
        return ("-" * 74 + "\n"
                "OUTCOME    %s\n"
                "Steps %d   Tools called %d   Actions that changed state %d   "
                "Irreversible %d\n" % (self.last.outcome, len(t.rows),
                                       len(t.tools_called), len(t.action_flows),
                                       len(t.irreversible_actions)))

    # ------------------------------------------------------------- viewers
    def show_tools(self):
        print(tools.registry_table())

    def show_memory(self, customer_id=None):
        cid = customer_id or scenarios.SCENARIOS[self.scenario_id]["customer_id"]
        notes = list(data.CUSTOMER_NOTES.get(cid, []))
        if self.config.attack == "A3":
            p = data.CUSTOMER_NOTES_POISONED.get(cid)
            if p:
                notes.append(p)
        print("PERSISTENT CUSTOMER NOTES: %s" % cid)
        print("-" * 74)
        for n in notes:
            print("  " + n)

    def show_scenarios(self):
        print(scenarios.menu())

    def show_policy(self):
        print(data.REFUND_SOP)

    # ------------------------------------------------------------- evidence
    def export_evidence(self, folder="evidence"):
        if not self.last:
            print("Run a scenario first.")
            return None
        b = self.last.trace.evidence_bundle()
        os.makedirs(folder, exist_ok=True)
        written = []
        for name in ("trace.jsonl", "trace.csv", "config.json", "summary.json"):
            path = os.path.join(folder, "%s_%s" % (b["filename_stem"], name))
            with open(path, "w") as f:
                f.write(b[name])
            written.append(path)
        print("Evidence bundle written. Upload these to VerifyWise.")
        for p in written:
            print("  " + p)
        return written


# --------------------------------------------------------------- widget UI
def launch():
    """Render the Console. Falls back to text mode without ipywidgets."""
    c = Console()
    try:
        import ipywidgets as W
        from IPython.display import display, clear_output
    except ImportError:
        print("Widgets unavailable. Using the text console.\n")
        print(c.header())
        print("\nUse: c.set_autonomy('L4'); c.set_scenario('S2'); c.run()")
        return c

    scen = W.Dropdown(options=[(f"{s['id']}  {s['title']}", s["id"])
                               for s in scenarios.SCENARIOS.values()],
                      value="S1", description="Scenario", style={"description_width": "110px"},
                      layout=W.Layout(width="520px"))
    auto = W.Dropdown(options=[(f"{l}  {AUTONOMY[l]['mgf_wording']}", l) for l in LEVELS],
                      value="L3", description="Autonomy", style={"description_width": "110px"},
                      layout=W.Layout(width="520px"))
    ceil = W.FloatSlider(value=200.0, min=0.0, max=1000.0, step=50.0,
                         description="Ceiling $", style={"description_width": "110px"},
                         layout=W.Layout(width="520px"), continuous_update=False)
    atk = W.Dropdown(options=[(f"{a['id']}  {a['title']}", a["id"])
                              for a in scenarios.ATTACKS.values()],
                     value="none", description="Attack", style={"description_width": "110px"},
                     layout=W.Layout(width="520px"))
    boxes = {k: W.Checkbox(value=v, description=CONTROL_LABELS[k], indent=False,
                           layout=W.Layout(width="380px"))
             for k, v in c.config.controls.as_dict().items()}

    run_btn = W.Button(description="Run scenario", button_style="primary",
                       layout=W.Layout(width="170px"))
    again_btn = W.Button(description="Run again (same day)",
                         tooltip="Run the same scenario without clearing the refund "
                                 "ledger, as if the customer came back a second time.",
                         layout=W.Layout(width="180px"))
    exp_btn = W.Button(description="Export Evidence", layout=W.Layout(width="170px"))
    tools_btn = W.Button(description="Tool registry", layout=W.Layout(width="150px"))
    mem_btn = W.Button(description="Memory", layout=W.Layout(width="150px"))
    out = W.Output()

    def sync():
        c.set_scenario(scen.value).set_autonomy(auto.value)
        c.set_ceiling(ceil.value).set_attack(atk.value)
        for k, b in boxes.items():
            c.set_control(k, b.value)

    def on_run(_):
        sync()
        with out:
            clear_output()
            c.run()

    def on_again(_):
        sync()
        with out:
            clear_output()
            print("SECOND CONTACT: refund ledger carried over from the previous run.\n")
            c.run(reset=False)

    def on_exp(_):
        with out:
            clear_output()
            c.export_evidence()

    def on_tools(_):
        with out:
            clear_output()
            c.show_tools()

    def on_mem(_):
        sync()
        with out:
            clear_output()
            c.show_memory()

    run_btn.on_click(on_run); again_btn.on_click(on_again); exp_btn.on_click(on_exp)
    tools_btn.on_click(on_tools); mem_btn.on_click(on_mem)

    display(W.VBox([
        W.HTML("<h3 style='margin-bottom:2px'>SupportFlow v2 Governance Console</h3>"
               "<div style='color:#666;margin-bottom:10px'>Set the configuration, "
               "run a scenario, read the trace. Nothing here requires code.</div>"),
        scen, auto, ceil, atk,
        W.HTML("<b style='display:block;margin-top:10px'>Controls</b>"),
        W.GridBox(list(boxes.values()),
                  layout=W.Layout(grid_template_columns="repeat(2, 390px)")),
        W.HBox([run_btn, again_btn, exp_btn, tools_btn, mem_btn],
               layout=W.Layout(margin="12px 0 0 0")),
        out,
    ]))
    return c
