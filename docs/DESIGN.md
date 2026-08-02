# Thiết kế giải pháp

## Bài toán

**Input**: 
- Một đoạn text theo cú pháp Mermaid (ví dụ `flowchart TD; A --> B`), thuộc
một trong nhiều loại diagram khác nhau (flowchart, sequence, state machine,
ER, gantt, quadrant, timeline, ...).
- Skill `diagram-design` (đặt trong thư mục ./.skills)

**Output**: một file HTML chứa SVG, trong đó diagram được vẽ lại theo đúng
một bộ quy tắc thiết kế cố định — cùng một bảng màu, cùng một bộ font, cùng
một cách bo góc/kẻ lưới — bất kể loại diagram nào, lấy từ một `style-guide.md` của skill `diagram-design`.

**Constraints**:
- Chỉ hỗ trợ các diagram có kích thước nhỏ (ngân sách độ phức tạp: khoảng
  ≤9 node / ≤12 cạnh mỗi diagram) — đây là công cụ cho hình minh hoạ trong
  tài liệu, không phải công cụ vẽ sơ đồ hệ thống lớn.
- Chỉ hỗ trợ các loại Mermaid có thể ánh xạ rõ ràng sang một trong các loại
  diagram mà style guide đã định nghĩa; loại nào không có ánh xạ hợp lý thì
  không nằm trong phạm vi.

## Bảng thuật ngữ

| Thuật ngữ | Nghĩa là gì | Ví dụ cụ thể |
|---|---|---|
| **IR** (Intermediate Representation — biểu diễn trung gian) | *Interface* đánh dấu "đây là kết quả của Parser", khai báo đúng **1 field dùng chung cho mọi loại**: `warnings` — ngoài field đó, không khai báo gì thêm. Từng loại diagram tự khai báo class con kế thừa `IR`, và class con đó mới khai báo property riêng (tên node, nhãn cạnh, ngày tháng...). Tuyệt đối không có toạ độ hay màu sắc. | `IR` khai `warnings: list[str]`. `FlowChartIR` (kế thừa `IR`) khai thêm `nodes`, `edges`. `GanttChartIR` (kế thừa `IR`) khai thêm `tasks`, `title`. Cả hai đều có `warnings` sẵn từ `IR`, không cần tự khai lại. |
| **Layout** | *Interface* tương tự `IR`, đánh dấu "đây là kết quả của Layout Builder", khai báo đúng **2 field dùng chung cho mọi loại**: `viewbox_w`, `viewbox_h` (mọi diagram, bất kể loại nào, đều cần khai kích thước khung nhìn để `Renderer` dựng `Canvas`). Từng loại diagram có class con riêng khai báo toạ độ cụ thể. Chỉ có số (x, y, chiều rộng, chiều cao, đường đi của cạnh), không có màu. | `Layout` khai `viewbox_w`, `viewbox_h`. `FlowChartLayout` (kế thừa `Layout`) khai thêm `rects: dict[str, Rect]`, `routes: list[EdgeRoute]`. `GanttChartLayout` khai thêm `task_rows`, không có khái niệm `rects` giống flowchart. |
| **Theme** | Bảng tra cứu các giá trị thiết kế cố định — màu theo vai trò (nền, chữ, nhấn...), tên font, độ dày nét — cho **đúng 2 lựa chọn có sẵn**: `light` và `dark`. Không phải màu hex rải rác trong code, mà một bảng duy nhất cho mỗi chế độ sáng/tối. Không hỗ trợ tuỳ biến/override từ bên ngoài. Một `Theme` được nạp một lần cho mỗi lần render, rồi truyền vào `Canvas`. | `theme.accent` = màu nhấn; `Theme.load(skin="dark")` nạp bảng màu tối có sẵn. |
| **Canvas** | Vật chứa tạm cho các mảnh SVG đã được ghép chuỗi, trong lúc Renderer đang chạy — cộng dồn từng đoạn `<rect>`, `<path>`, `<text>`... và theo dõi kích thước khung nhìn tổng thể. **Giữ luôn một tham chiếu tới `Theme`** (truyền vào lúc khởi tạo), để mọi hàm vẽ tiếp theo tra màu qua `canvas.theme` thay vì nhận `theme` như một tham số riêng lẻ mỗi lần gọi. Là *sản phẩm* của giai đoạn Render, chưa phải file HTML hoàn chỉnh. Mọi `Renderer` — bất kể loại diagram nào — đều trả về **cùng một class `Canvas`** cụ thể, không có `FlowChartCanvas`/`GanttChartCanvas` riêng, vì phần "khung chứa SVG" không có gì khác nhau giữa các loại. | Xem ví dụ đầy đủ ở mục 1.3 bên dưới. |
| **Rank (tầng)** | Vị trí của một node theo trục ngang trong layout kiểu đồ thị — node ở tầng 0 đứng trước, tầng 1 đứng sau, v.v. Không phải toạ độ x thật, chỉ là *thứ tự tầng*, còn phải nhân với khoảng cách mới ra x. | Trong `A --> B --> C`, A ở tầng 0, B ở tầng 1, C ở tầng 2. |
| **Order (thứ tự trong tầng)** | Vị trí của một node theo trục dọc, *trong cùng một tầng* — node thứ 0 ở trên cùng, thứ 1 ở dưới nó, v.v. Cũng không phải toạ độ y thật. | Nếu tầng 1 có 2 node B và D, order quyết định B ở trên hay D ở trên. |
| **Back-edge (cạnh ngược)** | Một cạnh trong đồ thị mà nếu tính vào lúc xếp tầng sẽ tạo ra vòng lặp vô hạn (vì trỏ ngược về một node đứng trước nó trong quá trình duyệt). Bị loại tạm khỏi bước xếp tầng, nhưng vẫn được vẽ ở bước cuối (dưới dạng nét đứt, đi vòng). | Trong `A --> B --> A` (chu trình), cạnh thứ hai (B → A) là back-edge. |
| **Registry (bảng ánh xạ)** | Một cấu trúc dữ liệu duy nhất, ánh xạ "tên loại diagram" → "bộ ba đối tượng xử lý loại đó" (một `Parser`, một `LayoutBuilder`, một `Renderer` — xem mục 1). Là điểm trung tâm duy nhất "biết" có bao nhiêu loại diagram được hỗ trợ. | `{"gantt": (GanttChartParser(), GanttChartLayoutBuilder(), GanttChartRenderer()), "flowchart": (...), ...}` |

