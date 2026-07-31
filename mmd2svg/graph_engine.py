"""Graph-based layout engine — 4 hàm thuần dùng chung cho flowchart & state machine.

Xem mục 3 DESIGN.md. Node được biểu diễn bằng id (str), edge là tuple (source, target).
Không phụ thuộc IR/Layout cụ thể của loại diagram nào — LayoutBuilder của từng loại
map field riêng của mình sang các kiểu dữ liệu tối giản ở đây rồi map ngược lại.
"""
from __future__ import annotations

from mmd2svg.layout import EdgeRoute, Point, Rect

Edge = tuple[str, str]

DEFAULT_COL_GAP = 64
DEFAULT_ROW_GAP = 32

# Khoảng cách tối thiểu (px) giữa 1 điểm xuất phát/vào node và điểm bẻ góc gần nhất —
# áp dụng cho MỌI loại diagram dùng route(), theo yêu cầu "không được bẻ sát ngay tại node".
STUB = 16


# ---------------------------------------------------------------------------
# Bước 1: back-edge detection + rank
# ---------------------------------------------------------------------------


def find_back_edges(nodes: list[str], edges: list[Edge]) -> set[Edge]:
    """DFS phát hiện cạnh trỏ về node đang trong quá trình duyệt dở (back-edge)."""
    adjacency: dict[str, list[str]] = {n: [] for n in nodes}
    for src, dst in edges:
        adjacency.setdefault(src, []).append(dst)

    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {n: WHITE for n in nodes}
    back_edges: set[Edge] = set()

    def dfs(u: str) -> None:
        color[u] = GRAY
        for v in adjacency.get(u, []):
            if color.get(v, WHITE) == GRAY:
                back_edges.add((u, v))
            elif color.get(v, WHITE) == WHITE:
                dfs(v)
        color[u] = BLACK

    for n in nodes:
        if color[n] == WHITE:
            dfs(n)
    return back_edges


def rank(nodes: list[str], edges: list[Edge]) -> dict[str, int]:
    """Xếp tầng theo 'đường đi dài nhất': rank[node] = max(rank[cha]) + 1.

    Loại bỏ back-edge trước khi xếp tầng để tránh vòng lặp vô hạn.
    """
    back_edges = find_back_edges(nodes, edges)
    acyclic_edges = [e for e in edges if e not in back_edges]

    children: dict[str, list[str]] = {n: [] for n in nodes}
    indegree: dict[str, int] = {n: 0 for n in nodes}
    for src, dst in acyclic_edges:
        children.setdefault(src, []).append(dst)
        indegree[dst] = indegree.get(dst, 0) + 1

    ranks: dict[str, int] = {n: 0 for n in nodes}
    # Topo-order (Kahn) trên đồ thị đã bỏ back-edge, rồi lan truyền longest-path.
    from collections import deque

    queue: deque[str] = deque(n for n in nodes if indegree.get(n, 0) == 0)
    visited_count = 0
    order_list: list[str] = []
    indegree_work = dict(indegree)
    while queue:
        u = queue.popleft()
        order_list.append(u)
        visited_count += 1
        for v in children.get(u, []):
            indegree_work[v] -= 1
            if indegree_work[v] == 0:
                queue.append(v)

    for u in order_list:
        for v in children.get(u, []):
            if ranks[v] < ranks[u] + 1:
                ranks[v] = ranks[u] + 1

    return ranks


# ---------------------------------------------------------------------------
# Bước 2: order (barycenter heuristic, 2 lượt)
# ---------------------------------------------------------------------------


def order(nodes: list[str], rank_map: dict[str, int], edges: list[Edge]) -> dict[str, int]:
    """Heuristic trọng tâm (barycenter), 2 lượt: top-down rồi bottom-up.

    Deterministic: input giống nhau luôn ra output giống nhau (tie-break theo
    thứ tự xuất hiện ban đầu trong `nodes`).
    """
    layers: dict[int, list[str]] = {}
    for n in nodes:
        layers.setdefault(rank_map[n], []).append(n)

    max_rank = max(layers) if layers else 0
    # order ban đầu: giữ nguyên thứ tự xuất hiện trong `nodes`.
    order_map: dict[str, int] = {}
    for r in sorted(layers):
        for i, n in enumerate(layers[r]):
            order_map[n] = i

    parents: dict[str, list[str]] = {n: [] for n in nodes}
    children: dict[str, list[str]] = {n: [] for n in nodes}
    for src, dst in edges:
        if src in order_map and dst in order_map:
            children.setdefault(src, []).append(dst)
            parents.setdefault(dst, []).append(src)

    def barycenter(n: str, neighbors: dict[str, list[str]]) -> float:
        neigh = neighbors.get(n, [])
        if not neigh:
            return order_map[n]
        return sum(order_map[m] for m in neigh) / len(neigh)

    def resweep(neighbors: dict[str, list[str]], rank_iter) -> None:
        for r in rank_iter:
            layer = layers.get(r, [])
            if not layer:
                continue
            scored = sorted(
                layer, key=lambda n: (barycenter(n, neighbors), layer.index(n))
            )
            for i, n in enumerate(scored):
                order_map[n] = i

    # Lượt 1: trên xuống, dùng vị trí cha (tầng trước) đã có thứ tự.
    resweep(parents, range(0, max_rank + 1))
    # Lượt 2: dưới lên, dùng vị trí con (tầng sau) để sửa lại thứ tự.
    resweep(children, range(max_rank, -1, -1))

    return order_map


