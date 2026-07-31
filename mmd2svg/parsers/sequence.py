"""Parser cho Mermaid sequenceDiagram (formulaic).

Cú pháp hỗ trợ:

    sequenceDiagram
      participant A
      participant B
      A->>B: Request
      B-->>A: Response
      A->>A: Self check

- `participant X` hoặc `participant X as Label`.
- Actor không khai `participant` được suy ra từ message đầu tiên nhắc tới nó,
  theo thứ tự xuất hiện.
- Message: `A->>B: text` (call, mũi tên liền), `A-->>B: text` (return, mũi tên đứt).
- Self-message: source == target.
- Comment `%%` bị bỏ qua.
"""
from __future__ import annotations

import re

from mmd2svg.base import Parser
from mmd2svg.ir import Actor, Message, SequenceIR

_HEADER_RE = re.compile(r"^sequenceDiagram\s*$", re.IGNORECASE)
_COMMENT_RE = re.compile(r"^\s*%%")
_PARTICIPANT_RE = re.compile(
    r"^participant\s+(?P<id>[A-Za-z0-9_\s]+?)(\s+as\s+(?P<alias>.+))?$", re.IGNORECASE
)
_MESSAGE_RE = re.compile(
    r"^(?P<src>[A-Za-z0-9_\s]+?)\s*(?P<arrow>-->>|->>|-->|->)\s*"
    r"(?P<dst>[A-Za-z0-9_\s]+?)\s*:\s*(?P<label>.*)$"
)

MAX_ACTORS = 5
MAX_MESSAGES = 12


class SequenceParser(Parser):
    def parse(self, text: str) -> SequenceIR:
        warnings: list[str] = []
        actors: dict[str, Actor] = {}
        messages: list[Message] = []
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

            pm = _PARTICIPANT_RE.match(ln)
            if pm:
                actor_id = pm.group("id")
                alias = pm.group("alias")
                actors[actor_id] = Actor(id=actor_id, label=(alias or actor_id).strip())
                continue

            mm = _MESSAGE_RE.match(ln)
            if mm:
                src, dst = mm.group("src"), mm.group("dst")
                arrow = mm.group("arrow")
                label = mm.group("label").strip()
                kind = "self" if src == dst else ("return" if "-->" in arrow else "call")

                if src not in actors:
                    actors[src] = Actor(id=src, label=src)
                if dst not in actors:
                    actors[dst] = Actor(id=dst, label=dst)

                messages.append(Message(source=src, target=dst, label=label, kind=kind))
                continue

            warnings.append(f"Không hiểu cú pháp dòng: {ln!r}")

        if len(actors) > MAX_ACTORS:
            warnings.append(
                f"Vượt ngân sách độ phức tạp: {len(actors)} actor > {MAX_ACTORS} cho phép"
            )
        if len(messages) > MAX_MESSAGES:
            warnings.append(
                f"Vượt ngân sách độ phức tạp: {len(messages)} message > {MAX_MESSAGES} cho phép"
            )

        return SequenceIR(title=title, actors=list(actors.values()), messages=messages, warnings=warnings)
