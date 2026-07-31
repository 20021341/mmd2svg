"""Parser cho Mermaid stateDiagram-v2 (graph-based).

Cú pháp hỗ trợ:

    stateDiagram-v2
      [*] --> Idle
      Idle --> Running : start
      Running --> Idle : stop
      Running --> [*]

- `[*]` đầu dòng bên trái -> transition từ start ảo.
- `[*]` bên phải -> transition tới end ảo.
- Transition: `A --> B` hoặc `A --> B : label`.
- Comment `%%` bị bỏ qua.
"""
from __future__ import annotations

import re

from mmd2svg.base import Parser
from mmd2svg.ir import SNode, STransition, StateMachineIR

_HEADER_RE = re.compile(r"^stateDiagram(-v2)?\s*$", re.IGNORECASE)
_COMMENT_RE = re.compile(r"^\s*%%")
_TRANSITION_RE = re.compile(
    r"^(?P<src>\[\*\]|[A-Za-z0-9_]+)\s*-->\s*(?P<dst>\[\*\]|[A-Za-z0-9_]+)\s*(:\s*(?P<label>.+))?$"
)

MAX_STATES = 9
MAX_TRANSITIONS = 12
START_ID = "__start__"
END_ID = "__end__"


class StateMachineParser(Parser):
    def parse(self, text: str) -> StateMachineIR:
        warnings: list[str] = []
        states: dict[str, SNode] = {}
        transitions: list[STransition] = []
        has_start = False
        end_count = 0
        title: str | None = None

        _TITLE_RE = re.compile(r"^\s*title\s+(.+)$", re.IGNORECASE)
        lines = [ln.strip() for ln in text.splitlines() if ln.strip() and not _COMMENT_RE.match(ln)]

        for ln in lines:
            if _HEADER_RE.match(ln):
                continue

            tm = _TITLE_RE.match(ln)
            if tm:
                title = tm.group(1).strip()
                continue

            m = _TRANSITION_RE.match(ln)
            if not m:
                warnings.append(f"Không hiểu cú pháp dòng: {ln!r}")
                continue

            src_token = m.group("src")
            dst_token = m.group("dst")
            label = m.group("label")
            label = label.strip() if label else None

            src_id = START_ID if src_token == "[*]" else src_token
            dst_id = END_ID if dst_token == "[*]" else dst_token

            if src_id == START_ID:
                has_start = True
                if START_ID not in states:
                    states[START_ID] = SNode(id=START_ID, label="", is_start=True)
            elif src_id not in states:
                states[src_id] = SNode(id=src_id, label=src_id)

            if dst_id == END_ID:
                end_count += 1
                if END_ID not in states:
                    states[END_ID] = SNode(id=END_ID, label="", is_end=True)
            elif dst_id not in states:
                states[dst_id] = SNode(id=dst_id, label=dst_id)

            transitions.append(STransition(source=src_id, target=dst_id, label=label))

        real_states = [s for s in states.values() if not s.is_start and not s.is_end]
        if len(real_states) > MAX_STATES:
            warnings.append(
                f"Vượt ngân sách độ phức tạp: {len(real_states)} state > {MAX_STATES} cho phép"
            )
        if len(transitions) > MAX_TRANSITIONS:
            warnings.append(
                f"Vượt ngân sách độ phức tạp: {len(transitions)} transition > {MAX_TRANSITIONS} cho phép"
            )
        if not has_start and real_states:
            warnings.append("Không tìm thấy trạng thái bắt đầu ([*] --> ...)")

        return StateMachineIR(title=title, states=list(states.values()), transitions=transitions, warnings=warnings)
