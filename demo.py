"""
Claude Agent SDK demo — subscription auth, no API key.

Asks Claude to:
  1. Write a small Python script to disk
  2. Execute it with python3 via the Bash tool
  3. Report stdout + a 1-line conclusion back to us

We then return the final text to whoever called main().

Auth: the SDK spawns the `claude` CLI as a subprocess. With ANTHROPIC_API_KEY
unset, that subprocess reads ~/.claude/.credentials.json and uses the user's
Claude Pro / Max subscription. No per-token API billing.
"""

import asyncio
import os
import shutil
import sys
from pathlib import Path

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
    query,
)

WORKSPACE = Path(__file__).parent / "workspace"

SYSTEM_PROMPT = """You are a Python coding assistant working in a sandbox directory.

For the user's task you will:
1. Write Python code to a file using the Write tool.
2. Execute it with `python3 <filename>` via the Bash tool.
3. Capture stdout/stderr in your reply.
4. Be concise — no preamble, just do the work and report.

Always have the script use the `logging` module at INFO level so the run produces
visible log lines."""

USER_PROMPT = """Write a script `fib_demo.py` that:
- Configures `logging` at INFO level with a simple format
- Logs "computing fibonacci" at the start
- Generates the first 10 Fibonacci numbers (start: 0, 1)
- Computes their sum
- Logs the list and the sum at INFO level
- Also prints the sum to stdout on the last line as `SUM=<value>`

Then run it with `python3 fib_demo.py` and report the captured output verbatim."""


def assert_subscription_mode() -> None:
    if os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit(
            "ANTHROPIC_API_KEY is set — that would force per-token API billing.\n"
            "Unset it before running so the SDK uses your subscription instead."
        )


def find_claude_cli() -> str | None:
    """Prefer `claude` on PATH; fall back to the common local install path;
    return None to let the SDK auto-discover if neither is found."""
    found = shutil.which("claude")
    if found:
        return found
    local = os.path.expanduser("~/.local/bin/claude")
    return local if os.path.exists(local) else None


def short(s: str, n: int = 240) -> str:
    s = s.strip()
    return s if len(s) <= n else s[:n] + f"…(+{len(s) - n} chars)"


async def run_demo() -> str:
    assert_subscription_mode()
    WORKSPACE.mkdir(exist_ok=True)

    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        allowed_tools=["Write", "Read", "Bash"],
        permission_mode="bypassPermissions",
        cwd=str(WORKSPACE),
        max_turns=8,
        cli_path=find_claude_cli(),
    )

    print(f"--- spawning claude (subscription auth, cwd={WORKSPACE}) ---\n")

    final_assistant_text = ""
    turn = 0

    async for msg in query(prompt=USER_PROMPT, options=options):
        if isinstance(msg, SystemMessage):
            data = getattr(msg, "data", None) or {}
            if isinstance(data, dict) and data.get("subtype") == "init":
                print(
                    f"[system] session started · "
                    f"model={data.get('model')} · "
                    f"tools={len(data.get('tools') or [])} · "
                    f"cwd={data.get('cwd')}"
                )
        elif isinstance(msg, AssistantMessage):
            turn += 1
            for block in msg.content:
                if isinstance(block, TextBlock):
                    text = block.text.strip()
                    if text:
                        print(f"\n[assistant turn {turn}]\n{text}\n")
                        final_assistant_text = text
                elif isinstance(block, ToolUseBlock):
                    args = str(block.input)
                    print(f"[tool-use turn {turn}] {block.name} input={short(args, 160)}")
        elif isinstance(msg, UserMessage):
            for block in msg.content:
                if isinstance(block, ToolResultBlock):
                    content = block.content
                    if isinstance(content, list):
                        for c in content:
                            if isinstance(c, dict) and c.get("type") == "text":
                                print(f"[tool-result] {short(c['text'], 320)}")
                    elif isinstance(content, str):
                        print(f"[tool-result] {short(content, 320)}")
        elif isinstance(msg, ResultMessage):
            print("\n--- session ended ---")
            for attr in ("subtype", "num_turns", "duration_ms", "total_cost_usd"):
                if hasattr(msg, attr):
                    print(f"  {attr}: {getattr(msg, attr)}")
            usage = getattr(msg, "usage", None)
            if isinstance(usage, dict):
                print(
                    f"  tokens: in={usage.get('input_tokens', '?')} "
                    f"out={usage.get('output_tokens', '?')}"
                )
            result_text = getattr(msg, "result", None)
            if result_text:
                final_assistant_text = result_text

    return final_assistant_text


if __name__ == "__main__":
    result = asyncio.run(run_demo())
    print("\n========== RESULT RETURNED TO CALLER ==========")
    print(result)
    print("===============================================")
