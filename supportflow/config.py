"""SupportFlow v2 configuration.

The autonomy dial, the control toggles, and the thresholds. Everything a
student changes in the Governance Console lands here, and everything here
is fingerprinted into the trace so a run can be reproduced exactly.

Autonomy levels map to MGF v1.5 section 1.1.3, which defines four levels of
human involvement. Level 3 is split into two operating points, L3 and L4,
because that split is where a refund ceiling lives.
"""

import hashlib
import json
from dataclasses import dataclass, asdict, field

AUTONOMY = {
    "L1": dict(
        mgf_level=1,
        mgf_wording="Agent proposes, human operates",
        behaviour="Drafts everything. A human executes every action",
        executes_reads=False,
        executes_writes=False,
        auto_refund_ceiling=0.0,
    ),
    "L2": dict(
        mgf_level=2,
        mgf_wording="Agent and human collaborate",
        behaviour="Executes reads. Asks before any write",
        executes_reads=True,
        executes_writes=False,
        auto_refund_ceiling=0.0,
    ),
    "L3": dict(
        mgf_level=3,
        mgf_wording="Agent operates, human approves (at critical steps)",
        behaviour="Auto-refunds under $200. Escalates above",
        executes_reads=True,
        executes_writes=True,
        auto_refund_ceiling=200.0,
    ),
    "L4": dict(
        mgf_level=3,
        mgf_wording="Agent operates, human approves (by exception only)",
        behaviour="Auto-refunds up to $500. Flags anomalies only",
        executes_reads=True,
        executes_writes=True,
        auto_refund_ceiling=500.0,
    ),
    "L5": dict(
        mgf_level=4,
        mgf_wording="Agent operates, human observes",
        behaviour="Full autonomy. After-the-fact audit only",
        executes_reads=True,
        executes_writes=True,
        auto_refund_ceiling=float("inf"),
    ),
}

LEVELS = ["L1", "L2", "L3", "L4", "L5"]


@dataclass
class Controls:
    """The nine independently toggleable controls.

    Defaults are the state a rushed pilot actually ships in: somebody thought
    about money, nobody thought about attackers.
    """
    human_approval_gate: bool = True
    check_history_before_refund: bool = False
    sanitise_retrieved_content: bool = False
    sanitise_customer_message: bool = False
    memory_write_review: bool = False
    email_recipient_allowlist: bool = False
    scoped_customer_lookup: bool = False
    log_full_context: bool = True

    def as_dict(self):
        return asdict(self)


@dataclass
class Config:
    autonomy: str = "L3"
    refund_ceiling: float = 200.0
    revenue_protection_threshold: float = 150.0
    controls: Controls = field(default_factory=Controls)
    attack: str = "none"
    model_mode: str = "offline"

    def __post_init__(self):
        if self.autonomy not in AUTONOMY:
            raise ValueError("autonomy must be one of %s" % LEVELS)

    @property
    def level(self):
        return AUTONOMY[self.autonomy]

    @property
    def effective_auto_ceiling(self):
        """The lower of the dial's ceiling and the configured refund ceiling.

        The dial and the ceiling are two different controls and students should
        be able to see them disagree.
        """
        return min(self.level["auto_refund_ceiling"], self.refund_ceiling)

    def snapshot(self):
        return {
            "autonomy": self.autonomy,
            "mgf_level": self.level["mgf_level"],
            "mgf_wording": self.level["mgf_wording"],
            "refund_ceiling": self.refund_ceiling,
            "revenue_protection_threshold": self.revenue_protection_threshold,
            "effective_auto_ceiling": (
                None if self.effective_auto_ceiling == float("inf")
                else self.effective_auto_ceiling
            ),
            "attack": self.attack,
            "model_mode": self.model_mode,
            "controls": self.controls.as_dict(),
        }

    @property
    def config_hash(self):
        """Stable fingerprint of every setting. Two runs with the same hash
        must produce the same trajectory."""
        blob = json.dumps(self.snapshot(), sort_keys=True).encode()
        return hashlib.sha256(blob).hexdigest()[:12]
