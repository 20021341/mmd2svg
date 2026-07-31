"""Primitives SVG dùng chung, theo mục 6 style-guide.md của skill diagram-design."""
from __future__ import annotations

from mmd2svg.layout import EdgeRoute, Rect
from mmd2svg.theme import Theme


def rect_node(rect: Rect, fill: str, stroke: str, rx: int = 6) -> str:
    return (
        f'<rect x="{rect.x:.0f}" y="{rect.y:.0f}" width="{rect.w:.0f}" '
        f'height="{rect.h:.0f}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="1"/>'
    )


def oval_node(rect: Rect, fill: str, stroke: str) -> str:
    return (
        f'<ellipse cx="{rect.cx:.0f}" cy="{rect.cy:.0f}" rx="{rect.w / 2:.0f}" '
        f'ry="{rect.h / 2:.0f}" fill="{fill}" stroke="{stroke}" stroke-width="1"/>'
    )


def diamond_node(rect: Rect, fill: str, stroke: str) -> str:
    cx, cy = rect.cx, rect.cy
    hw, hh = rect.w / 2, rect.h / 2
    points = f"{cx:.0f},{rect.y:.0f} {rect.x2:.0f},{cy:.0f} {cx:.0f},{rect.y2:.0f} {rect.x:.0f},{cy:.0f}"
    return f'<polygon points="{points}" fill="{fill}" stroke="{stroke}" stroke-width="1"/>'


def node_label(cx: float, cy: float, text: str, fill: str, font_size: int = 12) -> str:
    escaped = _escape(text)
    return (
        f'<text x="{cx:.0f}" y="{cy + 4:.0f}" fill="{fill}" font-size="{font_size}" '
        f'font-weight="600" font-family="\'Geist\', sans-serif" text-anchor="middle">{escaped}</text>'
    )


def multiline_node_label(cx: float, cy: float, text: str, fill: str, font_size: int = 11, max_chars_per_line: int = 22) -> str:
    words = text.split()
    lines: list[str] = []
    curr: list[str] = []
    curr_len = 0
    for w in words:
        if curr_len + len(w) + (1 if curr else 0) <= max_chars_per_line:
            curr.append(w)
            curr_len += len(w) + (1 if curr else 0)
        else:
            if curr:
                lines.append(" ".join(curr))
            curr = [w]
            curr_len = len(w)
    if curr:
        lines.append(" ".join(curr))

    line_height = font_size + 4
    total_height = len(lines) * line_height
    start_y = cy - (total_height / 2) + (font_size / 2) + 2

    tspans = []
    for i, ln in enumerate(lines):
        y_pos = start_y + i * line_height
        tspans.append(f'<tspan x="{cx:.0f}" y="{y_pos:.0f}">{_escape(ln)}</tspan>')

    return (
        f'<text fill="{fill}" font-size="{font_size}" font-weight="500" '
        f'font-family="\'Geist\', sans-serif" text-anchor="middle">{"".join(tspans)}</text>'
    )


def merge_dot(cx: float, cy: float, fill: str, r: int = 4) -> str:
    return f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r}" fill="{fill}"/>'


def filled_dot(cx: float, cy: float, fill: str, r: int = 6) -> str:
    return f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r}" fill="{fill}"/>'


def ringed_dot(cx: float, cy: float, stroke: str, fill: str, outer_r: int = 8, inner_r: int = 5) -> str:
    return (
        f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{outer_r}" fill="none" stroke="{stroke}" stroke-width="1.2"/>'
        f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{inner_r}" fill="{fill}"/>'
    )


def arrow_path(route: EdgeRoute, stroke: str, marker: str = "arrow", corner_radius: float = 6) -> str:
    d = _points_to_rounded_path(route.points, corner_radius)
    dash = ' stroke-dasharray="5,4"' if route.dashed else ""
    return (
        f'<path d="{d}" fill="none" stroke="{stroke}" stroke-width="1"{dash} '
        f'marker-end="url(#{marker})"/>'
    )


def _points_to_path(points) -> str:
    parts = [f"M {points[0].x:.0f} {points[0].y:.0f}"]
    for p in points[1:]:
        parts.append(f"L {p.x:.0f} {p.y:.0f}")
    return " ".join(parts)