## Tổng quan giải pháp

```
Mermaid ──Parser──▶ Intermediate Representation ──Layout Builder──▶ layout ──Renderer──▶ SVG
```

- **Parse**: đọc cú pháp Mermaid, hiểu "nội dung" của diagram (có những
  node/task/message nào, tên là gì, nối với nhau ra sao) — nhưng **không hề
  biết** node đó sẽ nằm ở đâu trên màn hình hay được tô màu gì.
- **Layout**: nhận dữ liệu ngữ nghĩa đó, tính ra toạ độ (x, y, chiều rộng,
  chiều cao) cho từng phần tử, và đường đi cho từng cạnh nối — nhưng
  **không hề biết** màu sắc hay font chữ.
- **Render**: nhận toạ độ đã tính sẵn cộng với một theme thiết kế, ghép lại thành chuỗi SVG.

Có hai loại diagram:
- Formulaic Diagram: Loại đồ thị mà vị trí của các phần tử có thể trực tiếp suy ra từ quan hệ giữa chúng (Ví dụ: gantt, timeline, quadrant,...)
- Graph-based Diagram: Loại đồ thị mà thứ tự các node **không** có sẵn trong
input — một flowchart chỉ cho biết "A nối B", không cho biết "A nên vẽ bên
trái hay bên phải B". Thứ tự đó phải được *suy luận* từ cấu trúc cạnh nối,
bằng thuật toán đồ thị thật sự.

> Cần có Graph-based layout engine dành riêng cho loại đồ thị graph-based tại bước Layout Builder.

## Triển khai giải pháp
### 1. Base classes

#### 1.1. `IR`

```
class IR:
    warnings: list[str]  

# Các diagram kế thừa IR
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

# Các layout của từng diagram kế thừa Layout
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

Loại graph-based diagram, sử dụng các hàm trong luồng xử lý graph-based layout engine:

```
# Các parser cho từng diagram kế thừa Parser
class FlowChartParser(Parser):
    def parse(self, text: str) -> FlowChartIR:
        ...  # đọc cú pháp flowchart, KHÔNG tính toạ độ, KHÔNG tô màu
        return FlowChartIR(nodes=..., edges=..., warnings=...)

