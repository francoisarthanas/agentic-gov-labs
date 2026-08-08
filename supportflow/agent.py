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
            self.model_name = model or "gemini-2.5-flash"
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
