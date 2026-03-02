from __future__ import annotations

from pathlib import Path


DEFAULT_APP_INFO = {
    "AppName": "PowerSupply Controller",
    "Version": "Unknown",
    "BuildTime": "Unknown",
}


def read_version_info(base_dir: str) -> dict[str, str]:
    version_file = Path(base_dir) / "version.txt"
    info = dict(DEFAULT_APP_INFO)
    if not version_file.exists():
        return info

    try:
        for line in version_file.read_text(encoding="utf-8").splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if key in info:
                info[key] = value
    except Exception:
        return dict(DEFAULT_APP_INFO)
    return info


def parse_version(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.strip().lstrip("v").split(".") if part.isdigit())


def is_newer_version(latest: str, current: str) -> bool:
    return parse_version(latest) > parse_version(current)

