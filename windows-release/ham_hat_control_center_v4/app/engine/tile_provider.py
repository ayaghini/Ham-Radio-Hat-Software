#!/usr/bin/env python3
"""TileProvider — OSM slippy-map tile cache (online + offline).

Coordinate system: standard Web Mercator (EPSG:3857) as used by OpenStreetMap.
Tile URL format: https://tile.openstreetmap.org/{z}/{x}/{y}.png
Disk cache layout: <cache_dir>/{z}/{x}/{y}.png
"""

from __future__ import annotations

import math
import threading
import time
from collections import OrderedDict
from pathlib import Path
from typing import Callable, Optional

try:
    from PIL import Image as _PILImage
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import requests as _requests
    _REQUESTS_AVAILABLE = True
except ImportError:
    import urllib.request as _urllib  # type: ignore[no-redef]
    _REQUESTS_AVAILABLE = False

TILE_SIZE = 256
OSM_TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
_USER_AGENT = "uConsole-HAM-HAT/1.0 (amateur radio APRS app)"
_MEM_CACHE_SIZE = 256
_DOWNLOAD_RATE_LIMIT_S = 0.1   # seconds between tile requests in bulk download


# ---------------------------------------------------------------------------
# Coordinate math (Web Mercator / OSM slippy-map)
# ---------------------------------------------------------------------------

def lat_lon_to_tile(lat: float, lon: float, z: int) -> tuple[int, int]:
    """Return OSM tile (x, y) containing the given lat/lon at zoom z."""
    n = 2 ** z
    x = int((lon + 180.0) / 360.0 * n)
    x = max(0, min(n - 1, x))
    lat_r = math.radians(max(-85.051129, min(85.051129, lat)))
    y = int((1.0 - math.log(math.tan(lat_r) + 1.0 / math.cos(lat_r)) / math.pi) / 2.0 * n)
    y = max(0, min(n - 1, y))
    return x, y


def lat_lon_to_world_px(lat: float, lon: float, z: int) -> tuple[float, float]:
    """Return world-pixel coordinates from top-left at zoom z (tile_size=256)."""
    n = 2 ** z
    px = (lon + 180.0) / 360.0 * n * TILE_SIZE
    lat_r = math.radians(max(-85.051129, min(85.051129, lat)))
    py = (1.0 - math.log(math.tan(lat_r) + 1.0 / math.cos(lat_r)) / math.pi) / 2.0 * n * TILE_SIZE
    return px, py


def world_px_to_lat_lon(px: float, py: float, z: int) -> tuple[float, float]:
    """Inverse of lat_lon_to_world_px."""
    n = 2 ** z
    lon = px / (n * TILE_SIZE) * 360.0 - 180.0
    arg = math.pi - 2.0 * math.pi * py / (n * TILE_SIZE)
    lat = math.degrees(math.atan(math.sinh(arg)))
    return max(-85.051129, min(85.051129, lat)), max(-180.0, min(180.0, lon))


# ---------------------------------------------------------------------------
# TileProvider
# ---------------------------------------------------------------------------

