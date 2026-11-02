"""Retain and check bounded local NTFS bytes; never authenticate their author.

Source-only until independently reviewed and locally admitted. Native calls are
lazy: importing this module opens nothing. Only exact DOS drive paths on a fixed
local NTFS volume are supported. A context retains the drive root, ancestors,
directories and files with read sharing only. All reads and repeat hashes use
the original file handles. No path reopening substitutes for a retained handle.

This is a local byte/namespace check, not host, source-review, or runtime
provenance admission. Sharing excludes ordinary incompatible Win32 opens. It
does not exclude preexisting writable mappings, kernel/filter/raw-volume writes,
privileged interference or hardware faults, and cannot promise an atomic
snapshot against those actors. verify() repeats bounded hashes and metadata.
See Microsoft CreateFileW, GetFinalPathNameByHandleW,
GetFileInformationByHandle, GetFileInformationByHandleEx (FileBasicInfo), and
GetVolumeInformationByHandleW documentation. No positive custody predicate is
implemented here.
"""

import ctypes
from ctypes import wintypes
import hashlib
import os
import re
import threading


MAX_ARTIFACT_BYTES = 16 * 1024 * 1024
MAX_TOTAL_ARTIFACT_BYTES = 64 * 1024 * 1024
MAX_ARTIFACTS = 64
MAX_HANDLES = 2048
READ_CHUNK = 64 * 1024
_RELATIVE = re.compile(r"[A-Za-z0-9_./-]{1,384}\Z")
_ROOT_COMPONENT = re.compile(r"[A-Za-z0-9_. -]{1,255}\Z")
_HASH = re.compile(r"[0-9a-f]{64}\Z")
_RESERVED = {"CON", "PRN", "AUX", "NUL", "CLOCK$"}
_RESERVED.update("COM" + str(i) for i in range(1, 10))
_RESERVED.update("LPT" + str(i) for i in range(1, 10))
FILE_ATTRIBUTE_DIRECTORY = 0x10
FILE_ATTRIBUTE_DEVICE = 0x40
FILE_ATTRIBUTE_REPARSE_POINT = 0x400
FILE_SHARE_READ = 1
FILE_READ_ATTRIBUTES = 0x80
GENERIC_READ = 0x80000000
FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000


class RetainedArtifactError(ValueError):
    """Unsupported input, unavailable guarantee, changed bytes, or native refusal."""


def _component(part):
    if (part in ("", ".", "..") or part.endswith((".", " "))
            or part.split(".", 1)[0].upper() in _RESERVED):
        raise RetainedArtifactError("path component alias refused")


def _reference(reference):
    if type(reference) is not dict or set(reference) != {"path", "bytes", "sha256"}:
        raise RetainedArtifactError("artifact reference must contain exact fields")
    path, size, digest = (reference[k] for k in ("path", "bytes", "sha256"))
    if type(path) is not str or _RELATIVE.fullmatch(path) is None:
        raise RetainedArtifactError("normalized relative artifact path required")
    for part in path.split("/"):
        _component(part)
    if type(size) is not int or not 0 <= size <= MAX_ARTIFACT_BYTES:
        raise RetainedArtifactError("artifact byte count exceeds bound or type")
    if type(digest) is not str or _HASH.fullmatch(digest) is None:
        raise RetainedArtifactError("lowercase SHA256 required")
    return {"path": path, "bytes": size, "sha256": digest}


def _root_path(value):
    if (type(value) is not str or not 3 <= len(value) <= 1024
            or re.match(r"[A-Z]:\\", value) is None or "/" in value):
        raise RetainedArtifactError("exact uppercase-drive absolute DOS root required")
    if value != value[:3]:
        for part in value[3:].split("\\"):
            if _ROOT_COMPONENT.fullmatch(part) is None:
                raise RetainedArtifactError("root path syntax or short-name alias refused")
            _component(part)
    return value


