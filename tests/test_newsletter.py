from __future__ import annotations

from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from bot.collectors import news as news_collector
from bot.models import FeedSource, RawItem
from bot.pipeline import daily
from bot.settings import load_settings


def test_collect_newspaper_rss_parses_entries(monkeypatch):
    feed_entry = SimpleNamespace(
        title="Example headline",
        summary="<p>Example summary</p>",
        link="https://example.com/story",
        published_parsed=(2026, 6, 9, 12, 30, 0, 0, 0, 0),
    )

    monkeypatch.setattr(
        news_collector.feedparser,
        "parse",
        lambda url, **kwargs: SimpleNamespace(entries=[feed_entry]),
    )

    items = news_collector.collect_newspaper_rss(
        [FeedSource(name="Example", niche="politics", rss="https://example.com/rss")]
    )

    assert len(items) == 1
    assert items[0].title == "Example headline"
    assert items[0].source == "Example"
    assert items[0].ts == datetime(2026, 6, 9, 12, 30)


def test_run_daily_writes_curated_newsletter(tmp_path, monkeypatch):
    _write_sources(
        tmp_path,
        """
        newspapers:
          - name: Example Politics
            niche: politics
            rss: https://example.com/politics.rss
          - name: Example Tech
            niche: tech
            rss: https://example.com/tech.rss
        """,
    )

    monkeypatch.setattr(
        daily,
        "collect_newspaper_rss",
        lambda sources: [
            RawItem(
                source="Example Politics",
                niche="politics",
                title="Headline One",
                text="Brief summary for the first story.",
                url="https://example.com/one",
                ts=datetime(2026, 6, 9, 12, 0),
            ),
            RawItem(
                source="Example Tech",
                niche="tech",
                title="Headline Two",
                text="Brief summary for the second story.",
                url="https://example.com/two",
                ts=datetime(2026, 6, 9, 12, 15),
            ),
        ],
    )

    settings = load_settings(tmp_path, output_dir=tmp_path / "newsletter-out")
    newsletter = daily.run_daily(settings, limit=10)

    markdown_path = Path(newsletter["output_paths"]["markdown"])
    json_path = Path(newsletter["output_paths"]["json"])

    assert newsletter["story_count"] == 2
    assert newsletter["section_count"] == 2
    assert "## Highlights" in newsletter["markdown"]
    assert "## Politics" in newsletter["markdown"]
    assert "## Tech" in newsletter["markdown"]
    assert markdown_path.exists()
    assert json_path.exists()
    assert (settings.data_dir / "latest_newsletter.json").exists()


def test_run_daily_dry_run_does_not_write_files(tmp_path, monkeypatch):
    _write_sources(
        tmp_path,
        """
        newspapers:
          - name: Example Politics
            niche: politics
            rss: https://example.com/politics.rss
        """,
    )

    monkeypatch.setattr(
        daily,
        "collect_newspaper_rss",
        lambda sources: [
            RawItem(
                source="Example Politics",
                niche="politics",
                title="Headline One",
                text="Brief summary for the first story.",
                url="https://example.com/one",
                ts=datetime(2026, 6, 9, 12, 0),
            )
        ],
    )

    settings = load_settings(tmp_path, output_dir=tmp_path / "dry-run-out")
    newsletter = daily.run_daily(settings, dry_run=True)

    assert "output_paths" not in newsletter
    assert "## Politics" in newsletter["markdown"]
    assert not settings.out_dir.exists()


def test_run_daily_rejects_invalid_feed_url(tmp_path):
    _write_sources(
        tmp_path,
        """
        newspapers:
          - name: Broken Feed
            niche: politics
            rss: not-a-valid-url
        """,
    )

    settings = load_settings(tmp_path)

    with pytest.raises(ValueError, match="invalid rss URL"):
        daily.run_daily(settings)


def _write_sources(root: Path, yaml_text: str) -> None:
    config_dir = root / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "sources.yaml").write_text(yaml_text.strip() + "\n", encoding="utf-8")