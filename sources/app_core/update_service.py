from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests


LATEST_RELEASE_URL = "https://api.github.com/repos/TruongBVD69/App_control_powersupply/releases/latest"


@dataclass(frozen=True)
class ReleaseAsset:
    name: str
    browser_download_url: str


@dataclass(frozen=True)
class LatestRelease:
    tag_name: str
    assets: list[ReleaseAsset]


def fetch_latest_release(url: str = LATEST_RELEASE_URL, timeout: int = 5) -> LatestRelease:
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    data: dict[str, Any] = resp.json()
    assets = [
        ReleaseAsset(
            name=str(item.get("name", "")),
            browser_download_url=str(item.get("browser_download_url", "")),
        )
        for item in data.get("assets", [])
    ]
    return LatestRelease(tag_name=str(data.get("tag_name", "")), assets=assets)


def first_download_url(release: LatestRelease) -> str | None:
    for asset in release.assets:
        if asset.browser_download_url:
            return asset.browser_download_url
    return None

