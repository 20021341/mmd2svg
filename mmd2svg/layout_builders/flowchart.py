"""LayoutBuilder cho flowchart — graph-based, gọi 4 hàm thuần của graph_engine."""
from __future__ import annotations

from mmd2svg.base import LayoutBuilder
from mmd2svg.graph_engine import find_back_edges, order, position, rank, route
from mmd2svg.ir import FlowChartIR
from mmd2svg.layout import FlowChartLayout

NODE_W = 140
NODE_H = 48
DIAMOND_W = 140
DIAMOND_H = 64
PADDING = 32


class FlowChartLayoutBuilder(LayoutBuilder):
    def layout(self, ir: FlowChartIR) -> FlowChartLayout:
        node_ids = [n.id for n in ir.nodes]
        edges = [(e.source, e.target) for e in ir.edges]
        shapes = {n.id: n.shape for n in ir.nodes}
        node_labels = {n.id: n.label for n in ir.nodes}

        if not node_ids:
            return FlowChartLayout(viewbox_w=PADDING * 2, viewbox_h=PADDING * 2)

        back_edges = find_back_edges(node_ids, edges)
        rank_map = rank(node_ids, edges)
        order_map = order(node_ids, rank_map, edges)

        sizes = {
            n.id: (DIAMOND_W, DIAMOND_H) if n.shape == "diamond" else (NODE_W, NODE_H)
            for n in ir.nodes
        }
        rects = position(rank_map, order_map, sizes)

        # Dịch toàn bộ layout vào trong padding.
        shifted_rects = {
            nid: r.__class__(r.x + PADDING, r.y + PADDING, r.w, r.h)
            for nid, r in rects.items()
        }

        labels = {(e.source, e.target): e.label for e in ir.edges}
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

        return FlowChartLayout(
            viewbox_w=int(max_x + PADDING),
            viewbox_h=int(max_y + PADDING),
            rects=shifted_rects,
            shapes=shapes,
            labels=node_labels,
            routes=routes,
        )
