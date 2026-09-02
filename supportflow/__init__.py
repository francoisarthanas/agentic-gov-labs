"""SupportFlow v2: the agent under review for the whole course.

This is a training target, not a reference implementation. It has real
weaknesses. That is what makes it worth reviewing. Do not copy this design
into a production system.
"""

from .config import Config, Controls, AUTONOMY, LEVELS
from .engine import run
from . import scenarios, tools, data, console, trace, prompts, agt, selftest

__version__ = "2.1.0"


def check(verbose=True):
    """Verify the whole toolchain and print a report you can screenshot."""
    return selftest.check(verbose=verbose)


def launch(share=False, **kwargs):
    """Open the Governance Console.

    Uses Gradio when it is available and falls back to the ipywidgets
    console otherwise. Both drive the same engine, so the results and the
    config_hash are identical either way.
    """
    from . import gradio_console
    return gradio_console.launch(share=share, **kwargs)


__all__ = ["Config", "Controls", "AUTONOMY", "LEVELS", "run", "launch",
           "check", "scenarios", "tools", "data", "console", "trace",
           "prompts", "agt", "selftest"]
