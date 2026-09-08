"""
Regression & behavior tests for the streaming layer:
  1. Cloudflare numeric delta content (the str+int crash / zero-eating bug)
  2. ToolCallStreamFilter — raw tool JSON never reaches the terminal,
     even when tags are split across tiny tokens.
"""
import json
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

from yohan.providers import _parse_sse_json, _extract_delta_content
from yohan.streamfilter import ToolCallStreamFilter


# ── Bug 1: Cloudflare sends delta content as raw JSON numbers ───────────────

def test_numeric_zero_content_is_preserved():
    chunk = json.loads('{"choices":[{"delta":{"content":0}}]}')
    assert _extract_delta_content(chunk) == "0"   # was silently dropped before

def test_numeric_digit_content_is_stringified():
    assert _extract_delta_content(json.loads('{"choices":[{"delta":{"content":42}}]}')) == "42"

def test_none_content_returns_none():
    assert _extract_delta_content(json.loads('{"choices":[{"delta":{"content":null}}]}')) is None

def test_multiline_sse_payload_reassembles():
    payload = "\n".join(['{"choices":[{"delta":{"content":"viewBox=', '0 0 24 24', '"}}]}'])
    chunk = _parse_sse_json(payload)
    assert chunk is not None and _extract_delta_content(chunk) == "viewBox=0 0 24 24"


# ── Bug 2: stream filter hides tool calls, keeps prose ─────────────────────

RESPONSE = (
    "Here is the plan.\n"
    "<tool_call>\n{\"tool\": \"write_file\", \"params\": {\"path\": \"src/App.tsx\","
    " \"content\": \"export default function App() { return <div>hi</div> }\"}}\n</tool_call>\n"
    "Created the entry point. Now the hero:\n"
    "<tool_call>{\"tool\": \"bash\", \"params\": {\"command\": \"npm install\"}}</tool_call>"
)

def _run_filter(text, chunk_size):
    f = ToolCallStreamFilter()
    shown = []
    for i in range(0, len(text), chunk_size):
        out = f.feed(text[i:i + chunk_size])
        if out:
            shown.append(out)
    tail = f.flush()
    if tail:
        shown.append(tail)
    return "".join(shown)

def test_tool_json_never_shown_whole_chunks():
    shown = _run_filter(RESPONSE, len(RESPONSE))
    assert "<tool_call>" not in shown and "write_file" not in shown
    assert "Here is the plan." in shown and "Created the entry point." in shown

def test_tool_json_never_shown_tiny_chunks():
    # Adversarial: tags split across 1-2 char tokens — the real-world case
    shown = _run_filter(RESPONSE, 2)
    assert "<tool_call>" not in shown and "</tool_call>" not in shown
    assert '"tool"' not in shown and "src/App.tsx" not in shown
    assert "Here is the plan." in shown

def test_tool_json_never_shown_one_char_chunks():
    shown = _run_filter(RESPONSE, 1)
    assert "<tool" not in shown and "tool_call" not in shown
    assert "Here is the plan." in shown and "Now the hero:" in shown

def test_flush_never_leaks_dangling_tool_json():
    f = ToolCallStreamFilter()
    assert f.feed("Let me write the file. <tool_call>{\"tool\": \"write_") == "Let me write the file. "
    assert f.flush() == ""          # dangling block swallowed, never printed

def test_plain_text_passthrough():
    # feed() holds back a safety margin (len("<tool_call>")-1 chars) in case a
    # tag is split across chunks; flush() at end-of-stream releases it, so the
    # terminal always sees the complete text.
    f = ToolCallStreamFilter()
    assert f.feed("Hello world, no tools here.") == "Hello world, no tools here."
    assert f.flush() == ""


def test_margin_released_when_tag_completes():
    f = ToolCallStreamFilter()
    assert f.feed("OK, writing now. <tool") == "OK, writing now. "
    assert f.feed("_call>{}</tool_call>") == ""
    assert f.flush() == ""

def test_multiple_tool_calls_in_one_response():
    shown = _run_filter(RESPONSE, 3)
    assert shown.count("Now the hero:") == 1

# ── Fenced tool calls (Gemini often uses ```json instead of XML tags) ───────

def test_fenced_tool_call_is_swallowed():
    text = ('Plan first.\n```json\n{"tool": "write_file", "params": '
            '{"path": "package.json", "content": "{}"}}\n```\nDone.')
    shown = _run_filter(text, 4)
    assert '"tool"' not in shown and 'package.json' not in shown
    assert 'Plan first.' in shown and 'Done.' in shown

def test_fenced_tool_call_split_into_one_char_chunks():
    text = 'Start\n```json\n{"tool": "bash", "params": {"command": "ls -la"}}\n```\nEnd'
    shown = _run_filter(text, 1)
    assert 'bash' not in shown and 'ls -la' not in shown
    assert shown.startswith('Start') and shown.endswith('End')

def test_fenced_plain_code_sample_is_still_shown():
    # The model may legitimately display code in fences — only tool JSON hides
    text = 'Here is the fix:\n```python\nprint("hello tool world")\n```\nEnd.'
    shown = _run_filter(text, 3)
    assert 'print("hello tool world")' in shown
    assert 'Here is the fix:' in shown and 'End.' in shown

def test_unclosed_tool_fence_never_leaks_on_flush():
    f = ToolCallStreamFilter()
    out = f.feed('Writing: ```json\n{"tool": "write_file", "params": {"path": "x"')
    assert '"tool"' not in out
    assert f.flush() == ""       # dangling tool fence swallowed, not flushed


# ── agent.py history-protection helpers ─────────────────────────────────────

def test_looks_like_tool_attempt():
    from yohan.agent import Agent
    assert Agent._looks_like_tool_attempt('blah {"tool": "write_file"')
    assert Agent._looks_like_tool_attempt('starts <tool')
    assert not Agent._looks_like_tool_attempt('a completely normal answer')

def test_strip_partial_tool_call():
    from yohan.agent import Agent
    # dangling XML block cut, prose kept
    assert Agent._strip_partial_tool_call('planning text <tool_call>{"tool": "wr') == 'planning text '
    # complete responses untouched
    t = 'ok <tool_call>{"tool": "bash", "params": {"command": "ls"}}</tool_call> done'
    assert Agent._strip_partial_tool_call(t) == t
    # truncated bare JSON with params cut, trailing prose-free
    cut = Agent._strip_partial_tool_call('I will fix it now {"tool": "write_file", "params": {"path": "x"')
    assert cut == 'I will fix it now '
    # answer merely discussing tool syntax (no params, complete) untouched
    t2 = 'Use {"tool": "bash"} in your config. Hope this helps!'
    assert Agent._strip_partial_tool_call(t2) == t2


if __name__ == "__main__":
    import traceback
    failed = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  ✓ {name}")
            except Exception:
                failed += 1
                print(f"  ✗ {name}")
                traceback.print_exc()
    if failed:
        print(f"\n{failed} test(s) FAILED")
        sys.exit(1)
    print(f"\nAll tests passed ✓")