# Các layout builder cho từng diagram kế thừa LayoutBuilder
class FlowChartLayoutBuilder(LayoutBuilder):
    def layout(self, ir: FlowChartIR) -> FlowChartLayout:
        ... # sử dụng graph-based layout engine
        return FlowChartLayout(rects=rects, routes=routes, viewbox_w=..., viewbox_h=...)

# Các renderer cho từng diagram kế thừa Renderer
class FlowChartRenderer(Renderer):
    def render(self, layout: FlowChartLayout, theme: Theme) -> Canvas:
        canvas = Canvas(layout.viewbox_w, layout.viewbox_h, theme)
        for node_id, rect in layout.rects.items():
            canvas.add(node_box(rect, theme.box_fill, ...))
        for route in layout.routes:
            canvas.add(arrow_path(route, theme.muted))
        return canvas
```

Và loại formulaic diagram tự viết logic tính dựa trên loại diagram tương ứng:

```
class GanttChartParser(Parser):
    def parse(self, text: str) -> GanttChartIR: ...

class GanttChartLayoutBuilder(LayoutBuilder):
    def layout(self, ir: GanttChartIR) -> GanttChartLayout:
        # công thức số học thuần theo ngày tháng, KHÔNG gọi graph-based layout engine
        ...

class GanttChartRenderer(Renderer):
    def render(self, layout: GanttChartLayout, theme: Theme) -> Canvas:
        canvas = Canvas(layout.viewbox_w, layout.viewbox_h, theme)
        ...
        return canvas
```


#### 1.4. `Theme` / `Canvas`

`Theme` là bảng tra cứu (immutable) các giá trị thiết kế theo *vai trò*,
không phải hex code rải rác:

```
theme = Theme.load(skin="light")   # hoặc skin="dark" — chỉ 2 lựa chọn, không có tham số custom
# theme.paper     = "#F7F5F0"   (màu nền giấy)
# theme.ink       = "#1A1A1A"   (màu chữ chính)
# theme.accent    = "#C1440E"   (màu nhấn)
# theme.box_fill  = "#FFFFFF"   (màu nền khung node)
# theme.muted     = "#8A8A8A"   (màu phụ, dùng cho mũi tên thường)
```

`Canvas` **giữ một tham chiếu tới đúng một `Theme` instance này** ngay từ
lúc khởi tạo, và mọi hàm vẽ gọi tiếp theo đọc màu qua `canvas.theme` thay
vì phải truyền `theme` lại làm tham số ở từng lời gọi:

```
class Canvas:
    def __init__(self, width: int, height: int, theme: Theme):
        self.width = width
        self.height = height
        self.theme = theme          # <-- Canvas "nhớ" bảng màu của lần render này
        self.elements: list[str] = []

    def add(self, svg_fragment: str) -> None:
        self.elements.append(svg_fragment)

    def add_arrow_markers(self) -> None:
        t = self.theme                          # đọc lại theme đã lưu, không cần truyền lại
        self.add_def(marker("arrow", fill=t.muted))
        self.add_def(marker("arrow-accent", fill=t.accent))
