"""SupportFlow agent loop.

Runs the conversation: assembles context, calls the model, executes any
tool calls the model requests, and returns the reply. Tool calls are
echoed to stdout when verbose=True.
"""

import functools
import inspect
import json
import os
import time

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


def available_models(api_key=None, client=None):
    """Model names this API key can call generateContent on.

    Pass an existing client where possible. models.list() returns a lazy
    pager, so the client must stay referenced for the whole iteration --
    a throwaway client can be collected mid-loop, closing the connection
    the pager is still reading from.
    """
    client = client or _client(api_key)   # keep the reference alive
    out = []
    for m in client.models.list():
        actions = getattr(m, "supported_actions", None) or []
        if actions and "generateContent" not in actions:
            continue
        name = (m.name or "").replace("models/", "")
        if not name or any(sk in name for sk in _SKIP):
            continue
        out.append(name)
    return out


def pick_model(api_key=None, verbose=False, client=None):
    """Choose the best model this key can actually reach."""
    try:
        avail = available_models(api_key, client=client)
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
        self.model_name = model or pick_model(self.api_key, client=self.client)

        # The SDK calls these directly and manages the tool-call loop,
        # including the thought signatures Gemini 3 requires. Each is
        # wrapped so the call is visible in the notebook.
        self._tool_fns = [self._wrap(name) for name in
                          ("kb_search", "crm_lookup", "issue_refund", "escalate")]

        self._start_chat(self.model_name)

    def _start_chat(self, model_name):
        """Open a chat session on the given model."""
        types = self._genai_types
        self.model_name = model_name
        self.chat = self.client.chats.create(
            model=model_name,
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

    # Transient server-side conditions. Not the caller's fault, and
    # usually gone within a few seconds.
    _RETRYABLE = ("503", "unavailable", "overloaded", "429",
                  "resource_exhausted", "rate limit", "500", "internal")

    def _retryable(self, err) -> bool:
        msg = str(err).lower()
        return any(k in msg for k in self._RETRYABLE)

    def send(self, message: str, retries: int = 3) -> str:
        """Send a customer message and return SupportFlow's reply.

        Retries transient 5xx/429 responses, then falls back to the next
        available model if the current one stays unavailable.
        """
        self.history.append({"role": "customer", "text": message})

        delay = 2
        last_err = None

        for attempt in range(retries + 1):
            try:
                response = self.chat.send_message(message)
                text = (getattr(response, "text", None)
                        or "(no text response)").strip()
                self.history.append({"role": "supportflow", "text": text})
                return text
            except Exception as e:
                last_err = e
                if not self._retryable(e) or attempt == retries:
                    break
                self._log(f"   ⏳ Model busy. Retrying in {delay}s "
                          f"(attempt {attempt + 2} of {retries + 1})...")
                time.sleep(delay)
                delay *= 2

        # Still failing. Try a different model before giving up.
        if self._retryable(last_err):
            for alt in PREFERRED_MODELS:
                if alt == self.model_name:
                    continue
                try:
                    self._log(f"   ↻ {self.model_name} is still busy. "
                              f"Switching to {alt}.")
                    self._start_chat(alt)
                    response = self.chat.send_message(message)
                    text = (getattr(response, "text", None)
                            or "(no text response)").strip()
                    self._log(f"   ✅ Now using {alt}.\n")
                    self.history.append({"role": "supportflow", "text": text})
                    return text
                except Exception as e:
                    last_err = e
                    continue

            raise RuntimeError(
                "Every model is busy right now. This is on Google's side, "
                "not yours. Wait a minute and press play again."
            ) from last_err

        raise last_err


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
