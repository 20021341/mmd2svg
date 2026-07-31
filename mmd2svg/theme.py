"""Theme (bảng token light/dark) và Canvas (vật chứa SVG fragment).

Nguồn token: .skills/diagram-design/references/style-guide.md
"""
from __future__ import annotations

from dataclasses import dataclass, field

_LIGHT = {
    "paper": "#f5f5f5",
    "paper2": "#ececec",
    "ink": "#2d3142",
    "muted": "#4f5d75",
    "soft": "#7a8399",
    "rule": "rgba(45,49,66,0.12)",
    "rule_solid": "#bfc0c0",
    "accent": "#eb6c36",
    "accent_tint": "rgba(235,108,54,0.08)",
    "link": "#2e5aa8",
}

_DARK = {
    "paper": "#2d3142",
    "paper2": "#393e53",
    "ink": "#f5f5f5",
    "muted": "#bfc0c0",
    "soft": "#8e98ac",
    "rule": "rgba(245,245,245,0.12)",
    "rule_solid": "rgba(191,192,192,0.25)",
    "accent": "#f08a59",
    "accent_tint": "rgba(240,138,89,0.10)",
    "link": "#6a95d8",
}

_VALID_SKINS = {"light": _LIGHT, "dark": _DARK}


@dataclass(frozen=True)
class Theme:
    skin: str
    paper: str
    paper2: str
    ink: str
    muted: str
    soft: str
    rule: str
    rule_solid: str
    accent: str
    accent_tint: str
    link: str

    @classmethod
    def load(cls, skin: str = "light") -> "Theme":
        if skin not in _VALID_SKINS:
            raise ValueError(f"Unknown skin {skin!r}, expected 'light' or 'dark'")
        tokens = _VALID_SKINS[skin]
        return cls(skin=skin, **tokens)


FONT_STACK_LINK = (
    'https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1'
    '&family=Geist:wght@400;500;600&family=Geist+Mono:wght@400;500;600&display=swap'
)


class Canvas:
    """Vật chứa tạm cho các mảnh SVG đã ghép chuỗi, giữ tham chiếu tới Theme."""

    def __init__(self, width: int, height: int, theme: Theme):
        self.width = width
        self.height = height
        self.theme = theme
        self.elements: list[str] = []
        self.defs: list[str] = []

    def add(self, svg_fragment: str) -> None:
        self.elements.append(svg_fragment)

    def add_def(self, svg_fragment: str) -> None:
        self.defs.append(svg_fragment)

    def add_arrow_markers(self) -> None:
        t = self.theme
        self.add_def(
            f'<marker id="arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" '
            f'orient="auto"><polygon points="0 0, 8 3, 0 6" fill="{t.muted}"/></marker>'
        )
        self.add_def(
            f'<marker id="arrow-accent" markerWidth="8" markerHeight="6" refX="7" refY="3" '
            f'orient="auto"><polygon points="0 0, 8 3, 0 6" fill="{t.accent}"/></marker>'
        )
        self.add_def(
            f'<marker id="arrow-link" markerWidth="8" markerHeight="6" refX="7" refY="3" '
            f'orient="auto"><polygon points="0 0, 8 3, 0 6" fill="{t.link}"/></marker>'
        )

    def to_svg(self) -> str:
        defs = "".join(self.defs)
        body = "".join(self.elements)
        return (
            f'<svg viewBox="0 0 {self.width} {self.height}" '
            f'width="{self.width}" height="{self.height}" '
            f'xmlns="http://www.w3.org/2000/svg">'
            f'<defs>{defs}</defs>'
            f'<rect width="100%" height="100%" fill="{self.theme.paper}"/>'
            f'{body}'
            f'</svg>'
        )

    def to_html(self, title: str, eyebrow: str) -> str:
        svg = self.to_svg()
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <link href="{FONT_STACK_LINK}" rel="stylesheet">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html, body {{
      margin: 0;
      padding: 0;
      background: {self.theme.paper};
    }}
    body {{
      font-family: 'Geist', system-ui, sans-serif;
      color: {self.theme.ink};
      width: fit-content;
      height: fit-content;
      padding: 3rem 2rem;
    }}
    .frame {{ width: fit-content; }}
    .eyebrow {{
      font-family: 'Geist Mono', ui-monospace, monospace;
      font-size: 0.66rem;
      font-weight: 500;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: {self.theme.muted};
      margin-bottom: 0.5rem;
    }}
    h1 {{
      font-family: 'Instrument Serif', serif;
      font-size: clamp(1.5rem, 2.4vw + 0.75rem, 2rem);
      font-weight: 400;
      letter-spacing: -0.02em;
      line-height: 1.15;
      margin-bottom: 1.5rem;
    }}
    svg {{ display: block; width: {self.width}px; height: {self.height}px; }}
  </style>
</head>
<body>
  <div class="frame">
    <p class="eyebrow">{eyebrow}</p>
    <h1>{title}</h1>
    {svg}
  </div>
</body>
</html>
"""
