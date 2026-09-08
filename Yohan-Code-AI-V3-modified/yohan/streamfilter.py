"""
YOHAN CODE - Streaming Output Filter
====================================
Hides raw tool-call syntax from the user's terminal while letting normal
prose stream through in real time. Handles everything a model may emit:

    Here is the plan.                    <- visible, streams live
    <tool_call> {...} </tool_call>       <- swallowed (XML format)
    ```json
    {"tool": "write_file", ...}          <- swallowed (fenced format)
    ```
    All done!                            <- visible again

Why a filter instead of "just don't print tool calls"?
Opening/closing markers can be split across tokens at arbitrary boundaries
("<to", "ol_ca", "ll>" / "```js", "on {\"to", ..."), and long code payloads
arrive in hundreds of small chunks. Detection therefore uses a sliding
buffer that only ever holds back a tail which is literally a prefix of a
marker — never per-chunk string matching.

Fences: only swallowed when the fenced block actually contains a tool-call
JSON ({"tool": ...}); ordinary code samples shown in fences still pass
through, as the system prompt allows the model to display code.
"""

import re

OPEN_TAG = "<tool_call>"
CLOSE_TAG = "</tool_call>"
FENCE = "```"

# A fenced block is declared a tool call if it contains this pattern ...
_TOOL_JSON = re.compile(r'\{\s*"tool"\s*:')
# ... within this many chars of the fence opening. Beyond that (and with no
# closing fence yet) we assume it is a legitimate code sample.
FENCE_PEEK = 600

NORMAL, XML, FENCE_DECIDING, FENCE_TOOL = "normal", "xml", "fence", "fence_tool"


class ToolCallStreamFilter:
    """Stateful pass-through filter for streamed model output.

    feed()  -> push a chunk of streamed text, returns the part safe to
               display right now ("" while inside a tool block).
    flush() -> end of stream; releases remaining visible text and
               guarantees raw tool JSON is never flushed to the terminal.
    """

    def __init__(self):
        self._state = NORMAL
        self._buf = ""
        self._fence_buf = ""

    def feed(self, chunk: str) -> str:
        if not chunk:
            return ""
        self._buf += chunk
        visible: list[str] = []

        while True:
            if self._state == NORMAL:
                if not self._buf:
                    break
                i_xml = self._buf.find(OPEN_TAG)
                i_fence = self._buf.find(FENCE)
                if i_xml == -1 and i_fence == -1:
                    # No marker — emit everything except a tail that is a
                    # prefix of a marker (markers split across chunks)
                    hold = self._tail_hold(self._buf)
                    if hold:
                        visible.append(self._buf[:-hold])
                        self._buf = self._buf[-hold:]
                    else:
                        visible.append(self._buf)
                        self._buf = ""
                    break
                if i_xml == -1 or (i_fence != -1 and i_fence < i_xml):
                    visible.append(self._buf[:i_fence])
                    self._buf = self._buf[i_fence + len(FENCE):]
                    self._state = FENCE_DECIDING
                    self._fence_buf = ""
                else:
                    visible.append(self._buf[:i_xml])
                    self._buf = self._buf[i_xml + len(OPEN_TAG):]
                    self._state = XML
                continue

            if self._state == XML:
                end = self._buf.find(CLOSE_TAG)
                if end == -1:
                    self._buf = self._buf[-(len(CLOSE_TAG) - 1):]
                    break
                self._buf = self._buf[end + len(CLOSE_TAG):]
                self._state = NORMAL
                continue

            if self._state == FENCE_DECIDING:
                self._fence_buf += self._buf
                self._buf = ""
                if _TOOL_JSON.search(self._fence_buf):
                    self._fence_buf = ""
                    self._state = FENCE_TOOL
                    continue
                end = self._fence_buf.find(FENCE)
                if end != -1 or len(self._fence_buf) > FENCE_PEEK:
                    # Legitimate code sample — show it, fence included
                    visible.append(FENCE + self._fence_buf)
                    self._fence_buf = ""
                    self._state = NORMAL
                    continue
                break

            if self._state == FENCE_TOOL:
                end = self._buf.find(FENCE)
                if end == -1:
                    self._buf = self._buf[-(len(FENCE) - 1):]
                    break
                self._buf = self._buf[end + len(FENCE):]
                self._state = NORMAL
                continue

        return "".join(visible)

    def flush(self) -> str:
        """Stream ended. Return remaining visible text; never tool JSON."""
        if self._state == NORMAL:
            rest = self._buf
        elif self._state == FENCE_DECIDING:
            rest = "" if _TOOL_JSON.search(self._fence_buf) \
                else FENCE + self._fence_buf + self._buf
        else:  # XML or FENCE_TOOL — dangling tool call, never leak it
            rest = ""
        self._buf = ""
        self._fence_buf = ""
        self._state = NORMAL
        return rest

    @staticmethod
    def _tail_hold(buf: str) -> int:
        """Length of a trailing partial marker (a proper prefix of the open
        tag or of a fence) that must be held until more chunks arrive."""
        for k in range(min(len(buf), len(OPEN_TAG) - 1), 0, -1):
            tail = buf[-k:]
            if OPEN_TAG.startswith(tail) or FENCE.startswith(tail):
                return k
        return 0
