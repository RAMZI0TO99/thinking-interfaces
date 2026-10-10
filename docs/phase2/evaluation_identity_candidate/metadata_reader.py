"""Read a bounded subset of NPY identity metadata, without NumPy or pickle."""
import ast
import hashlib
import os
from pathlib import Path
import re
import stat
import zipfile

MAX_MEMBER = 1024 * 1024
MAX_ARCHIVE = 512 * 1024 * 1024
MAX_HEADER = 4096
MAX_ITEMS = 10000
IDENTITY_MEMBERS = ("sessions.npy", "runs.npy", "trial_indices.npy")
ARCHIVE_MEMBERS = set(IDENTITY_MEMBERS) | {"signals.npy", "labels.npy", "channel_names.npy"}


def stable_stat(point):
    return point.st_size, point.st_mtime_ns, point.st_ino, point.st_dev


def local_file(root, path):
    """Reject escape, symlink and Windows reparse components before reading."""
    root = Path(root).absolute()
    path = Path(path).absolute()
    if not path.is_relative_to(root) or ".." in path.parts:
        raise ValueError("input outside owned workspace")
    components = [root]
    for part in path.relative_to(root).parts:
        components.append(components[-1] / part)
    for component in components:
        point = component.lstat()
        if stat.S_ISLNK(point.st_mode) or getattr(point, "st_file_attributes", 0) & 0x400:
            raise ValueError("reparse/symlink input component")
    if not stat.S_ISREG(path.lstat().st_mode):
        raise ValueError("regular input file required")
    return path


def read_small(root, path):
    path = local_file(root, path)
    before = path.stat()
    if before.st_size > MAX_MEMBER:
        raise ValueError("small metadata file exceeds bound")
    with path.open("rb") as stream:
        data = stream.read(MAX_MEMBER + 1)
        after_handle = os.fstat(stream.fileno())
    if len(data) != before.st_size or stable_stat(before) != stable_stat(after_handle) or stable_stat(before) != stable_stat(path.stat()):
        raise ValueError("metadata input changed while reading")
    return data


