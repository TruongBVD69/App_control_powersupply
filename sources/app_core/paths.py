from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import sys


@dataclass(frozen=True)
class AppPaths:
    appdata_root: Path
    config_dir: Path
    download_dir: Path
    temp_dir: Path


def build_app_paths(app_name: str) -> AppPaths:
    appdata = Path(os.getenv("APPDATA", Path.home()))
    appdata_root = appdata / app_name
    config_dir = appdata_root / "config"
    download_dir = appdata_root / "download"
    temp_dir = appdata_root / "temp"

    config_dir.mkdir(parents=True, exist_ok=True)
    download_dir.mkdir(parents=True, exist_ok=True)
    temp_dir.mkdir(parents=True, exist_ok=True)

    return AppPaths(
        appdata_root=appdata_root,
        config_dir=config_dir,
        download_dir=download_dir,
        temp_dir=temp_dir,
    )


def resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works in dev and PyInstaller builds."""
    if getattr(sys, "frozen", False):
        base_path = Path(sys.executable).parent
    else:
        base_path = Path(__file__).resolve().parents[2]
    return str(base_path / relative_path)

