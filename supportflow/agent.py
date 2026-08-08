"""SupportFlow agent loop.

Runs the conversation: assembles context, calls the model, executes any
tool calls the model requests, and returns the reply. Tool calls are
echoed to stdout when verbose=True.
"""

import json
import os

from .prompt import SYSTEM_PROMPT
from .tools import TOOL_REGISTRY, TOOL_DECLARATIONS

MAX_TOOL_ROUNDS = 6

# Tried in order. Google retires models regularly, so the first one this
# API key can actually reach wins.
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


def available_models(api_key=None):
    """Model names this API key can call generateContent on."""
    import google.generativeai as genai
    if api_key:
        genai.configure(api_key=api_key)
    out = []
    for m in genai.list_models():
        methods = getattr(m, "supported_generation_methods", []) or []
        if "generateContent" not in methods:
            continue
        name = m.name.replace("models/", "")
        if any(sk in name for sk in _SKIP):
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
    if avail:
        return avail[0]
    return PREFERRED_MODELS[0]


class SupportFlow:
    def __init__(self, api_key=None, provider="google",
                 model=None, verbose=True, trace=None):
        self.provider = provider
        self.verbose = verbose
        self.history = []
        self.trace = trace if trace is not None else []
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")

        if provider == "google":
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.model_name = model or pick_model(self.api_key)
            self._client = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=SYSTEM_PROMPT,
                tools=[{"function_declarations": TOOL_DECLARATIONS}],
            )
            self._chat = self._client.start_chat(history=[])
        else:
            raise ValueError(
                f"Unsupported provider: {provider!r}. Use provider='google'."
            )

    # -- helpers ---------------------------------------------------------

    def _log(self, msg):
        if self.verbose:
            print(msg)

    def _run_tool(self, name, args):
        fn = TOOL_REGISTRY.get(name)
        if not fn:
            return json.dumps({"error": f"Unknown tool: {name}"})

        pretty = ", ".join(f"{k}={v!r}" for k, v in args.items())
        self._log(f"   🔧 {name}({pretty})")

        try:
            result = fn(**args)
        except Exception as e:
            result = json.dumps({"error": f"{type(e).__name__}: {e}"})

        self.trace.append({"tool": name, "args": args, "result": result})

        preview = result if len(result) < 220 else result[:220] + " ...(truncated)"
        self._log(f"   ↳ {preview}\n")
        return result

    # -- main entry point ------------------------------------------------

    def send(self, message: str) -> str:
        """Send a customer message and return SupportFlow's reply."""
        self.history.append({"role": "customer", "text": message})
        response = self._chat.send_message(message)

        for _ in range(MAX_TOOL_ROUNDS):
            calls = []
            for part in response.candidates[0].content.parts:
                fc = getattr(part, "function_call", None)
                if fc and fc.name:
                    calls.append(fc)

            if not calls:
                break

            replies = []
            for fc in calls:
                args = {k: v for k, v in fc.args.items()}
                out = self._run_tool(fc.name, args)
                replies.append({
                    "function_response": {
                        "name": fc.name,
                        "response": {"result": out},
                    }
                })
            response = self._chat.send_message(replies)

        try:
            text = response.text
        except Exception:
            text = "(no text response)"

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
        reply = agent.send(msg)
        print(f"SupportFlow: {reply}\n")
