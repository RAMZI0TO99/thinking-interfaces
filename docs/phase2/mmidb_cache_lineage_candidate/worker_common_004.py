"""Finite, read-only data reconstruction helpers; stdlib-only at import."""
import hashlib
import importlib.metadata
import json
import os
import stat
import sys
import traceback
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path("D:/Aenv/pro3")
PKG = Path(__file__).resolve().parent
FIELDS = ("signals", "labels", "sessions", "runs", "trial_indices", "channel_names")


def sha(path, *, allow_empty=False):
    path = Path(path)
    initial = path.stat()
    if not stat.S_ISREG(initial.st_mode) or not (0 if allow_empty else 1) <= initial.st_size <= 512 * 1024**2:
        raise ValueError("bounded regular file required: " + str(path))
    digest = hashlib.sha256()
    count = 0
    with path.open("rb") as stream:
        opened = os.fstat(stream.fileno())
        if not os.path.samestat(initial, opened):
            raise ValueError("file identity changed before hashing")
        for block in iter(lambda: stream.read(1024**2), b""):
            count += len(block)
            if count > initial.st_size:
                raise ValueError("file grew during hashing")
            digest.update(block)
        final_handle = os.fstat(stream.fileno())
    final = path.stat()
    if any(not os.path.samestat(initial, item) or item.st_size != initial.st_size
           or item.st_mtime_ns != initial.st_mtime_ns for item in (final_handle, final)) or count != initial.st_size:
        raise ValueError("file changed during hashing")
    return digest.hexdigest()


