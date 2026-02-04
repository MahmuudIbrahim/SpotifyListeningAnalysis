from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple

import lyricsgenius


@dataclass(frozen=True)
class GeniusConfig:
    access_token: str
    timeout: int = 8
    retries: int = 1
    sleep_seconds: float = 0.3
    remove_section_headers: bool = True
    skip_non_songs: bool = True


def _canonical_key(uri: str, artist: str, title: str) -> str:
    return f"{uri.strip()}__{artist.strip().lower()}__{title.strip().lower()}"




def load_jsonl_cache(cache_fp: Path) -> Dict[str, dict]:
    """Loads JSONL cache into dict keyed by canonical_key."""
    cache: Dict[str, dict] = {}
    if not cache_fp.exists():
        return cache
    with cache_fp.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            key = obj.get("canonical_key")
            if key:
                cache[key] = obj
    return cache


def append_jsonl(cache_fp: Path, obj: dict) -> None:
    cache_fp.parent.mkdir(parents=True, exist_ok=True)
    with cache_fp.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def make_genius_client(cfg: GeniusConfig) -> lyricsgenius.Genius:
    g = lyricsgenius.Genius(
        cfg.access_token,
        timeout=cfg.timeout,
        retries=cfg.retries,
        sleep_time=cfg.sleep_seconds,
        remove_section_headers=cfg.remove_section_headers,
        skip_non_songs=cfg.skip_non_songs,
    )
    # Avoid verbose prints
    g.verbose = False
    return g


def fetch_one(
    genius: lyricsgenius.Genius,
    artist: str,
    title: str,
) -> Tuple[bool, Optional[int], Optional[str], Optional[str]]:
    """
    Returns: (found, genius_song_id, lyrics, full_title)
    """
    try:
        song = genius.search_song(title=title, artist=artist)
        if not song or not getattr(song, "lyrics", None):
            return False, None, None, None
        sid = getattr(song, "id", None)
        lyrics = song.lyrics
        full_title = getattr(song, "full_title", None)
        return True, sid, lyrics, full_title
    except Exception:
        return False, None, None, None


def fetch_lyrics_for_tracks(
    tracks: Iterable[dict],
    cache_fp: Path,
    genius_cfg: GeniusConfig,
    limit: Optional[int] = None,
    log_every: int = 25,
) -> None:
    """
    Fetch lyrics for tracks and append to JSONL cache.
    - Resumable (skips cached canonical_key)
    - Limit applies to NEW fetches this run
    - Uses lyricsgenius internal sleep_time; does NOT double-sleep
    """
    genius = make_genius_client(genius_cfg)
    cache = load_jsonl_cache(cache_fp)

    total_seen = 0
    newly_fetched = 0

    start = time.time()

    for t in tracks:
        total_seen += 1

        if limit is not None and newly_fetched >= limit:
            break

        uri = t.get("spotify_track_uri")
        artist = (t.get("artist_name_primary") or "").strip()
        title = (t.get("track_name") or "").strip()

        if not uri or not artist or not title:
            continue

        key = _canonical_key(uri, artist, title)
        if key in cache:
            continue

        found, song_id, lyrics, full_title = fetch_one(genius, artist, title)

        obj = {
            "canonical_key": key,
            "spotify_track_uri": uri,
            "artist": artist,
            "track": title,
            "found": found,
            "genius_song_id": song_id,
            "genius_full_title": full_title,
            "lyrics": lyrics if found else None,
            "retrieved_at_unix": int(time.time()),
        }

        append_jsonl(cache_fp, obj)
        cache[key] = obj
        newly_fetched += 1

        if log_every and newly_fetched % log_every == 0:
            elapsed = time.time() - start
            print(
                f"[lyrics] fetched {newly_fetched} new "
                f"(seen={total_seen}, cache={len(cache)}), "
                f"elapsed={elapsed:.1f}s"
            )

    elapsed = time.time() - start
    print(f"[lyrics] done. new={newly_fetched}, seen={total_seen}, cache={len(cache)}, elapsed={elapsed:.1f}s")
