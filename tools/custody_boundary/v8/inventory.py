"""Retained, bounded present-byte witnesses; not historical custody evidence.

This module is static work in progress and has not been independently reviewed.
"""
import ctypes
import hashlib
import msvcrt
import os
import stat
import re
from pathlib import Path

MAX_FILES = 1024
MAX_TOTAL = 64 * 1024 * 1024
MAX_FILE = 16 * 1024 * 1024


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def checked_path(path):
    path = Path(path)
    if not path.is_absolute() or str(path).startswith('\\\\') or path != path.resolve():
        raise ValueError('canonical local path required')
    if len(path.parts) > 32 or len(str(path)) > 1024:
        raise ValueError('path depth/length bound')
    for part in path.parts[1:]:
        if (not re.fullmatch(r'[A-Za-z0-9_. -]{1,255}', part) or part in {'.', '..'}
                or part.endswith(('.', ' ')) or part.split('.')[0].upper() in
                {'CON', 'PRN', 'AUX', 'NUL', *('COM'+str(i) for i in range(1,10)), *('LPT'+str(i) for i in range(1,10))}):
            raise ValueError('path component alias refused')
    for node in [*reversed(path.parents), path]:
        item = node.lstat()
        if item.st_file_attributes & 1024 or stat.S_ISLNK(item.st_mode):
            raise ValueError('reparse path refused')
    return path


class RetainedInventory:
    def __init__(self):
        self.api = ctypes.WinDLL('kernel32.dll', use_last_error=True, winmode=0x800)
        self.api.CreateFileW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32,
                                        ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p]
        self.api.CreateFileW.restype = ctypes.c_void_p
        self.api.CloseHandle.argtypes = [ctypes.c_void_p]
        self.api.CloseHandle.restype = ctypes.c_int
        self.api.GetFinalPathNameByHandleW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32]
        self.api.GetFinalPathNameByHandleW.restype = ctypes.c_uint32
        self.api.GetVolumeInformationW.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint32,
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_uint32]
        self.api.GetVolumeInformationW.restype = ctypes.c_int
        self.api.GetVolumeInformationByHandleW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_uint32,
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_uint32]
        self.api.GetVolumeInformationByHandleW.restype = ctypes.c_int
        self.api.GetDriveTypeW.argtypes = [ctypes.c_wchar_p]
        self.api.GetDriveTypeW.restype = ctypes.c_uint32
        self.api.GetFileType.argtypes = [ctypes.c_void_p]
        self.api.GetFileType.restype = ctypes.c_uint32
        self.directories = {}
        self.files = []
        self.total = 0
        self.identities = set()
        self.checkpoint = lambda: None

    def retain_directory(self, path):
        if path not in self.directories:
            if len(self.directories) >= 1024:
                raise ValueError('directory handle bound')
            handle = self._open(path, True)
            self.directories[path] = (handle, None)
            self.directories[path] = (handle, native_identity(self.api, handle))

    def read_stream(self, stream, cap):
        chunks, size = [], 0
        while size <= cap:
            self.checkpoint()
            chunk = stream.read(min(1048576, cap + 1 - size))
            if not chunk:
                break
            chunks.append(chunk)
            size += len(chunk)
        if size > cap:
            raise ValueError('read exceeds bound')
        return b''.join(chunks)

    def _open(self, path, directory=False):
        self.checkpoint()
        path = checked_path(path)
        filesystem = ctypes.create_unicode_buffer(64)
        if self.api.GetDriveTypeW(path.anchor) != 3:
            raise ValueError('fixed local drive required')
        handle = self.api.CreateFileW(str(path), 0x80000000, 1, None, 3,
                                      0x00200000 | (0x02000000 if directory else 0), None)
        if handle in (None, ctypes.c_void_p(-1).value):
            raise OSError(ctypes.get_last_error(), 'retained open failed')
        try:
            if not self.api.GetVolumeInformationByHandleW(handle, None, 0, None, None, None, filesystem, len(filesystem)) or filesystem.value != 'NTFS':
                raise ValueError('retained local NTFS required')
            identity = native_identity(self.api, handle)
            if bool(identity[4] & 16) != directory:
                raise ValueError('handle type differs')
            checked_path(path)
            final = ctypes.create_unicode_buffer(32768)
            count = self.api.GetFinalPathNameByHandleW(handle, final, len(final), 0)
            if not 0 < count < len(final) or final.value != '\\\\?\\' + str(path):
                raise ValueError('path alias refused')
            return handle
        except BaseException:
            if not self.api.CloseHandle(handle):
                raise OSError(ctypes.get_last_error(), 'failed-open handle close')
            raise

    @staticmethod
    def identity(s):
        return (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_nlink)

    def read(self, path, expected=None):
        path = checked_path(path)
        if len(self.files) >= MAX_FILES:
            raise ValueError('file count limit')
        for directory in reversed(path.parents):
            self.retain_directory(directory)
        handle = self._open(path)
        try:
            fd = msvcrt.open_osfhandle(handle, os.O_RDONLY | os.O_BINARY)
        except BaseException:
            self.api.CloseHandle(handle)
            raise
        try:
            stream = os.fdopen(fd, 'rb')
        except BaseException:
            os.close(fd)
            raise
        try:
            before = os.fstat(stream.fileno())
            identity = self.identity(before)
            native = native_identity(self.api, msvcrt.get_osfhandle(stream.fileno()))
            if (not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or
                    before.st_size > MAX_FILE or self.total + before.st_size > MAX_TOTAL or
                    (native[0], native[1]) in self.identities or native[2] != 1 or native[3] != before.st_size):
                raise ValueError('file type, link, alias or size limit')
            raw = self.read_stream(stream, MAX_FILE)
            if self.identity(os.fstat(stream.fileno())) != identity or len(raw) != before.st_size:
                raise ValueError('file changed during read')
            pin = {'bytes': len(raw), 'sha256': digest(raw)}
            if expected is not None and (type(expected) is not dict or set(expected) != {'bytes', 'sha256'} or type(expected['bytes']) is not int or type(expected['sha256']) is not str or expected != pin):
                raise ValueError('pin mismatch')
            witness = {'path': str(path), **pin, 'device': native[0],
                       'file_id': native[1], 'links': native[2]}
            self.total += len(raw)
            self.identities.add((native[0], native[1]))
            self.files.append((stream, identity, witness, native))
            return raw
        except BaseException:
            stream.close()
            raise

    def verify(self):
        for directory, (handle, native) in self.directories.items():
            self.checkpoint()
            if native is None or native_identity(self.api, handle)[:3] != native[:3] or checked_path(directory) != directory:
                raise ValueError('ancestor identity changed')
        for stream, identity, witness, native in self.files:
            stream.seek(0)
            raw = self.read_stream(stream, MAX_FILE)
            if native_identity(self.api, msvcrt.get_osfhandle(stream.fileno())) != native or self.identity(os.fstat(stream.fileno())) != identity or len(raw) != witness['bytes'] or digest(raw) != witness['sha256']:
                raise ValueError('retained witness changed')
        return [witness.copy() for _, _, witness, _ in self.files]

    def close(self):
        errors = []
        for stream, _, _, _ in reversed(self.files):
            try:
                stream.close()
            except OSError as exc:
                errors.append(str(exc))
        self.files.clear()
        for handle, _ in reversed(list(self.directories.values())):
            if not self.api.CloseHandle(handle):
                errors.append('directory close failed')
        self.directories.clear()
        if errors:
            raise RuntimeError('; '.join(errors))

