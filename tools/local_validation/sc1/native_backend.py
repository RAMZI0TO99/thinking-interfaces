"""Windows original-handle backend for SC1; source only, not qualified.

Depends on LQ19 RetainedReader private contracts: checked_path, _check, _open,
_facts, _hash, _close_handle, retained directory maps, retain/read_small/verify
and close. _open checks disk/NTFS/type/link/final spelling/identity before it
returns. No P launcher, compiler, alternate writer or temporary file is used.
"""

import ctypes
import hashlib
import os

from ..lq19.native_reader import RetainedReader, checked_path, CHUNK_BYTES
from .publisher import PHASE, require


class NativeBackend:
    def __init__(self, checkpoint):
        require(callable(checkpoint), "live metadata checkpoint required")
        self.checkpoint = checkpoint
        self.reader = None
        self.closed = False
        self.cleanup_errors = []
        self._prepared = False

    def _check(self):
        require(not self.closed and self.checkpoint() is True, "native metadata guard refused")

    def prepare(self, sources, phase):
        self._check()
        require(not self._prepared and self.reader is None and phase == PHASE, "one exact native preparation")
        try:
            self.reader = RetainedReader(self.checkpoint, max_files=528,
                                         max_total_bytes=64 * 1024**2, max_file_bytes=16 * 1024**2)
            self.reader.retain_directory(checked_path(phase))
            for path, pin in sources.items():
                self._check()
                self.reader.retain(checked_path(path), pin)
            self.reader.verify()
            self._prepared = True
        except BaseException:
            # The controller calls close and reports any cleanup error together
            # with the original failure. Do not hide partial-constructor custody.
            raise

    def _path(self, path):
        require(checked_path(path) == path and path.rpartition("/")[0] == PHASE,
                "exact fixed metadata phase")
        return path

    def require_absent(self, path):
        self._check(); self._path(path)
        require(self._prepared and self.reader is not None, "native ancestry prepared")
        self.reader.retain_directory(PHASE)
        self._verify_ancestry(self.reader)
        try:
            os.lstat(path)
        except FileNotFoundError:
            self._check()
            return
        raise ValueError("metadata output already occupied")

    @staticmethod
    def _verify_ancestry(reader):
        for path, (handle, descriptor) in reader._directories.items():
            require(reader._facts(handle, path, True)[0] == descriptor["native_identity"],
                    "retained metadata ancestry changed")

    def verify_inputs(self):
        self._check()
        require(self._prepared and self.reader is not None, "native input set unavailable")
        self.reader.verify()

    def write_new(self, path, raw):
        self._check(); self._path(path)
        require(self._prepared and type(raw) is bytes and len(raw) <= 1048576,
                "bounded complete metadata bytes")
        owner, handle, initial = None, None, None
        primary, cleanup = None, []
        result = None
        file_closed = ancestry_closed = False
        try:
            # Independent publication ancestry is held through original close;
            # input ancestry stays independently retained by self.reader.
            owner = RetainedReader(self.checkpoint, max_files=1, max_total_bytes=1048576,
                                   max_file_bytes=1048576)
            owner.retain_directory(PHASE)
            require(len(owner._directories) <= 32, "publication ancestry count")
            self.require_absent(path)
            handle, initial = owner._open(path, create=True)
            require(initial[1] == 0, "CreateNew returned nonempty file")
            # _open has already checked ordinary disk file, one link, exact
            # final native path/identity, NTFS and retained ancestry before write.
            self._verify_ancestry(owner)
            offset = 0
            while offset < len(raw):
                owner._check()
                chunk = raw[offset:offset + CHUNK_BYTES]
                buffer, written = ctypes.create_string_buffer(chunk), ctypes.c_uint32()
                if not owner.api.WriteFile(handle, buffer, len(chunk), ctypes.byref(written), None):
                    raise owner._error("metadata write failed")
                owner._check()
                require(written.value == len(chunk), "metadata short write")
                offset += written.value
            owner._check()
            if not owner.api.FlushFileBuffers(handle):
                raise owner._error("metadata flush failed")
            owner._check()
            facts = owner._facts(handle, path, False)
            require(facts[0] == initial[0] and facts[1] == len(raw), "metadata original identity/length drift")
            pin, _ = owner._hash(handle, len(raw))
            require(pin == {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
                    and owner._facts(handle, path, False) == facts, "metadata original content/facts drift")
            self._verify_ancestry(owner)
            self.verify_inputs()
            result = {"path": path, **pin, "native_identity": facts[0]}
        except BaseException as error:
            primary = error
        finally:
            if owner is not None and handle is not None:
                try:
                    owner._close_handle(handle)
                    file_closed = True
                except BaseException as error:
                    cleanup.append(type(error).__name__ + ": " + str(error)[:256])
                # Close was attempted once. Unknown failure is retained, not
                # retried through a possibly reused numeric handle.
                handle = None
            if owner is not None:
                try:
                    owner.close()
                    ancestry_closed = True
                except BaseException as error:
                    cleanup.append(type(error).__name__ + ": " + str(error)[:256])
            if cleanup:
                self.cleanup_errors.extend(cleanup)
        if primary is not None or cleanup:
            raise RuntimeError("metadata publication refused: " +
                               (type(primary).__name__ + ": " + str(primary)[:512] if primary else "close failure") +
                               ("; custody unknown: " + "; ".join(cleanup) if cleanup else "")) from primary
        require(result is not None and file_closed and ancestry_closed, "original publication closure unknown")
        result.update(original_file_closed=True, original_ancestry_closed=True)
        return result

    def verify_publication(self, reference):
        self._check()
        path = self._path(reference["path"])
        pin = {key: reference[key] for key in ("bytes", "sha256")}
        descriptor = self.reader.retain(path, pin)
        require(descriptor["native_identity"] == reference["native_identity"], "published native identity changed")
        raw = self.reader.read_small(path, pin, max_bytes=1048576)
        require(len(raw) == pin["bytes"] and hashlib.sha256(raw).hexdigest() == pin["sha256"],
                "published original bytes changed")
        self._verify_ancestry(self.reader)

    def close(self):
        if self.closed:
            require(not self.cleanup_errors, "earlier metadata cleanup failure")
            return
        self.closed = True
        if self.reader is not None:
            try:
                self.reader.close()
            except BaseException as error:
                self.cleanup_errors.append(type(error).__name__ + ": " + str(error)[:512])
        require(not self.cleanup_errors, "metadata input/publication custody unknown: " + "; ".join(self.cleanup_errors))
