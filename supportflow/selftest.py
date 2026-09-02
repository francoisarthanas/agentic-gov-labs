"""Setup verification for the course toolchain.

Runs every check that Lab 0 depends on and prints one block a student can
screenshot. Each check reports OK, WARN or FAIL, and anything that fails
says what to do about it.

    import supportflow as sf
    sf.check()
"""

import hashlib
import os
import platform
import sys

RESULTS = []

_OK, _WARN, _FAIL = "OK", "WARN", "FAIL"
_W = 62


def _row(name, detail, status, fix=""):
    RESULTS.append((name, detail, status, fix))
    return status


# ------------------------------------------------------------------ checks

def _check_python():
    v = sys.version_info
    s = f"{v.major}.{v.minor}.{v.micro}"
    if v >= (3, 11):
        return _row("Python", s, _OK)
    return _row("Python", s, _FAIL,
                "The governance toolkit needs 3.11 or newer. Use Colab.")


def _check_supportflow():
    try:
        from . import __version__
        return _row("SupportFlow", f"v{__version__}", _OK)
    except Exception as e:
        return _row("SupportFlow", str(e)[:28], _FAIL, "Re-run the setup cell.")


def _check_gradio():
    try:
        import gradio
        return _row("Gradio console", f"v{gradio.__version__}", _OK)
    except ImportError:
        return _row("Gradio console", "not installed", _WARN,
                    "The widget console will be used instead. Same results.")


def _check_toolkit():
    from . import agt
    if agt.available():
        return _row("Governance toolkit", f"v{agt.PINNED}", _OK)
    return _row("Governance toolkit", "not installed", _WARN,
                "Only needed from Week 2. Run the Lab 2 notebook then.")


def _check_api_key():
    key = os.environ.get("GOOGLE_API_KEY", "")
    if key and len(key) > 20:
        return _row("API key", f"found, ends {key[-4:]}", _OK)
    if key:
        return _row("API key", "looks too short", _WARN,
                    "Check you pasted the whole key.")
    return _row("API key", "not set", _WARN,
                "Needed from Week 4. Add it to Colab Secrets as "
                "GOOGLE_API_KEY.")


def _check_engine():
    """Three scenarios must produce three known outcomes."""
    from .config import Config, Controls
    from .engine import run
    from .scenarios import get
    from . import tools
    expected = [("S1", "L3", 200.0, "refunded $89.00"),
                ("S2", "L3", 200.0, "escalated for approval"),
                ("S2", "L4", 500.0, "refunded $310.00")]
    bad = []
    for sid, lvl, ceil, want in expected:
        tools.reset_ledger()
        got = run(get(sid, "none"),
                  Config(autonomy=lvl, refund_ceiling=ceil,
                         controls=Controls())).outcome
        if got != want:
            bad.append(f"{sid}/{lvl}: expected {want!r}, got {got!r}")
    if bad:
        return _row("Engine", f"{len(bad)} of 3 wrong", _FAIL, bad[0])
    return _row("Engine", "3 of 3 scenarios", _OK)


def _check_determinism():
    """The same settings must produce byte-identical output."""
    from .config import Config, Controls
    from .engine import run
    from .scenarios import get
    from . import tools
    hashes = []
    for _ in range(2):
        tools.reset_ledger()
        ctx = run(get("S1", "none"),
                  Config(autonomy="L3", refund_ceiling=200.0,
                         controls=Controls()))
        blob = "|".join(f"{r['step']}{r['agent']}{r.get('tool')}"
                        f"{r['reasoning']}" for r in ctx.trace.rows)
        hashes.append(hashlib.sha256(blob.encode()).hexdigest())
    if hashes[0] == hashes[1]:
        return _row("Determinism", "verified", _OK)
    return _row("Determinism", "runs differ", _FAIL,
                "Report this. Findings would not be reproducible.")


def _check_case_packet():
    """The prompts in the package must match what the documents say."""
    from . import prompts
    n = len(prompts.AGENTS)
    if n == 5:
        return _row("Agent instructions", "5 of 5 loaded", _OK)
    return _row("Agent instructions", f"{n} of 5", _FAIL,
                "Re-run the setup cell.")


def _check_tools():
    from . import tools
    reg = tools.REGISTRY
    writes = [t for t in reg if t["access"] == "write"]
    irrev = [t for t in reg if t["reversible"] == "no"]
    if len(reg) == 10 and len(writes) == 3 and len(irrev) == 1:
        return _row("Tool registry", "10 tools, 3 writes", _OK)
    return _row("Tool registry", f"{len(reg)} tools", _FAIL,
                "Re-run the setup cell.")


CHECKS = [_check_python, _check_supportflow, _check_gradio, _check_toolkit,
          _check_api_key, _check_engine, _check_determinism,
          _check_case_packet, _check_tools]


# ------------------------------------------------------------------ report

def setup_id():
    """A short fingerprint of this environment, for the submission."""
    parts = [f"{s[0]}={s[2]}" for s in RESULTS]
    parts.append(platform.python_version())
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:8]


def check(verbose=True):
    """Run every check and print the report. Returns True if nothing failed."""
    RESULTS.clear()
    for fn in CHECKS:
        try:
            fn()
        except Exception as e:                      # never crash the cell
            _row(fn.__name__.replace("_check_", ""), str(e)[:26], _FAIL,
                 "Re-run the setup cell. If it repeats, post in Questions.")

    failed = [r for r in RESULTS if r[2] == _FAIL]
    warned = [r for r in RESULTS if r[2] == _WARN]

    if not verbose:
        return not failed

    print("=" * _W)
    print("  AGENT GOVERNANCE TOOLCHAIN: SETUP CHECK")
    print("=" * _W)
    for name, detail, status, _fix in RESULTS:
        mark = {"OK": "  OK  ", "WARN": " WARN ", "FAIL": " FAIL "}[status]
        print(f"  {name:<22}{detail:<26}{mark}")
    print("=" * _W)

    if failed:
        print(f"  {len(failed)} CHECK(S) FAILED. Setup is not complete.\n")
        for name, _d, _s, fix in failed:
            print(f"    {name}: {fix}")
        print("\n  Fix these, then run this cell again.")
    else:
        print("  ALL CHECKS PASSED. Your toolchain is ready.")
        if warned:
            print(f"  {len(warned)} warning(s), none of them blocking:\n")
            for name, _d, _s, fix in warned:
                print(f"    {name}: {fix}")
        print(f"\n  Setup ID: {setup_id()}")
        print("  Screenshot this block and submit it with your Lab 0.")
    print("=" * _W)
    return not failed