# ---------------------------------------------------------------------------
# Bước 3: position (thuần công thức hình học)
# ---------------------------------------------------------------------------


def position(
    rank_map: dict[str, int],
    order_map: dict[str, int],
    sizes: dict[str, tuple[float, float]],
    col_gap: float = DEFAULT_COL_GAP,
    row_gap: float = DEFAULT_ROW_GAP,
) -> dict[str, Rect]:
    """x = rank * (col_width + col_gap), y = order * (row_height + row_gap).

    Cột ít node hơn được căn giữa so với cột đông node nhất theo trục dọc.
    """
    layers: dict[int, list[str]] = {}
    for n, r in rank_map.items():
        layers.setdefault(r, []).append(n)

    col_width = max((w for w, _ in sizes.values()), default=120)
    row_height = max((h for _, h in sizes.values()), default=48)

    max_layer_count = max((len(v) for v in layers.values()), default=1)
    total_h = max_layer_count * row_height + (max_layer_count - 1) * row_gap

    rects: dict[str, Rect] = {}
    for r, members in layers.items():
        x = r * (col_width + col_gap)
        layer_h = len(members) * row_height + (len(members) - 1) * row_gap
        y_offset = (total_h - layer_h) / 2  # căn giữa cột so với cột đông nhất
        sorted_members = sorted(members, key=lambda n: order_map[n])
        for i, n in enumerate(sorted_members):
            w, h = sizes.get(n, (col_width, row_height))
            x_centered = x + (col_width - w) / 2
            y = y_offset + i * (row_height + row_gap) + (row_height - h) / 2
            rects[n] = Rect(x_centered, y, w, h)

    return rects


# ---------------------------------------------------------------------------
# Bước 4: route (elbow router, né vật cản)
#
# Nguyên tắc bắt buộc (áp dụng cho mọi cạnh do route() sinh ra):
#   - Điểm xuất phát luôn là trung điểm của MỘT trong 4 cạnh bounding box của
#     node nguồn, hướng ra vuông góc với cạnh đó.
#   - Điểm đến luôn là trung điểm của MỘT trong 4 cạnh bounding box của node
#     đích, hướng vào vuông góc với cạnh đó.
#   - Trước khi bẻ góc, đường đi phải đi một đoạn tối thiểu STUB kể từ node
#     nguồn/node đích — không bẻ sát ngay tại node.
#   - Vì `position()` luôn xếp rank dọc theo trục x (mục 3 DESIGN.md), một
#     cạnh nối 2 rank khác nhau luôn là quan hệ trái-phải (exit phải/trái);
#     chỉ khi 2 node cùng cột (cùng rank, khác order) mới là quan hệ trên-dưới.
# ---------------------------------------------------------------------------


_OPPOSITE = {"left": "right", "right": "left", "top": "bottom", "bottom": "top"}

# Vai trò của mỗi midpoint: EXIT_ONLY cho phép thêm exit nhưng từ chối entry;
# ENTRY_ONLY cho phép thêm entry nhưng từ chối exit.
_ROLE_EXIT  = "exit"
_ROLE_ENTRY = "entry"

# Hướng vector ra ngoài node theo từng cạnh (dùng trong _elbow_for_sides).
_SIDE_OUT: dict[str, tuple[float, float]] = {
    "right": (1, 0), "left": (-1, 0),
    "top":   (0, -1), "bottom": (0, 1),
}


def _side_point(rect: Rect, side: str) -> Point:
    if side == "left":
        return Point(rect.x, rect.cy)
    if side == "right":
        return Point(rect.x2, rect.cy)
    if side == "top":
        return Point(rect.cx, rect.y)
    return Point(rect.cx, rect.y2)  # bottom


