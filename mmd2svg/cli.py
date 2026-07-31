"""CLI entrypoint: mmd2svg input.mmd -o output.html [--skin light|dark]."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from mmd2svg.registry import UnsupportedDiagramError, detect_diagram_type, get_pipeline
from mmd2svg.theme import Theme


def convert(text: str, skin: str = "light") -> str:
    """Chạy trọn pipeline Mermaid text -> HTML string."""
    import re
    fm_m = re.search(r"---\s*\n\s*title\s*:\s*(.+?)\s*\n\s*---", text, re.IGNORECASE)
    fm_title = fm_m.group(1).strip().strip('"\'') if fm_m else None

    diagram_type = detect_diagram_type(text)
    parser, layout_builder, renderer = get_pipeline(diagram_type)

    ir = parser.parse(text)
    layout = layout_builder.layout(ir)
    theme = Theme.load(skin)
    canvas = renderer.render(layout, theme)

    title = getattr(ir, "title", None) or fm_title or diagram_type.replace("_", " ").title()
    eyebrow = f"{diagram_type.title()} · mmd2svg"
    return canvas.to_html(title=title, eyebrow=eyebrow)


def convert_to_svg(text: str, skin: str = "light") -> str:
    """Chạy pipeline Mermaid text -> SVG string."""
    diagram_type = detect_diagram_type(text)
    parser, layout_builder, renderer = get_pipeline(diagram_type)
    ir = parser.parse(text)
    layout = layout_builder.layout(ir)
    theme = Theme.load(skin)
    canvas = renderer.render(layout, theme)
    return canvas.to_svg()


def convert_to_png(text: str, output_path: Path, skin: str = "light") -> None:
    """Chạy pipeline và xuất trực tiếp ra file PNG (đã auto-trim)."""
    import tempfile
    from playwright.sync_api import sync_playwright
    from PIL import Image, ImageChops

    html = convert(text, skin=skin)
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as tmp:
        tmp.write(html)
        tmp_path = tmp.name

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(f"file://{tmp_path}")
        page.wait_for_timeout(300)
        page.screenshot(path=str(output_path), full_page=True)
        browser.close()

    try:
        img = Image.open(output_path).convert("RGB")
        bg_color = img.getpixel((0, 0))
        bg = Image.new(img.mode, img.size, bg_color)
        diff = ImageChops.difference(img, bg)
        bbox = diff.getbbox()
        if bbox:
            l, u, r, d = bbox
            pad = 32
            l = max(0, l - pad)
            u = max(0, u - pad)
            r = min(img.width, r + pad)
            d = min(img.height, d + pad)
            cropped = img.crop((l, u, r, d))
            cropped.save(output_path)
    except Exception:
        pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mmd2svg", description="Chuyển đổi Mermaid sang SVG/HTML/PNG.")
    parser.add_argument("input", type=Path, help="File .mmd đầu vào")
    parser.add_argument("-o", "--output", type=Path, required=True, help="File đầu ra (.html, .svg, hoặc .png)")
    parser.add_argument("--skin", choices=["light", "dark"], default="light", help="Bảng màu")
    args = parser.parse_args(argv)

    text = args.input.read_text(encoding="utf-8")
    try:
        suffix = args.output.suffix.lower()
        if suffix == ".png":
            convert_to_png(text, args.output, skin=args.skin)
        elif suffix == ".svg":
            svg = convert_to_svg(text, skin=args.skin)
            args.output.write_text(svg, encoding="utf-8")
        else:
            html = convert(text, skin=args.skin)
            args.output.write_text(html, encoding="utf-8")
    except UnsupportedDiagramError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
