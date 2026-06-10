from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    root: Path
    data_dir: Path
    out_dir: Path
    sources_file: Path


def load_settings(root: Path, output_dir: Path | None = None) -> Settings:
    root = root.resolve()
    data_dir = root / "data"
    out_dir = _resolve_output_dir(root, output_dir)

    return Settings(
        root=root,
        data_dir=data_dir,
        out_dir=out_dir,
        sources_file=root / "config" / "sources.yaml",
    )


def _resolve_output_dir(root: Path, output_dir: Path | None) -> Path:
    if output_dir is None:
        return root / "output"

    path = Path(output_dir).expanduser()
    if path.is_absolute():
        return path
    return (root / path).resolve()