```

### 2. Nguyên tắc ranh giới giữa 3 giai đoạn

Đây là luật thiết kế bắt buộc, áp dụng cho mọi loại diagram — không phải chi
tiết cài đặt của riêng loại nào:

- **`Parser.parse()` không được biết `Layout`** — hàm
  `parse(text: str) -> IR` không hề nhận hay tính toạ độ. Nếu một
  `Parser` tính luôn toạ độ, sẽ không thể test nó chỉ bằng cách so sánh
  IR — test sẽ vỡ mỗi khi đổi công thức của `LayoutBuilder`, dù nội dung ngữ nghĩa không đổi.
- **`LayoutBuilder.layout()` không được biết `Theme`** — hàm
  `layout(ir: IR) -> Layout` không nhận `theme`. Nếu biết màu, sẽ không thể
  đổi theme hay các giá trị thuộc tính trong theme mà không chạy lại toàn bộ thuật toán rank/order/route.
- **`Renderer.render()` không tự quyết `Layout`** - hàm
  `render(layout: Layout, theme: Theme) -> Canvas` chỉ đọc `Layout` đã có
  sẵn và tô `Theme` lên, không tự tính lại toạ độ. Điều này giữ khả năng
  dùng lại cùng một `Renderer` nếu sau này có 2 loại diagram khác cú pháp
  nhưng chung hình học.

### 3. Thiết kế graph-based engine layout

4 bước của engine layout:
1. Xếp tầng theo chiều ngang: Quyết định node nào đứng trước, node nào đứng sau trên trục ngang.
2. Xếp các node cùng tầng theo chiều dọc: Quyết định trong cùng một tầng, node nào ở trên, node nào ở dưới trên trục dọc, sao cho cạnh ít cắt nhau nhất có thể.
3. Tính toạ độ các node trong tầng: Chuyển tầng và thứ tự trong tầng thành số x, y cụ thể bằng công thức hình học.
4. Vẽ đường nối các node: Vẽ cạnh giữa các toạ độ đã có bằng công thức elbow, với điểm neo tách nhánh cho các cạnh dùng chung một node. Nếu một cạnh phải đi ngang qua một node không liên quan, đường đi sẽ được nắn lại vòng qua node đó thay vì cắt xuyên qua.

```
1) rank(nodes, edges) -> {node: rank}
```
- **Vấn đề cần giải**: đồ thị có thể có chu trình → không thể xếp tầng bằng
  topo-sort thông thường (topo-sort giả định không có chu trình).
- **Chiến lược**: trước tiên tìm các back-edge (định nghĩa ở bảng thuật
  ngữ) bằng cách duyệt đồ thị và phát hiện cạnh trỏ về node đang trong quá
  trình duyệt dở; loại các cạnh này ra khỏi tập cạnh dùng để xếp tầng. Trên
  phần đồ thị còn lại (không còn chu trình), xếp tầng theo nguyên tắc
  "đường đi dài nhất": `rank[node] = max(rank[cha]) + 1`, để một node có
  nhiều cha luôn đứng sau cha xa nhất, không phải cha gần nhất.
- Back-edge không bị xoá khỏi diagram — chỉ bị "gỡ tạm" khỏi bước xếp tầng
  để không phá vỡ thứ tự, rồi được vẽ riêng ở bước 4 (nét đứt, đi vòng).

```
2) order(nodes, rank, edges) -> {node: order}
```
- **Vấn đề cần giải**: trong cùng một tầng, xếp các node theo thứ tự nào để
  cạnh nối ít cắt nhau nhất khi vẽ? Tìm thứ tự *tối ưu tuyệt đối* là bài
  toán NP-hard (crossing minimization).
- **Chiến lược (đánh đổi có chủ đích)**: heuristic "trọng tâm" (barycenter),
  chạy đúng 2 lượt thay vì lặp tới hội tụ:
  - Lượt 1 (trên xuống): mỗi node trong một tầng được xếp theo vị trí trung
    bình (trọng tâm) của các node cha (tầng trước) đã có thứ tự.
  - Lượt 2 (dưới lên): làm lại tương tự nhưng theo node con (tầng sau), để
    sửa lại thứ tự đã xếp ở lượt 1.
- **Vì sao chỉ 2 lượt**: thuật toán Sugiyama chuẩn lặp heuristic này 4–24
  lượt tới khi hội tụ, để tối ưu toàn cục. Ở quy mô ≤9 node/diagram (ngân
  sách độ phức tạp), 2 lượt đã đủ tốt cho một layout đọc được, và đổi lấy
  code đơn giản hơn nhiều. Đây là trade-off tường minh: chấp nhận không tối
  ưu toàn cục để giữ thuật toán dễ hiểu, dễ kiểm chứng, ở quy mô nhỏ.

```
3) position(rank, order) -> {node: Rect(x, y, w, h)}
```
- Đây là bước thuần công thức, không phải thuật toán: `x = rank × (bề rộng
  cột + khoảng cách)`, `y = order × (chiều cao hàng + khoảng cách)`, các cột
  ít node hơn được căn giữa so với cột đông node nhất.
- Bước này **phải đứng sau** bước (2), vì công thức cần `order` làm đầu
  vào — không thể tính toạ độ trước khi biết thứ tự trong tầng.

```
4) route(edges, rects) -> {edge: path}
```
- **Vấn đề cần giải**: đã có toạ độ node (từ bước 3), giờ vẽ đường nối giữa
  chúng sao cho không cắt xuyên qua node khác không liên quan tới cạnh đó.
- **Chiến lược, 2 tầng ưu tiên** (đơn giản trước, phức tạp sau, chỉ dùng khi
  cần):
  1. Nếu điểm đầu và điểm cuối cùng trục (x hoặc y bằng nhau) → vẽ đường
     thẳng.
  2. Nếu khác trục → dùng công thức "elbow" chuẩn (đường gấp khúc bo góc
     90 độ).
  3. **Trước khi dùng công thức elbow**, kiểm tra: có node nào không phải
     2 đầu mút của cạnh này, mà lại nằm trong vùng bao (bounding box) của
     đường đi dự kiến không? Nếu có, đó là "vật cản" (thường là node ở tầng
     giữa, do cạnh nhảy qua hơn 1 tầng). Cách xử lý, ưu tiên đường đi ngắn
     nhất có thể:
     - Nếu một trong hai đầu mút đã có toạ độ y nằm ngoài phạm vi y của vật
       cản, giữ nguyên y đó, đi ngang qua khỏi mép vật cản rồi mới bẻ
       hướng — đây là phương án "né cục bộ", tốn ít quãng đường nhất.
     - Chỉ khi **cả hai** đầu mút đều bị vật cản che theo trục y (không đầu
       nào né được) → mới vòng lên hẳn phía trên toàn bộ sơ đồ. Đây là
       phương án dự phòng, tốn quãng đường hơn nhưng luôn đúng trong mọi
       trường hợp.


### 4. Thiết kế mở rộng

**Quy trình thêm 1 loại diagram mới**:
1. Xác định loại đó là formulaic hay graph-based.
2. Khai `<Ten>IR(IR)`: property nào cần thiết cho loại đó (không toạ
   độ, không màu).
3. Viết `<Ten>Parser(Parser)`, override `parse(text) -> <Ten>IR`.
4. Khai `<Ten>Layout(Layout)`: property toạ độ cần thiết cho loại đó.
5. Viết `<Ten>LayoutBuilder(LayoutBuilder)`, override
   `layout(ir) -> <Ten>Layout` — nếu graph-based, gọi lại 4 hàm thuần ở
   mục 3 thay vì viết lại; nếu formulaic, viết công thức số học riêng ngay
   trong method này.
6. Viết `<Ten>Renderer(Renderer)`, override
   `render(layout, theme) -> Canvas`.
7. Thêm mapping mới vào `registry`.

### 5. Thiết kế bộ test bằng pytest

**Nguyên tắc chủ đạo**: vì mục 2 đã tách cứng ranh giới `Parser` /
`LayoutBuilder` / `Renderer` (mỗi hàm chỉ nhận/trả đúng 1 loại dữ liệu, không
biết gì về giai đoạn liền sau), bộ test cũng phải tách theo đúng ranh giới
đó — mỗi giai đoạn có bộ test riêng, chạy độc lập, không cần dựng cả pipeline
mới test được một giai đoạn. Test end-to-end (`Mermaid text → SVG`) chỉ giữ
lại vài smoke test để xác nhận 3 giai đoạn ráp lại đúng, không dùng để phủ
hết các trường hợp — phủ trường hợp (coverage) là việc của test riêng từng
giai đoạn.

```
tests/
  parsers/
    test_flowchart_parser.py
    test_gantt_parser.py
    ...  # 1 file / loại diagram
  layout/
    test_rank.py          # bước 1 của graph-based engine
    test_order.py          # bước 2
    test_position.py       # bước 3
    test_route.py          # bước 4
    test_flowchart_layout_builder.py   # ráp 4 bước cho 1 loại graph-based cụ thể
    test_gantt_layout_builder.py       # formulaic, test công thức riêng
    ...
  renderers/
    test_flowchart_renderer.py
    ...
  fixtures/
    mermaid_samples/       # text Mermaid mẫu, xem 5.4
  test_pipeline_smoke.py   # vài smoke test end-to-end, không lặp lại phạm vi ở trên
