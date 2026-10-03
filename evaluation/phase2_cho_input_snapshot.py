"""Private, selector-lifetime snapshots of already verified Cho Profile A inputs.

This changes I/O only. Public loaders still return owned arrays, and every
evidence boundary must rehash all touched artifacts and configuration files.
"""

from __future__ import annotations

import stat
from collections import OrderedDict
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from core.config import config_digest, config_snapshot
from evaluation.phase2_cho_profile_a import load_cho_profile_a_subject
from evaluation.phase2_profile_binding import BCIProfileASubject
from evaluation.phase2_protocol import TrialCatalog
from scripts.audit_phase2_protocol import file_digest, validate_protocol

_MAXIMUM_RETAINED_BYTES = 3 * 1024**3 // 2


@dataclass(frozen=True, slots=True)
class _FilePin:
    path: Path
    resolved_path: Path
    identity: tuple[int, int, int, int, int]
    sha256: str

    @staticmethod
    def _identity(path: Path) -> tuple[Path, tuple[int, int, int, int, int]]:
        resolved = path.resolve(strict=True)
        status = path.stat()
        if not stat.S_ISREG(status.st_mode):
            raise ValueError("Cho input snapshot requires an ordinary file")
        return resolved, (
            status.st_dev, status.st_ino, status.st_size,
            status.st_mtime_ns, status.st_ctime_ns,
        )

    @classmethod
    def capture(cls, root: Path, path: Path, expected_sha256: str | None = None) -> _FilePin:
        resolved, identity = cls._identity(path)
        if not resolved.is_relative_to(root):
            raise ValueError("Cho input snapshot path escapes the project")
        digest = file_digest(path)
        if expected_sha256 is not None and digest != expected_sha256:
            raise ValueError("Cho input snapshot bytes differ from the catalog")
        result = cls(path, resolved, identity, digest)
        result.check_metadata()
        return result

    def check_metadata(self) -> None:
        if self._identity(self.path) != (self.resolved_path, self.identity):
            raise ValueError("Cho input snapshot file identity changed")

    def verify_bytes(self) -> None:
        self.check_metadata()
        # Deliberately unconditional: unchanged metadata cannot prove unchanged bytes.
        actual = file_digest(self.path)
        self.check_metadata()
        if actual != self.sha256:
            raise ValueError("Cho input snapshot bytes changed")


class _ChoInputSnapshot:
    """Bounded lazy LRU; permitted catalogs exclude the outer target at construction.

    Only signal/label bytes survive a cache insertion. The original loader's
    writable arrays and NPZ buffers are never retained. File pins survive eviction.
    """

    def __init__(
        self, root: Path, protocol_config: Mapping[str, Any],
        permitted_catalogs: tuple[TrialCatalog, ...],
        *, maximum_retained_bytes: int = _MAXIMUM_RETAINED_BYTES,
    ) -> None:
        if (
            type(maximum_retained_bytes) is not int
            or not 0 <= maximum_retained_bytes <= _MAXIMUM_RETAINED_BYTES
        ):
            raise ValueError("Cho input snapshot byte limit must be within 1.5 GiB")
        if (
            not permitted_catalogs
            or any(c.dataset != "cho2017" for c in permitted_catalogs)
            or len({c.subject for c in permitted_catalogs}) != len(permitted_catalogs)
        ):
            raise ValueError("Cho input snapshot requires unique permitted Cho catalogs")
        self._root = root.resolve()
        config: dict[str, Any] = config_snapshot(protocol_config)
        validate_protocol(config)
        if config["datasets"]["cho2017"]["artifact_directory"] != (
            "data/processed/cho2017/profile_a"
        ):
            raise ValueError("Cho input snapshot requires the fixed Profile A directory")
        self._config_sha256 = config_digest(config)
        self._catalogs = {c.subject: c for c in permitted_catalogs}
        self._base_path = self._root / "configs/base.toml"
        self._threshold_path = self._root / config["preparation"]["threshold_config"]
        self._configuration_pins: tuple[_FilePin, ...] = ()
        self._artifact_pins: dict[str, _FilePin] = {}
        self._entries: OrderedDict[str, BCIProfileASubject] = OrderedDict()
        self._maximum_retained_bytes = maximum_retained_bytes
        self._retained_bytes = 0

    def _check_configuration(self, protocol_config: Mapping[str, Any]) -> None:
        if config_digest(protocol_config) != self._config_sha256:
            raise ValueError("Cho input snapshot protocol configuration changed")
        for pin in self._configuration_pins:
            pin.check_metadata()

    def load(
        self, protocol_config: Mapping[str, Any], catalog: TrialCatalog,
    ) -> BCIProfileASubject:
        if self._catalogs.get(catalog.subject) != catalog:
            raise ValueError("Cho input snapshot catalog is outside the permitted source cohort")
        self._check_configuration(protocol_config)
        if not self._configuration_pins:
            self._configuration_pins = (
                _FilePin.capture(self._root, self._base_path),
                _FilePin.capture(self._root, self._threshold_path),
            )
        pin = self._artifact_pins.get(catalog.subject)
        if pin is None:
            path = self._root / "data/processed/cho2017/profile_a" / f"{catalog.subject}.npz"
            pin = _FilePin.capture(self._root, path, catalog.artifact_sha256)
            self._artifact_pins[catalog.subject] = pin
        else:
            pin.check_metadata()
        cached = self._entries.get(catalog.subject)
        if cached is not None:
            self._entries.move_to_end(catalog.subject)
            return cached
        loaded = load_cho_profile_a_subject(self._root, protocol_config, catalog)
        self._check_configuration(protocol_config)
        pin.check_metadata()
        if (
            loaded.manifest_sha256 != catalog.artifact_sha256
            or loaded.base_config_sha256 != self._configuration_pins[0].sha256
        ):
            raise ValueError("Cho input snapshot loaded identity differs from its pinned files")
        size = loaded.signals.nbytes + loaded.labels.nbytes
        if size > self._maximum_retained_bytes:
            return loaded  # Ordinary owned loader output; the artifact pin still survives.
        while self._retained_bytes + size > self._maximum_retained_bytes:
            _, evicted = self._entries.popitem(last=False)
            self._retained_bytes -= evicted.signals.nbytes + evicted.labels.nbytes
        immutable = BCIProfileASubject(
            np.frombuffer(loaded.signals.tobytes(order="C"), dtype=loaded.signals.dtype).reshape(
                loaded.signals.shape
            ),
            np.frombuffer(loaded.labels.tobytes(order="C"), dtype=loaded.labels.dtype).reshape(
                loaded.labels.shape
            ),
            loaded.artifact_rows, loaded.manifest_sha256, loaded.base_config_sha256,
        )
        self._entries[catalog.subject] = immutable
        self._retained_bytes += size
        return immutable

    def verify(self, protocol_config: Mapping[str, Any]) -> None:
        """Full streaming SHA for every touched file, including evicted/bypassed inputs."""
        self._check_configuration(protocol_config)
        for pin in (*self._configuration_pins, *self._artifact_pins.values()):
            pin.verify_bytes()