class _FileInfo(ctypes.Structure):
    _fields_ = [('attributes', ctypes.c_uint32), ('created_low', ctypes.c_uint32),
                ('created_high', ctypes.c_uint32), ('access_low', ctypes.c_uint32),
                ('access_high', ctypes.c_uint32), ('write_low', ctypes.c_uint32),
                ('write_high', ctypes.c_uint32), ('volume', ctypes.c_uint32),
                ('size_high', ctypes.c_uint32), ('size_low', ctypes.c_uint32),
                ('links', ctypes.c_uint32), ('index_high', ctypes.c_uint32),
                ('index_low', ctypes.c_uint32)]


def native_identity(api, handle):
    info = _FileInfo()
    api.GetFileInformationByHandle.argtypes = [ctypes.c_void_p, ctypes.POINTER(_FileInfo)]
    api.GetFileInformationByHandle.restype = ctypes.c_int
    if not api.GetFileInformationByHandle(handle, ctypes.byref(info)):
        raise OSError(ctypes.get_last_error(), 'native identity failed')
    identifier = (info.index_high << 32) | info.index_low
    if not info.volume or not identifier or api.GetFileType(handle) != 1 or info.attributes & 0x440:
        raise ValueError('ambiguous native identity')
    return (info.volume, identifier, info.links, (info.size_high << 32) | info.size_low, info.attributes)


class Outputs:
    """Create-once files held against writes/deletes until caller closes."""
    def __init__(self, inventory, directory):
        self.inventory = inventory
        self.directory = checked_path(directory)
        for ancestor in [*reversed(self.directory.parents), self.directory]:
            inventory.retain_directory(ancestor)
        self.files = []

    def write(self, name, raw):
        self.inventory.checkpoint()
        if name not in {'claim.json', 'dispatch.json', 'deadline.json', 'payload.json', 'receipt.json'}:
            raise ValueError('output name refused')
        if not isinstance(raw, bytes) or len(raw) > 1048576:
            raise ValueError('output bound')
        path = self.directory / name
        api = self.inventory.api
        handle = api.CreateFileW(str(path), 0xC0000000, 1, None, 1, 0x00200000, None)
        if handle in (None, ctypes.c_void_p(-1).value):
            raise OSError(ctypes.get_last_error(), 'create-new output failed')
        try:
            fd = msvcrt.open_osfhandle(handle, os.O_RDWR | os.O_BINARY)
        except BaseException:
            api.CloseHandle(handle)
            raise
        try:
            stream = os.fdopen(fd, 'w+b', buffering=0)
        except BaseException:
            os.close(fd)
            raise
        try:
            native = native_identity(api, handle)
            if native[2] != 1:
                raise ValueError('output links refused')
            checked_path(path)
            final = ctypes.create_unicode_buffer(32768)
            n = api.GetFinalPathNameByHandleW(handle, final, len(final), 0)
            if not 0 < n < len(final) or final.value != '\\\\?\\' + str(path):
                raise ValueError('output containment refused')
            if stream.write(raw) != len(raw):
                raise ValueError('partial output')
            stream.flush()
            os.fsync(stream.fileno())
            stream.seek(0)
            reread = stream.read(len(raw) + 1)
            after = native_identity(api, handle)
            if reread != raw or after[:3] != native[:3] or after[3] != len(raw):
                raise ValueError('output readback/identity failed')
            self.files.append((stream, after, digest(raw)))
        except BaseException:
            stream.close()
            raise

    def verify(self):
        for stream, identity, expected in self.files:
            self.inventory.checkpoint()
            stream.seek(0)
            raw = stream.read(1048577)
            if native_identity(self.inventory.api, msvcrt.get_osfhandle(stream.fileno())) != identity or digest(raw) != expected:
                raise ValueError('output changed')

    def close(self):
        failures = []
        for stream, _, _ in reversed(self.files):
            try:
                stream.close()
            except OSError as exc:
                failures.append(str(exc))
        self.files.clear()
        if failures:
            raise RuntimeError('; '.join(failures))