def _dedupe(points: list[Point]) -> list[Point]:
    result = [points[0]]
    for p in points[1:]:
        if p.x != result[-1].x or p.y != result[-1].y:
            result.append(p)
    return result


def _clamp_mid(v1: float, v2: float, stub: float = STUB) -> float:
    """Điểm bẻ góc giữa v1 và v2, cách cả 2 đầu tối thiểu `stub` khi khoảng
    cách đủ lớn; nếu quá ngắn, dùng trung điểm thuần tuý (không thể đạt đủ
    stub cả 2 phía cùng lúc)."""
    lo, hi = sorted((v1, v2))
    mid = (v1 + v2) / 2
    if hi - lo > 2 * stub:
        mid = min(max(mid, lo + stub), hi - stub)
    return mid


def _obstacles(edge: Edge, rects: dict[str, Rect]) -> list[Rect]:
    src, dst = edge
    return [r for nid, r in rects.items() if nid not in (src, dst)]


def _edge_attach_side(a: Rect, b: Rect) -> str:
    """Cạnh tự nhiên của `a` để xuất phát hướng về `b`.
    Rank xếp theo trục x: lệch cx → quan hệ trái-phải; cùng cx → trên-dưới."""
    if a.cx == b.cx:
        return "bottom" if b.cy >= a.cy else "top"
    return "right" if b.cx >= a.cx else "left"


def _assign_sides(
    edges: list[Edge],
    rects: dict[str, Rect],
    back_edges: set[Edge],
) -> dict[Edge, tuple[str, str]]:
    """Phân công (exit_side, entry_side) cho từng edge, tuân thủ ràng buộc:
      EXIT_ONLY  — cạnh đã dùng làm exit: cho phép thêm exit, từ chối mọi entry.
      ENTRY_ONLY — cạnh đã dùng làm entry: cho phép thêm entry, từ chối mọi exit.

    Ưu tiên: forward edges trước (theo thứ tự gốc), back-edges sau.
    Khi side ưu tiên bị xung đột, fallback theo thứ tự phụ thuộc vị trí tương đối
    giữa src và dst để chọn side hợp lý về mặt hình học.
    """
    roles: dict[tuple[str, str], str] = {}  # (node_id, side) -> role

    def available(node: str, side: str, role: str) -> bool:
        current = roles.get((node, side))
        return current is None or current == role

    def _exit_order(natural: str, a: Rect, b: Rect) -> list[str]:
        """Ưu tiên fallback exit: thử side gần hướng đích trước."""
        if natural in ("left", "right"):
            sec, ter = ("top", "bottom") if b.cy <= a.cy else ("bottom", "top")
        else:
            sec, ter = ("left", "right") if b.cx <= a.cx else ("right", "left")
        return [natural, sec, ter, _OPPOSITE[natural]]

    def _entry_order(natural: str, a: Rect, b: Rect) -> list[str]:
        """Ưu tiên fallback entry: thử side gần phía src trước."""
        if natural in ("left", "right"):
            sec, ter = ("bottom", "top") if a.cy >= b.cy else ("top", "bottom")
        else:
            sec, ter = ("right", "left") if a.cx >= b.cx else ("left", "right")
        return [natural, sec, ter, _OPPOSITE[natural]]

    forward = [e for e in edges if e not in back_edges]
    backs   = [e for e in edges if e in back_edges]
    assignments: dict[Edge, tuple[str, str]] = {}

    for edge in forward + backs:
        src, dst = edge
        a, b = rects[src], rects[dst]
        nat_exit  = _edge_attach_side(a, b)
        nat_entry = _OPPOSITE[nat_exit]

        exit_side = next(
            (s for s in _exit_order(nat_exit, a, b)   if available(src, s, _ROLE_EXIT)),
            nat_exit,
        )
        entry_side = next(
            (s for s in _entry_order(nat_entry, a, b) if available(dst, s, _ROLE_ENTRY)),
            nat_entry,
        )

        roles[(src, exit_side)]  = _ROLE_EXIT
        roles[(dst, entry_side)] = _ROLE_ENTRY
        assignments[edge] = (exit_side, entry_side)

    return assignments


def _can_go_straight(points: list[Point], obstacles: list[Rect]) -> bool:
    """Đường thẳng (2 điểm) có hợp lệ không: không cắt bất kỳ vật cản nào."""
    return not any(_route_blocked_by(points, o) for o in obstacles)


