from __future__ import annotations

import html
import xml.etree.ElementTree as ET

from research_loop.config import Settings
from research_loop.models import RawItem, Source

from .base import Collector, CollectorError
from .http import fetch_text


class RSSCollector(Collector):
    source_type = "rss"

    def __init__(self, settings: Settings):
        self.settings = settings

    def collect(self, source: Source) -> list[RawItem]:
        xml_text = fetch_text(
            source.url,
            timeout_seconds=self.settings.request_timeout_seconds,
            user_agent=self.settings.user_agent,
        )
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as exc:
            raise CollectorError(f"invalid RSS/XML from {source.url}") from exc

        items = list(root.findall(".//item"))
        if not items:
            items = list(root.findall(".//{http://www.w3.org/2005/Atom}entry"))

        raw_items: list[RawItem] = []
        for item in items[:50]:
            title = _first_text(item, ["title", "{http://www.w3.org/2005/Atom}title"])
            link = _first_text(item, ["link", "guid", "{http://www.w3.org/2005/Atom}id"])
            atom_link = item.find("{http://www.w3.org/2005/Atom}link")
            if atom_link is not None:
                link = atom_link.attrib.get("href", link)
            description = _first_text(
                item,
                [
                    "description",
                    "summary",
                    "{http://www.w3.org/2005/Atom}summary",
                    "{http://www.w3.org/2005/Atom}content",
                ],
            )
            published_at = _first_text(
                item,
                ["pubDate", "published", "updated", "{http://www.w3.org/2005/Atom}updated"],
            )
            if not title and not description:
                continue
            raw_items.append(
                RawItem(
                    source_id=source.source_id,
                    source_type=source.source_type,
                    url=link,
                    title=html.unescape(title),
                    text=html.unescape(description),
                    published_at=published_at,
                    metadata={"collector": "rss"},
                )
            )
        return raw_items


def _first_text(element: ET.Element, names: list[str]) -> str:
    for name in names:
        child = element.find(name)
        if child is not None and child.text:
            return child.text.strip()
    return ""