```

#### 5.1. Test riêng `Parser`: input là text, oracle là IR

Vì `Parser.parse(text) -> IR` không phụ thuộc `Layout`/`Theme`, test chỉ cần
so sánh `IR` trả về với `IR` kỳ vọng — không cần render hay tính toạ độ gì
cả. Dùng `pytest.mark.parametrize` để phủ **tất cả loại diagram mà dự án hỗ
trợ** (flowchart, sequence, state machine, ER, gantt, quadrant, timeline...),
mỗi loại tối thiểu:

- 1 ca hợp lệ tối thiểu (1 node/task, không cạnh).
- 1 ca hợp lệ "đầy đủ tính năng cú pháp" của loại đó (label có ký tự đặc
  biệt, node ẩn danh, cạnh có nhãn, subgraph nếu có...).
- 1–2 ca cú pháp sai/không rõ nghĩa, để xác nhận `warnings` được điền đúng
  chứ không phải exception hay im lặng bỏ qua.

```python
@pytest.mark.parametrize("text,expected", FLOWCHART_CASES)
def test_flowchart_parser(text, expected):
    ir = FlowChartParser().parse(text)
    assert ir.nodes == expected.nodes
    assert ir.edges == expected.edges
    assert ir.warnings == expected.warnings

def test_parser_never_sets_coordinates():
    ir = FlowChartParser().parse("flowchart TD; A --> B")
    assert not hasattr(ir, "x") and not hasattr(ir, "rects")  # IR tuyệt đối không có toạ độ