def _points_to_rounded_path(points, radius: float) -> str:
    """Vẽ path orthogonal với bo góc tại mỗi điểm bẻ (không phải 2 đầu mút).

    Mỗi góc giữa được cắt bớt tối đa `radius` (nhưng không vượt quá nửa chiều
    dài đoạn liền kề, để không đảo ngược hướng đi trên đoạn ngắn) và nối bằng
    cung tròn bậc 2 (Q), giữ nguyên orthogonal ở phần thẳng.
    """
    if len(points) <= 2:
        return _points_to_path(points)

    parts = [f"M {points[0].x:.0f} {points[0].y:.0f}"]
    n = len(points)
    for i in range(1, n - 1):
        prev_p, corner, next_p = points[i - 1], points[i], points[i + 1]
        seg_in = ((corner.x - prev_p.x) ** 2 + (corner.y - prev_p.y) ** 2) ** 0.5
        seg_out = ((next_p.x - corner.x) ** 2 + (next_p.y - corner.y) ** 2) ** 0.5
        r = min(radius, seg_in / 2, seg_out / 2)

        if r <= 0.5:
            parts.append(f"L {corner.x:.0f} {corner.y:.0f}")
            continue

        # Điểm cắt bớt trên đoạn vào và đoạn ra, cách góc đúng `r`.
        in_ratio = r / seg_in if seg_in else 0
        out_ratio = r / seg_out if seg_out else 0
        pre = (
            corner.x - (corner.x - prev_p.x) * in_ratio,
            corner.y - (corner.y - prev_p.y) * in_ratio,
        )
        post = (
            corner.x + (next_p.x - corner.x) * out_ratio,
            corner.y + (next_p.y - corner.y) * out_ratio,
        )
        parts.append(f"L {pre[0]:.1f} {pre[1]:.1f}")
        parts.append(f"Q {corner.x:.1f} {corner.y:.1f} {post[0]:.1f} {post[1]:.1f}")

    last = points[-1]
    parts.append(f"L {last.x:.0f} {last.y:.0f}")
    return " ".join(parts)


def arrow_label(mid_x: float, mid_y: float, text: str, paper: str, muted: str) -> str:
    """Mask rect + label với gap 6-10px phía trên đường nối (mid_y là y của connector)."""
    escaped = _escape(text)
    label_y = mid_y - 11
    mask_y = mid_y - 20
    width = max(24, len(text) * 6)
    return (
        f'<rect x="{mid_x - width / 2:.0f}" y="{mask_y:.0f}" width="{width:.0f}" height="12" rx="2" fill="{paper}"/>'
        f'<text x="{mid_x:.0f}" y="{label_y:.0f}" fill="{muted}" font-size="8" '
        f'font-family="\'Geist Mono\', monospace" text-anchor="middle" letter-spacing="0.06em">{escaped}</text>'
    )


def legend_strip(y: float, width: float, items: list[tuple[str, str]], rule: str, muted: str) -> str:
    """items: list of (swatch_color, label)."""
    frags = [
        f'<line x1="30" y1="{y - 8:.0f}" x2="{width - 30:.0f}" y2="{y - 8:.0f}" '
        f'stroke="{rule}" stroke-width="0.8"/>',
        f'<text x="30" y="{y + 8:.0f}" fill="{muted}" font-size="8" '
        f'font-family="\'Geist Mono\', monospace" letter-spacing="0.14em">LEGEND</text>',
    ]
    x = 140
    for color, label in items:
        frags.append(f'<circle cx="{x:.0f}" cy="{y + 4:.0f}" r="4" fill="{color}"/>')
        frags.append(
            f'<text x="{x + 12:.0f}" y="{y + 8:.0f}" fill="{muted}" font-size="8" '
            f'font-family="\'Geist Mono\', monospace">{_escape(label)}</text>'
        )
        x += 160
    return "".join(frags)


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def lifeline(cx: float, top: float, bottom: float, color: str) -> str:
    return (
        f'<line x1="{cx:.0f}" y1="{top:.0f}" x2="{cx:.0f}" y2="{bottom:.0f}" '
        f'stroke="{color}" stroke-width="1" stroke-dasharray="3,3"/>'
    )


def activation_bar(cx: float, top: float, bottom: float, fill: str, stroke: str) -> str:
    return (
        f'<rect x="{cx - 4:.0f}" y="{top:.0f}" width="8" height="{bottom - top:.0f}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="0.8"/>'
    )


