"""Private bounded Cho 60 Hz maximum-shot snapshots for LaBraM source SGD only.

The normal binding loader verifies each miss. Validation and public loaders keep
their ordinary owned-array behavior. Every public selection evidence boundary
must fully hash all touched files and release resident signal/label arrays.
"""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Mapping
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from core.config import config_digest, config_snapshot
from evaluation.phase2_cho_input_snapshot import _FilePin
from evaluation.phase2_profile_binding import (
    ChoProfileAssets60Hz,
    ChoProfileBinding60Hz,
    ChoProfileEpisode,
    load_cho_profile_b_episode,
)
from evaluation.phase2_protocol import TrialCatalog, nested_episode
from evaluation.phase2_records import verify_envelope
from scripts.audit_phase2_protocol import inside, validate_protocol

_MAXIMUM_RETAINED_BYTES = 2 * 1024**3
_B_DIRECTORY = "data/processed/cho2017/profile_b_60hz_v1"
_VARIANT_CONFIG = "configs/phase2/cho_profile_b_60hz.toml"


def _episode_bytes(episode: ChoProfileEpisode) -> int:
    return sum(
        array.nbytes for array in (
            episode.support_signals, episode.query_signals,
            episode.support_labels, episode.query_labels,
        )
    )


def _immutable(array: NDArray[Any]) -> NDArray[Any]:
    # Bytes, rather than a writable ndarray owner, make setflags(write=True) fail.
    return np.frombuffer(array.tobytes(order="C"), dtype=array.dtype).reshape(array.shape)


