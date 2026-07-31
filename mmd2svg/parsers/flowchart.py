"""Parser cho Mermaid flowchart (graph-based).

Cú pháp hỗ trợ (tập con tối giản, đủ cho hình minh hoạ tài liệu):

    flowchart TD
      A[Start] --> B{Decision}
      B -->|Yes| C[Do X]
      B -->|No| D[Do Y]
      C --> E((End))

- Khai báo đầu dòng: `flowchart` hoặc `graph` + hướng (TD/LR/..., hướng bị bỏ qua ở IR).
- Node id + shape: `id[label]` (rect), `id(label)` hoặc `id([label])` (oval), `id{label}` (diamond),
  `id((label))` (oval — dùng cho start/end tròn).
- Node không khai shape/label -> rect, label = id.
- Cạnh: `A --> B`, `A -->|label| B`, `A -- label --> B`.
- Comment dòng bắt đầu bằng `%%` bị bỏ qua.
"""
from __future__ import annotations

import re

from mmd2svg.base import Parser
from mmd2svg.ir import FEdge, FlowChartIR, FNode

_HEADER_RE = re.compile(r"^(flowchart|graph)\s+\w*", re.IGNORECASE)
_COMMENT_RE = re.compile(r"^\s*%%")

_NODE_SHAPES = [
    # (regex thân node, shape) — thử theo thứ tự cụ thể -> chung chung.
    (re.compile(r"^([A-Za-z0-9_]+)\(\((.*)\)\)$"), "oval"),
    (re.compile(r"^([A-Za-z0-9_]+)\(\[(.*)\]\)$"), "oval"),
    (re.compile(r"^([A-Za-z0-9_]+)\{(.*)\}$"), "diamond"),
    (re.compile(r"^([A-Za-z0-9_]+)\((.*)\)$"), "oval"),
    (re.compile(r"^([A-Za-z0-9_]+)\[(.*)\]$"), "rect"),
    (re.compile(r"^([A-Za-z0-9_]+)$"), "rect"),
]

# Tách một dòng cạnh thành 2 nửa quanh mũi tên "-->", chấp nhận:
#   A --> B
#   A -- label --> B
#   A -->|label| B
_ARROW_SPLIT_RE = re.compile(r"--\s*(?P<inline_label>[^-]+?)\s*-->|-->")
_PIPE_LABEL_RE = re.compile(r"^\|(?P<label>[^|]*)\|\s*(?P<rest>.*)$")

MAX_NODES = 9
MAX_EDGES = 12


def _parse_node_token(token: str) -> FNode:
    token = token.strip()
    for pattern, shape in _NODE_SHAPES:
        m = pattern.match(token)
        if m:
            node_id = m.group(1)
            label = m.group(2) if m.lastindex and m.lastindex >= 2 else node_id
            return FNode(id=node_id, label=label.strip(), shape=shape)
    node_id = re.split(r"[\[\(\{]", token)[0].strip()
    return FNode(id=node_id or token, label=token, shape="rect")


def _split_edge_line(line: str):
    """Trả về (src_token, label, dst_token) hoặc None nếu không phải dòng cạnh."""
    m = _ARROW_SPLIT_RE.search(line)
    if not m:
        return None
    src_token = line[: m.start()].strip()
    rest = line[m.end():].strip()
    label = m.group("inline_label")
    label = label.strip() if label else None

    pipe_m = _PIPE_LABEL_RE.match(rest)
    if pipe_m:
        label = pipe_m.group("label").strip()
        dst_token = pipe_m.group("rest").strip()
    else:
        dst_token = rest

    if not src_token or not dst_token:
        return None
    return src_token, label, dst_token


class FlowChartParser(Parser):
    def parse(self, text: str) -> FlowChartIR:
        warnings: list[str] = []
        nodes: dict[str, FNode] = {}
        edges: list[FEdge] = []
        title: str | None = None

        _TITLE_RE = re.compile(r"^\s*title\s+(.+)$", re.IGNORECASE)

        lines = [ln for ln in text.splitlines() if ln.strip() and not _COMMENT_RE.match(ln)]
        body_lines = []
        for ln in lines:
            if _HEADER_RE.match(ln.strip()):
                continue
            tm = _TITLE_RE.match(ln.strip())
            if tm:
                title = tm.group(1).strip()
                continue
            body_lines.append(ln.strip())

        for ln in body_lines:
            split = _split_edge_line(ln)
            if split:
                src_token, label, dst_token = split
                src_node = _parse_node_token(src_token)
                dst_node = _parse_node_token(dst_token)

                if src_node.id not in nodes:
                    nodes[src_node.id] = src_node
                else:
                    _merge_shape(nodes[src_node.id], src_node)
                if dst_node.id not in nodes:
                    nodes[dst_node.id] = dst_node
                else:
                    _merge_shape(nodes[dst_node.id], dst_node)

                edges.append(FEdge(source=src_node.id, target=dst_node.id, label=label))
                continue

            # Không phải cạnh -> có thể là khai báo node đơn lẻ (vd: `A[Start]`).
            if re.match(r"^[A-Za-z0-9_]+", ln):
                node = _parse_node_token(ln)
                if node.id not in nodes:
                    nodes[node.id] = node
                else:
                    _merge_shape(nodes[node.id], node)
                continue

            warnings.append(f"Không hiểu cú pháp dòng: {ln!r}")

        if len(nodes) > MAX_NODES:
            warnings.append(
                f"Vượt ngân sách độ phức tạp: {len(nodes)} node > {MAX_NODES} cho phép"
            )
        if len(edges) > MAX_EDGES:
            warnings.append(
                f"Vượt ngân sách độ phức tạp: {len(edges)} cạnh > {MAX_EDGES} cho phép"
            )

        return FlowChartIR(title=title, nodes=list(nodes.values()), edges=edges, warnings=warnings)


def _merge_shape(existing: FNode, new: FNode) -> None:
    """Nếu node đã khai báo trước đó không có label/shape rõ ràng, dùng lần khai báo sau."""
    if new.shape != "rect" and existing.shape == "rect" and existing.label == existing.id:
        existing.shape = new.shape
        existing.label = new.label
    elif existing.label == existing.id and new.label != new.id:
        existing.label = new.label