def _straight_route(a: Rect, b: Rect) -> list[Point]:
    side = _edge_attach_side(a, b)
    start = _side_point(a, side)
    end = _side_point(b, _OPPOSITE[side])
    return [start, end]


def _elbow_for_sides(
    a: Rect, b: Rect, exit_side: str, entry_side: str
) -> list[Point]:
    """Sinh path orthogonal cho bất kỳ cặp (exit_side, entry_side) được gán trước.

    Đoạn đầu vuông góc với exit_side (dài STUB), đoạn cuối vuông góc với
    entry_side (dài STUB). Hai stub được nối qua đoạn chuyển hướng:
      - Cùng trục (h↔h, v↔v): [start, p_exit, mid, p_entry, end]  — 5 điểm
      - Khác trục (h↔v, v↔h): [start, p_exit, corner, p_entry, end] — 4-5 điểm
    """
    start = _side_point(a, exit_side)
    end   = _side_point(b, entry_side)

    edx, edy = _SIDE_OUT[exit_side]    # hướng ra khỏi node nguồn
    idx, idy = _SIDE_OUT[entry_side]   # hướng outward từ node đích (ngược chiều vào)

    p_exit  = Point(start.x + edx * STUB, start.y + edy * STUB)
    p_entry = Point(end.x   + idx * STUB, end.y   + idy * STUB)

    exit_h  = exit_side  in ("left", "right")
    entry_h = entry_side in ("left", "right")

    if exit_h == entry_h:
        # Cùng trục → 1 đoạn chuyển hướng vuông góc
        mid = Point(p_exit.x, p_entry.y) if exit_h else Point(p_entry.x, p_exit.y)
        pts = [start, p_exit, mid, p_entry, end]
    else:
        # Khác trục → L-shape, corner tại giao điểm 2 vector stub
        corner = Point(p_entry.x, p_exit.y) if exit_h else Point(p_exit.x, p_entry.y)
        pts = [start, p_exit, corner, p_entry, end]

    return _dedupe(pts)


def _route_blocked_by(points: list[Point], obstacle: Rect) -> bool:
    tmp = EdgeRoute(source="", target="", points=points)
    return tmp.intersects(obstacle)


def _local_detour(a: Rect, b: Rect, obstacle: Rect) -> list[Point] | None:
    """Nếu một đầu mút có y nằm ngoài phạm vi y của vật cản, né cục bộ: ra
    khỏi cạnh trái/phải một đoạn tối thiểu STUB, rẽ tới 'lane' an toàn (y của
    đầu mút nằm ngoài phạm vi vật cản), đi ngang qua, rồi rẽ vào lại y của
    đầu kia — cũng cách nó tối thiểu STUB trước khi cập bến."""
    a_outside = a.y2 <= obstacle.y or a.y >= obstacle.y2
    b_outside = b.y2 <= obstacle.y or b.y >= obstacle.y2
    if not (a_outside or b_outside):
        return None

    exit_side = "right" if b.cx >= a.cx else "left"
    entry_side = _OPPOSITE[exit_side]
    start = _side_point(a, exit_side)
    end = _side_point(b, entry_side)
    lane_y = start.y if a_outside else end.y

    sign = 1 if exit_side == "right" else -1
    stub_a_x = start.x + sign * STUB
    stub_b_x = end.x - sign * STUB
    # Đảm bảo 2 điểm stub không "vượt qua nhau" khi khoảng cách quá ngắn.
    if (stub_a_x - stub_b_x) * sign > 0:
        stub_a_x = stub_b_x = (start.x + end.x) / 2

    points = [
        start,
        Point(stub_a_x, start.y),
        Point(stub_a_x, lane_y),
        Point(stub_b_x, lane_y),
        Point(stub_b_x, end.y),
        end,
    ]
    return _dedupe(points)


