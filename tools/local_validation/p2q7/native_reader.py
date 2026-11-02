"""Q4 retained NTFS witnesses. Source only until independent run admission.

These witnesses exclude ordinary incompatible opens, not privileged kernel
mutation. Directory handles do not freeze membership: recipes are resampled.
All original handles remain owned until explicit close, including publication.
"""

import ctypes
import hashlib
import os
from pathlib import Path

from ..v1.records import (Refusal, canonical_bytes, defensive_copy, exact_int, exact_string,
                         require, validate_file_descriptor, validate_snapshot,
                         windows_path)

CHUNK_BYTES = 65_536
MAX_DIRECTORIES = 25_000
MAX_ENTRIES = 50_000
MAX_OUTPUT_FILES = 256
MAX_OUTPUT_BYTES = 64 * 1024**2
MAX_OUTPUT_FILE_BYTES = 8 * 1024**2
INVALID_HANDLE = ctypes.c_void_p(-1).value


class _Info(ctypes.Structure):
    _fields_ = [(name, ctypes.c_uint32) for name in (
        "attributes", "created_low", "created_high", "access_low", "access_high",
        "write_low", "write_high", "volume", "size_high", "size_low", "links",
        "index_high", "index_low")]


class _FileId(ctypes.Structure):
    _fields_ = [("volume", ctypes.c_uint64), ("identifier", ctypes.c_ubyte * 16)]


def checked_path(value):
    """Accept one spelling; normalization is never used to rescue aliases."""
    require(type(value) is str or isinstance(value, Path), "path string required")
    text = str(value)
    # pathlib Windows inputs conventionally have backslashes; mixed spelling is
    # refused. Descriptors always use v1's canonical forward-slash spelling.
    require(not ("/" in text and "\\" in text), "mixed path separators")
    text = text.replace("\\", "/")
    windows_path(text, absolute=True)
    return text


def _ancestors(path, include=False):
    parts = path[3:].split("/") if path[3:] else []
    result = [path[:3]]
    for index in range(1, len(parts) + (1 if include else 0)):
        result.append(path[:3] + "/".join(parts[:index]))
    return result


def _pin(expected):
    if expected is None:
        return None
    require(type(expected) is dict and set(expected) == {"bytes", "sha256"}, "exact pin fields")
    exact_int(expected["bytes"], upper=2 * 1024**3)
    require(type(expected["sha256"]) is str and len(expected["sha256"]) == 64
            and all(c in "0123456789abcdef" for c in expected["sha256"]), "pin SHA256")
    return expected.copy()


