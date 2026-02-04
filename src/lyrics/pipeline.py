from __future__ import annotations

import json
from pathlib import Path
from typing import List

import pandas as pd

from .features import extract_features, features_to_dict


def build_lyrics_features_from_cache(cache_fp: Path) -> pd.DataFrame:
    rows: List[dict] = []
    if not cache_fp.exists():
        raise FileNotFoundError(f"lyrics cache not found: {cache_fp}")

    with cache_fp.open("r", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            uri = obj.get("spotify_track_uri")
            found = bool(obj.get("found"))
            lyrics = obj.get("lyrics") if found else None

            feats = extract_features(lyrics)
            row = {
                "spotify_track_uri": uri,
                "genius_song_id": obj.get("genius_song_id"),
                "genius_full_title": obj.get("genius_full_title"),
            }
            row.update(features_to_dict(feats))
            rows.append(row)

    df = pd.DataFrame(rows).dropna(subset=["spotify_track_uri"])
    df = df.drop_duplicates(subset=["spotify_track_uri"], keep="last")
    return df


def write_lyrics_features(cache_fp: Path, out_fp: Path) -> Path:
    out_fp.parent.mkdir(parents=True, exist_ok=True)
    df = build_lyrics_features_from_cache(cache_fp)
    df.to_parquet(out_fp, index=False)
    return out_fp
