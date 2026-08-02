# mmd2svg

Convert Mermaid diagram text to SVG/HTML/PNG using a single fixed editorial style guide — same color palette, same font, same corner radius — regardless of diagram type.

## Features

- Supports 5 diagram types: `flowchart`, `sequence`, `state machine`, `timeline`, `quadrant`.
- Outputs 3 formats: HTML (embedded SVG), plain SVG, or PNG (auto-cropped whitespace).
- Deterministic rendering: the same input always produces the same output.

## Installation

```bash
git clone https://github.com/20021341/mmd2svg.git
cd mmd2svg
pip install -e .
```

Or install directly from a prebuilt wheel in `dist/`:

```bash
pip install dist/mmd2svg-0.1.0-py3-none-any.whl
```

PNG output additionally needs the Chromium browser binary used by Playwright
(HTML and SVG output do not need this step):

```bash
playwright install --with-deps chromium
```

## Usage

```bash
mmd2svg input.mmd -o output.html
mmd2svg input.mmd -o output.svg
mmd2svg input.mmd -o output.png
mmd2svg input.mmd -o output.html --skin dark
```

The output format is auto-detected from the file extension passed to `-o`.

## Development

```bash
uv sync
uv run pytest tests/
```

See [`docs/DESIGN.md`](docs/DESIGN.md) for the full architecture design
(pipeline stages, base classes, layout engine).

### Adding support for a new diagram type

1. Decide whether the new type is formulaic (position derivable directly from the input, e.g. gantt) or graph-based (position must be inferred from edges, e.g. flowchart).
2. Declare `<Name>IR(IR)` with the properties that type needs (no coordinates, no colors).
3. Write `<Name>Parser(Parser)`, overriding `parse(text) -> <Name>IR`.
4. Declare `<Name>Layout(Layout)` with the coordinate properties that type needs.
5. Write `<Name>LayoutBuilder(LayoutBuilder)`, overriding `layout(ir) -> <Name>Layout` — reuse the shared graph layout engine for graph-based types, or write dedicated formulas for formulaic types.
6. Write `<Name>Renderer(Renderer)`, overriding `render(layout, theme) -> Canvas`.
7. Register the new type in `registry.py`.

## License

MIT