```

#### 5.2. Test riêng `LayoutBuilder`: tách theo 4 hàm thuần của graph-based engine

Vì mục 3 định nghĩa 4 hàm thuần độc lập (`rank`, `order`, `position`,
`route`), mỗi hàm test riêng bằng input/output tối giản — không cần dựng
`IR` đầy đủ, không cần `LayoutBuilder` bọc ngoài, không cần theme:

- **`rank`**: linear graph (`A→B→C`), branching graph có convergence (nhiều
  cha cùng 1 con: `A→C, B→C`) để xác nhận `rank[con] = max(rank[cha]) + 1`
  (không phải cha gần nhất), và **bắt buộc có ca graph chứa cycle** (tối
  thiểu: cycle 2 node `A→B→A`, và cycle dài hơn `A→B→C→A`) để xác nhận
  back-edge được phát hiện đúng và phần còn lại vẫn xếp tầng được, không rơi
  vào đệ quy vô hạn.
- **`order`**: một tầng có nhiều node cùng chung cha/con ở tầng liền kề, xác
  nhận heuristic 2 lượt (trên xuống, dưới lên) cho ra thứ tự ổn định
  (deterministic) — chạy lại cùng input phải ra cùng output, vì không có gì
  ngẫu nhiên trong thuật toán.
- **`position`**: input là `rank`/`order` cố định, oracle là công thức số học
  thuần (`x = rank × ...`, `y = order × ...`) — so khớp số chính xác, không
  cần "gần đúng".
- **`route`**: đây là nhóm test quan trọng nhất cho mục tiêu "không cắt qua
  node không liên quan" — xem 5.3.

#### 5.3. Bộ test chống overlap và chống edge-crossing-node

Đây là 2 loại lỗi hình học mà mục 3 mô tả thuật toán để tránh, nên cần test
**assertion hình học tổng quát**, chạy trên nhiều bộ dữ liệu ngẫu nhiên/biên,
thay vì chỉ so khớp toạ độ cố định của vài ca thủ công:

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

Áp 2 assertion trên cho một **test matrix** biến thiên trên 3 trục, sinh
bằng `pytest.mark.parametrize` (hoặc property-based bằng `hypothesis`, xem
dưới):

| Trục biến thiên | Giá trị cần phủ |
|---|---|
| Số lượng node | nhỏ nhất (1–2), trung bình (5–6), biên trên của ngân sách độ phức tạp (9, theo constraint ở đầu tài liệu) |
| Số lượng edge / mật độ | thưa (tree, mỗi node ≤1 cha), dày (gần với 12 edge — biên trên constraint), có node "hub" (1 node nhận/xuất nhiều edge, dễ gây chồng đường) |
| Số lượng cycle | 0 (DAG thuần), 1 cycle ngắn (2 node), 1 cycle dài hơn (≥3 node), nhiều cycle lồng/độc lập trong cùng diagram |

Ca obstacle ở mục 3 bước 4 cần test riêng, dựng thủ công chứ không sinh
ngẫu nhiên, vì phải chủ động ép vào đúng tình huống thuật toán mô tả:

```python
def test_route_avoids_obstacle_with_local_detour():
    # A ở tầng 0, B ở tầng 2 (nhảy qua C ở tầng 1, cùng hàng),
    # nhưng A có y nằm ngoài phạm vi y của C -> phải né cục bộ, không vòng lên đỉnh sơ đồ
    ...