def message_arrow(x1: float, y: float, x2: float, stroke: str, dashed: bool, marker: str = "arrow") -> str:
    dash = ' stroke-dasharray="5,4"' if dashed else ""
    return (
        f'<line x1="{x1:.0f}" y1="{y:.0f}" x2="{x2:.0f}" y2="{y:.0f}" '
        f'stroke="{stroke}" stroke-width="1"{dash} marker-end="url(#{marker})"/>'
    )


def self_message_loop(x: float, y: float, stroke: str, marker: str = "arrow") -> str:
    """U-shaped loop nhỏ quay lại cùng lifeline."""
    x2 = x + 40
    return (
        f'<path d="M {x:.0f} {y:.0f} C {x2:.0f} {y:.0f}, {x2:.0f} {y + 24:.0f}, {x:.0f} {y + 24:.0f}" '
        f'fill="none" stroke="{stroke}" stroke-width="1" marker-end="url(#{marker})"/>'
    )


def actor_box(cx: float, top: float, label: str, fill: str, stroke: str, ink: str) -> str:
    w, h = 120, 36
    x, y = cx - w / 2, top
    return (
        f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" rx="6" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="1"/>'
        f'<text x="{cx:.0f}" y="{y + h / 2 + 4:.0f}" fill="{ink}" font-size="12" font-weight="600" '
        f'font-family="\'Geist\', sans-serif" text-anchor="middle">{_escape(label)}</text>'
    )


def baseline(x1: float, x2: float, y: float, stroke: str) -> str:
    return f'<line x1="{x1:.0f}" y1="{y:.0f}" x2="{x2:.0f}" y2="{y:.0f}" stroke="{stroke}" stroke-width="1"/>'


def timeline_event_dot(cx: float, y: float, fill: str, is_milestone: bool) -> str:
    r = 6 if is_milestone else 4
    return f'<circle cx="{cx:.0f}" cy="{y:.0f}" r="{r}" fill="{fill}"/>'


def timeline_event_label(cx: float, dot_y: float, text: str, above: bool, ink: str, is_milestone: bool) -> str:
    weight = "600" if is_milestone else "400"
    if above:
        label_y = dot_y - 16
        drop_y2 = dot_y - 4
    else:
        label_y = dot_y + 24
        drop_y2 = dot_y + 4
    drop = f'<line x1="{cx:.0f}" y1="{dot_y:.0f}" x2="{cx:.0f}" y2="{drop_y2:.0f}" stroke="{ink}" stroke-width="1" opacity="0.3"/>'
    text_el = (
        f'<text x="{cx:.0f}" y="{label_y:.0f}" fill="{ink}" font-size="12" font-weight="{weight}" '
        f'font-family="\'Geist\', sans-serif" text-anchor="middle">{_escape(text)}</text>'
    )
    return drop + text_el


def axis_cross(cx: float, cy: float, half_w: float, half_h: float, stroke: str, marker: str = "arrow") -> str:
    h_line = (
        f'<line x1="{cx - half_w:.0f}" y1="{cy:.0f}" x2="{cx + half_w:.0f}" y2="{cy:.0f}" '
        f'stroke="{stroke}" stroke-width="1" marker-end="url(#{marker})"/>'
    )
    v_line = (
        f'<line x1="{cx:.0f}" y1="{cy + half_h:.0f}" x2="{cx:.0f}" y2="{cy - half_h:.0f}" '
        f'stroke="{stroke}" stroke-width="1" marker-end="url(#{marker})"/>'
    )
    return h_line + v_line


def axis_label_tip(x: float, y: float, text: str, ink: str, anchor: str, dominant_baseline: str | None = None) -> str:
    baseline_attr = f' dominant-baseline="{dominant_baseline}"' if dominant_baseline else ""
    return (
        f'<text x="{x:.0f}" y="{y:.0f}" fill="{ink}" font-size="9" font-weight="500" '
        f'font-family="\'Geist Mono\', monospace" text-anchor="{anchor}"{baseline_attr} '
        f'letter-spacing="0.18em">{_escape(text.upper())}</text>'
    )


def quadrant_item_dot(cx: float, cy: float, label: str, fill: str, ink: str) -> str:
    dot = f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="4" fill="{fill}"/>'
    text = (
        f'<text x="{cx + 10:.0f}" y="{cy + 3:.0f}" fill="{ink}" font-size="10" '
        f'font-family="\'Geist\', sans-serif">{_escape(label)}</text>'
    )
    return dot + text
