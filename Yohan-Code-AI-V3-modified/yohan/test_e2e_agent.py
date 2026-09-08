"""End-to-end: replay the exact Gemini failure sequence and verify recovery."""
import sys
sys.path.insert(0, "/mnt/agents/output/Yohan-Code-AI/yohan-code")
import yohan.agent as agent_mod
from yohan.agent import Agent


class MockProvider:
    """Replays scripted token streams, one per model turn."""
    def __init__(self, turns):
        self.turns = list(turns)
        self.seen_histories = []
    def chat(self, messages, model, stream, system, **kw):
        self.seen_histories.append([dict(m) for m in messages])
        toks = self.turns.pop(0)
        return iter(toks)


def run(turns):
    visible = []
    prov = MockProvider(turns)
    agent_mod.get_provider = lambda pid: prov   # monkeypatch
    a = Agent(chat_id="e2etest", provider_id="gemini",
              on_token=lambda t: visible.append(t))
    a.chat("fix package.json please")
    return a, prov, "".join(visible)


# ── Scenario: Gemini turn 1 = bare JSON attempt cut off; turn 2 = proper XML ──
t1 = ["Let me fix it. ", '{"tool": "write_file", "params": {"path": "package.j', 'son", "content": "{\n \"na']
t2 = ["<tool_call>", '{"tool": "write_file", "params": {"path": "package.json", "content": "{}"}}', "</tool_call>"]
agent, prov, shown = run([t1, t2, ["Done! package.json is fixed."]])

hist = agent.history
print("visible to user:", repr(shown))
assert any(m["role"] == "user" and "Send the SAME tool call again" in m["content"] for m in hist), "nudge missing"
# history must contain NO dangling tool JSON
for m in hist:
    c = m["content"]
    assert c.count("<tool_call>") == c.count("</tool_call>"), f"dangling tag in history: {c[:80]}"
    if m["role"] == "assistant" and "</tool_call>" not in c:
        assert not ('"params"' in c and not c.rstrip().endswith("}")), f"truncated JSON in history: {c[:80]}"
# tool actually executed
from yohan.sandbox import sandbox_read
assert sandbox_read("e2etest", "package.json") == "{}", "file not written"
print("✓ scenario 1: bare-JSON truncation recovered, history clean, file written")

# ── Scenario: XML truncated mid-JSON, then compact re-send ──
t3 = ["On it. <tool_call>", '{"tool": "write_file", "params": {"path": "a.txt", "content": "truncate']
t4 = ["<tool_call>", '{"tool": "write_file", "params": {"path": "a.txt", "content": "ok"}}', "</tool_call>"]
agent2, prov2, shown2 = run([t3, t4, ["All set."]])
hist2 = agent2.history
assert '"content": "truncate' not in "".join(m["content"] for m in hist2 if m["role"] == "assistant"), "partial JSON leaked into history"
assert sandbox_read("e2etest", "a.txt") == "ok"
print("✓ scenario 2: XML truncation recovered, no partial JSON in history")

# ── Scenario: normal prose answer passes through untouched ──
t5 = ["Just a plain answer, no tools. 100% fine."]
agent3, _, shown3 = run([t5])
assert shown3 == "Just a plain answer, no tools. 100% fine."
print("✓ scenario 3: plain answers untouched (100% intact, zeros preserved)")

print("\nE2E: all scenarios passed ✓")
