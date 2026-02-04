from __future__ import annotations

from dataclasses import dataclass

from dataclasses import asdict

from typing import Dict, Any

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from .clean_lyrics import clean_lyrics, contains_cjk

from typing import Dict, Any


@dataclass
class LyricsFeatures:
    lyrics_found: bool
    contains_cjk: bool
    lyric_len_chars: int
    lyric_len_words: int
    unique_word_ratio: float
    vader_compound: float
    vader_pos: float
    vader_neg: float
    vader_neu: float


_analyzer = SentimentIntensityAnalyzer()


def extract_features(raw_lyrics: Optional[str]) -> LyricsFeatures:
    cleaned = clean_lyrics(raw_lyrics)
    if not cleaned:
        return LyricsFeatures(
            lyrics_found=False,
            contains_cjk=False,
            lyric_len_chars=0,
            lyric_len_words=0,
            unique_word_ratio=0.0,
            vader_compound=0.0,
            vader_pos=0.0,
            vader_neg=0.0,
            vader_neu=0.0,
        )
    
    has_cjk = contains_cjk(cleaned)
    words = cleaned.split()
    unique_ratio = (len({w.lower() for w in words}) / len(words)) if words else 0.0
    scores = _analyzer.polarity_scores(cleaned)

    return LyricsFeatures(
        lyrics_found=True,
        contains_cjk=has_cjk,
        lyric_len_chars=len(cleaned),
        lyric_len_words=len(words),
        unique_word_ratio=float(unique_ratio),
        vader_compound=float(scores["compound"]),
        vader_pos=float(scores["pos"]),
        vader_neg=float(scores["neg"]),
        vader_neu=float(scores["neu"]),
    )



def features_to_dict(f: LyricsFeatures) -> Dict[str, Any]:
    return asdict(f)

avg_line_length: float