def test_route_falls_back_to_top_detour_when_both_endpoints_blocked():
    # A và B cùng hàng với C (obstacle) ở tầng giữa, cả 2 đầu đều bị che theo trục y
    # -> phải vòng lên trên toàn bộ sơ đồ
    ...
```

**Khuyến nghị dùng `hypothesis`** cho riêng nhóm test này: sinh ngẫu nhiên
directed graph trong ngân sách (≤9 node, ≤12 edge, số cycle 0–3), chạy qua đủ
4 bước layout, rồi áp `assert_no_rect_overlap` và
`assert_no_route_crosses_unrelated_node` như 2 *invariant* bắt buộc đúng với
**mọi** graph hợp lệ — không chỉ với các ca thủ công đã nghĩ ra trước, để bắt
được tổ hợp edge/cycle mà người viết test không lường tới.

#### 5.4. Fixture: kho mẫu Mermaid theo loại diagram

Gom text Mermaid mẫu vào `tests/fixtures/mermaid_samples/<diagram_type>/*.mmd`
(mỗi file 1 ca), nạp bằng fixture dùng chung, để cùng 1 bộ mẫu có thể tái sử
dụng ở cả test riêng `Parser` lẫn smoke test end-to-end — tránh việc mẫu bị
lệch nhau giữa 2 tầng test:

```python
@pytest.fixture(params=sorted(Path("tests/fixtures/mermaid_samples/flowchart").glob("*.mmd")))
def flowchart_sample(request) -> str:
    return request.param.read_text()
```

#### 5.5. Test riêng `Renderer`: input là `Layout` dựng tay, không chạy `LayoutBuilder`

Vì `Renderer.render(layout, theme) -> Canvas` không tự tính toạ độ (mục 2),
test dựng `Layout` bằng tay (không lấy từ `LayoutBuilder` thật) để cô lập
lỗi — nếu SVG sai, chắc chắn lỗi nằm ở `Renderer`, không lẫn với lỗi
`LayoutBuilder`. Phủ:

- Mỗi field của `Theme` (`light` và `dark`) đều xuất hiện đúng vai trò trong
  SVG (màu nền dùng `theme.paper`, không lẫn `theme.accent`...).
- `Canvas` được truyền đúng 1 `Theme` instance, mọi phần tử vẽ ra đọc từ
  `canvas.theme`, không có tham số `theme` rời rạc lọt vào chữ ký hàm vẽ con.
- SVG sinh ra hợp lệ về cú pháp (parse lại bằng `xml.etree.ElementTree` không
  lỗi) và `viewBox` khớp đúng `layout.viewbox_w/h`.

#### 5.6. Smoke test end-to-end và test `registry`

- `test_pipeline_smoke.py`: 1 ca mỗi loại diagram, chạy trọn
  `Mermaid → IR → Layout → Canvas → HTML`, chỉ xác nhận không lỗi và SVG hợp
  lệ — không lặp lại các assertion chi tiết đã có ở test riêng từng giai
  đoạn.
- Test riêng `registry`: mỗi loại diagram trong registry phải có đủ bộ ba
  `(Parser, LayoutBuilder, Renderer)`, và loại Mermaid nằm ngoài phạm vi hỗ
  trợ (constraint ở đầu tài liệu) phải trả lỗi rõ ràng thay vì im lặng dùng
  nhầm parser khác.