# Solution design

*(Vietnamese version: [DESIGN.vi.md](DESIGN.vi.md))*

## Problem statement

**Input**:
- A piece of text written in Mermaid syntax (e.g. `flowchart TD; A --> B`),
  belonging to one of several diagram types (flowchart, sequence, state
  machine, ER, gantt, quadrant, timeline, ...).
- The `diagram-design` skill (located in `./.skills`).

**Output**: an HTML file containing SVG, where the diagram is redrawn
following one fixed set of design rules — the same color palette, the same
font, the same corner-rounding/gridline treatment — regardless of diagram
type, taken from a `style-guide.md` inside the `diagram-design` skill.

**Constraints**:
- Only small diagrams are supported (complexity budget: roughly ≤9 nodes /
  ≤12 edges per diagram) — this tool is for illustrative figures inside
  documents, not a tool for drawing large system architecture diagrams.
- Only Mermaid diagram types that can be unambiguously mapped onto one of
  the diagram types defined by the style guide are supported; any type
  without a reasonable mapping is out of scope.

## Glossary

| Term | Meaning | Concrete example |
|---|---|---|
| **IR** (Intermediate Representation) | An *interface* marking "this is the output of a Parser," declaring exactly **1 field shared by every type**: `warnings` — nothing else is declared on it. Each diagram type declares its own subclass inheriting from `IR`, and that subclass is where type-specific properties live (node names, edge labels, dates, ...). It never holds coordinates or colors. | `IR` declares `warnings: list[str]`. `FlowChartIR` (inherits `IR`) adds `nodes`, `edges`. `GanttChartIR` (inherits `IR`) adds `tasks`, `title`. Both already have `warnings` from `IR`, no need to redeclare it. |
| **Layout** | An *interface* similar to `IR`, marking "this is the output of a Layout Builder," declaring exactly **2 fields shared by every type**: `viewbox_w`, `viewbox_h` (every diagram, regardless of type, needs a viewport size so the `Renderer` can build a `Canvas`). Each diagram type has its own subclass declaring concrete coordinates. Only numbers (x, y, width, height, edge paths), never colors. | `Layout` declares `viewbox_w`, `viewbox_h`. `FlowChartLayout` (inherits `Layout`) adds `rects: dict[str, Rect]`, `routes: list[EdgeRoute]`. `GanttChartLayout` adds `task_rows`, with no `rects` concept like flowchart has. |
| **Theme** | A lookup table of fixed design values — role-based colors (background, text, accent, ...), font name, stroke width — for **exactly 2 available choices**: `light` and `dark`. Not hex codes scattered across the code, but a single table per light/dark mode. No external customization/override support. A `Theme` is loaded once per render, then passed into the `Canvas`. | `theme.accent` = accent color; `Theme.load(skin="dark")` loads the built-in dark palette. |
| **Canvas** | A temporary container for the SVG fragments concatenated together while the Renderer is running — accumulating `<rect>`, `<path>`, `<text>` fragments, etc., and tracking overall viewport size. **It always keeps a reference to the `Theme`** (passed in at construction time), so every subsequent drawing function looks up colors through `canvas.theme` instead of receiving `theme` as a separate parameter on every call. It is the *product* of the Render stage, not yet a complete HTML file. Every `Renderer` — regardless of diagram type — returns **the same concrete `Canvas` class**, with no separate `FlowChartCanvas`/`GanttChartCanvas`, because the "SVG container" part is identical across types. | See the full example in section 1.3 below. |
| **Rank** | The position of a node along the horizontal axis in a graph-style layout — nodes at rank 0 come first, rank 1 comes after, and so on. Not a real x coordinate, just a *rank order*, which still needs to be multiplied by a spacing value to become x. | In `A --> B --> C`, A is at rank 0, B at rank 1, C at rank 2. |
| **Order** | The position of a node along the vertical axis, *within the same rank* — the node at order 0 is topmost, order 1 sits below it, and so on. Also not a real y coordinate. | If rank 1 has two nodes B and D, order decides whether B or D is on top. |
| **Back-edge** | An edge in the graph which, if included when computing ranks, would create an infinite loop (because it points back to a node that comes earlier in the traversal). It is temporarily excluded from the ranking step, but is still drawn in the final step (as a dashed, routed-around line). | In `A --> B --> A` (a cycle), the second edge (B → A) is a back-edge. |
| **Registry** | A single data structure mapping "diagram type name" → "the trio of objects that handle that type" (one `Parser`, one `LayoutBuilder`, one `Renderer` — see section 1). It is the single central place that "knows" how many diagram types are supported. | `{"gantt": (GanttChartParser(), GanttChartLayoutBuilder(), GanttChartRenderer()), "flowchart": (...), ...}` |

