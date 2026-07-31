"""Parser cho Mermaid quadrantChart (formulaic).

Cú pháp hỗ trợ:

    quadrantChart
      title Reach vs Effort
      x-axis Low Effort --> High Effort
      y-axis Low Reach --> High Reach
      Item A: [0.3, 0.6]
      Item B: [0.8, 0.9]

- `x-axis <low> --> <high>`, `y-axis <low> --> <high>`.
- Item: `<label>: [x, y]` với x, y trong [0, 1].
- Comment `%%` bị bỏ qua.
"""
from __future__ import annotations

import re

from mmd2svg.base import Parser
from mmd2svg.ir import QuadrantIR, QuadrantItem

_HEADER_RE = re.compile(r"^quadrantChart\s*$", re.IGNORECASE)
_TITLE_RE = re.compile(r"^title\s+(?P<title>.+)$", re.IGNORECASE)
_XAXIS_RE = re.compile(r"^x-axis\s+(?P<low>.+?)\s*-->\s*(?P<high>.+)$", re.IGNORECASE)
_YAXIS_RE = re.compile(r"^y-axis\s+(?P<low>.+?)\s*-->\s*(?P<high>.+)$", re.IGNORECASE)
_ITEM_RE = re.compile(
    r"^(?P<label>[^:]+):\s*\[\s*(?P<x>[0-9.]+)\s*,\s*(?P<y>[0-9.]+)\s*\]$"
)
_COMMENT_RE = re.compile(r"^\s*%%")

MAX_ITEMS = 12


class QuadrantParser(Parser):
    def parse(self, text: str) -> QuadrantIR:
        warnings: list[str] = []
        title: str | None = None
        x_low, x_high, y_low, y_high = "", "", "", ""
        items: list[QuadrantItem] = []

        lines = [ln.strip() for ln in text.splitlines() if ln.strip() and not _COMMENT_RE.match(ln)]

        for ln in lines:
            if _HEADER_RE.match(ln):
                continue
            tm = _TITLE_RE.match(ln)
            if tm:
                title = tm.group("title").strip()
                continue
            xm = _XAXIS_RE.match(ln)
            if xm:
                x_low, x_high = xm.group("low").strip(), xm.group("high").strip()
                continue
            ym = _YAXIS_RE.match(ln)
            if ym:
                y_low, y_high = ym.group("low").strip(), ym.group("high").strip()
                continue
            im = _ITEM_RE.match(ln)
            if im:
                x, y = float(im.group("x")), float(im.group("y"))
                if not (0 <= x <= 1 and 0 <= y <= 1):
                    warnings.append(f"Toạ độ ngoài phạm vi [0,1]: {ln!r}")
                    continue
                items.append(QuadrantItem(label=im.group("label").strip(), x=x, y=y))
                continue

            warnings.append(f"Không hiểu cú pháp dòng: {ln!r}")

        if len(items) > MAX_ITEMS:
            warnings.append(
                f"Vượt ngân sách độ phức tạp: {len(items)} item > {MAX_ITEMS} cho phép"
            )

        return QuadrantIR(
            title=title,
            x_label_low=x_low,
            x_label_high=x_high,
            y_label_low=y_low,
            y_label_high=y_high,
            items=items,
            warnings=warnings,
        )