def write_new(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def verify_plan(plan):
    for name, expected in plan["operation_pins"].items():
        if sha(PKG / name) != expected:
            raise ValueError("operation pin changed: " + name)
    for name, expected in plan["input_pins"].items():
        if sha(ROOT / name) != expected:
            raise ValueError("input pin changed: " + name)
    for item in plan["runtime_file_pins"].values():
        if sha(item["path"], allow_empty=True) != item["sha256"]:
            raise ValueError("runtime pin changed: " + item["path"])
    if sha(ROOT / "runs/quality_status.json") != plan["quality_pointer_sha256"]:
        raise ValueError("quality pointer changed")


def install_boundary(out):
    """Reject Python-visible network, child processes and unowned writes."""
    counts = {"network": 0, "subprocess": 0, "outside_write": 0, "expected_existing_directory_probes": 0}
    out = out.resolve(strict=True)

    def allow_write(value, *, directory_probe=False):
        if isinstance(value, int):
            return
        path = Path(os.fsdecode(value)).resolve()
        if not path.is_relative_to(out):
            counts["outside_write"] += 1
            known = {ROOT / ".cache/mne-home/.mne", ROOT / ".cache/matplotlib"}
            if directory_probe and path in known and path.is_dir() and not path.stat().st_file_attributes & 1024:
                counts["expected_existing_directory_probes"] += 1
            raise PermissionError("write outside fresh owned attempt rejected")

    def audit(event, args):
        if event in {"socket.connect", "socket.getaddrinfo", "socket.gethostbyname", "socket.gethostbyaddr"}:
            counts["network"] += 1
            raise PermissionError("network denied for read-only reconstruction")
        if event in {"subprocess.Popen", "os.system", "os.spawn", "os.posix_spawn"}:
            counts["subprocess"] += 1
            raise PermissionError("child process denied for read-only reconstruction")
        if event == "open":
            mode, flags = args[1], args[2]
            if (isinstance(mode, str) and any(char in mode for char in "wax+")) or flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
                allow_write(args[0])
        elif event in {"os.mkdir", "os.remove", "os.rmdir", "os.chmod", "os.utime", "os.truncate"}:
            allow_write(args[0], directory_probe=event == "os.mkdir")
        elif event in {"os.rename", "os.link", "os.symlink"}:
            allow_write(args[0])
            allow_write(args[1])

    sys.addaudithook(audit)
    return counts


def start(out, plan_path, stage):
    if not sys.flags.isolated or not sys.dont_write_bytecode or out.parent != PKG or not out.is_dir():
        raise ValueError("isolated fresh owned scientific worker required")
    if plan_path != PKG / ("launch_plan_" + stage + ".json"):
        raise ValueError("wrong stage plan")
    log = (out / "worker.log").open("x", encoding="utf-8", buffering=1)
    sys.stdout = sys.stderr = log
    def record_exception(kind, value, trace):
        traceback.print_exception(kind, value, trace, file=log)
        log.flush()
        write_new(out / "worker_failure.json", {"stage": stage, "error_type": kind.__name__, "error": str(value)[:4000],
            "traceback": "".join(traceback.format_exception(kind, value, trace))[-40000:]})
    sys.excepthook = record_exception
    print("DIAGNOSTIC_WORKER_START", stage)
    plan = json.loads(plan_path.read_bytes())
    if plan["stage"] != stage or plan["attempt"] != out.name:
        raise ValueError("plan/attempt mismatch")
    verify_plan(plan)
    policy = json.loads((PKG / ("resource_policy_" + stage + ".json")).read_bytes())
    if any(os.environ.get(key) != value for key, value in policy["thread_environment"].items()):
        raise ValueError("one-thread CPU environment differs")
    private = out / "runtime"
    private.mkdir()
    for name in ("tmp", "mne-home", "matplotlib", "mne-data"):
        (private / name).mkdir()
    (private / "mne-home/.mne").mkdir()
    for key, suffix in {"TEMP": "tmp", "TMP": "tmp", "TMPDIR": "tmp", "_MNE_FAKE_HOME_DIR": "mne-home", "MPLCONFIGDIR": "matplotlib", "MNE_DATA": "mne-data"}.items():
        os.environ[key] = str(private / suffix)
    os.environ["MOABB_DOWNLOAD_PROVIDER"] = "upstream"
    sys.path.insert(0, str(ROOT))
    boundary = install_boundary(out)
    return plan, boundary


def load_runtime():
    print("IMPORT", 'import mne')
    import mne
    print("IMPORT", 'import numpy as np')
    import numpy as np
    print("IMPORT", 'from mne.io.edf.edf import read_raw_edf')
    from mne.io.edf.edf import read_raw_edf
    print("IMPORT", 'from threadpoolctl import threadpool_info')
    from threadpoolctl import threadpool_info
    print("IMPORT", 'from data.mmidb import drop_incomplete_motor_annotations')
    from data.mmidb import drop_incomplete_motor_annotations
    print("IMPORT", 'from data.profile_a import ProfileAConfig')
    from data.profile_a import ProfileAConfig
    print("IMPORT", 'from data.unified import preprocess_raw_runs_profile_a')
    from data.unified import preprocess_raw_runs_profile_a
    # Some installed dataset dependencies import torch; record that fact and
    # restrict its CPU threads without constructing a model or CUDA context.
    torch = sys.modules.get("torch")
    if torch is not None:
        torch.set_num_threads(1)
        if torch.cuda.is_initialized():
            raise ValueError("unexpected CUDA context")
    return np, mne, read_raw_edf, threadpool_info, drop_incomplete_motor_annotations, ProfileAConfig, preprocess_raw_runs_profile_a


def configuration(Config):
    import tomllib
    value = tomllib.loads((ROOT / "configs/base.toml").read_text(encoding="utf-8"))["preprocessing"]["profile_a"]
    return Config(value["bandpass_low_hz"], value["bandpass_high_hz"], value["resample_hz"], value["pre_cue_s"], value["epoch_duration_s"], value["reference"])


def artifact_arrays(artifact, np):
    return {**{name: getattr(artifact, name) for name in FIELDS[:-1]}, "channel_names": np.asarray(artifact.channel_names)}


def compare_arrays(cached, rebuilt, np):
    """Report mismatches without changing arrays or relaxing tolerances."""
    if set(cached) != set(FIELDS) or set(rebuilt) != set(FIELDS):
        raise ValueError("exact six-member artifact required")
    identities = {}
    for name in FIELDS[1:]:
        left, right = cached[name], rebuilt[name]
        identities[name] = {"shape_equal": left.shape == right.shape, "dtype_equal": left.dtype == right.dtype,
                            "values_equal": bool(np.array_equal(left, right))}
    left, right = cached["signals"], rebuilt["signals"]
    shape_equal = left.shape == right.shape
    finite = bool(np.isfinite(left).all() and np.isfinite(right).all())
    dtype_ok = left.dtype == right.dtype == np.dtype("float32")
    usable = shape_equal and finite and dtype_ok
    delta = np.abs(left.astype(np.float64) - right.astype(np.float64)) if usable else None
    signal = {"shape_cached": list(left.shape), "shape_rebuilt": list(right.shape), "shape_equal": shape_equal,
              "dtype_cached": str(left.dtype), "dtype_rebuilt": str(right.dtype), "float32_both": dtype_ok, "finite_both": finite,
              "absolute_tolerance_volts": 1e-12, "relative_tolerance": 1e-6,
              "exact_equal": bool(usable and np.array_equal(left, right)),
              "within_tolerance": bool(usable and np.allclose(right, left, rtol=1e-6, atol=1e-12, equal_nan=False)),
              "maximum_absolute_error_volts": float(delta.max()) if usable else None,
              "root_mean_square_error_volts": float(np.sqrt(np.mean(delta**2))) if usable else None,
              "values_outside_tolerance": int(np.count_nonzero(delta > 1e-12 + 1e-6 * np.abs(left.astype(np.float64)))) if usable else None}
    passed = signal["within_tolerance"] and all(all(row.values()) for row in identities.values())
    return {"passed": passed, "identities": identities, "signals": signal}


def runtime_evidence(threadpool_info):
    pools = threadpool_info()
    if not pools or any(item["num_threads"] != 1 for item in pools):
        raise ValueError("physical thread pools differ from one thread")
    files = {}
    for module in tuple(sys.modules.values()):
        value = getattr(module, "__file__", None)
        if value:
            path = Path(value).resolve()
            if path.is_file() and (path.is_relative_to(ROOT / ".venv") or path.is_relative_to(ROOT / "data") or path.is_relative_to(ROOT / "core")):
                files[str(path)] = path
    if len(files) > 8000 or sum(path.stat().st_size for path in files.values()) > 512 * 1024**2:
        raise ValueError("imported runtime file bound exceeded")
    pins = {name: sha(path, allow_empty=True) for name, path in sorted(files.items())}
    torch = sys.modules.get("torch")
    if torch is not None and (torch.get_num_threads() != 1 or torch.cuda.is_initialized()):
        raise ValueError("torch thread or CUDA boundary changed")
    return {"python": sys.version, "executable": sys.executable,
            "versions": {name: importlib.metadata.version(name) for name in ("numpy", "scipy", "mne", "moabb", "scikit-learn", "threadpoolctl")},
            "threadpools": pools, "torch_imported": torch is not None, "torch_threads": torch.get_num_threads() if torch else None,
            "cuda_context_initialized": False, "imported_module_file_pins": pins, "imported_files": len(pins)}


def finish(out, plan, boundary, values, threadpool_info):
    verify_plan(plan)
    environment = runtime_evidence(threadpool_info)
    if boundary != {"network": 0, "subprocess": 0, "outside_write": 2, "expected_existing_directory_probes": 2}:
        raise ValueError("unexpected forbidden operation was attempted")
    record = {"schema": "pro3_mmidb_data_only_engineering_result_v1", "created_utc": datetime.now(UTC).isoformat(),
              "source_sha256": plan["canonical_source_sha256"], "execution_git_commit": plan["execution_git_commit"],
              "environment": environment, "boundary_denials": boundary, "shared_directory_creation_requests_denied": True, "model_constructed_or_fit": False, "checkpoint_opened": False,
              "recorder_invoked": False, "original_case_attempts_remaining": 0, "scientific_gate_or_freeze_signed": False,
              "checkpoint_cohort_or_overlap_verified": False, "authenticated_historical_cache_generation": False, **values}
    write_new(out / "result.json", record)
    print(json.dumps({"passed": record["passed"], "stage": plan["stage"], "imported_files": environment["imported_files"]}))
    return record