def decode_npy(data, kind):
    if kind not in ("unicode", "integer") or len(data) > MAX_MEMBER:
        raise ValueError("unsupported metadata kind or member size")
    if len(data) < 10 or data[:6] != b"\x93NUMPY":
        raise ValueError("invalid NPY magic or prefix")
    version = tuple(data[6:8])
    if version == (1, 0):
        length_bytes, encoding = 2, "latin1"
    elif version in ((2, 0), (3, 0)):
        length_bytes, encoding = 4, "utf-8" if version == (3, 0) else "latin1"
    else:
        raise ValueError("unsupported NPY version")
    header_start = 8 + length_bytes
    header_size = int.from_bytes(data[8:header_start], "little")
    payload_start = header_start + header_size
    if not 1 <= header_size <= MAX_HEADER or payload_start > len(data) or payload_start % 16:
        raise ValueError("invalid bounded/aligned NPY header")
    header_text = data[header_start:payload_start].decode(encoding, errors="strict")
    if not header_text.endswith("\n"):
        raise ValueError("NPY header needs final newline")
    tree = ast.parse(header_text.strip(), mode="eval")
    if not isinstance(tree.body, ast.Dict) or len(list(ast.walk(tree))) > 32:
        raise ValueError("small literal NPY dictionary required")
    keys = [ast.literal_eval(key) for key in tree.body.keys]
    if len(keys) != 3 or len(set(keys)) != 3 or set(keys) != {"descr", "fortran_order", "shape"}:
        raise ValueError("exact unique NPY header keys required")
    header = ast.literal_eval(tree)
    shape = header["shape"]
    if type(header["fortran_order"]) is not bool or type(shape) is not tuple or len(shape) != 1 or type(shape[0]) is not int or not 0 <= shape[0] <= MAX_ITEMS:
        raise ValueError("bounded one-dimensional metadata required")
    descriptor = header["descr"]
    pattern = r"([<>])U([1-9][0-9]{0,2})" if kind == "unicode" else r"([<>|])i([1248])"
    match = re.fullmatch(pattern, descriptor) if type(descriptor) is str else None
    if match is None:
        raise ValueError("object/structured/other dtype is not metadata")
    byte_order, width_text = match.groups()
    width = int(width_text)
    if (kind == "unicode" and width > 128) or (kind == "integer" and byte_order == "|" and width != 1):
        raise ValueError("unsupported metadata element width or endian marker")
    item_size = width * 4 if kind == "unicode" else width
    payload = data[payload_start:]
    if len(payload) != shape[0] * item_size:
        raise ValueError("NPY payload length disagrees with shape/dtype")
    values = []
    for offset in range(0, len(payload), item_size):
        chunk = payload[offset:offset + item_size]
        if kind == "unicode":
            value = chunk.decode("utf-32-le" if byte_order == "<" else "utf-32-be", errors="strict").rstrip("\x00")
            if not value or "\x00" in value or any(ord(char) < 32 or ord(char) == 127 for char in value):
                raise ValueError("empty or control-bearing identity")
        else:
            value = int.from_bytes(chunk, "big" if byte_order == ">" else "little", signed=True)
        values.append(value)
    return values, {"npy_version": list(version), "descriptor": descriptor, "items": shape[0], "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def recording_groups(sessions, runs, trial_indices):
    if not sessions or len(sessions) != len(runs) or len(sessions) != len(trial_indices):
        raise ValueError("metadata array lengths differ or are empty")
    seen, groups = set(), {}
    for session, run, trial in zip(sessions, runs, trial_indices):
        if type(trial) is not int or trial < 0:
            raise ValueError("nonnegative project trial index required")
        key = (session, run, trial)
        if key in seen:
            raise ValueError("duplicate project epoch identity")
        seen.add(key)
        groups.setdefault((session, run), []).append(trial)
    return [{"session": session, "run": run, "trial_indices": sorted(indices), "epoch_count": len(indices)}
            for (session, run), indices in sorted(groups.items())]


def inspect_archive(root, path):
    path = local_file(root, path)
    before = path.stat()
    if not 0 < before.st_size <= MAX_ARCHIVE:
        raise ValueError("bounded compressed archive required")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        if stable_stat(os.fstat(stream.fileno())) != stable_stat(before):
            raise ValueError("archive replaced before read")
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
        stream.seek(0)
        with zipfile.ZipFile(stream) as archive:
            entries = archive.infolist()
            names = [item.filename for item in entries]
            if len(names) != len(set(names)) or set(names) != ARCHIVE_MEMBERS:
                raise ValueError("exact six unique flat archive members required")
            decoded, pins, opened = {}, {}, []
            for name in IDENTITY_MEMBERS:
                entry = archive.getinfo(name)
                if entry.file_size > MAX_MEMBER or entry.flag_bits & 1 or entry.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
                    raise ValueError("unsupported/oversized metadata ZIP entry")
                with archive.open(entry, "r") as member:
                    data = member.read(MAX_MEMBER + 1)
                if len(data) != entry.file_size:
                    raise ValueError("metadata ZIP size disagreement")
                decoded[name], pins[name] = decode_npy(data, "integer" if name == "trial_indices.npy" else "unicode")
                opened.append(name)
        after_handle = os.fstat(stream.fileno())
    if stable_stat(before) != stable_stat(after_handle) or stable_stat(before) != stable_stat(path.stat()):
        raise ValueError("archive changed while reading")
    groups = recording_groups(decoded["sessions.npy"], decoded["runs.npy"], decoded["trial_indices.npy"])
    return {"artifact": {"path": path.relative_to(Path(root).absolute()).as_posix(), "bytes": before.st_size, "sha256": digest.hexdigest(), "mtime_ns": before.st_mtime_ns},
            "opened_members": opened, "metadata_member_pins": pins, "project_recording_groups": groups,
            "epoch_count": len(decoded["sessions.npy"]), "signal_or_label_arrays_decoded": False}