class RetainedReader:
    def __init__(self, checkpoint, max_files=25_000,
                 max_total_bytes=4 * 1024**3, max_file_bytes=2 * 1024**3):
        require(os.name == "nt", "Windows NTFS reader required")
        require(callable(checkpoint), "checkpoint callable required")
        exact_int(max_files, 1, 25_000)
        exact_int(max_total_bytes, 0, 4 * 1024**3)
        exact_int(max_file_bytes, 0, 2 * 1024**3)
        self.checkpoint = checkpoint
        self.max_files, self.max_total_bytes, self.max_file_bytes = max_files, max_total_bytes, max_file_bytes
        self._files, self._directories, self._paths, self._identities = {}, {}, {}, {}
        self._recipes = []
        self._total = 0
        self._closed = False
        self.cleanup_errors = []
        self.api = ctypes.WinDLL("kernel32.dll", use_last_error=True, winmode=0x800)
        signatures = {
            "CreateFileW": ([ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p,
                             ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p], ctypes.c_void_p),
            "CloseHandle": ([ctypes.c_void_p], ctypes.c_int),
            "GetDriveTypeW": ([ctypes.c_wchar_p], ctypes.c_uint32),
            "GetFileType": ([ctypes.c_void_p], ctypes.c_uint32),
            "GetFinalPathNameByHandleW": ([ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32], ctypes.c_uint32),
            "GetFileInformationByHandle": ([ctypes.c_void_p, ctypes.POINTER(_Info)], ctypes.c_int),
            "GetFileInformationByHandleEx": ([ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32], ctypes.c_int),
            "GetVolumeInformationByHandleW": ([ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_uint32,
                ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_uint32], ctypes.c_int),
            "SetFilePointerEx": ([ctypes.c_void_p, ctypes.c_int64, ctypes.c_void_p, ctypes.c_uint32], ctypes.c_int),
            "ReadFile": ([ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32), ctypes.c_void_p], ctypes.c_int),
            "WriteFile": ([ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32), ctypes.c_void_p], ctypes.c_int),
            "FlushFileBuffers": ([ctypes.c_void_p], ctypes.c_int),
        }
        for name, (arguments, result) in signatures.items():
            getattr(self.api, name).argtypes = arguments
            getattr(self.api, name).restype = result

    def _check(self):
        require(not self._closed, "reader closed")
        require(self.checkpoint() is True, "checkpoint refused")

    @staticmethod
    def _error(message):
        return ctypes.WinError(ctypes.get_last_error(), message)

    def _close_handle(self, handle):
        if not self.api.CloseHandle(handle):
            error = str(self._error("CloseHandle failed"))
            self.cleanup_errors.append(error)
            raise OSError(error)

    def _facts(self, handle, path, directory):
        self._check()
        info, identifier = _Info(), _FileId()
        if not self.api.GetFileInformationByHandle(handle, ctypes.byref(info)):
            raise self._error("file information failed")
        if not self.api.GetFileInformationByHandleEx(handle, 18, ctypes.byref(identifier), ctypes.sizeof(identifier)):
            raise self._error("128-bit file identity failed")
        require(self.api.GetFileType(handle) == 1, "disk file required")
        require(not (info.attributes & 0x440), "reparse/device refused")
        require(bool(info.attributes & 0x10) == directory, "native file type differs")
        require(directory or info.links == 1, "hardlink refused")
        require(identifier.volume != 0 and any(identifier.identifier), "ambiguous native identity")
        filesystem = ctypes.create_unicode_buffer(64)
        if not self.api.GetVolumeInformationByHandleW(handle, None, 0, None, None, None,
                                                      filesystem, len(filesystem)):
            raise self._error("handle filesystem query failed")
        require(filesystem.value == "NTFS", "qualified local NTFS required")
        require(self.api.GetDriveTypeW(path[:3].replace("/", "\\")) == 3, "fixed local volume required")
        final = ctypes.create_unicode_buffer(32768)
        count = self.api.GetFinalPathNameByHandleW(handle, final, len(final), 0)
        require(0 < count < len(final) and final.value == "\\\\?\\" + path.replace("/", "\\"),
                "final native spelling/identity differs")
        native = {"schema": "cho51_lv_native_identity_v1", "volume_serial": format(identifier.volume, "016x"),
                  "file_id": bytes(identifier.identifier).hex(), "volume_kind": "local_fixed", "filesystem": "NTFS"}
        return native, (info.size_high << 32) | info.size_low, info.links, info.attributes

    def _register(self, path, native):
        key = path.lower()
        require(key not in self._paths or self._paths[key] == path, "case-colliding path refused")
        identity = (native["volume_serial"], native["file_id"])
        require(identity not in self._identities or self._identities[identity] == path, "native identity alias refused")
        self._paths[key], self._identities[identity] = path, path

    def _open(self, path, directory=False, create=False):
        self._check()
        handle = self.api.CreateFileW(path.replace("/", "\\"), 0xC0000000 if create else 0x80000000,
            1, None, 1 if create else 3, 0x00200000 | (0x02000000 if directory else 0), None)
        if handle in (None, INVALID_HANDLE):
            raise self._error("create-new/open retained handle failed")
        try:
            facts = self._facts(handle, path, directory)
            self._register(path, facts[0])
            return handle, facts
        except BaseException:
            self._close_handle(handle)
            raise

    def retain_directory(self, path):
        self._check()
        path = checked_path(path)
        for item in _ancestors(path, include=True):
            if item in self._directories:
                continue
            require(len(self._directories) < MAX_DIRECTORIES, "directory bound")
            handle, facts = self._open(item, directory=True)
            descriptor = {"schema": "cho51_lv_directory_descriptor_v1", "path": item,
                          "native_identity": facts[0], "file_type": "directory", "reparse_point": False}
            self._directories[item] = (handle, descriptor)
        return defensive_copy(self._directories[path][1])

    def _seek(self, handle):
        self._check()
        if not self.api.SetFilePointerEx(handle, 0, None, 0):
            raise self._error("retained stream rewind failed")

    def _hash(self, handle, length, collect=False):
        self._seek(handle)
        digest, count, chunks = hashlib.sha256(), 0, []
        while True:
            self._check()
            amount = min(CHUNK_BYTES, length - count + 1)
            require(1 <= amount <= 65_536, "invalid chunk bound")
            buffer, read = ctypes.create_string_buffer(amount), ctypes.c_uint32()
            if not self.api.ReadFile(handle, buffer, amount, ctypes.byref(read), None):
                raise self._error("retained stream read failed")
            self._check()
            require(read.value <= amount, "invalid read length")
            if read.value == 0:
                require(count == length, "short retained stream")
                return {"bytes": count, "sha256": digest.hexdigest()}, b"".join(chunks) if collect else None
            count += read.value
            require(count <= length, "long retained stream")
            chunk = buffer.raw[:read.value]
            digest.update(chunk)
            if collect:
                chunks.append(chunk)

    def retain(self, path, expected=None):
        return self._retain(path, expected, self.max_file_bytes)

    def _retain(self, path, expected, cap):
        self._check()
        path, expected = checked_path(path), _pin(expected)
        if path in self._files:
            descriptor = self._files[path][1]
            require(descriptor["bytes"] <= cap, "read byte bound")
            require(expected is None or expected == {k: descriptor[k] for k in ("bytes", "sha256")}, "duplicate pin conflict")
            return defensive_copy(descriptor)
        require(len(self._files) < self.max_files, "file count bound")
        for ancestor in _ancestors(path):
            self.retain_directory(ancestor)
        handle, facts = self._open(path)
        try:
            require(facts[1] <= min(cap, self.max_file_bytes) and self._total + facts[1] <= self.max_total_bytes, "file/aggregate byte bound")
            observed, _ = self._hash(handle, facts[1])
            require(self._facts(handle, path, False) == facts, "file facts changed while hashing")
            require(expected is None or observed == expected, "pin mismatch")
            descriptor = validate_file_descriptor({"schema": "cho51_lv_file_descriptor_v1", "path": path,
                "native_identity": facts[0], "file_type": "regular", "reparse_point": False,
                "link_count": 1, **observed})
            self._files[path] = (handle, descriptor, facts)
            self._total += facts[1]
            return defensive_copy(descriptor)
        except BaseException:
            self._close_handle(handle)
            raise

    def read_small(self, path, expected=None, max_bytes=8 * 1024**2):
        exact_int(max_bytes, 0, 8 * 1024**2)
        path = checked_path(path)
        descriptor = self._retain(path, expected, max_bytes)
        require(descriptor["bytes"] <= max_bytes, "small read byte bound")
        handle, _, facts = self._files[path]
        pin, raw = self._hash(handle, descriptor["bytes"], collect=True)
        require(pin == {k: descriptor[k] for k in ("bytes", "sha256")}
                and self._facts(handle, path, False) == facts, "small read drift")
        return raw

    def _enumerate(self, root, suffixes, excluded_dirs):
        pending, recipe, directories, files, count = [root], [], set(), set(), 0
        while pending:
            self._check()
            directory = pending.pop()
            self.retain_directory(directory)
            directories.add(directory)
            with os.scandir(directory) as entries:
                for entry in entries:
                    self._check()
                    count += 1
                    require(count <= MAX_ENTRIES, "enumeration entry bound")
                    path = checked_path(directory.rstrip("/") + "/" + entry.name)
                    require(path.startswith(root.rstrip("/") + "/"), "enumeration outside root")
                    # Windows DirEntry.stat omits the hardlink count. Query
                    # full no-follow path metadata, then retain selected files
                    # and recheck their native handle facts as before.
                    info = os.stat(path, follow_symlinks=False)
                    require(not (info.st_file_attributes & 0x440), "enumerated reparse/device refused")
                    is_directory = bool(info.st_file_attributes & 0x10)
                    require(is_directory or info.st_nlink == 1, "enumerated hardlink refused")
                    recipe.append((path, is_directory))
                    if is_directory and entry.name not in excluded_dirs:
                        require(len(directories) + len(pending) < MAX_DIRECTORIES, "enumeration directory bound")
                        pending.append(path)
                    elif not is_directory and any(entry.name.endswith(suffix) for suffix in suffixes):
                        require(len(files) < self.max_files, "enumeration file bound")
                        files.add(path)
            self._check()
        require(len({path.lower() for path, _ in recipe}) == len(recipe), "enumeration case collision")
        return tuple(sorted(recipe)), directories, files

    def observe_tree(self, root, label, role, suffixes=(".json",), excluded_dirs=()):
        self._check()
        root = checked_path(root)
        require(exact_string(label, 128) != "", "snapshot label required")
        require(type(role) is str and role in ("source", "runtime", "package", "metadata"), "snapshot role")
        require(type(suffixes) is tuple and 1 <= len(suffixes) <= 32
                and all(type(s) is str and s.startswith(".") and 1 < len(s) <= 32
                        and s.isascii() and all(c.isalnum() or c in "._-" for c in s) for s in suffixes), "explicit suffix recipe required")
        require(type(excluded_dirs) is tuple and len(excluded_dirs) <= 256
                and all(type(n) is str and "/" not in n and "\\" not in n
                        and checked_path(root.rstrip("/") + "/" + n) for n in excluded_dirs), "excluded directory recipe")
        before, directories, files = self._enumerate(root, suffixes, excluded_dirs)
        descriptors = [self.retain(path) for path in sorted(files)]
        after, after_dirs, after_files = self._enumerate(root, suffixes, excluded_dirs)
        require((before, directories, files) == (after, after_dirs, after_files), "enumeration changed during observation")
        ancestors = set(_ancestors(root, include=True))
        snapshot = validate_snapshot({"schema": "cho51_lv_observed_snapshot_v1", "label": label, "role": role,
            "root": root, "complete_enumeration": True,
            "directories": [self._directories[p][1] for p in sorted(directories | ancestors)], "files": descriptors})
        canonical_bytes(snapshot)  # retain the stricter v1 aggregate JSON bound
        self._recipes.append((root, suffixes, excluded_dirs, before, directories, files))
        return snapshot

    def verify(self):
        self._check()
        for path, (handle, descriptor) in self._directories.items():
            require(self._facts(handle, path, True)[0] == descriptor["native_identity"], "ancestor identity changed")
        for path, (handle, descriptor, facts) in self._files.items():
            require(self._facts(handle, path, False) == facts, "retained file identity/facts changed")
            pin, _ = self._hash(handle, descriptor["bytes"])
            require(pin == {k: descriptor[k] for k in ("bytes", "sha256")}
                    and self._facts(handle, path, False) == facts, "retained file content changed")
        for root, suffixes, excluded_dirs, recipe, directories, files in self._recipes:
            require(self._enumerate(root, suffixes, excluded_dirs) == (recipe, directories, files), "added/missing recipe member")
        return [defensive_copy(self._files[path][1]) for path in sorted(self._files)]

    def close(self):
        if self._closed:
            require(not self.cleanup_errors, "earlier handle cleanup failed")
            return
        self._closed = True
        for record in reversed(list(self._files.values()) + list(self._directories.values())):
            try:
                self._close_handle(record[0])
            except OSError:
                pass
        self._files.clear()
        self._directories.clear()
        require(not self.cleanup_errors, "handle cleanup failed: " + "; ".join(self.cleanup_errors))

    def __enter__(self):
        self._check()
        return self

    def __exit__(self, *_):
        self.close()


