"""SupportFlow agent loop.

Runs the conversation: assembles context, calls the model, executes any
tool calls the model requests, and returns the reply. Tool calls are
echoed to stdout when verbose=True.
"""

import functools
import inspect
import json
import os

from .prompt import SYSTEM_PROMPT
from . import tools as _tools

# Tried in order. Models are retired on a rolling schedule, so the first
# one this API key can actually reach wins.
PREFERRED_MODELS = [
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-flash-latest",
]

_SKIP = ("image", "tts", "live", "embedding", "veo", "lyria",
         "robotics", "computer-use", "deep-research")


def _client(api_key=None):
    from google import genai
    return genai.Client(api_key=api_key or os.getenv("GOOGLE_API_KEY"))


def available_models(api_key=None):
    """Model names this API key can call generateContent on."""
    out = []
    for m in _client(api_key).models.list():
        actions = getattr(m, "supported_actions", None) or []
        if actions and "generateContent" not in actions:
            continue
        name = (m.name or "").replace("models/", "")
        if not name or any(sk in name for sk in _SKIP):
            continue
        out.append(name)
    return out


def pick_model(api_key=None, verbose=False):
    """Choose the best model this key can actually reach."""
    try:
        avail = available_models(api_key)
    except Exception as e:
        if verbose:
            print(f"   (could not list models: {type(e).__name__})")
        return PREFERRED_MODELS[0]

    for want in PREFERRED_MODELS:
        if want in avail:
            return want
    flashes = [a for a in avail if "flash" in a]
    if flashes:
        return flashes[0]
    return avail[0] if avail else PREFERRED_MODELS[0]


class SupportFlow:
    """The Northwind Retail customer service agent."""

    def __init__(self, api_key=None, model=None, verbose=True, trace=None,
                 provider="google"):
        if provider != "google":
            raise ValueError(f"Unsupported provider: {provider!r}")

        from google.genai import types

        self.verbose = verbose
        self.history = []
        self.trace = trace if trace is not None else []
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")

        self._genai_types = types
        self.client = _client(self.api_key)
        self.model_name = model or pick_model(self.api_key)

        # The SDK calls these directly and manages the tool-call loop,
        # including the thought signatures Gemini 3 requires. Each is
        # wrapped so the call is visible in the notebook.
        self._tool_fns = [self._wrap(name) for name in
                          ("kb_search", "crm_lookup", "issue_refund", "escalate")]

        self.chat = self.client.chats.create(
            model=self.model_name,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=self._tool_fns,
            ),
        )

    # -- helpers ---------------------------------------------------------

    def _log(self, msg):
        if self.verbose:
            print(msg)

    def _wrap(self, name):
        """Wrap a tool so every call is logged and recorded.

        The SDK builds each tool's schema by inspecting the function
        signature, so the wrapper must expose the same signature as the
        real tool rather than a bare **kwargs.
        """
        real = getattr(_tools, name)
        sig = inspect.signature(real)

        def wrapped(*args, **kwargs):
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            clean = {k: v for k, v in bound.arguments.items() if v is not None}
            pretty = ", ".join(f"{k}={v!r}" for k, v in clean.items())
            self._log(f"   🔧 {name}({pretty})")
            try:
                result = real(**clean)
            except Exception as e:
                result = json.dumps({"error": f"{type(e).__name__}: {e}"})
            self.trace.append({"tool": name, "args": clean, "result": result})
            preview = result if len(result) < 220 else result[:220] + " ...(truncated)"
            self._log(f"   ↳ {preview}\n")
            return result

        functools.update_wrapper(wrapped, real)
        wrapped.__signature__ = sig
        return wrapped

    # -- main entry point ------------------------------------------------

    def send(self, message: str) -> str:
        """Send a customer message and return SupportFlow's reply."""
        self.history.append({"role": "customer", "text": message})
        response = self.chat.send_message(message)
        text = (getattr(response, "text", None) or "(no text response)").strip()
        self.history.append({"role": "supportflow", "text": text})
        return text


def chat_loop(agent=None, **kwargs):
    """Simple REPL. Type 'quit' to exit."""
    agent = agent or SupportFlow(**kwargs)
    print("SupportFlow is ready. Type 'quit' to exit.\n")
    while True:
        try:
            msg = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            return
        if msg.lower() in {"quit", "exit"}:
            print("Goodbye.")
            return
        if not msg:
            continue
        print()
        print(f"SupportFlow: {agent.send(msg)}\n")
