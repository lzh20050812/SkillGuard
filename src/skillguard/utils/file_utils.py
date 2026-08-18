from __future__ import annotations

from pathlib import Path


def is_probably_binary(path: Path, sample_size: int = 4096) -> bool:
    try:
        sample = path.read_bytes()[:sample_size]
    except OSError:
        return True
    if b"\x00" in sample:
        return True
    if not sample:
        return False
    text_bytes = sum(byte in b"\t\n\r\f\b" or 32 <= byte <= 126 or byte >= 128 for byte in sample)
    return text_bytes / len(sample) < 0.75