class RetainedOutputs:
    """Create-new original output handles remain open through publication."""
    def __init__(self, reader, directory):
        require(type(reader) is RetainedReader, "retained reader required")
        self.reader, self.directory = reader, checked_path(directory)
        reader.retain_directory(self.directory)
        self._files, self._total, self._closed = {}, 0, False
        self.cleanup_errors = []

    def write(self, name, raw):
        self.reader._check()
        require(not self._closed, "outputs closed")
        require(type(name) is str and "/" not in name and "\\" not in name, "one output basename required")
        path = checked_path(self.directory.rstrip("/") + "/" + name)
        require(type(raw) is bytes and len(raw) <= MAX_OUTPUT_FILE_BYTES
                and len(self._files) < MAX_OUTPUT_FILES and self._total + len(raw) <= MAX_OUTPUT_BYTES, "output bounds")
        require(path not in self._files, "output already published")
        handle, initial = self.reader._open(path, create=True)
        try:
            offset = 0
            while offset < len(raw):
                self.reader._check()
                chunk = raw[offset:offset + CHUNK_BYTES]
                require(0 < len(chunk) <= 65_536, "output chunk bound")
                buffer, written = ctypes.create_string_buffer(chunk), ctypes.c_uint32()
                if not self.reader.api.WriteFile(handle, buffer, len(chunk), ctypes.byref(written), None):
                    raise self.reader._error("output write failed")
                self.reader._check()
                require(written.value == len(chunk), "partial output write")
                offset += written.value
            self.reader._check()
            if not self.reader.api.FlushFileBuffers(handle):
                raise self.reader._error("output flush failed")
            self.reader._check()
            facts = self.reader._facts(handle, path, False)
            require(facts[0] == initial[0] and facts[1] == len(raw), "output identity/length changed")
            observed, _ = self.reader._hash(handle, len(raw))
            require(observed == {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}, "output same-handle readback differs")
            descriptor = validate_file_descriptor({"schema": "cho51_lv_file_descriptor_v1", "path": path,
                "native_identity": facts[0], "file_type": "regular", "reparse_point": False,
                "link_count": 1, **observed})
            self._files[path] = (handle, descriptor, facts)
            self._total += len(raw)
            return defensive_copy(descriptor)
        except BaseException:
            self.reader._close_handle(handle)
            raise

    def verify(self):
        self.reader._check()
        require(not self._closed, "outputs closed")
        for path, (handle, descriptor, facts) in self._files.items():
            require(self.reader._facts(handle, path, False) == facts, "output facts changed")
            pin, _ = self.reader._hash(handle, descriptor["bytes"])
            require(pin == {k: descriptor[k] for k in ("bytes", "sha256")}
                    and self.reader._facts(handle, path, False) == facts, "output verify differs")
        return [defensive_copy(self._files[path][1]) for path in sorted(self._files)]

    def close(self):
        if self._closed:
            require(not self.cleanup_errors, "earlier output cleanup failed")
            return
        self._closed = True
        for handle, _, _ in reversed(list(self._files.values())):
            try:
                self.reader._close_handle(handle)
            except OSError as exc:
                self.cleanup_errors.append(str(exc))
        self._files.clear()
        require(not self.cleanup_errors, "output cleanup failed: " + "; ".join(self.cleanup_errors))





