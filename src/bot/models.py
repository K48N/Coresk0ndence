from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(slots=True)
class FeedSource:
    name: str
    niche: str
    rss: str


@dataclass(slots=True)
class RawItem:
    source: str
    niche: str
    title: str
    text: str = ""
    url: str = ""
    ts: datetime = field(default_factory=lambda: datetime.now(UTC))