## Solution overview

```
Mermaid ──Parser──▶ Intermediate Representation ──Layout Builder──▶ layout ──Renderer──▶ SVG
```

- **Parse**: reads Mermaid syntax, understands the "content" of the diagram
  (which nodes/tasks/messages exist, what they're named, how they connect)
  — but **has no idea at all** where a node will sit on screen or what
  color it will get.
- **Layout**: takes that semantic data and computes coordinates (x, y,
  width, height) for every element, plus the path for every connecting
  edge — but **has no idea at all** about colors or fonts.
- **Render**: takes the already-computed coordinates plus a design theme,
  and assembles them into an SVG string.

There are two categories of diagram:
- Formulaic diagrams: diagram types whose element positions can be derived
  directly from the relationships between them (e.g. gantt, timeline,
  quadrant, ...).
- Graph-based diagrams: diagram types where node ordering is **not**
  given in the input — a flowchart only tells you "A connects to B," not
  whether "A should be drawn to the left or right of B." That ordering has
  to be *inferred* from the edge structure, using an actual graph
  algorithm.

> A dedicated graph-based layout engine is needed for graph-based diagram
> types at the Layout Builder stage.

## Implementation

### 1. Base classes

#### 1.1. `IR`

```
class IR:
    warnings: list[str]

# Each diagram type inherits from IR
class FlowChartIR(IR):
    nodes: list[FNode]
    edges: list[FEdge]

class GanttChartIR(IR):
    title: str | None
    tasks: list[Task]
    sections: list[str]

class TimelineChartIR(IR):
    title: str | None
    events: list[TimelineEvent]
```

#### 1.2. `Layout`

```
class Layout:
    viewbox_w: int
    viewbox_h: int

# Each diagram type's layout inherits from Layout
class FlowChartLayout(Layout):
    rects: dict[str, Rect]
    routes: list[EdgeRoute]

class GanttChartLayout(Layout):
    task_rows: list[TaskRow]
    section_zones: list[SectionZone]
```

#### 1.3. `Parser` / `LayoutBuilder` / `Renderer`

```
from abc import ABC, abstractmethod

class Parser(ABC):
    @abstractmethod
    def parse(self, text: str) -> IR

class LayoutBuilder(ABC):
    @abstractmethod
    def layout(self, ir: IR) -> Layout

class Renderer(ABC):
    @abstractmethod
    def render(self, layout: Layout, theme: Theme) -> Canvas
```

Graph-based diagram types use the functions from the graph-based layout
engine pipeline:

```
# Each diagram type's parser inherits from Parser
class FlowChartParser(Parser):
    def parse(self, text: str) -> FlowChartIR:
        ...  # reads flowchart syntax, does NOT compute coordinates, does NOT assign colors
        return FlowChartIR(nodes=..., edges=..., warnings=...)

# Each diagram type's layout builder inherits from LayoutBuilder
class FlowChartLayoutBuilder(LayoutBuilder):
    def layout(self, ir: FlowChartIR) -> FlowChartLayout:
        ... # uses the graph-based layout engine
        return FlowChartLayout(rects=rects, routes=routes, viewbox_w=..., viewbox_h=...)

# Each diagram type's renderer inherits from Renderer
class FlowChartRenderer(Renderer):
    def render(self, layout: FlowChartLayout, theme: Theme) -> Canvas:
        canvas = Canvas(layout.viewbox_w, layout.viewbox_h, theme)
        for node_id, rect in layout.rects.items():
            canvas.add(node_box(rect, theme.box_fill, ...))
        for route in layout.routes:
            canvas.add(arrow_path(route, theme.muted))
        return canvas
```

Formulaic diagram types write their own computation logic specific to that
diagram type:

```
class GanttChartParser(Parser):
    def parse(self, text: str) -> GanttChartIR: ...

class GanttChartLayoutBuilder(LayoutBuilder):
    def layout(self, ir: GanttChartIR) -> GanttChartLayout:
        # pure arithmetic formulas based on dates, does NOT call the graph-based layout engine
        ...

class GanttChartRenderer(Renderer):
    def render(self, layout: GanttChartLayout, theme: Theme) -> Canvas:
        canvas = Canvas(layout.viewbox_w, layout.viewbox_h, theme)
        ...
        return canvas
```

#### 1.4. `Theme` / `Canvas`

`Theme` is an (immutable) lookup table of design values keyed by *role*,
not hex codes scattered around:

```
theme = Theme.load(skin="light")   # or skin="dark" — only 2 choices, no custom parameter
# theme.paper     = "#F7F5F0"   (paper background color)
# theme.ink       = "#1A1A1A"   (primary text color)
# theme.accent    = "#C1440E"   (accent color)
# theme.box_fill  = "#FFFFFF"   (node box fill color)
# theme.muted     = "#8A8A8A"   (secondary color, used for ordinary arrows)
```

`Canvas` **holds a reference to exactly one `Theme` instance** from the
moment it is constructed, and every subsequent drawing call reads colors
through `canvas.theme` instead of having `theme` passed back in as a
parameter on each call:

```
class Canvas:
    def __init__(self, width: int, height: int, theme: Theme):
        self.width = width
        self.height = height
        self.theme = theme          # <-- Canvas "remembers" this render's palette
        self.elements: list[str] = []

    def add(self, svg_fragment: str) -> None:
        self.elements.append(svg_fragment)

    def add_arrow_markers(self) -> None:
        t = self.theme                          # read the stored theme, no need to pass it in again
        self.add_def(marker("arrow", fill=t.muted))
        self.add_def(marker("arrow-accent", fill=t.accent))
```

### 2. Boundary rules between the 3 stages

These are mandatory design rules that apply to every diagram type — not
implementation details specific to any one type:

- **`Parser.parse()` must not know about `Layout`** — the function
  `parse(text: str) -> IR` never receives or computes coordinates. If a
  `Parser` also computed coordinates, it could no longer be tested by
  simply comparing the resulting `IR` — the test would break every time
  the `LayoutBuilder`'s formula changed, even though the semantic content
  never changed.
- **`LayoutBuilder.layout()` must not know about `Theme`** — the function
  `layout(ir: IR) -> Layout` never receives `theme`. If it knew about
  colors, the theme (or any attribute value inside the theme) could not be
  changed without re-running the entire rank/order/route algorithm.
- **`Renderer.render()` does not decide the `Layout` itself** — the
  function `render(layout: Layout, theme: Theme) -> Canvas` only reads an
  already-computed `Layout` and paints the `Theme` onto it, without
  recomputing coordinates itself. This preserves the ability to reuse the
  same `Renderer` if two diagram types later turn out to have different
  syntax but the same geometry.

### 3. Graph-based layout engine design

The layout engine has 4 steps:
1. Horizontal ranking: decide which node comes before which along the
   horizontal axis.
2. Vertical ordering within each rank: decide, within the same rank, which
   node sits above which along the vertical axis, so that edges cross each
   other as little as possible.
3. Computing node coordinates: convert rank and order into concrete x, y
   numbers using a geometric formula.
4. Routing edges between nodes: draw edges between the already-computed
   coordinates using an elbow formula, with a separate anchor point for
   edges sharing the same node. If an edge would have to pass through an
   unrelated node, the path is rerouted around that node instead of
   cutting through it.

```
1) rank(nodes, edges) -> {node: rank}
```
- **Problem to solve**: the graph may contain cycles, so ranks cannot be
  computed with an ordinary topological sort (topo-sort assumes an
  acyclic graph).
- **Strategy**: first find back-edges (defined in the glossary) by
  traversing the graph and detecting edges that point back to a node
  currently mid-traversal; remove those edges from the edge set used for
  ranking. On the remaining graph (now acyclic), compute ranks using the
  "longest path" rule: `rank[node] = max(rank[parent]) + 1`, so that a
  node with multiple parents always ends up after its furthest parent, not
  its nearest one.
- Back-edges are not deleted from the diagram — they are only "temporarily
  removed" from the ranking step so they don't break the ordering, then
  drawn separately in step 4 (as a dashed, routed-around line).

```
2) order(nodes, rank, edges) -> {node: order}
```
- **Problem to solve**: within the same rank, in what order should nodes
  be arranged so connecting edges cross each other as little as possible
  when drawn? Finding the *absolute optimal* ordering is an NP-hard
  problem (crossing minimization).
- **Strategy (a deliberate trade-off)**: the "barycenter" heuristic, run
  for exactly 2 passes instead of iterating to convergence:
  - Pass 1 (top-down): each node in a rank is ordered by the average
    position (barycenter) of its already-ordered parent nodes (previous
    rank).
  - Pass 2 (bottom-up): the same process is repeated using child nodes
    (next rank) instead, to correct the ordering computed in pass 1.
- **Why only 2 passes**: the standard Sugiyama algorithm iterates this
  heuristic 4–24 times until convergence, to optimize globally. At the
  scale of ≤9 nodes/diagram (the complexity budget), 2 passes are already
  good enough for a readable layout, in exchange for much simpler code.
  This is an explicit trade-off: accepting a non-globally-optimal result
  to keep the algorithm easy to understand and easy to verify at small
  scale.

```
3) position(rank, order) -> {node: Rect(x, y, w, h)}
```
- This step is pure formula, not an algorithm: `x = rank × (column width +
  spacing)`, `y = order × (row height + spacing)`, with columns that have
  fewer nodes centered relative to the busiest column.
- This step **must come after** step (2), because the formula needs
  `order` as input — coordinates cannot be computed before the
  within-rank ordering is known.

```
4) route(edges, rects) -> {edge: path}
```
- **Problem to solve**: node coordinates already exist (from step 3), now
  draw connecting paths between them such that they don't cut through any
  unrelated node.
- **Strategy, 2 priority tiers** (simple case first, complex case only
  when needed):
  1. If the start and end points share an axis (equal x or equal y), draw
     a straight line.
  2. If they don't share an axis, use the standard "elbow" formula (a
     path bent at a 90-degree, rounded corner).
  3. **Before applying the elbow formula**, check: is there any node,
     other than the two endpoints of this edge, that falls inside the
     bounding box of the intended path? If so, that is an "obstacle"
     (usually a node in a middle rank, because the edge skips more than
     one rank). Handling, preferring the shortest possible path:
     - If one of the two endpoints already has a y-coordinate outside the
       obstacle's y-range, keep that y, route horizontally past the edge
       of the obstacle, then bend — this is the "local detour" option,
       costing the least extra distance.
     - Only when **both** endpoints are blocked by the obstacle along the
       y-axis (neither can detour locally) does the path route all the
       way above the entire diagram. This is the fallback option, costing
       more distance but always correct in every case.

