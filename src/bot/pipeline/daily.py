from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from urllib.parse import urlparse

from bot.collectors.news import collect_newspaper_rss
from bot.models import FeedSource, RawItem
from bot.settings import Settings
from bot.storage.io import load_yaml, save_json, save_text, today_stamp
from bot.text_utils import clean_text, trim_sentence_boundary, trim_word_boundary


SECTION_ORDER = ["politics", "economics", "finance", "tech", "markets", "general"]


def run_daily(settings: Settings, limit: int = 20, dry_run: bool = False) -> dict[str, object]:
    cfg = load_yaml(settings.sources_file)
    sources = _validate_sources(cfg.get("newspapers", []))

    raw = collect_newspaper_rss(sources)
    items = _dedupe_items(raw)
    curated_items = _curate_items(items, sources)[: max(1, limit)]

    newsletter = _build_newsletter(curated_items, generated_at=datetime.now(UTC), sources=sources)
    if not dry_run:
        _write_newsletter(settings, newsletter)
    return newsletter


def _write_newsletter(settings: Settings, newsletter: dict[str, object]) -> None:
    settings.out_dir.mkdir(parents=True, exist_ok=True)
    settings.data_dir.mkdir(parents=True, exist_ok=True)

    stamp = today_stamp()
    md_path = settings.out_dir / f"newsletter-{stamp}.md"
    json_path = settings.out_dir / f"newsletter-{stamp}.json"
    latest_md = settings.out_dir / "newsletter-latest.md"
    latest_json = settings.data_dir / "latest_newsletter.json"

    markdown = str(newsletter["markdown"])
    save_text(md_path, markdown)
    save_text(latest_md, markdown)
    save_json(json_path, newsletter)
    save_json(latest_json, newsletter)

    newsletter["output_paths"] = {
        "markdown": str(md_path),
        "json": str(json_path),
        "latest_markdown": str(latest_md),
        "latest_json": str(latest_json),
    }


def _build_newsletter(items: list[RawItem], generated_at: datetime, sources: list[FeedSource]) -> dict[str, object]:
    grouped: dict[str, list[RawItem]] = defaultdict(list)
    for item in items:
        grouped[item.niche].append(item)

    source_names = sorted({source.name for source in sources})
    sections = _ordered_sections(grouped)

    markdown_lines = [
        f"# Coresk0ndence ({generated_at.date().isoformat()})",
        "",
        "A short personal digest built from the RSS feeds I keep an eye on.",
        "",
        "## In This Issue",
        "",
        f"- Stories included: {len(items)}",
        f"- Sections covered: {len(sections)}",
        f"- Sources scanned: {len(source_names)}",
        "",
    ]

    featured_items = items[: min(3, len(items))]
    if featured_items:
        markdown_lines.extend(["## Highlights", ""])
        for item in featured_items:
            markdown_lines.extend(_render_story(item, include_published=False, summary_limit=180))

    payload_items: list[dict[str, object]] = []
    for section in sections:
        markdown_lines.extend([f"## {section.title()}", ""])
        section_items = sorted(grouped[section], key=lambda item: _story_sort_key(item, sources))
        for item in section_items:
            markdown_lines.extend(_render_story(item, include_published=True, summary_limit=240))
            payload_items.append(
                {
                    "source": item.source,
                    "niche": item.niche,
                    "title": clean_text(item.title),
                    "summary": trim_sentence_boundary(item.text or item.title, 240, min_chars=40),
                    "url": item.url,
                    "published_at": item.ts.isoformat(),
                }
            )

    if not payload_items:
        markdown_lines.extend(["No stories were collected from the configured feeds.", ""])

    markdown = "\n".join(markdown_lines).rstrip() + "\n"
    return {
        "generated_at": generated_at.isoformat(),
        "story_count": len(payload_items),
        "section_count": len(sections),
        "sources": [{"name": source.name, "niche": source.niche, "rss": source.rss} for source in sources],
        "items": payload_items,
        "markdown": markdown,
    }


def _render_story(item: RawItem, include_published: bool, summary_limit: int) -> list[str]:
    title = clean_text(item.title)
    summary = trim_sentence_boundary(item.text or title, summary_limit, min_chars=40)
    if not include_published:
        summary = trim_word_boundary(summary, summary_limit)
    heading = f"### [{title}]({item.url})" if item.url else f"### {title}"
    lines = [heading, f"Source: {clean_text(item.source)}"]
    if include_published:
        lines.append(f"Published: {item.ts.isoformat(timespec='minutes')}")
    if summary:
        lines.append(f"Summary: {summary}")
    lines.append("")
    return lines


def _validate_sources(raw_sources: object) -> list[FeedSource]:
    if not isinstance(raw_sources, list):
        raise ValueError("config/sources.yaml: newspapers must be a list of feed definitions")
    if not raw_sources:
        raise ValueError("config/sources.yaml: newspapers is empty")

    validated: list[FeedSource] = []
    for index, source in enumerate(raw_sources, start=1):
        if not isinstance(source, dict):
            raise ValueError(f"config/sources.yaml: newspapers[{index}] must be a mapping")

        name = str(source.get("name", "")).strip()
        niche = str(source.get("niche", "")).strip().lower()
        rss = str(source.get("rss", "")).strip()

        if not name:
            raise ValueError(f"config/sources.yaml: newspapers[{index}] is missing a name")
        if not niche:
            raise ValueError(f"config/sources.yaml: newspapers[{index}] is missing a niche")
        if not _is_valid_http_url(rss):
            raise ValueError(f"config/sources.yaml: newspapers[{index}] has an invalid rss URL: {rss!r}")

        validated.append(FeedSource(name=name, niche=niche, rss=rss))

    return validated


def _is_valid_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _curate_items(items: list[RawItem], sources: list[FeedSource]) -> list[RawItem]:
    source_order = {source.name.lower(): index for index, source in enumerate(sources)}
    return sorted(items, key=lambda item: _story_sort_key(item, sources, source_order))


def _story_sort_key(
    item: RawItem,
    sources: list[FeedSource],
    source_order: dict[str, int] | None = None,
) -> tuple[int, int, float, str]:
    if source_order is None:
        source_order = {source.name.lower(): index for index, source in enumerate(sources)}

    niche = item.niche.lower()
    section_rank = SECTION_ORDER.index(niche) if niche in SECTION_ORDER else len(SECTION_ORDER)
    priority = source_order.get(item.source.lower(), len(source_order))
    return (section_rank, priority, -item.ts.timestamp(), item.title.lower())


def _ordered_sections(grouped: dict[str, list[RawItem]]) -> list[str]:
    known = [section for section in SECTION_ORDER if section in grouped]
    unknown = sorted(section for section in grouped if section not in SECTION_ORDER)
    return known + unknown


def _dedupe_items(items: list[RawItem]) -> list[RawItem]:
    seen: set[str] = set()
    out: list[RawItem] = []
    for item in items:
        key = clean_text(item.title).lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out
