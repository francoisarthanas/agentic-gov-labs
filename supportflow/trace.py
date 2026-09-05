"""Structured trace for SupportFlow v2.

One JSONL object per step. Every step records what changed in the world,
whether it can be undone, which controls evaluated, and the config hash of
the run that produced it.

The config hash is what lets Lab 4 say reproduce this exact failure and
Lab 5 say this is the configuration we tested.
"""

import csv
import io
import json
import re
from datetime import datetime, timezone

# Fields that carry customer identifiers into the trace. When the
# log_full_context control is OFF these are redacted at write time, so the
# trace holds less evidence and less personal data. That trade is the point.
PII_KEYS = ("to", "recipient", "email", "phone", "shipping_address", "full_name")
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
REDACTED = "[redacted: log_full_context off]"


def _redact_args(args):
    return {k: (REDACTED if k in PII_KEYS else v) for k, v in (args or {}).items()}


def _redact_text(text):
    if text is None:
        return None
    return _EMAIL.sub("[redacted]", str(text))

FIELDS = [
    "run_id", "ts", "step", "agent", "phase", "reasoning", "tool", "tool_args",
    "tool_result_summary", "state_change", "reversible", "control_checks",
    "approval_required", "approval_outcome", "autonomy_level", "config_hash",
    "weakness_triggered",
]


class Trace:
    def __init__(self, run_id, config, instructor_mode=False):
        self.run_id = run_id
        self.config = config
        self.instructor_mode = instructor_mode
        self.rows = []
        self._step = 0

    def add(self, agent, phase, reasoning, tool=None, tool_args=None,
            tool_result_summary=None, state_change=False, reversible="n/a",
            control_checks=None, approval_required=False, approval_outcome=None,
            weakness=None):
        self._step += 1
        if not getattr(self.config.controls, "log_full_context", True):
            tool_args = _redact_args(tool_args)
            tool_result_summary = _redact_text(tool_result_summary)
        self.rows.append({
            "run_id": self.run_id,
            "ts": datetime.now(timezone.utc).isoformat(),
            "step": self._step,
            "agent": agent,
            "phase": phase,
            "reasoning": reasoning,
            "tool": tool,
            "tool_args": tool_args or {},
            "tool_result_summary": tool_result_summary,
            "state_change": state_change,
            "reversible": reversible,
            "control_checks": control_checks or [],
            "approval_required": approval_required,
            "approval_outcome": approval_outcome,
            "autonomy_level": self.config.autonomy,
            "config_hash": self.config.config_hash,
            # Off by default: the trace should show what happened, not label it
            "weakness_triggered": weakness if self.instructor_mode else None,
        })
        return self.rows[-1]

    # ---------------------------------------------------------------- output
    def to_jsonl(self):
        return "\n".join(json.dumps(r, default=str) for r in self.rows)

    def to_csv(self):
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in self.rows:
            flat = dict(r)
            flat["tool_args"] = json.dumps(r["tool_args"], default=str)
            flat["control_checks"] = "; ".join(
                "%s=%s" % (c["control"], c["verdict"]) for c in r["control_checks"]
            )
            w.writerow(flat)
        return buf.getvalue()

    # ------------------------------------------------------------- summaries
    @property
    def action_flows(self):
        """Steps that changed the state of the world. The orange arrows."""
        return [r for r in self.rows if r["state_change"]]

    @property
    def irreversible_actions(self):
        return [r for r in self.rows if r["state_change"] and r["reversible"] == "no"]

    @property
    def tools_called(self):
        return [r["tool"] for r in self.rows if r["tool"]]

    def summary(self):
        return {
            "run_id": self.run_id,
            "config_hash": self.config.config_hash,
            "autonomy": self.config.autonomy,
            "steps": len(self.rows),
            "tools_called": len(self.tools_called),
            "action_flows": len(self.action_flows),
            "irreversible_actions": len(self.irreversible_actions),
            "approvals_required": sum(1 for r in self.rows if r["approval_required"]),
        }

    def evidence_bundle(self):
        """What the Export Evidence button produces."""
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        return {
            "filename_stem": "supportflow_%s_%s" % (self.run_id, stamp),
            "trace.jsonl": self.to_jsonl(),
            "trace.csv": self.to_csv(),
            "config.json": json.dumps(self.config.snapshot(), indent=2),
            "summary.json": json.dumps(self.summary(), indent=2),
        }

    def render(self, show_reasoning=True):
        """Human-readable trace for the notebook output."""
        out = []
        for r in self.rows:
            icon = "!!" if r["state_change"] else "  "
            head = "%s [%02d] %-12s %-5s" % (icon, r["step"], r["agent"], r["phase"])
            if r["tool"]:
                args = ", ".join("%s=%r" % (k, v) for k, v in r["tool_args"].items())
                head += "  %s(%s)" % (r["tool"], args)
            out.append(head)
            if show_reasoning and r["reasoning"]:
                out.append("        %s" % r["reasoning"])
            if r["tool_result_summary"]:
                out.append("        -> %s" % r["tool_result_summary"])
            for c in r["control_checks"]:
                out.append("        [control] %s: %s" % (c["control"], c["verdict"]))
            if r["approval_required"]:
                out.append("        [approval] required, outcome: %s" % r["approval_outcome"])
        return "\n".join(out)