def _top_detour(a: Rect, b: Rect, all_rects: list[Rect], lane_index: int = 0) -> list[Point]:
    """Phương án dự phòng: vòng lên hẳn phía trên toàn bộ sơ đồ.
    Nếu có node nằm đè trên đầu a hoặc b, tự động đi luồn ra hành lang bên cạnh
    để không bao giờ đâm xuyên qua bất kỳ node nào.
    """
    lane_step = 20
    top_y = min(r.y for r in all_rects) - max(STUB, 24) - (lane_index * lane_step)

    # 1. Xác định đường thoát khỏi node a
    obstacles_above_a = [
        r for r in all_rects if r != a and r.y2 <= a.y + 2 and r.x <= a.cx <= r.x2
    ]
    if obstacles_above_a:
        exit_pt = _side_point(a, "right")
        corridor_a_x = max(a.x2, max(r.x2 for r in obstacles_above_a)) + 20
        start_pts = [exit_pt, Point(corridor_a_x, exit_pt.y), Point(corridor_a_x, top_y)]
    else:
        start_pt = _side_point(a, "top")
        start_pts = [start_pt, Point(start_pt.x, top_y)]

    # 2. Xác định đường đi vào node b
    obstacles_above_b = [
        r for r in all_rects if r != b and r.y2 <= b.y + 2 and r.x <= b.cx <= r.x2
    ]
    if obstacles_above_b:
        entry_pt = _side_point(b, "right")
        corridor_b_x = max(b.x2, max(r.x2 for r in obstacles_above_b)) + 20
        end_pts = [Point(corridor_b_x, top_y), Point(corridor_b_x, entry_pt.y), entry_pt]
    else:
        end_pt = _side_point(b, "top")
        end_pts = [Point(end_pt.x, top_y), end_pt]

    return _dedupe(start_pts + end_pts)


def route(edges: list[Edge], rects: dict[str, Rect], back_edges: set[Edge] | None = None,
          labels: dict[Edge, str | None] | None = None) -> list[EdgeRoute]:
    """Tính đường đi cho tất cả edges.

    Quy trình:
      1. _assign_sides() phân công (exit_side, entry_side) per edge theo ràng
         buộc EXIT_ONLY / ENTRY_ONLY — bidirectional tự động được tách side.
      2. Pre-calculate các edges cần _top_detour và gán lane_index theo độ dài quãng đường
         để các đường detour nằm lồng vào nhau, không bị đè lên nhau.
      3. _elbow_for_sides() sinh path vuông góc từ các side đã gán.
      4. Nếu bị chặn: _local_detour() → _top_detour(lane_index).
    """
    back_edges = back_edges or set()
    labels = labels or {}
    routes: list[EdgeRoute] = []
    all_rects = list(rects.values())

    # Bước 1: phân công side trước khi tính đường đi.
    assignments = _assign_sides(edges, rects, back_edges)

    # Bước 2: Phân tích trước các cạnh sẽ rơi vào _top_detour để chia lane riêng.
    top_detour_candidates: list[tuple[Edge, float]] = []
    for edge in edges:
        src, dst = edge
        a, b = rects[src], rects[dst]
        exit_side, entry_side = assignments[edge]
        obstacles = _obstacles(edge, rects)
        elbow_pts = _elbow_for_sides(a, b, exit_side, entry_side)
        blocking = [o for o in obstacles if _route_blocked_by(elbow_pts, o)]
        if blocking:
            detoured = None
            for obstacle in blocking:
                candidate = _local_detour(a, b, obstacle)
                if candidate and not any(_route_blocked_by(candidate, o) for o in obstacles):
                    detoured = candidate
                    break
            if detoured is None:
                top_detour_candidates.append((edge, abs(b.cx - a.cx)))

    top_detour_candidates.sort(key=lambda x: x[1])
    top_lane_map = {edge: idx for idx, (edge, _) in enumerate(top_detour_candidates)}

    for edge in edges:
        src, dst = edge
        a, b = rects[src], rects[dst]
        label    = labels.get(edge)
        is_back  = edge in back_edges
        exit_side, entry_side = assignments[edge]
        obstacles = _obstacles(edge, rects)

        # Bước 3: thử path với side đã gán.
        elbow_pts = _elbow_for_sides(a, b, exit_side, entry_side)
        blocking  = [o for o in obstacles if _route_blocked_by(elbow_pts, o)]

        if not blocking:
            routes.append(EdgeRoute(source=src, target=dst, points=elbow_pts,
                                     label=label, dashed=is_back))
            continue

        # Bước 4a: né cục bộ vật cản.
        detoured = None
        for obstacle in blocking:
            candidate = _local_detour(a, b, obstacle)
            if candidate is not None:
                if not any(_route_blocked_by(candidate, o) for o in obstacles):
                    detoured = candidate
                    break

        # Bước 4b: fallback — vòng lên trên toàn bộ sơ đồ ở lane_index tương ứng.
        if detoured is None:
            lane_idx = top_lane_map.get(edge, 0)
            detoured = _top_detour(a, b, all_rects, lane_index=lane_idx)

        routes.append(EdgeRoute(source=src, target=dst, points=_dedupe(detoured),
                                 label=label, dashed=is_back))

    return routes
