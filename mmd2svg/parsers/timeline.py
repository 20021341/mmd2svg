"""Parser cho Mermaid timeline (formulaic).

Cú pháp hỗ trợ:

    timeline
      title Release history
      2022 : v1 launch
      2023 : v2 launch
      2024 : v3 launch : v3.1 patch

- `title X` (tuỳ chọn).
- Mỗi dòng: `<period> : <event1> : <event2> : ...` — nhiều event cùng period tách
  bởi dấu `:`, mỗi event tạo một `TimelineEvent` riêng với cùng `period`.
- Milestone: nếu period được đánh dấu bằng tiền tố `!` (vd `!2024`), event đó
  được coi là milestone (mở rộng tối giản, vì cú pháp Mermaid gốc không có khái
  niệm milestone tường minh cho timeline).
- Comment `%%` bị bỏ qua. `section ...` bị bỏ qua ở v1 (ngoài phạm vi).
"""
from __future__ import annotations

import re

from mmd2svg.base import Parser
from mmd2svg.ir import TimelineEvent, TimelineIR

_HEADER_RE = re.compile(r"^timeline\s*$", re.IGNORECASE)
_TITLE_RE = re.compile(r"^title\s+(?P<title>.+)$", re.IGNORECASE)
_SECTION_RE = re.compile(r"^section\s+.+$", re.IGNORECASE)
_COMMENT_RE = re.compile(r"^\s*%%")

MAX_EVENTS = 12


class TimelineParser(Parser):
    def parse(self, text: str) -> TimelineIR:
        warnings: list[str] = []
        title: str | None = None
        events: list[TimelineEvent] = []

        lines = [ln.strip() for ln in text.splitlines() if ln.strip() and not _COMMENT_RE.match(ln)]

        for ln in lines:
            if _HEADER_RE.match(ln):
                continue
            tm = _TITLE_RE.match(ln)
            if tm:
                title = tm.group("title").strip()
                continue
            if _SECTION_RE.match(ln):
                continue

            if ":" not in ln:
                warnings.append(f"Không hiểu cú pháp dòng: {ln!r}")
                continue

            parts = [p.strip() for p in ln.split(":")]
            period = parts[0]
            event_labels = [p for p in parts[1:] if p]
            if not period or not event_labels:
                warnings.append(f"Không hiểu cú pháp dòng: {ln!r}")
                continue

            is_milestone = period.startswith("!")
            if is_milestone:
                period = period[1:].strip()

            for label in event_labels:
                events.append(TimelineEvent(label=label, period=period, is_milestone=is_milestone))

        if len(events) > MAX_EVENTS:
            warnings.append(
                f"Vượt ngân sách độ phức tạp: {len(events)} event > {MAX_EVENTS} cho phép"
            )

        return TimelineIR(title=title, events=events, warnings=warnings)
