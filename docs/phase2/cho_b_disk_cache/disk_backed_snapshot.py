"""Windows-only operational prototype; original Cho B input checks stay in force.

Each first load uses the unchanged verified loader. Immutable episode bytes are
sealed in a private bounded file store, using read handles that deny write/delete
sharing. An evicted episode can then be mapped read-only and inserted into the
original LRU before its normal request/configuration/source-pin checks. No model,
RNG, source roster, trial binding or scientific configuration is changed.
Explicit close is required after all borrowed episode views have been released.
"""
from __future__ import annotations

import ctypes
import gc
import hashlib
import mmap
import msvcrt
import os
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from evaluation.phase2_cho_b_input_snapshot import _ChoBInputSnapshot, _episode_bytes
from evaluation.phase2_profile_binding import ChoProfileEpisode

FIELDS = ("support_signals", "query_signals", "support_labels", "query_labels")
GIB = 1024**3
_kernel = ctypes.WinDLL("kernel32", use_last_error=True)
_create = _kernel.CreateFileW
_create.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p]
_create.restype = ctypes.c_void_p
_close = _kernel.CloseHandle
_close.argtypes = [ctypes.c_void_p]
_close.restype = ctypes.c_int
INVALID_HANDLE = ctypes.c_void_p(-1).value

def lock_read_only(path: Path):
    handle = _create(str(path), 0x80000000, 1, None, 3, 0x80, None)
    if handle == INVALID_HANDLE:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        descriptor = msvcrt.open_osfhandle(handle, os.O_RDONLY | os.O_BINARY)
    except BaseException:
        _close(handle)
        raise
    return os.fdopen(descriptor, "rb", buffering=0)

def identity(path):
    value = path.stat()
    return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns)

@dataclass
class StoredEpisode:
    path: Path
    stream: object
    binding: object
    arrays: tuple
    size: int
    sha256: str
    file_identity: tuple

    def check(self):
        if self.path.is_symlink() or self.path.resolve() != self.path or identity(self.path) != self.file_identity:
            raise ValueError("private mapped cache file identity changed")

    def mapped(self):
        self.check()
        view = mmap.mmap(self.stream.fileno(), 0, access=mmap.ACCESS_READ)
        arrays = tuple(np.ndarray(shape=shape, dtype=dtype, buffer=view, offset=offset) for shape, dtype, offset in self.arrays)
        if any(array.flags.writeable for array in arrays):
            raise ValueError("private mapped cache returned writable arrays")
        return ChoProfileEpisode(self.binding, *arrays)

    def verify(self):
        self.check()
        digest = hashlib.sha256()
        self.stream.seek(0)
        while block := self.stream.read(1024**2):
            digest.update(block)
        self.check()
        if digest.hexdigest() != self.sha256:
            raise ValueError("private mapped cache bytes changed")