class _ChoBInputSnapshot:
    """Lazy source-only LRU; exact verified maximum-shot binding is preserved.

    Cached arrays contain every retained source trial exactly once. No NPZ/raw
    buffers or second signal copy survive insertion. Pins outlive eviction and
    resident-array cleanup; there is no process/global cache or outer prefetch.
    """

    def __init__(
        self, root: Path, protocol_config: Mapping[str, Any],
        permitted_catalogs: tuple[TrialCatalog, ...],
        permitted_assets: Mapping[str, ChoProfileAssets60Hz],
        *, maximum_retained_bytes: int = _MAXIMUM_RETAINED_BYTES,
    ) -> None:
        if (
            type(maximum_retained_bytes) is not int
            or not 0 <= maximum_retained_bytes <= _MAXIMUM_RETAINED_BYTES
        ):
            raise ValueError("Cho B input snapshot byte limit must be within 2 GiB")
        if (
            not permitted_catalogs
            or any(c.dataset != "cho2017" for c in permitted_catalogs)
            or len({c.subject for c in permitted_catalogs}) != len(permitted_catalogs)
            or set(permitted_assets) != {c.subject for c in permitted_catalogs}
            or any(not isinstance(a, ChoProfileAssets60Hz) for a in permitted_assets.values())
        ):
            raise ValueError("Cho B input snapshot requires permitted Cho 60 Hz sources/assets")
        self._root = root.resolve()
        config: dict[str, Any] = config_snapshot(protocol_config)
        shots = validate_protocol(config)
        if config["datasets"]["cho2017"]["artifact_directory"] != (
            "data/processed/cho2017/profile_a"
        ):
            raise ValueError("Cho B input snapshot requires the fixed Profile A directory")
        self._config_sha256 = config_digest(config)
        self._catalogs = {c.subject: c for c in permitted_catalogs}
        self._assets = dict(permitted_assets)
        self._episodes = {
            c.subject: nested_episode(c, shots=shots, protocol_sha256=self._config_sha256)
            for c in permitted_catalogs
        }
        self._maximum_shots = shots[-1]
        self._configuration_paths = (
            self._root / "configs/base.toml",
            self._root / config["preparation"]["threshold_config"],
            self._root / _VARIANT_CONFIG,
        )
        self._configuration_pins: tuple[_FilePin, ...] = ()
        self._subject_pins: dict[str, tuple[_FilePin, ...]] = {}
        self._entries: OrderedDict[str, ChoProfileEpisode] = OrderedDict()
        self._maximum_retained_bytes = maximum_retained_bytes
        self._retained_bytes = 0

    def clear(self) -> None:
        """Release all resident arrays; retain provenance pins for future verification."""
        self._entries.clear()
        self._retained_bytes = 0

    def _check_configuration(self, protocol_config: Mapping[str, Any]) -> None:
        if config_digest(protocol_config) != self._config_sha256:
            raise ValueError("Cho B input snapshot protocol configuration changed")
        # These files are small. Check exact bytes on hits even with restored mtimes.
        for pin in self._configuration_pins:
            pin.verify_bytes()

    def load(
        self, protocol_config: Mapping[str, Any], catalog: TrialCatalog,
        episode_record: Mapping[str, Any], *, shots_per_class: int,
        profile_assets: ChoProfileAssets60Hz,
    ) -> ChoProfileEpisode:
        try:
            return self._load(
                protocol_config, catalog, episode_record,
                shots_per_class=shots_per_class, profile_assets=profile_assets,
            )
        except BaseException:
            self.clear()
            raise

    def _load(
        self, protocol_config: Mapping[str, Any], catalog: TrialCatalog,
        episode_record: Mapping[str, Any], *, shots_per_class: int,
        profile_assets: ChoProfileAssets60Hz,
    ) -> ChoProfileEpisode:
        if (
            self._catalogs.get(catalog.subject) != catalog
            or self._assets.get(catalog.subject) != profile_assets
        ):
            raise ValueError("Cho B input snapshot catalog/assets are outside permitted sources")
        if (
            type(shots_per_class) is not int or shots_per_class != self._maximum_shots
            or not verify_envelope(
                episode_record, kind="episode_manifest",
                expected_payload=self._episodes[catalog.subject].payload(),
            )
        ):
            raise ValueError("Cho B input snapshot requires the exact maximum-shot episode")
        self._check_configuration(protocol_config)
        if not self._configuration_pins:
            self._configuration_pins = tuple(
                _FilePin.capture(
                    self._root, path,
                    profile_assets.variant_config_sha256 if index == 2 else None,
                )
                for index, path in enumerate(self._configuration_paths)
            )
        if self._configuration_pins[2].sha256 != profile_assets.variant_config_sha256:
            raise ValueError("Cho B input snapshot variant configuration differs")
        pins = self._subject_pins.get(catalog.subject)
        if pins is not None:
            for pin in pins:
                pin.check_metadata()
        cached = self._entries.get(catalog.subject)
        if cached is not None:
            self._entries.move_to_end(catalog.subject)
            return cached
        if pins is None:
            paths = (
                self._root / "data/processed/cho2017/profile_a" / f"{catalog.subject}.npz",
                self._root / _B_DIRECTORY / f"{catalog.subject}.npz",
                self._root / _B_DIRECTORY / f"{catalog.subject}.manifest.json",
            )
            # Preserve lexical paths so later alias/replacement changes are detectable.
            if paths[1].parent.resolve() != paths[1].parent:
                raise ValueError("Cho B input snapshot versioned directory aliases a namespace")
            pins = tuple(
                _FilePin.capture(self._root, path, expected)
                for path, expected in zip(paths, (
                    catalog.artifact_sha256, profile_assets.profile_b_artifact_sha256,
                    profile_assets.profile_b_manifest_sha256,
                ), strict=True)
            )
            if any(pin.path != pin.resolved_path for pin in pins[1:]):
                raise ValueError("Cho B input snapshot subject file aliases another namespace")
            self._subject_pins[catalog.subject] = pins
        loaded = load_cho_profile_b_episode(
            self._root, protocol_config, catalog, episode_record,
            shots_per_class=shots_per_class, **asdict(profile_assets),
        )
        self._check_configuration(protocol_config)
        for pin in pins:
            pin.check_metadata()
        binding = loaded.binding
        if (
            not isinstance(binding, ChoProfileBinding60Hz)
            or binding.profile_a_artifact_sha256 != catalog.artifact_sha256
            or binding.profile_b_artifact_sha256 != profile_assets.profile_b_artifact_sha256
            or binding.profile_b_manifest_sha256 != profile_assets.profile_b_manifest_sha256
            or binding.base_config_sha256 != self._configuration_pins[0].sha256
            or binding.variant_config_sha256 != profile_assets.variant_config_sha256
        ):
            raise ValueError("Cho B input snapshot loaded binding differs from pinned identities")
        if len(pins) == 3:
            raw_path = self._root / binding.source_file
            raw_root = inside(self._root, "data/raw/moabb/cho2017")
            if not raw_path.resolve().is_relative_to(raw_root):
                raise ValueError("Cho B input snapshot raw provenance escapes the raw root")
            pins = (*pins, _FilePin.capture(self._root, raw_path, binding.source_sha256))
            self._subject_pins[catalog.subject] = pins
        elif (
            pins[3].path != self._root / binding.source_file
            or pins[3].sha256 != binding.source_sha256
        ):
            raise ValueError("Cho B input snapshot raw provenance differs from its pin")
        ids = binding.support_trial_ids + binding.query_trial_ids
        if len(ids) != len(catalog.trial_ids) or set(ids) != set(catalog.trial_ids):
            raise ValueError("Cho B input snapshot maximum pool differs from retained trials")
        size = _episode_bytes(loaded)
        if size > self._maximum_retained_bytes:
            return loaded  # Owned loader output; all input pins still survive the bypass.
        while self._retained_bytes + size > self._maximum_retained_bytes:
            _, evicted = self._entries.popitem(last=False)
            self._retained_bytes -= _episode_bytes(evicted)
            del evicted
        immutable = ChoProfileEpisode(
            binding, _immutable(loaded.support_signals), _immutable(loaded.query_signals),
            _immutable(loaded.support_labels), _immutable(loaded.query_labels),
        )
        self._entries[catalog.subject] = immutable
        self._retained_bytes += size
        return immutable

    def verify(self, protocol_config: Mapping[str, Any]) -> None:
        """Unconditional streaming SHA for all touched files, including evictions/bypasses."""
        try:
            self._check_configuration(protocol_config)
            # Deduplicate shared raw/config paths without discarding their identity pins.
            checked: set[tuple[Path, str]] = set()
            for pin in (
                *self._configuration_pins,
                *(pin for pins in self._subject_pins.values() for pin in pins),
            ):
                key = (pin.path, pin.sha256)
                if key not in checked:
                    pin.verify_bytes()
                    checked.add(key)
                else:
                    pin.check_metadata()
        except BaseException:
            self.clear()
            raise
