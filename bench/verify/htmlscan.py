"""Just enough HTML parsing to check page structure without depending on any one framework."""

from __future__ import annotations

import dataclasses
from html.parser import HTMLParser

HEADINGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
FIELDS = {"input", "textarea", "select"}
SKIP_TEXT = {"script", "style", "noscript", "template"}


@dataclasses.dataclass
class PageScan:
    title: str = ""
    headings: list[tuple[str, str]] = dataclasses.field(default_factory=list)
    forms: int = 0
    field_names: set[str] = dataclasses.field(default_factory=set)
    links: list[str] = dataclasses.field(default_factory=list)
    has_viewport: bool = False
    text: str = ""
    scripts: int = 0

    @classmethod
    def parse(cls, html: str) -> "PageScan":
        parser = _Parser()
        try:
            parser.feed(html)
            parser.close()
        except Exception:  # malformed markup still yields whatever was parsed so far
            pass
        return parser.scan

    def heading_with(self, needle: str, level: str | None = None) -> bool:
        needle = needle.lower()
        return any(needle in text.lower() for tag, text in self.headings if level in (None, tag))

    def looks_client_rendered(self) -> bool:
        """An almost empty body plus scripts usually means a single-page app shell."""
        return self.scripts > 0 and len(self.text) < 200 and not self.headings


class _Parser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.scan = PageScan()
        self._capture: list[list[str]] = []  # stack of open heading/title buffers
        self._capture_tags: list[str] = []
        self._skip = 0
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {k: (v or "") for k, v in attrs}
        if tag == "form":
            self.scan.forms += 1
        elif tag in FIELDS and values.get("name"):
            self.scan.field_names.add(values["name"])
        elif tag == "a" and values.get("href"):
            self.scan.links.append(values["href"])
        elif tag == "meta" and values.get("name", "").lower() == "viewport":
            self.scan.has_viewport = True
        if tag == "script":
            self.scan.scripts += 1
        if tag in SKIP_TEXT:
            self._skip += 1
        if tag in HEADINGS or tag == "title":
            self._capture.append([])
            self._capture_tags.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag in SKIP_TEXT and self._skip:
            self._skip -= 1
        if self._capture_tags and self._capture_tags[-1] == tag:
            text = " ".join("".join(self._capture.pop()).split())
            self._capture_tags.pop()
            if tag == "title":
                self.scan.title = text
            else:
                self.scan.headings.append((tag, text))
                if self._capture:
                    self._capture[-1].append(text)

    def handle_data(self, data: str) -> None:
        if self._capture:
            self._capture[-1].append(data)
        if not self._skip:
            self._text.append(data)

    def close(self) -> None:
        super().close()
        self.scan.text = " ".join(" ".join(self._text).split())
