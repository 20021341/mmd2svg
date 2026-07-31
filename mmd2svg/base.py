"""Parser / LayoutBuilder / Renderer — abstract base classes (mục 1.3 DESIGN.md)."""
from __future__ import annotations

from abc import ABC, abstractmethod

from mmd2svg.ir import IR
from mmd2svg.layout import Layout
from mmd2svg.theme import Canvas, Theme


class Parser(ABC):
    @abstractmethod
    def parse(self, text: str) -> IR: ...


class LayoutBuilder(ABC):
    @abstractmethod
    def layout(self, ir: IR) -> Layout: ...


class Renderer(ABC):
    @abstractmethod
    def render(self, layout: Layout, theme: Theme) -> Canvas: ...
