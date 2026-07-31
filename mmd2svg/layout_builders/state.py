"""LayoutBuilder cho state machine — graph-based, gọi 4 hàm thuần của graph_engine.

Start là dot nhỏ (r=6), End là ringed dot (r=8) — kích thước nhỏ hơn state thường,
để position() dành đủ chỗ nhưng không lãng phí không gian cho node ảo.
"""
from __future__ import annotations

from mmd2svg.base import LayoutBuilder
from mmd2svg.graph_engine import find_back_edges, order, position, rank, route
from mmd2svg.ir import StateMachineIR
from mmd2svg.layout import StateMachineLayout
from mmd2svg.parsers.state import END_ID, START_ID

STATE_W = 140
STATE_H = 48
DOT_SIZE = 20  # bounding box cho start/end dot, đủ chỗ vẽ r=8 + padding
PADDING = 32


class StateMachineLayoutBuilder(LayoutBuilder):
    def layout(self, ir: StateMachineIR) -> StateMachineLayout:
        node_ids = [s.id for s in ir.states]
        edges = [(t.source, t.target) for t in ir.transitions]

        if not node_ids:
            return StateMachineLayout(viewbox_w=PADDING * 2, viewbox_h=PADDING * 2)

        back_edges = find_back_edges(node_ids, edges)
        rank_map = rank(node_ids, edges)
        order_map = order(node_ids, rank_map, edges)

        sizes = {
            s.id: (DOT_SIZE, DOT_SIZE) if s.is_start or s.is_end else (STATE_W, STATE_H)
            for s in ir.states
        }
        rects = position(rank_map, order_map, sizes)
        shifted_rects = {
            nid: r.__class__(r.x + PADDING, r.y + PADDING, r.w, r.h)
            for nid, r in rects.items()
        }

        labels = {(t.source, t.target): t.label for t in ir.transitions}
        routes = route(edges, shifted_rects, back_edges=back_edges, labels=labels)

        # Tính min/max bao gồm cả rects và tất cả route points (detours)
        all_x = [r.x for r in shifted_rects.values()] + [r.x2 for r in shifted_rects.values()]
        all_y = [r.y for r in shifted_rects.values()] + [r.y2 for r in shifted_rects.values()]
        for rt in routes:
            for p in rt.points:
                all_x.append(p.x)
                all_y.append(p.y)

        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)

        offset_x = PADDING - min_x if min_x < PADDING else 0
        offset_y = PADDING - min_y if min_y < PADDING else 0

        if offset_x > 0 or offset_y > 0:
            from mmd2svg.layout import EdgeRoute, Point
            shifted_rects = {
                nid: r.__class__(r.x + offset_x, r.y + offset_y, r.w, r.h)
                for nid, r in shifted_rects.items()
            }
            routes = [
                EdgeRoute(
                    source=rt.source,
                    target=rt.target,
                    points=[Point(p.x + offset_x, p.y + offset_y) for p in rt.points],
                    label=rt.label,
                    dashed=rt.dashed,
                )
                for rt in routes
            ]
            max_x += offset_x
            max_y += offset_y

        node_labels = {s.id: s.label for s in ir.states}
        starts = [s.id for s in ir.states if s.is_start]
        ends = [s.id for s in ir.states if s.is_end]

        return StateMachineLayout(
            viewbox_w=int(max_x + PADDING),
            viewbox_h=int(max_y + PADDING),
            rects=shifted_rects,
            labels=node_labels,
            starts=starts,
            ends=ends,
            routes=routes,
        )
