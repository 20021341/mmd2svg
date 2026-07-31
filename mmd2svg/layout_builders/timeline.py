"""LayoutBuilder cho timeline — formulaic: vị trí = thứ tự period xuất hiện.

Vì Mermaid timeline chỉ cho nhãn thời gian dạng text (không phải ngày ISO chuẩn),
ta xếp các period theo đúng thứ tự xuất hiện trong input với khoảng cách đều —
đây là "thứ tự khai báo" trung thực với input, không giả định khoảng cách thời
gian thực giữa các nhãn (tránh suy diễn sai lệch mà DESIGN.md cảnh báo).
Nếu nhiều event cùng period, chúng xếp chồng dọc quanh cùng 1 điểm x.
"""
from __future__ import annotations

from mmd2svg.base import LayoutBuilder
from mmd2svg.ir import TimelineIR
from mmd2svg.layout import TimelineLayout

PERIOD_SPACING = 160
PADDING = 40
BASELINE_Y = 120


class TimelineLayoutBuilder(LayoutBuilder):
    def layout(self, ir: TimelineIR) -> TimelineLayout:
        if not ir.events:
            return TimelineLayout(viewbox_w=80, viewbox_h=80)

        # Nhóm các event theo period (giữ nguyên thứ tự xuất hiện)
        from mmd2svg.ir import TimelineEvent
        periods_map: dict[str, list[TimelineEvent]] = {}
        for e in ir.events:
            if e.period not in periods_map:
                periods_map[e.period] = []
            periods_map[e.period].append(e)

        CARD_W = 200
        COL_GAP = 28
        PADDING_X = 40
        PADDING_Y = 40
        HEADER_H = 40
        AXIS_GAP = 20
        STEM_GAP = 20
        CARD_GAP = 12

        HEADER_Y = PADDING_Y
        AXIS_Y = HEADER_Y + HEADER_H + AXIS_GAP

        from mmd2svg.layout import Rect, TimelineCardPos, TimelineHeaderPos, TimelineStemPos

        headers: list[TimelineHeaderPos] = []
        stems: list[TimelineStemPos] = []
        cards: list[TimelineCardPos] = []

        for p_idx, (period, events) in enumerate(periods_map.items()):
            col_x = PADDING_X + p_idx * (CARD_W + COL_GAP)
            is_milestone = any(e.is_milestone for e in events)

            # Period Header Card tại đỉnh mỗi cột
            header_rect = Rect(col_x, HEADER_Y, CARD_W, HEADER_H)
            headers.append(TimelineHeaderPos(period=period, rect=header_rect, is_milestone=is_milestone))

            stem_x = col_x + CARD_W / 2
            curr_y = AXIS_Y + STEM_GAP

            for e in events:
                words = e.label.split()
                lines_count = 1
                curr_len = 0
                for w in words:
                    if curr_len + len(w) + 1 <= 24:
                        curr_len += len(w) + 1
                    else:
                        lines_count += 1
                        curr_len = len(w)
                card_h = max(44, 20 + lines_count * 18)

                card_rect = Rect(col_x, curr_y, CARD_W, card_h)
                cards.append(TimelineCardPos(label=e.label, rect=card_rect, is_milestone=e.is_milestone))
                curr_y += card_h + CARD_GAP

            stem_end_y = curr_y - CARD_GAP
            stems.append(TimelineStemPos(x=stem_x, y1=HEADER_Y + HEADER_H, y2=stem_end_y, is_milestone=is_milestone))

        axis_start_x = PADDING_X - 16
        axis_end_x = PADDING_X + len(periods_map) * (CARD_W + COL_GAP) - COL_GAP + 16

        viewbox_w = int(axis_end_x + PADDING_X)
        max_card_bottom = max(c.rect.y2 for c in cards) if cards else AXIS_Y + 60
        viewbox_h = int(max_card_bottom + PADDING_Y)

        return TimelineLayout(
            viewbox_w=viewbox_w,
            viewbox_h=viewbox_h,
            axis_y=AXIS_Y,
            axis_start_x=axis_start_x,
            axis_end_x=axis_end_x,
            headers=headers,
            stems=stems,
            cards=cards,
        )