### 4. Extension design

**Process for adding a new diagram type**:
1. Determine whether the type is formulaic or graph-based.
2. Declare `<Name>IR(IR)`: whichever properties that type needs (no
   coordinates, no colors).
3. Write `<Name>Parser(Parser)`, overriding `parse(text) -> <Name>IR`.
4. Declare `<Name>Layout(Layout)`: whichever coordinate properties that
   type needs.
5. Write `<Name>LayoutBuilder(LayoutBuilder)`, overriding
   `layout(ir) -> <Name>Layout` — if graph-based, call back into the 4
   pure functions from section 3 instead of rewriting them; if formulaic,
   write dedicated arithmetic formulas directly inside this method.
6. Write `<Name>Renderer(Renderer)`, overriding
   `render(layout, theme) -> Canvas`.
7. Add the new mapping to the `registry`.

### 5. Test design with pytest

**Guiding principle**: since section 2 hard-separates the boundaries
between `Parser` / `LayoutBuilder` / `Renderer` (each function only
receives/returns exactly one kind of data, and knows nothing about the
stage that follows it), the test suite must be split along the same
boundaries — each stage gets its own test suite, runnable independently,
without needing to assemble the whole pipeline to test one stage.
End-to-end tests (`Mermaid text → SVG`) only keep a handful of smoke tests
to confirm the 3 stages assemble correctly, and are not used to cover
every case — case coverage is the job of each stage's own tests.

