"""Dataset-independent EEG channel-name canonicalisation."""

from __future__ import annotations

import re
from collections.abc import Iterable

from mne.channels import make_standard_montage  # type: ignore[import-untyped]

_KNOWN_CASE = {
    "FPZ": "Fpz",
    "FP1": "Fp1",
    "FP2": "Fp2",
    "AFZ": "AFz",
    "FZ": "Fz",
    "FCZ": "FCz",
    "CZ": "Cz",
    "CPZ": "CPz",
    "PZ": "Pz",
    "POZ": "POz",
    "OZ": "Oz",
    "IZ": "Iz",
}
_STANDARD_1005_CASE: dict[str, str] = {
    str(name).casefold(): str(name)
    for name in make_standard_montage("standard_1005").ch_names
}


def canonicalize_channel_name(name: str) -> str:
    """Normalize whitespace/dot padding and common 10-20 letter case."""

    cleaned = re.sub(r"[.\s]+$", "", name.strip())
    cleaned = re.sub(r"^EEG\s+", "", cleaned, flags=re.IGNORECASE)
    if not cleaned:
        raise ValueError("channel name is empty after canonicalisation")
    standard = _STANDARD_1005_CASE.get(cleaned.casefold())
    if standard is not None:
        return standard
    upper = cleaned.upper()
    if upper in _KNOWN_CASE:
        return _KNOWN_CASE[upper]
    match = re.fullmatch(r"([A-Z]+)(\d+)", upper)
    if match:
        prefix, number = match.groups()
        if prefix == "FP":
            prefix = "Fp"
        elif len(prefix) > 1:
            prefix = prefix[0] + prefix[1:].lower()
        return f"{prefix}{number}"
    return cleaned


def canonicalize_channel_names(names: Iterable[str]) -> tuple[str, ...]:
    canonical = tuple(canonicalize_channel_name(name) for name in names)
    if len(set(canonical)) != len(canonical):
        raise ValueError("canonical channel names must be unique")
    return canonical