class _FileInformation(ctypes.Structure):
    _fields_ = [("attributes", wintypes.DWORD), ("creation", wintypes.FILETIME),
                ("access", wintypes.FILETIME), ("write", wintypes.FILETIME),
                ("volume", wintypes.DWORD), ("size_high", wintypes.DWORD),
                ("size_low", wintypes.DWORD), ("links", wintypes.DWORD),
                ("index_high", wintypes.DWORD), ("index_low", wintypes.DWORD)]


class _BasicInformation(ctypes.Structure):
    _fields_ = [("creation", ctypes.c_longlong), ("access", ctypes.c_longlong),
                ("write", ctypes.c_longlong), ("change", ctypes.c_longlong),
                ("attributes", wintypes.DWORD)]


class _Win32:
    """Small explicitly typed native surface, instantiated only on Windows."""

    def __init__(self):
        if os.name != "nt":
            raise RetainedArtifactError("only native Windows local NTFS is supported")
        self.dll = ctypes.WinDLL("kernel32.dll", use_last_error=True, winmode=0x800)
        signatures = {
            "CreateFileW": ([wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                             ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD,
                             wintypes.HANDLE], wintypes.HANDLE),
            "CloseHandle": ([wintypes.HANDLE], wintypes.BOOL),
            "GetFileType": ([wintypes.HANDLE], wintypes.DWORD),
            "GetFileInformationByHandle": ([wintypes.HANDLE, ctypes.POINTER(_FileInformation)], wintypes.BOOL),
            "GetFileInformationByHandleEx": ([wintypes.HANDLE, ctypes.c_int,
                                               ctypes.c_void_p, wintypes.DWORD], wintypes.BOOL),
            "GetFinalPathNameByHandleW": ([wintypes.HANDLE, wintypes.LPWSTR,
                                            wintypes.DWORD, wintypes.DWORD], wintypes.DWORD),
            "GetDriveTypeW": ([wintypes.LPCWSTR], wintypes.UINT),
            "GetVolumeInformationByHandleW": ([wintypes.HANDLE, wintypes.LPWSTR,
                                                wintypes.DWORD, ctypes.POINTER(wintypes.DWORD),
                                                ctypes.POINTER(wintypes.DWORD), ctypes.POINTER(wintypes.DWORD),
                                                wintypes.LPWSTR, wintypes.DWORD], wintypes.BOOL),
            "SetFilePointerEx": ([wintypes.HANDLE, ctypes.c_longlong,
                                    ctypes.POINTER(ctypes.c_longlong), wintypes.DWORD], wintypes.BOOL),
            "ReadFile": ([wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD,
                           ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p], wintypes.BOOL),
        }
        for name, (arguments, result) in signatures.items():
            function = getattr(self.dll, name)
            function.argtypes, function.restype = arguments, result

    @staticmethod
    def failure(operation):
        return RetainedArtifactError(operation + " refused (Win32 " + str(ctypes.get_last_error()) + ")")

    def open(self, path, directory):
        handle = self.dll.CreateFileW("\\\\?\\" + path,
                                      FILE_READ_ATTRIBUTES if directory else GENERIC_READ,
                                      FILE_SHARE_READ, None, 3,
                                      FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT, None)
        if handle is None or handle == ctypes.c_void_p(-1).value:
            raise self.failure("CreateFileW")
        return handle

    def close(self, handle):
        if not self.dll.CloseHandle(handle):
            raise self.failure("CloseHandle")

    def snapshot(self, handle, path, directory):
        if self.dll.GetFileType(handle) != 1:  # FILE_TYPE_DISK only
            raise RetainedArtifactError("non-disk handle refused")
        info, basic = _FileInformation(), _BasicInformation()
        if not self.dll.GetFileInformationByHandle(handle, ctypes.byref(info)):
            raise self.failure("GetFileInformationByHandle")
        if not self.dll.GetFileInformationByHandleEx(handle, 0, ctypes.byref(basic), ctypes.sizeof(basic)):
            raise self.failure("GetFileInformationByHandleEx")
        attributes = int(info.attributes)
        if (attributes & (FILE_ATTRIBUTE_REPARSE_POINT | FILE_ATTRIBUTE_DEVICE)
                or bool(attributes & FILE_ATTRIBUTE_DIRECTORY) != directory
                or attributes != basic.attributes):
            raise RetainedArtifactError("reparse, device, inconsistent or unexpected handle type")
        if not directory and info.links != 1:
            raise RetainedArtifactError("artifact hard-link count must equal one")
        buffer = ctypes.create_unicode_buffer(2048)
        length = self.dll.GetFinalPathNameByHandleW(handle, buffer, len(buffer), 0)
        if length == 0:
            raise self.failure("GetFinalPathNameByHandleW")
        if length >= len(buffer) or buffer.value != "\\\\?\\" + path:
            raise RetainedArtifactError("finalized path differs: alias or namespace substitution")
        result = {"final_path": path, "volume_serial": int(info.volume),
                  "file_index": (int(info.index_high) << 32) | int(info.index_low),
                  "attributes": attributes, "directory": directory}
        if not result["file_index"]:
            raise RetainedArtifactError("unavailable file identity refused")
        if not directory:
            result.update(bytes=(int(info.size_high) << 32) | int(info.size_low),
                          links=int(info.links), creation_100ns=int(basic.creation),
                          write_100ns=int(basic.write), change_100ns=int(basic.change))
        return result

    def volume(self, handle, drive):
        if self.dll.GetDriveTypeW(drive) != 3:  # DRIVE_FIXED only
            raise RetainedArtifactError("fixed local drive required")
        name = ctypes.create_unicode_buffer(261)
        serial = wintypes.DWORD()
        if not self.dll.GetVolumeInformationByHandleW(handle, None, 0, ctypes.byref(serial),
                                                       None, None, name, len(name)):
            raise self.failure("GetVolumeInformationByHandleW")
        if name.value != "NTFS":
            raise RetainedArtifactError("only NTFS is supported")
        return int(serial.value)

    def chunks(self, handle, size):
        if not self.dll.SetFilePointerEx(handle, 0, None, 0):
            raise self.failure("SetFilePointerEx")
        buffer = ctypes.create_string_buffer(READ_CHUNK)
        remaining = size
        while remaining:
            wanted = min(remaining, READ_CHUNK)
            got = wintypes.DWORD()
            if not self.dll.ReadFile(handle, buffer, wanted, ctypes.byref(got), None):
                raise self.failure("ReadFile")
            if not 0 < got.value <= wanted:
                raise RetainedArtifactError("short or invalid artifact read")
            remaining -= got.value
            yield buffer.raw[:got.value]
        got = wintypes.DWORD()
        if not self.dll.ReadFile(handle, buffer, 1, ctypes.byref(got), None):
            raise self.failure("ReadFile EOF")
        if got.value != 0:
            raise RetainedArtifactError("artifact exceeds declared size")