```
tests/
  parsers/
    test_flowchart_parser.py
    test_gantt_parser.py
    ...  # 1 file per diagram type
  layout/
    test_rank.py          # step 1 of the graph-based engine
    test_order.py          # step 2
    test_position.py       # step 3
    test_route.py          # step 4
    test_flowchart_layout_builder.py   # assembles the 4 steps for one specific graph-based type
    test_gantt_layout_builder.py       # formulaic, tests its own formula
    ...
  renderers/
    test_flowchart_renderer.py
    ...
  fixtures/
    mermaid_samples/       # sample Mermaid text, see 5.4
  test_pipeline_smoke.py   # a handful of end-to-end smoke tests, not repeating the scope above
```

#### 5.1. `Parser` tests: input is text, the oracle is IR

Since `Parser.parse(text) -> IR` does not depend on `Layout`/`Theme`, tests
only need to compare the returned `IR` against the expected `IR` — no
rendering or coordinate computation required. Use
`pytest.mark.parametrize` to cover **every diagram type the project
supports** (flowchart, sequence, state machine, ER, gantt, quadrant,
timeline, ...), each with at minimum:

- 1 minimal valid case (1 node/task, no edges).
- 1 valid "full syntax feature" case for that type (labels with special
  characters, anonymous nodes, labeled edges, subgraphs if applicable,
  ...).