class TileProvider:
    """Fetch, cache (memory + disk), and serve OSM slippy-map tiles.

    Thread-safe: designed to be called from both the main (UI) thread and
    background worker threads.
    """

    def __init__(
        self,
        cache_dir: Path,
        url_template: str = OSM_TILE_URL,
        max_workers: int = 4,
    ) -> None:
        self._cache_dir = cache_dir
        self._url = url_template
        self._mem: OrderedDict[tuple[int, int, int], object] = OrderedDict()
        self._pending: set[tuple[int, int, int]] = set()
        self._lock = threading.Lock()
        self._callbacks: dict[tuple[int, int, int], list[Callable]] = {}
        self._online = True
        self._session: object = None

        if _REQUESTS_AVAILABLE:
            self._session = _requests.Session()
            self._session.headers["User-Agent"] = _USER_AGENT  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def pil_available(self) -> bool:
        """True if Pillow is installed (tile rendering possible)."""
        return PIL_AVAILABLE

    @property
    def online(self) -> bool:
        return self._online

    def set_online(self, value: bool) -> None:
        self._online = value

    # ------------------------------------------------------------------
    # Tile access
    # ------------------------------------------------------------------

    def get_tile(self, z: int, x: int, y: int) -> "Optional[_PILImage.Image]":
        """Return tile image immediately from memory or disk cache, or None."""
        if not PIL_AVAILABLE:
            return None
        key = (z, x, y)
        with self._lock:
            if key in self._mem:
                self._mem.move_to_end(key)
                return self._mem[key]  # type: ignore[return-value]

        path = self._tile_path(z, x, y)
        if path.exists():
            try:
                from PIL import Image
                img = Image.open(path).convert("RGB")
                self._store_mem(key, img)
                return img
            except Exception:
                pass
        return None

    def request_tile(
        self,
        z: int,
        x: int,
        y: int,
        on_ready: Optional[Callable] = None,
    ) -> None:
        """Non-blocking: fetch tile in background; call on_ready() when done.

        on_ready() is called from a background thread — callers must schedule
        any UI updates via after() or similar.
        """
        if not PIL_AVAILABLE:
            return
        if self.get_tile(z, x, y) is not None:
            if on_ready:
                on_ready()
            return

        key = (z, x, y)
        with self._lock:
            if key in self._pending:
                if on_ready:
                    self._callbacks.setdefault(key, []).append(on_ready)
                return
            self._pending.add(key)
            if on_ready:
                self._callbacks.setdefault(key, []).append(on_ready)

        threading.Thread(
            target=self._fetch_worker, args=(z, x, y), daemon=True
        ).start()

    # ------------------------------------------------------------------
    # Region download (call from a background thread)
    # ------------------------------------------------------------------

    def tile_count_for_region(
        self,
        lat_min: float,
        lat_max: float,
        lon_min: float,
        lon_max: float,
        z_min: int,
        z_max: int,
    ) -> int:
        """Estimate the number of tiles needed to cover a region."""
        total = 0
        for z in range(z_min, z_max + 1):
            x0, y0 = lat_lon_to_tile(lat_max, lon_min, z)
            x1, y1 = lat_lon_to_tile(lat_min, lon_max, z)
            total += (abs(x1 - x0) + 1) * (abs(y1 - y0) + 1)
        return total

    def download_region(
        self,
        lat_min: float,
        lat_max: float,
        lon_min: float,
        lon_max: float,
        z_min: int,
        z_max: int,
        progress_cb: Optional[Callable[[int, int], None]] = None,
        cancel_flag: Optional[list] = None,
    ) -> tuple[int, int]:
        """Download all tiles for a region synchronously.

        Rate-limited to be a good OSM citizen.
        Returns (tiles_downloaded, tiles_skipped).
        Call from a background thread.
        """
        downloaded = skipped = done = 0
        total = self.tile_count_for_region(lat_min, lat_max, lon_min, lon_max, z_min, z_max)

        for z in range(z_min, z_max + 1):
            if cancel_flag and cancel_flag[0]:
                break
            x0, y0 = lat_lon_to_tile(lat_max, lon_min, z)
            x1, y1 = lat_lon_to_tile(lat_min, lon_max, z)
            for x in range(min(x0, x1), max(x0, x1) + 1):
                if cancel_flag and cancel_flag[0]:
                    break
                for y in range(min(y0, y1), max(y0, y1) + 1):
                    if cancel_flag and cancel_flag[0]:
                        break
                    path = self._tile_path(z, x, y)
                    if path.exists():
                        skipped += 1
                    else:
                        img = self._fetch_online(z, x, y)
                        if img is not None:
                            self._store_mem((z, x, y), img)
                            downloaded += 1
                            time.sleep(_DOWNLOAD_RATE_LIMIT_S)
                        else:
                            skipped += 1
                    done += 1
                    if progress_cb:
                        progress_cb(done, total)

        return downloaded, skipped

    # ------------------------------------------------------------------
    # Cache info
    # ------------------------------------------------------------------

    def cached_tile_count(self) -> int:
        """Count tiles currently on disk."""
        if not self._cache_dir.exists():
            return 0
        return sum(1 for _ in self._cache_dir.rglob("*.png"))

    def clear_disk_cache(self) -> None:
        """Delete all cached tiles from disk."""
        import shutil
        if self._cache_dir.exists():
            shutil.rmtree(self._cache_dir)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _fetch_worker(self, z: int, x: int, y: int) -> None:
        key = (z, x, y)
        img = None
        try:
            if self._online:
                img = self._fetch_online(z, x, y)
            if img is None:
                img = self._load_disk(z, x, y)
        finally:
            with self._lock:
                self._pending.discard(key)
                cbs = self._callbacks.pop(key, [])
            if img is not None:
                self._store_mem(key, img)
            for cb in cbs:
                try:
                    cb()
                except Exception:
                    pass

    def _fetch_online(self, z: int, x: int, y: int) -> "Optional[object]":
        if not PIL_AVAILABLE:
            return None
        url = self._url.format(z=z, x=x, y=y)
        path = self._tile_path(z, x, y)
        try:
            if _REQUESTS_AVAILABLE and self._session is not None:
                r = self._session.get(url, timeout=8)  # type: ignore[attr-defined]
                r.raise_for_status()
                data = r.content
            else:
                req = _urllib.Request(url, headers={"User-Agent": _USER_AGENT})  # type: ignore[attr-defined]
                with _urllib.urlopen(req, timeout=8) as resp:  # type: ignore[attr-defined]
                    data = resp.read()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            from io import BytesIO
            from PIL import Image
            return Image.open(BytesIO(data)).convert("RGB")
        except Exception:
            self._online = False
            return None

    def _load_disk(self, z: int, x: int, y: int) -> "Optional[object]":
        if not PIL_AVAILABLE:
            return None
        path = self._tile_path(z, x, y)
        if path.exists():
            try:
                from PIL import Image
                return Image.open(path).convert("RGB")
            except Exception:
                pass
        return None

    def _store_mem(self, key: tuple, img: object) -> None:
        with self._lock:
            self._mem[key] = img
            self._mem.move_to_end(key)
            while len(self._mem) > _MEM_CACHE_SIZE:
                self._mem.popitem(last=False)

    def _tile_path(self, z: int, x: int, y: int) -> Path:
        return self._cache_dir / str(z) / str(x) / f"{y}.png"
