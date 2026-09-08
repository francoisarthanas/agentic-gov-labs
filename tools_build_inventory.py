"""Regenerate docs/supportflow_control_inventory.md from the running code.

The inventory is what a reviewer gets handed instead of a shell. Generating it
from config.py and tools.py means it cannot drift from the system it describes.

    python3 tools_build_inventory.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from supportflow import threatmodel as T, tools, scenarios
from supportflow.config import Controls

ORDER = T.LAYER_ORDER
rows = []
for name, meta in T.CONTROL_MAP.items():
    rows.append(dict(meta, control=name,
                     state="ON" if getattr(Controls(), name) else "OFF"))
rows.append(dict(T.CEILING, control="refund_ceiling", state="ALWAYS ON"))
rows.sort(key=lambda r: ORDER.index(r["layer"]))

on = sum(1 for r in rows if r["state"] in ("ON", "ALWAYS ON"))
walls = sum(1 for r in rows if r["kind"] == "WALL")

L = []
w = L.append
w("# SupportFlow control inventory")
w("")
w("**NorthWind Home Goods · agentic refund and resolution · live in three "
  "regions, handling 61% of refund tickets.**")
w("")
w("This page is generated from the running system. It is the documentation a "
  "reviewer would be handed: what controls exist, where each one is enforced, "
  "and whether it is switched on in the configuration that ships.")
w("")
w("---")
w("")
w("## 1. Controls, by layer")
w("")
w("| Layer | Control | Enforced in code or written down | On in the shipped configuration |")
w("|---|---|---|---|")
for r in rows:
    kind = "**Code**" if r["kind"] == "WALL" else "Written down"
    st = "**ON**" if r["state"] in ("ON", "ALWAYS ON") else "**OFF**"
    if r["state"] == "ALWAYS ON":
        st = "**ON**, and not switchable"
    w(f"| {r['layer']} | `{r['control']}` | {kind} | {st} |")
w("")
w(f"**{len(rows)} of {len(ORDER)} layers have a control. "
  f"{walls} are enforced in code. {on} of {len(rows)} are on.**")
w("")
w("## 2. What each control stops, and where it lives")
w("")
w("| Control | What it stops | Where it is enforced |")
w("|---|---|---|")
for r in rows:
    w(f"| `{r['control']}` | {r['stops']} | {r['where']} |")
w("")
w("## 3. The attack library, and the control built for each one")
w("")
w("Each of these is a prepared adversarial scenario that can be armed against "
  "the system.")
w("")
w("| Attack | What it does | The control for it | Default |")
w("|---|---|---|---|")
for aid in sorted(T.ATTACK_CONTROL):
    a = scenarios.ATTACKS[aid]
    c = T.ATTACK_CONTROL[aid]
    st = "**ON**" if getattr(Controls(), c) else "**OFF**"
    w(f"| **{aid}** {a['title']} | {a['description']} | `{c}` | {st} |")
w("")
off = sum(1 for c in T.ATTACK_CONTROL.values() if not getattr(Controls(), c))
w(f"**{len(T.ATTACK_CONTROL)} attacks. {len(T.ATTACK_CONTROL)} controls written "
  f"for them. {off} of those {len(T.ATTACK_CONTROL)} are off by default.**")
w("")
w("## 4. Tools the agent can call")
w("")
w("| Tool | Class | Access | Reversible | Called by |")
w("|---|---|---|---|---|")
irr = []
for t in tools.REGISTRY:
    if t["reversible"] == "no":
        irr.append(t["name"])
    w(f"| `{t['name']}` | {t['tool_class']} | {t['access']} | "
      f"**{t['reversible']}** | {t['agent']} |")
w("")
w(f"**{len(tools.REGISTRY)} tools. {len(irr)} cannot be undone: "
  + ", ".join(f"`{x}`" for x in irr) + ".**")
w("")
w("---")
w("")
w("*Every customer, order and address in this system is fictional.*")

out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "docs", "supportflow_control_inventory.md")
os.makedirs(os.path.dirname(out), exist_ok=True)
open(out, "w").write("\n".join(L) + "\n")
print("wrote", out, "|", len(L), "lines")