- 1–2 invalid/ambiguous syntax cases, to confirm `warnings` gets filled in
  correctly rather than raising an exception or silently ignoring the
  issue.

```python
@pytest.mark.parametrize("text,expected", FLOWCHART_CASES)
def test_flowchart_parser(text, expected):
    ir = FlowChartParser().parse(text)
    assert ir.nodes == expected.nodes
    assert ir.edges == expected.edges
    assert ir.warnings == expected.warnings

def test_parser_never_sets_coordinates():
    ir = FlowChartParser().parse("flowchart TD; A --> B")
    assert not hasattr(ir, "x") and not hasattr(ir, "rects")  # IR must never carry coordinates
```

#### 5.2. `LayoutBuilder` tests: split by the graph-based engine's 4 pure functions

Since section 3 defines 4 independent pure functions (`rank`, `order`,
`position`, `route`), each one is tested separately with minimal
input/output — no need to build a full `IR`, no need for a wrapping
`LayoutBuilder`, no need for a theme:

- **`rank`**: a linear graph (`A→B→C`), a branching graph with convergence
  (multiple parents sharing one child: `A→C, B→C`) to confirm
  `rank[child] = max(rank[parent]) + 1` (not the nearest parent), and
  **must include a case with a cycle** (at minimum: a 2-node cycle
  `A→B→A`, and a longer cycle `A→B→C→A`) to confirm back-edges are
  detected correctly and the rest of the graph still gets ranked, without
  falling into infinite recursion.
- **`order`**: a rank with multiple nodes sharing parents/children in an
  adjacent rank, confirming the 2-pass heuristic (top-down, bottom-up)
  produces a stable (deterministic) ordering — running the same input
  again must produce the same output, since nothing in the algorithm is
  random.
- **`position`**: input is fixed `rank`/`order`, oracle is the pure
  arithmetic formula (`x = rank × ...`, `y = order × ...`) — matched
  exactly, no "approximately equal."
- **`route`**: this is the most important test group for the "never cuts
  through an unrelated node" goal — see 5.3.

#### 5.3. Overlap and edge-crossing-node regression tests

These are the two geometric failure modes that section 3's algorithm is
designed to avoid, so they need **general geometric assertions**, run
against many random/edge-case datasets, rather than only matching fixed
coordinates for a handful of hand-written cases:

```python
def assert_no_rect_overlap(rects: dict[str, Rect]) -> None:
    for id_a, id_b in itertools.combinations(rects, 2):
        assert not rects[id_a].intersects(rects[id_b]), f"{id_a} overlaps {id_b}"

def assert_no_route_crosses_unrelated_node(route: EdgeRoute, rects: dict[str, Rect]) -> None:
    endpoints = {route.source, route.target}
    for node_id, rect in rects.items():
        if node_id in endpoints:
            continue
        assert not route.path.intersects(rect), f"edge {route.source}->{route.target} crosses {node_id}"
```