class DiskBackedChoSnapshot:
    """Composition around the original LRU, with a bounded immutable file tier."""
    def __init__(self, root, protocol_config, permitted_catalogs, permitted_assets,
                 *, cache_directory, maximum_retained_bytes=512 * 1024**2,
                 maximum_disk_bytes=2 * GIB):
        if os.name != "nt":
            raise ValueError("prototype requires Windows deny-write/delete file sharing")
        if type(maximum_disk_bytes) is not int or not 0 <= maximum_disk_bytes <= 2 * GIB:
            raise ValueError("private cache disk budget must be within2GiB")
        self._snapshot = _ChoBInputSnapshot(root, protocol_config, permitted_catalogs, permitted_assets, maximum_retained_bytes=maximum_retained_bytes)
        parent = Path(cache_directory)
        parent.mkdir(parents=True, exist_ok=True)
        if parent.resolve() != parent or parent.is_symlink():
            raise ValueError("private mapped cache parent aliases a path")
        self.directory = Path(tempfile.mkdtemp(prefix="source_cache_", dir=parent))
        self._records = {}
        self._retired = []
        self._disk_bytes = 0
        self._maximum_disk_bytes = maximum_disk_bytes
        self._closing = False
        self._closed = False
        self.statistics = {"original_loads": 0, "resident_hits": 0, "disk_restores": 0, "disk_budget_bypasses": 0}

    def __getattr__(self, attribute):
        return getattr(self._snapshot, attribute)

    def _store(self, subject, episode):
        size = _episode_bytes(episode)
        if size > self._maximum_retained_bytes or self._disk_bytes + size > self._maximum_disk_bytes:
            self.statistics["disk_budget_bypasses"] += 1
            return episode
        path = self.directory / (uuid.uuid4().hex + ".bin")
        layouts = []
        digest = hashlib.sha256()
        offset = 0
        stream = None
        try:
            with path.open("xb", buffering=0) as target:
                for field in FIELDS:
                    array = getattr(episode, field)
                    if not array.flags.c_contiguous or array.dtype.hasobject:
                        raise ValueError("private mapped cache requires contiguous scalar arrays")
                    layouts.append((array.shape, array.dtype, offset))
                    data = memoryview(array).cast("B")
                    digest.update(data)
                    written = target.write(data)
                    if written != len(data):
                        raise OSError("private mapped cache write was incomplete")
                    offset += array.nbytes
                target.flush()
                os.fsync(target.fileno())
            if offset != size:
                raise ValueError("private mapped cache byte count differs")
            stream = lock_read_only(path)
            record = StoredEpisode(path, stream, episode.binding, tuple(layouts), size, digest.hexdigest(), identity(path))
            record.verify()
            mapped = record.mapped()
            self._records[subject] = record
            self._disk_bytes += size
            return mapped
        except BaseException:
            if stream is not None:
                stream.close()
            path.unlink(missing_ok=True)
            raise

    def load(self, protocol_config, catalog, episode_record, *, shots_per_class, profile_assets):
        if self._closing:
            raise ValueError("private mapped cache is closing or closed")
        subject = catalog.subject
        try:
            resident = subject in self._entries
            stored = self._records.get(subject)
            if stored is not None:
                stored.check()
            if not resident and stored is not None:
                mapped = stored.mapped()
                while self._retained_bytes + stored.size > self._maximum_retained_bytes:
                    _, old = self._entries.popitem(last=False)
                    self._snapshot._retained_bytes -= _episode_bytes(old)
                    del old
                self._entries[subject] = mapped
                self._snapshot._retained_bytes += stored.size
                del mapped
            # All original catalog/assets/manifest/config/source-pin checks still run.
            episode = self._snapshot.load(protocol_config, catalog, episode_record,
                                          shots_per_class=shots_per_class, profile_assets=profile_assets)
            if resident:
                self.statistics["resident_hits"] += 1
            elif stored is not None:
                self.statistics["disk_restores"] += 1
            else:
                self.statistics["original_loads"] += 1
                if subject in self._entries:
                    mapped = self._store(subject, episode)
                    self._entries[subject] = mapped
                    episode = mapped
            return episode
        except BaseException:
            self.clear()
            raise

    def clear(self):
        # Discard reusable episodes exactly as the original cache does. Borrowed
        # immutable views remain valid; Windows defers their file deletion until
        # the last mapping is released. Those bytes still count against the budget.
        self._snapshot.clear()
        records = list(self._records.values())
        self._records.clear()
        for record in records:
            record.stream.close()
            try:
                record.path.unlink(missing_ok=True)
                self._disk_bytes -= record.size
            except OSError:
                self._retired.append(record)

    def verify(self, protocol_config):
        try:
            self._snapshot.verify(protocol_config)
            for record in self._records.values():
                record.verify()
        except BaseException:
            self.clear()
            raise

    def close(self):
        if self._closed:
            return
        self._closing = True
        self.clear()
        gc.collect()
        failures = []
        for record in self._retired:
            record.stream.close()
            try:
                record.path.unlink(missing_ok=True)
            except OSError as error:
                failures.append(error)
        if failures:
            raise RuntimeError("private mapped cache cleanup requires releasing borrowed episode views") from failures[0]
        self.directory.rmdir()
        self._records.clear()
        self._retired.clear()
        self._disk_bytes = 0
        self._closed = True