class RetainedArtifactSet:
    """One bounded retained-read set. Any refusal closes and poisons the set.

    read(ref) returns bytes; witnesses returns copies of successful file pins.
    verify() rechecks all retained paths/identities and all successful hashes.
    Repeated exact references reuse their retained file and recheck bytes.
    Always close or use a context manager; there is no garbage-collection proof.
    Root spelling must already match the filesystem exactly (including case).
    """

    def __init__(self, approved_root):
        self._lock = threading.RLock()
        self._handles, self._entries, self._artifacts = [], {}, {}
        self._total, self._closed = 0, False
        self._root = _root_path(approved_root)
        self._native = _Win32()
        self._volume = None
        try:
            drive = self.root[:3]
            entry = self._retain(drive, True)
            self._volume = self._native.volume(entry["handle"], drive)
            if entry["pin"]["volume_serial"] != self._volume:
                raise RetainedArtifactError("volume identity mismatch")
            current = drive
            if len(self.root) > 3:
                for part in self.root[3:].split("\\"):
                    current = current.rstrip("\\") + "\\" + part
                    self._retain(current, True)
        except BaseException:
            self.close()
            raise

    def _retain(self, path, directory):
        if path in self._entries:
            entry = self._entries[path]
            if entry["pin"]["directory"] != directory:
                raise RetainedArtifactError("retained type conflict")
            return entry
        if len(self._handles) >= MAX_HANDLES:
            raise RetainedArtifactError("retained handle cap exceeded")
        handle = self._native.open(path, directory)
        self._handles.append(handle)  # adopt before any subsequent fallible call
        pin = self._native.snapshot(handle, path, directory)
        if self._volume is not None and pin["volume_serial"] != self._volume:
            raise RetainedArtifactError("cross-volume artifact refused")
        entry = {"handle": handle, "pin": pin}
        self._entries[path] = entry
        return entry

    @property
    def root(self):
        """Approved root spelling; changing it requires a fresh retained set."""
        return self._root

    def _active(self):
        if self._closed:
            raise RetainedArtifactError("retained artifact set is closed")

    def _check(self, entry):
        pin = entry["pin"]
        if self._native.snapshot(entry["handle"], pin["final_path"], pin["directory"]) != pin:
            raise RetainedArtifactError("retained identity, type, size or time changed")

    def _read(self, entry, ref, keep):
        self._check(entry)
        if entry["pin"]["bytes"] != ref["bytes"]:
            raise RetainedArtifactError("declared byte count differs from retained size")
        digest, pieces = hashlib.sha256(), []
        for piece in self._native.chunks(entry["handle"], ref["bytes"]):
            digest.update(piece)
            if keep:
                pieces.append(piece)
        self._check(entry)
        if digest.hexdigest() != ref["sha256"]:
            raise RetainedArtifactError("retained artifact SHA256 mismatch")
        return b"".join(pieces) if keep else None

    def read(self, reference):
        with self._lock:
            self._active()
            try:
                ref = _reference(reference)
                previous = self._artifacts.get(ref["path"])
                if previous is not None:
                    if previous[0] != ref:
                        raise RetainedArtifactError("conflicting repeated artifact reference")
                    return self._read(previous[1], ref, True)
                if (len(self._artifacts) >= MAX_ARTIFACTS
                        or self._total + ref["bytes"] > MAX_TOTAL_ARTIFACT_BYTES):
                    raise RetainedArtifactError("artifact count or aggregate byte cap exceeded")
                current = self.root.rstrip("\\")
                parts = ref["path"].split("/")
                for part in parts[:-1]:
                    current += "\\" + part
                    self._retain(current, True)
                entry = self._retain(current + "\\" + parts[-1], False)
                data = self._read(entry, ref, True)
                self._artifacts[ref["path"]] = (ref, entry)
                self._total += ref["bytes"]
                # The whole chain is still the one that was retained before open.
                for retained in self._entries.values():
                    self._check(retained)
                return data
            except BaseException:
                self.close()
                raise

    @property
    def witnesses(self):
        with self._lock:
            self._active()
            return tuple(dict(entry["pin"], path=ref["path"], sha256=ref["sha256"],
                              filesystem="NTFS", share_mode=FILE_SHARE_READ,
                              claim="checked retained local bytes only")
                         for ref, entry in self._artifacts.values())

    def verify(self):
        with self._lock:
            self._active()
            try:
                for entry in self._entries.values():
                    self._check(entry)
                for ref, entry in self._artifacts.values():
                    self._read(entry, ref, False)
                for entry in self._entries.values():
                    self._check(entry)
            except BaseException:
                self.close()
                raise

    def close(self):
        with self._lock:
            self._closed = True
            failed = []
            for handle in reversed(self._handles):
                try:
                    self._native.close(handle)
                except BaseException as error:
                    failed.append((handle, error))
            self._handles = [handle for handle, _ in reversed(failed)]
            if failed:
                raise RetainedArtifactError("failed to close " + str(len(failed)) + " retained handle(s)") from failed[0][1]

    def __enter__(self):
        self._active()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False
