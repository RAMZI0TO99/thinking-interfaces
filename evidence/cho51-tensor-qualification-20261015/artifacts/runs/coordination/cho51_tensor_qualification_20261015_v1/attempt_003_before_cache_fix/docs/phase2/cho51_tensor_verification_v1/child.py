"""Restore exactly one independently pinned Cho-51 selected tensor state.

This is the actual native child, not an injectable executor. The launcher
establishes the finite private Job; this child retains the canonical tensor
verifier's RAM checks and adds read/write, network and no-fitting refusals.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
SITE_PACKAGES = ROOT / ".venv" / "Lib" / "site-packages"
sys.dont_write_bytecode = True
sys.path[:0] = [str(ROOT), str(SITE_PACKAGES)]

_PAUSE_PATHS = tuple(
    Path("D:/Aenv/pro2/WORK") / f"resume-{day}-001"
    / "coordination/PRO2_REQUEST_PRO3_PAUSE.json"
    for day in ("20261007", "20261012", "20261013", "20261015")
)
_FORBIDDEN_ARRAY_SUFFIXES = frozenset({
    ".npz", ".npy", ".mat", ".edf", ".gdf", ".fif", ".set",
})
_WEIGHT_SUFFIXES = frozenset({".pt", ".pth", ".ckpt", ".safetensors"})
_GIT_COMMANDS = frozenset({
    ("--no-optional-locks", "rev-parse", "--verify", "HEAD"),
    ("--no-optional-locks", "status", "--porcelain", "--untracked-files=all"),
})


def _path(value: str | bytes | os.PathLike[str]) -> Path:
    decoded = os.fsdecode(value)
    if decoded.startswith("\\\\?\\"):
        decoded = decoded[4:]
    return Path(decoded).resolve()


def _pause_check() -> None:
    present = [str(path) for path in _PAUSE_PATHS if path.exists()]
    if present:
        raise RuntimeError("peer pause is present: " + ", ".join(present))


def _exclusive_json(path: Path, value: dict[str, Any]) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


class _ChildAudit:
    """Fail closed on denied events, including a denial caught by a library."""

    def __init__(
        self, *, workspace: Path, project_root: Path,
        assets: frozenset[Path], git_executable: Path, probe_sha256: str,
    ) -> None:
        self.workspace = workspace
        self.project_root = project_root
        self.assets = assets
        self.git_executable = git_executable
        self.git_command_executable = shutil.which('git')
        if self.git_command_executable is None or _path(self.git_command_executable) != git_executable:
            raise ValueError('read-only Git command spelling is not the pinned executable')
        self.denied: list[dict[str, str]] = []
        self.hostname_queries = 0
        self.git_queries = 0
        self.probe_source = ROOT / '.venv/Lib/site-packages/urllib3/util/connection.py'
        self.expected_probe = dict(event='socket.__new__', classification='blocked_optional_ipv6_import_probe',
                                   source_file=str(self.probe_source), source_sha256=probe_sha256)

    def refuse(self, event: str, detail: object = None) -> None:
        self.denied.append({"event": event, "detail": repr(detail)[:500]})
        raise PermissionError("Cho-51 tensor child denied: " + event)

    def _inside_workspace(self, value: object) -> None:
        if isinstance(value, (str, bytes, os.PathLike)):
            if not _path(value).is_relative_to(self.workspace):
                self.refuse("outside_workspace_write", value)
        else:
            # An unbound descriptor cannot establish ownership of a mutation.
            self.refuse("unbound_descriptor_write", value)

    def _source_git_call(self) -> bool:
        frame = sys._getframe(2)
        while frame is not None:
            if (
                frame.f_code.co_name == "capture_source"
                and _path(frame.f_code.co_filename) == ROOT / "core" / "provenance.py"
            ):
                return True
            frame = frame.f_back
        return False

    def _git(self, values: tuple[Any, ...]) -> None:
        executable, arguments, cwd, environment = values
        if type(arguments) is str:
            # Windows subprocess converts a sequence with list2cmdline before
            # emitting the audit event. Match the whole known command, never
            # parse or execute an arbitrary shell command string.
            exact_command = arguments in {
                subprocess.list2cmdline([self.git_command_executable, *tail])
                for tail in _GIT_COMMANDS
            }
            executable_matches = (
                executable is None and os.name == "nt"
            ) or (
                isinstance(executable, (str, bytes, os.PathLike))
                and _path(executable) == self.git_executable
            )
        elif isinstance(arguments, (list, tuple)):
            exact_command = (
                bool(arguments) and all(type(argument) is str for argument in arguments)
                and _path(arguments[0]) == self.git_executable
                and tuple(arguments[1:]) in _GIT_COMMANDS
            )
            executable_matches = (
                isinstance(executable, (str, bytes, os.PathLike))
                and _path(executable) == self.git_executable
            )
        else:
            exact_command = executable_matches = False
        if (
            not exact_command or not executable_matches
            or not isinstance(cwd, (str, bytes, os.PathLike))
            or _path(cwd) != self.project_root
            or environment is not None
            or not self._source_git_call()
        ):
            self.refuse("subprocess.Popen", values)
        self.git_queries += 1

    def __call__(self, event: str, values: tuple[Any, ...]) -> None:
        if event == "socket.gethostname":
            self.hostname_queries += 1
        elif event.startswith("socket."):
            if event == 'socket.__new__' and values[1:] == (socket.AF_INET6, socket.SOCK_STREAM, 0):
                frame = sys._getframe(1)
                while frame is not None:
                    if frame.f_code.co_name == '_has_ipv6' and _path(frame.f_code.co_filename) == self.probe_source:
                        self.denied.append(dict(self.expected_probe))
                        raise PermissionError('optional IPv6 import probe blocked before socket creation')
                    frame = frame.f_back
            self.refuse(event, values)
        elif event == "subprocess.Popen":
            self._git(values)
        elif event in {"os.system", "os.startfile", "os.posix_spawn", "os.fork", "os.forkpty", "pty.spawn"} or event.startswith(("os.exec", "os.spawn")):
            self.refuse(event, values)
        elif event == "open":
            mode = values[1] if isinstance(values[1], str) else ""
            flags = values[2] if isinstance(values[2], int) else 0
            writing = any(character in mode for character in "wax+") or bool(
                flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)
            )
            if not isinstance(values[0], (str, bytes, os.PathLike)):
                if writing:
                    self._inside_workspace(values[0])
                return
            path = _path(values[0])
            mode = values[1] if isinstance(values[1], str) else ""
            flags = values[2] if isinstance(values[2], int) else 0
            writing = any(character in mode for character in "wax+") or bool(
                flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)
            )
            if writing:
                self._inside_workspace(path)
            else:
                lowered_parts = tuple(part.lower() for part in path.parts)
                data_directory = any(
                    lowered_parts[index:index + 2] in {
                        ("data", "raw"), ("data", "processed"), ("data", "interim"),
                    }
                    for index in range(len(lowered_parts) - 1)
                )
                if path.suffix.lower() in _FORBIDDEN_ARRAY_SUFFIXES or data_directory:
                    self.refuse("recording_or_processed_array_read", path)
                if path.suffix.lower() in _WEIGHT_SUFFIXES and path not in self.assets:
                    # .pth dependency declarations are not checkpoint files.
                    if not (path.suffix.lower() == ".pth" and path.is_relative_to(SITE_PACKAGES)):
                        self.refuse("unpinned_weights_read", path)
                if "weights" in lowered_parts and path not in self.assets:
                    self.refuse("unpinned_weights_directory_read", path)
        elif event in {
            "os.mkdir", "os.remove", "os.rmdir", "os.rename", "os.replace",
            "os.link", "os.symlink", "os.chmod", "os.utime", "os.truncate",
        }:
            count = 2 if event in {"os.rename", "os.replace", "os.link", "os.symlink"} else 1
            for value in values[:count]:
                self._inside_workspace(value)
        elif event == "os.chdir":
            self._inside_workspace(values[0])

    def require_clean(self) -> None:
        if len(self.denied) > 1 or any(row != self.expected_probe for row in self.denied):
            raise RuntimeError("tensor child observed an audit denial")


def _environment(workspace: Path) -> None:
    directories = {
        "TEMP": "temp", "TMP": "temp", "TMPDIR": "temp",
        "MPLCONFIGDIR": "mpl", "HF_HOME": "hf",
        "HF_HUB_CACHE": "hf/hub", "HUGGINGFACE_HUB_CACHE": "hf/hub",
        "TRANSFORMERS_CACHE": "hf/transformers", "TORCH_HOME": "torch",
        "NUMBA_CACHE_DIR": "numba", "JOBLIB_TEMP_FOLDER": "joblib",
        "XDG_CACHE_HOME": "cache",
    }
    for relative in sorted(set(directories.values()), key=lambda name: (name.count("/"), name)):
        (workspace / relative).mkdir()
    for name, relative in directories.items():
        os.environ[name] = str(workspace / relative)
    for name in (
        "OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
        "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS",
    ):
        os.environ[name] = "1"
    os.environ.update(
        CUDA_VISIBLE_DEVICES="", HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
        PYTHONDONTWRITEBYTECODE="1", TOKENIZERS_PARALLELISM="false",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--expect-bundle", required=True)
    arguments = parser.parse_args()

    # The bootstrap and launcher use the standard library only. Every admitted
    # source/runtime/asset pin is checked before numerical dependencies import.
    from docs.phase2.cho51_tensor_verification_v1 import launcher

    bundle = launcher.load_bundle(arguments.bundle, arguments.expect_bundle)
    if (
        Path(bundle["source_root"]) != ROOT
        or Path(bundle["native_child_path"]) != Path(__file__).resolve()
    ):
        raise ValueError("native tensor child source identity differs")
    workspace = Path(bundle["workspace"])
    witness_path = Path(bundle["witness_path"])
    scope_path = workspace / "child-scope.json"
    if witness_path.exists() or scope_path.exists():
        raise FileExistsError("tensor child output already exists")
    payload = launcher.read_json(Path(bundle["input_path"]), maximum_bytes=1024**2,
                                 expected_sha256=bundle['input_file_sha256'])
    if launcher.digest(Path(bundle["input_path"])) != bundle["input_file_sha256"]:
        raise ValueError("tensor child input changed before admission")
    if not isinstance(payload, dict) or not isinstance(payload.get("project_root"), str):
        raise ValueError("tensor child input project root is missing")
    project_root = Path(payload["project_root"])
    if not project_root.is_absolute() or project_root.resolve(strict=True) != project_root:
        raise ValueError("tensor child project root aliases another directory")
    git_executable = Path(bundle["git_executable"])
    discovered_git = shutil.which("git")
    if (
        discovered_git is None or _path(discovered_git) != git_executable
        or str(git_executable) not in bundle["runtime"]
    ):
        raise ValueError("live read-only Git executable differs from its runtime pin")
    _pause_check()
    launcher.verify_bundle_pins(bundle)
    _environment(workspace)
    audit = _ChildAudit(
        workspace=workspace, project_root=project_root,
        assets=frozenset(Path(path) for path in bundle["assets"]),
        git_executable=git_executable,
        probe_sha256=bundle['files'][str(ROOT / '.venv/Lib/site-packages/urllib3/util/connection.py')],
    )
    sys.addaudithook(audit)
    started = time.monotonic()
    restored = False
    hooks_installed = False
    observed_threads: int | None = None
    observed_interop_threads: int | None = None
    observed_environment_sha256: str | None = None
    status = "failed"
    error: str | None = None
    try:
        _pause_check()
        import torch

        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)

        def no_fitting_or_pickle(*args: object, **kwargs: object) -> Any:
            audit.refuse("training_or_pickle_call")

        torch.load = no_fitting_or_pickle
        torch.optim.Optimizer.__init__ = no_fitting_or_pickle
        torch.Tensor.backward = no_fitting_or_pickle
        torch.autograd.backward = no_fitting_or_pickle
        hooks_installed = True
        observed_threads = torch.get_num_threads()
        observed_interop_threads = torch.get_num_interop_threads()
        # Request imports transitively include torch, hence they follow the
        # numerical bootstrap and no-fitting hooks rather than preceding it.
        from docs.phase2.cho51_tensor_verification_v1.contract import (
            WITNESS_SCHEMA, load_tensor_request, validate_tensor_witness,
        )
        from evaluation.phase2_cho_selected_manifest_bridge import (
            verify_cho_selected_manifest_files,
        )
        from evaluation.phase2_cho_source_restore import verify_cho_selected_source_state
        from evaluation.phase2_runner import environment_digest

        request = load_tensor_request(payload)
        if request.sha256 != bundle["request_sha256"]:
            raise ValueError("tensor child request differs from independent bundle pin")
        publication = request.publication
        observed_environment_sha256 = environment_digest()
        if observed_environment_sha256 != publication.environment_sha256:
            raise ValueError("live tensor environment differs from independent publication pin")
        if publication.manifest_path not in audit.assets:
            raise ValueError("selected manifest is missing its independent physical asset pin")
        _pause_check()
        audit.require_clean()
        manifest = verify_cho_selected_manifest_files(
            request.project_root, publication.manifest_path,
            manifest_sha256=publication.manifest_sha256,
            evidence_sha256=publication.evidence_sha256,
            selection_contract_sha256=publication.selection_contract_sha256,
            selected_candidate=publication.selected_candidate,
            protocol_config_sha256=publication.protocol_config_sha256,
            expected_source=request.expected_source,
            model_recipe_sha256=publication.model_recipe_sha256,
            model_state_sha256=publication.model_state_sha256,
        )
        record = launcher.read_json(publication.manifest_path, maximum_bytes=4 * 1024**2)
        if record["payload"].get("weights_format", "full_v1") != "full_v1":
            raise ValueError("native tensor verification supports full_v1 weights only")
        if manifest.weights_sha256 != publication.weights_sha256:
            raise ValueError("selected publication weight bytes differ from request")
        if any(path not in audit.assets for path in (
            manifest.manifest_path, manifest.evidence_path, manifest.weights_path,
        )):
            raise ValueError("selected publication file is missing its independent physical asset pin")
        _pause_check()
        audit.require_clean()
        state = verify_cho_selected_source_state(
            root=request.project_root, plan=request.plan,
            method_config=payload["method_config"],
            expected_method_config_sha256=publication.method_config_sha256,
            selected_candidate=publication.selected_candidate,
            manifest_sha256=publication.manifest_sha256,
            evidence_sha256=publication.evidence_sha256,
            protocol_config=payload["protocol_config"],
            expected_model_recipe_sha256=publication.model_recipe_sha256,
            expected_model_state_sha256=publication.model_state_sha256,
        )
        restored = True
        witness = {
            "schema": WITNESS_SCHEMA,
            "request_sha256": request.sha256,
            "case_id": request.plan.case_id,
            "manifest_sha256": state.manifest_sha256,
            "evidence_sha256": state.evidence_sha256,
            "selected_candidate": state.selected_candidate,
            "model_recipe_sha256": state.model_recipe_sha256,
            "model_state_sha256": state.model_state_sha256,
            "weights_sha256": state.weights_sha256,
            "training_performed": False,
        }
        validate_tensor_witness(request, witness)
        manifest.verify_stable()
        launcher.verify_bundle_pins(bundle)
        if launcher.digest(arguments.bundle) != arguments.expect_bundle:
            raise ValueError("tensor bundle changed during child verification")
        if torch.get_num_threads() != 1 or torch.get_num_interop_threads() != 1:
            raise RuntimeError("tensor child thread settings changed")
        _pause_check()
        audit.require_clean()
        _exclusive_json(witness_path, witness)
        status = "verified"
        print(json.dumps({"case_id": request.plan.case_id, "tensor_state_verified": True}), flush=True)
        return 0
    except BaseException as exc:
        error = type(exc).__name__ + ": " + str(exc)[:1000]
        raise
    finally:
        _exclusive_json(scope_path, {
            "schema": "cho51_tensor_child_scope_v1",
            "request_sha256": bundle["request_sha256"],
            "status": status,
            "elapsed_seconds": time.monotonic() - started,
            "actual_tensor_restoration_performed": restored,
            "canonical_tensor_verifier_unchanged": True,
            "no_fitting_hooks_installed": hooks_installed,
            "torch_threads": observed_threads,
            "torch_interop_threads": observed_interop_threads,
            "gpu_hidden": os.environ.get("CUDA_VISIBLE_DEVICES") == "",
            "environment_sha256": observed_environment_sha256,
            "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
            "hostname_queries": audit.hostname_queries,
            "read_only_git_queries": audit.git_queries,
            "denied_operations": audit.denied,
            "peer_pause_paths": [str(path) for path in _PAUSE_PATHS],
            "error": error,
        })


if __name__ == "__main__":
    raise SystemExit(main())
