"""Bridge to the Microsoft Agent Governance Toolkit.

AGT is an MIT-licensed toolkit from Microsoft for governing autonomous
agents. Two parts of it are used in this course.

**The red-team scanner** grades a set of system prompts against twelve
prompt-attack vectors and returns a letter grade. Point it at SupportFlow's
own instructions and see what they score.

**The policy engine** turns a YAML file into enforcement. An action the
policy denies does not fail sometimes; it cannot happen. That distinction is
the whole point.

Nothing here is required to run SupportFlow. It is the tooling students use
to assess it.

Reference: https://github.com/microsoft/agent-governance-toolkit
"""

import os
import shutil
import subprocess
import sys

from . import prompts

PINNED = "4.1.0"
_MIN_PY = (3, 11)

VECTORS = [
    "role-escape", "instruction-override", "data-leakage",
    "output-manipulation", "multilang-bypass", "unicode-attack",
    "context-overflow", "indirect-injection", "social-engineering",
    "output-weaponization", "abuse-prevention", "input-validation",
]

ACTIONS = ["allow", "deny", "audit", "block", "escalate", "rate_limit"]
OPERATORS = ["eq", "ne", "gt", "lt", "gte", "lte", "in", "not_in",
             "matches", "contains"]

POLICY_STARTER = """\
# SupportFlow authority boundary, starter file.
#
# This is the same decision as the authority matrix, written as something
# that executes. Every rule is evaluated in code before the agent's intent
# reaches the tool. An action this file denies is not unlikely. It cannot
# happen.
#
# Actions you may use:   allow  deny  audit  block  escalate  rate_limit
# Operators you may use: eq ne gt lt gte lte in not_in matches contains
#
# Check your edits before you rely on them:   agt lint-policy .

version: "1.0"
name: supportflow-authority-boundary
default_action: allow

rules:

  # Money leaving the company is the action that matters most.
  - name: refund-ceiling
    description: "Refunds above the ceiling are not the agent's to make."
    condition:
      field: refund.amount
      operator: gt
      value: 200
    action: deny

  # Irreversible and external. The recipient is a free parameter, which is
  # precisely why a human should see it.
  - name: outbound-email-to-a-human
    description: "Email cannot be recalled once it is sent."
    condition:
      field: tool.name
      operator: eq
      value: send_customer_email
    action: escalate

  # ------------------------------------------------------------------
  # Your turn. Three findings from Lab 2, none of them fixed yet.
  #
  #  1. The service account can read ANY customer record, not only the
  #     one in this conversation. Write the rule that stops it.
  #
  #  2. Nothing prevents two refunds against the same order in separate
  #     conversations. You watched this pay out $400 on a $400 order.
  #     Write the rule that stops it.
  #
  #  3. Exactly one tool in the registry is marked REVERSIBLE = no.
  #     Decide whether your policy treats it differently from the others,
  #     and write a description saying why.
  #
  # Then run the console again and show that the behaviour changed.
  # ------------------------------------------------------------------
"""


def _too_old():
    return sys.version_info < _MIN_PY


def available():
    """Is the agt CLI on the path?"""
    return shutil.which("agt") is not None


def install_hint():
    if _too_old():
        return (f"AGT needs Python {_MIN_PY[0]}.{_MIN_PY[1]} or newer. This "
                f"interpreter is {sys.version_info.major}."
                f"{sys.version_info.minor}. Google Colab is fine; a local "
                f"Python may not be.")
    return (f'Install it with:\n'
            f'    pip install "agent-governance-toolkit=={PINNED}"\n'
            f'Pinned deliberately: AGT is in public preview and says '
            f'breaking changes are possible.')


def scan(folder="prompts", min_grade="C", write=True):
    """Grade SupportFlow's agent instructions for prompt-attack defences.

    Writes the five prompts to `folder`, runs the AGT red-team scanner over
    them, and returns the report as text.
    """
    if not available():
        return "The agt CLI is not installed.\n\n" + install_hint()
    if write:
        prompts.write_files(folder)
    try:
        res = subprocess.run(
            ["agt", "red-team", "scan", folder, "--min-grade", min_grade],
            capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired:
        return "The scan timed out."
    return (res.stdout or "") + (res.returncode and res.stderr or "")


def lint(policy="policy.yaml"):
    """Check a policy file for mistakes before you rely on it."""
    if not available():
        return "The agt CLI is not installed.\n\n" + install_hint()
    target = policy if os.path.isdir(policy) else os.path.dirname(policy) or "."
    res = subprocess.run(["agt", "lint-policy", target],
                         capture_output=True, text=True, timeout=120)
    return (res.stdout or "") + (res.stderr or "")


def write_policy_starter(path="policy.yaml", overwrite=False):
    """Drop the starter policy file next to the notebook."""
    if os.path.exists(path) and not overwrite:
        return f"{path} already exists. Pass overwrite=True to replace it."
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(POLICY_STARTER)
    return (f"Wrote {path}\n\nTwo rules are written for you. Three findings "
            f"are left as TODO.\nOpen the file, finish it, then run:  "
            f"agt lint-policy .")


def doctor():
    """Report whether the toolkit is healthy in this environment."""
    if not available():
        return "The agt CLI is not installed.\n\n" + install_hint()
    res = subprocess.run(["agt", "doctor"], capture_output=True,
                         text=True, timeout=120)
    return (res.stdout or "") + (res.stderr or "")
