"""Guard-owned cleanup of one registered, bounded private cache directory.

No recursive deletion and no data-directory fallback. Registration and directory
identity receipts survive cleanup. The guard calls this only after its owned Job
is empty and closed; unsupported paths/content fail before any deletion.
"""
import hashlib
import json
import os
import re
import stat
from pathlib import Path

PHASE = Path(__file__).resolve().parent
MAXIMUM_BYTES = 2 * 1024**3

def identity(path):
    value = path.lstat()
    return [value.st_dev, value.st_ino]

def plain_path(path, *, directory):
    if path.absolute() != path.resolve() or path.is_symlink():
        raise ValueError("private cleanup path aliases another path")
    value = path.lstat()
    if getattr(value, "st_file_attributes", 0) & 0x400:
        raise ValueError("private cleanup path is a Windows reparse point")
    expected = stat.S_ISDIR if directory else stat.S_ISREG
    if not expected(value.st_mode):
        raise ValueError("private cleanup path has an unsupported file kind")
    return value

def owned_output(output):
    output = Path(output).absolute()
    try:
        relative = output.relative_to(PHASE)
    except ValueError:
        raise ValueError("private cleanup output escapes the owned phase") from None
    if not 1 <= len(relative.parts) <= 2 or any(not re.fullmatch(r"[a-z_0-9]+", part) for part in relative.parts):
        raise ValueError("private cleanup output escapes the owned phase")
    if len(relative.parts) == 2:
        plain_path(output.parent, directory=True)
    plain_path(output, directory=True)
    return output

def write_new(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())

def register_owned_cache(output, directory, *, maximum_bytes, worker_sha256):
    output = owned_output(output)
    directory = Path(directory).absolute()
    if type(maximum_bytes) is not int or not 0 <= maximum_bytes <= MAXIMUM_BYTES:
        raise ValueError("private cleanup disk budget exceeds2GiB")
    if not re.fullmatch(r"[0-9a-f]{64}", worker_sha256):
        raise ValueError("private cleanup requires actual worker bytes")
    if directory.parent != output / "backing" or not re.fullmatch(r"source_cache_[a-zA-Z0-9_]+", directory.name):
        raise ValueError("private cleanup directory is not the registered cache tier")
    plain_path(directory.parent, directory=True)
    plain_path(directory, directory=True)
    registry = {"schema": "pro3_owned_private_cache_registration_v1", "output": str(output), "directory_name": directory.name, "directory_identity": identity(directory), "backing_identity": identity(directory.parent), "maximum_bytes": maximum_bytes, "worker_sha256": worker_sha256}
    write_new(output / "cache_registry.json", registry)
    return registry

def cleanup_registered_cache(output, *, owned_job_closed, expected_worker_sha256):
    if owned_job_closed is not True:
        raise ValueError("private cleanup requires physical owned Job release")
    output = owned_output(output)
    path = output / "cache_registry.json"
    if not path.exists():
        return {"schema": "pro3_owned_private_cache_cleanup_v1", "registered": False, "completed": True, "deleted_files": []}
    value = plain_path(path, directory=False)
    if value.st_size > 16384:
        raise ValueError("private cleanup registry is oversized")
    raw = path.read_bytes()
    registry = json.loads(raw)
    if registry.get("schema") != "pro3_owned_private_cache_registration_v1" or registry.get("output") != str(output) or registry.get("worker_sha256") != expected_worker_sha256:
        raise ValueError("private cleanup registry does not match this owned worker")
    name = registry.get("directory_name", "")
    maximum = registry.get("maximum_bytes")
    if not isinstance(name, str) or not re.fullmatch(r"source_cache_[a-zA-Z0-9_]+", name) or type(maximum) is not int or not 0 <= maximum <= MAXIMUM_BYTES:
        raise ValueError("private cleanup registry path or budget is invalid")
    backing = output / "backing"
    plain_path(backing, directory=True)
    if identity(backing) != registry["backing_identity"]:
        raise ValueError("private cleanup backing directory was replaced")
    directory = backing / name
    receipt = {"schema": "pro3_owned_private_cache_cleanup_v1", "registered": True, "registry_sha256": hashlib.sha256(raw).hexdigest(), "directory": directory.relative_to(output).as_posix(), "completed": False, "deleted_files": [], "maximum_bytes": maximum}
    if not directory.exists():
        if directory.is_symlink():
            raise ValueError("private cleanup missing directory is an alias")
        receipt.update(completed=True, already_removed_by_worker=True, total_deleted_bytes=0)
        return receipt
    plain_path(directory, directory=True)
    if identity(directory) != registry["directory_identity"]:
        raise ValueError("private cleanup registered directory was replaced")
    files = []
    total = 0
    # Check every child and the aggregate budget before deleting the first file.
    for child in sorted(directory.iterdir()):
        if not re.fullmatch(r"[0-9a-f]{32}\.bin", child.name):
            raise ValueError("private cleanup refuses unregistered cache content")
        value = plain_path(child, directory=False)
        files.append((child, value))
        total += value.st_size
    if total > maximum:
        raise ValueError("private cleanup aggregate files exceed the registered budget")
    for child, before in files:
        digest = hashlib.sha256()
        with child.open("rb") as stream:
            while block := stream.read(1024**2):
                digest.update(block)
        after = plain_path(child, directory=False)
        if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
            raise ValueError("private cleanup file changed before deletion")
        child.unlink()
        receipt["deleted_files"].append({"name": child.name, "bytes": before.st_size, "sha256": digest.hexdigest()})
    directory.rmdir()
    receipt.update(completed=True, already_removed_by_worker=False, total_deleted_bytes=total)
    return receipt
