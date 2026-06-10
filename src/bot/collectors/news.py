from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import feedparser

from bot.models import FeedSource, RawItem


def collect_newspaper_rss(newspapers: list[FeedSource], max_per_feed: int = 12) -> list[RawItem]:
    if max_per_feed < 1:
        max_per_feed = 1

    items: list[RawItem] = []
    for src in newspapers:
        rss_url = src.rss.strip()
        if not rss_url:
            continue

        try:
            feed = feedparser.parse(rss_url, timeout=10)
            for entry in feed.entries[:max_per_feed]:
                title = _entry_value(entry, "title").strip()
                if not title:
                    continue

                items.append(
                    RawItem(
                        source=src.name,
                        niche=src.niche,
                        title=title,
                        text=_entry_value(entry, "summary").strip(),
                        url=str(_entry_value(entry, "link", "")),
                        ts=_entry_time(entry),
                    )
                )
        except Exception:
            continue

    return items


def _entry_time(entry: Any) -> datetime:
    published = _entry_value(entry, "published_parsed", None)
    if published:
        return datetime(*published[:6])
    return datetime.now(UTC)


def _entry_value(entry: Any, key: str, default: Any = "") -> Any:
    value = entry.get(key, default) if hasattr(entry, "get") else getattr(entry, key, default)
    return default if value is None else value