Apply both assertions across a **test matrix** that varies along 3 axes,
generated with `pytest.mark.parametrize` (or property-based testing with
`hypothesis`, see below):

| Axis | Values to cover |
|---|---|
| Node count | smallest (1–2), medium (5–6), the upper bound of the complexity budget (9, per the constraint stated at the top of this document) |
| Edge count / density | sparse (a tree, each node ≤1 parent), dense (close to 12 edges — the upper-bound constraint), with a "hub" node (1 node receiving/emitting many edges, prone to causing overlapping paths) |
| Cycle count | 0 (pure DAG), 1 short cycle (2 nodes), 1 longer cycle (≥3 nodes), multiple nested/independent cycles in the same diagram |

The obstacle case from section 3, step 4 needs its own dedicated,
hand-built tests rather than randomly generated ones, since the situation
described by the algorithm has to be deliberately forced:

```python
def test_route_avoids_obstacle_with_local_detour():
    # A is at rank 0, B is at rank 2 (skipping over C at rank 1, same row),
    # but A's y falls outside C's y-range -> must detour locally, not route above the whole diagram
    ...

def test_route_falls_back_to_top_detour_when_both_endpoints_blocked():
    # A and B are on the same row as C (the obstacle) in a middle rank, both endpoints are blocked along the y-axis
    # -> must route above the entire diagram
    ...
```

**Recommended: use `hypothesis`** for this test group specifically:
randomly generate directed graphs within the budget (≤9 nodes, ≤12 edges,
0–3 cycles), run them through all 4 layout steps, then apply
`assert_no_rect_overlap` and `assert_no_route_crosses_unrelated_node` as 2
*invariants* that must hold for **every** valid graph — not just the
hand-picked cases thought of in advance — in order to catch edge/cycle
combinations the test author didn't anticipate.

#### 5.4. Fixtures: a sample-Mermaid store by diagram type

Collect sample Mermaid text under
`tests/fixtures/mermaid_samples/<diagram_type>/*.mmd` (one file per case),
loaded through a shared fixture, so the same sample set can be reused by
both the dedicated `Parser` tests and the end-to-end smoke tests — avoiding
drift between the samples used at the two test layers:

```python
@pytest.fixture(params=sorted(Path("tests/fixtures/mermaid_samples/flowchart").glob("*.mmd")))
def flowchart_sample(request) -> str:
    return request.param.read_text()
```

#### 5.5. `Renderer` tests: input is a hand-built `Layout`, `LayoutBuilder` is never run

Since `Renderer.render(layout, theme) -> Canvas` never computes
coordinates itself (section 2), tests build a `Layout` by hand (not
obtained from a real `LayoutBuilder`) to isolate failures — if the SVG is
wrong, the bug is guaranteed to be in the `Renderer`, not mixed up with a
`LayoutBuilder` bug. Coverage should include:

- Every field of `Theme` (both `light` and `dark`) shows up in its correct
  role in the SVG (background uses `theme.paper`, never confused with
  `theme.accent`, ...).
- `Canvas` is passed exactly 1 `Theme` instance, every drawing element
  reads from `canvas.theme`, with no stray `theme` parameter leaking into
  any inner drawing function's signature.
- The generated SVG is syntactically valid (re-parsing it with
  `xml.etree.ElementTree` raises no error) and its `viewBox` matches
  `layout.viewbox_w/h` exactly.

#### 5.6. End-to-end smoke tests and `registry` tests

- `test_pipeline_smoke.py`: one case per diagram type, running the full
  `Mermaid → IR → Layout → Canvas → HTML` path, only confirming there is
  no error and the SVG is valid — not repeating the detailed assertions
  already covered by each stage's own tests.
- Dedicated `registry` tests: every diagram type in the registry must have
  a complete `(Parser, LayoutBuilder, Renderer)` trio, and a Mermaid type
  outside the supported scope (the constraint stated at the top of this
  document) must return a clear error instead of silently being handled
  by the wrong parser.
