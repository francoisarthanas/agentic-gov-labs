"""SupportFlow v2: the agent under review for the whole course.

This is a training target, not a reference implementation. It has real
weaknesses. That is what makes it worth reviewing. Do not copy this design
into a production system.
"""

from .config import Config, Controls, AUTONOMY, LEVELS
from .engine import run
from . import scenarios, tools, data, console, trace

__version__ = "2.0.0"
__all__ = ["Config", "Controls", "AUTONOMY", "LEVELS", "run",
           "scenarios", "tools", "data", "console", "trace"]
