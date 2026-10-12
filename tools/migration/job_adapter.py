"""Atomic Windows Job adapter extracted from the qualified 2026-10-08 parent.

Original parent SHA256: 3ca90de6dcf62f7c272301e9da2358189bf7095f9d2afe2436552448bc6e2e79.
Only the adapter is reused. No historical admission, case runner or deadline is copied.
Migration callers set their own process/aggregate caps before installing it.
"""
from __future__ import annotations
import ctypes
from types import ModuleType
from typing import Any
MEMORY_LIMIT_BYTES = 4 * 1024**3
AGGREGATE_LIMIT_BYTES = 5 * 1024**3
JOB_MEMORY_FLAG = 0x00000200
JOB_LIST_ATTRIBUTE = 0x0002000D

def install_job_adapter(
    primitive: ModuleType, state: dict[str, Any], job_name: str
) -> None:
    # This existing isolated API also exposes the native attribute-list
    # functions. It does not create any pipe or process in its constructor.
    original_api = primitive._FrameWinApi
    original_peaks = primitive._job_memory_peaks

    def key(handle: Any) -> int:
        return int(getattr(handle, "value", handle) or 0)

    def peaks(api: Any, job: Any) -> tuple[int, int]:
        measured = original_peaks(api, job)
        state["peak_samples"] += 1
        state["peak_process_commit_bytes"] = max(state["peak_process_commit_bytes"], measured[0])
        state["peak_job_commit_bytes"] = max(state["peak_job_commit_bytes"], measured[1])
        return measured

    def limits(api: Any, job: Any, process_limit: int | None) -> None:
        if process_limit != MEMORY_LIMIT_BYTES:
            raise primitive.SupervisionError("first-case process cap must remain 6 GiB")
        configured = primitive._ExtendedLimit()
        flags = (
            primitive.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            | primitive.JOB_OBJECT_LIMIT_PROCESS_MEMORY | JOB_MEMORY_FLAG
        )
        configured.BasicLimitInformation.LimitFlags = flags
        configured.ProcessMemoryLimit = MEMORY_LIMIT_BYTES
        configured.JobMemoryLimit = AGGREGATE_LIMIT_BYTES
        if not api.set_job(
            job, primitive.JOB_OBJECT_EXTENDED_LIMIT_INFORMATION_CLASS,
            ctypes.byref(configured), ctypes.sizeof(configured),
        ):
            raise primitive.SupervisionError("aggregate Job limit could not be set")
        state["limits_set"] = True
        observed = primitive._ExtendedLimit()
        if not api.query_job(
            job, primitive.JOB_OBJECT_EXTENDED_LIMIT_INFORMATION_CLASS,
            ctypes.byref(observed), ctypes.sizeof(observed), None,
        ) or (
            observed.BasicLimitInformation.LimitFlags != flags
            or observed.JobMemoryLimit != AGGREGATE_LIMIT_BYTES or observed.ProcessMemoryLimit != MEMORY_LIMIT_BYTES  # noqa: E501
        ):
            raise primitive.SupervisionError("aggregate/process/kill-on-close limits not verified")
        state.update({
            "limits_query_verified": True, "limit_flags": flags,
            "aggregate_limit_bytes": int(observed.JobMemoryLimit),
            "process_limit_bytes": int(observed.ProcessMemoryLimit),
        })

    class ObservedApi:
        def __init__(self) -> None:
            self.api = original_api()
            self.job: Any = None
            self.process: Any = None
            self.thread: Any = None
            self.created_info: Any = None

        def remember_created_handles(self) -> None:
            # Keep the live native output structure before calling creation.
            # This also recovers ownership if Python is interrupted after the
            # OS creates the child but before the primitive copies its handles.
            if self.created_info is not None and self.created_info.hProcess:
                self.process = self.created_info.hProcess
                self.thread = self.created_info.hThread
                state["root_pid"] = int(self.created_info.dwProcessId)
                state["created_suspended"] = True

        def __getattr__(self, name: str) -> Any:
            return getattr(self.api, name)

        def create_job(self, *args: Any) -> Any:
            self.job = self.api.create_job(args[0], job_name)
            state["job_created"] = bool(self.job)
            state["job_named"] = job_name
            return self.job

        def create_process(self, *args: Any) -> Any:
            if (
                not self.job or not state["limits_query_verified"] or len(args) != 10
                or args[4]
                or args[5] != (primitive.CREATE_SUSPENDED | primitive.CREATE_NO_WINDOW)
            ):
                raise primitive.SupervisionError("atomic capped suspended creation required")
            # Attach the private Job in CreateProcessW itself. A watchdog kill
            # during or immediately after native creation can then only leave
            # a Job member, which noninherited kill-on-close already contains.
            # Unsupported systems fail during setup, before any child exists.
            size = ctypes.c_size_t()
            ctypes.set_last_error(0)
            if (
                self.api.init_attributes(None, 1, 0, ctypes.byref(size))
                or ctypes.get_last_error() != primitive.ERROR_INSUFFICIENT_BUFFER
                or not 0 < size.value <= 65536
            ):
                raise primitive._error("InitializeProcThreadAttributeList(Job list size)")
            buffer = ctypes.create_string_buffer(size.value)
            attributes = ctypes.cast(buffer, ctypes.c_void_p)
            if not self.api.init_attributes(attributes, 1, 0, ctypes.byref(size)):
                raise primitive._error("InitializeProcThreadAttributeList(Job list)")
            native_error: int | None = None
            try:
                jobs = (primitive.wintypes.HANDLE * 1)(key(self.job))
                if not self.api.update_attribute(
                    attributes, 0, JOB_LIST_ATTRIBUTE,
                    ctypes.cast(jobs, ctypes.c_void_p), ctypes.sizeof(jobs), None, None,
                ):
                    raise primitive._error("UpdateProcThreadAttribute(Job list)")
                startup = primitive._StartupInfoEx()
                ctypes.memmove(
                    ctypes.byref(startup.StartupInfo), args[8],
                    ctypes.sizeof(primitive._StartupInfo),
                )
                startup.StartupInfo.cb = ctypes.sizeof(startup)
                startup.lpAttributeList = attributes
                creation = list(args)
                creation[5] |= primitive.EXTENDED_STARTUPINFO_PRESENT
                creation[8] = ctypes.cast(
                    ctypes.byref(startup), ctypes.POINTER(primitive._StartupInfo)
                )
                state["atomic_job_assignment_requested"] = True
                state["creation_flags"] = creation[5]
                state["child_handle_inheritance"] = False
                self.created_info = ctypes.cast(
                    args[-1], ctypes.POINTER(primitive._ProcessInfo)
                ).contents
                outcome = self.api.create_process(*creation)
                native_error = ctypes.get_last_error()
                if outcome:
                    self.remember_created_handles()
                return outcome
            finally:
                try:
                    self.api.delete_attributes(attributes)
                    state["attribute_cleanup_confirmed"] = True
                except (Exception, KeyboardInterrupt) as error:
                    # Never conceal a successful native creation from the
                    # primitive. Resume rejects this error while still suspended.
                    state["cleanup_errors"].append(f"attribute cleanup: {error}")
                if native_error is not None:
                    ctypes.set_last_error(native_error)

        def assign(self, *args: Any) -> Any:
            # The primitive's assignment step verifies existing membership;
            # never attempt a second AssignProcessToJobObject on the same Job.
            state["assignment_step_seen"] = True
            if (
                len(args) != 2 or key(args[0]) != key(self.job)
                or key(args[1]) != key(self.process)
                or not state["atomic_job_assignment_requested"]
            ):
                raise primitive.SupervisionError("unexpected atomic Job verification scope")
            present = primitive.wintypes.BOOL()
            outcome = self.api.in_job(args[1], args[0], ctypes.byref(present))
            verified = bool(outcome and present.value)
            state["atomic_job_assignment_verified"] = verified
            state["assigned"] = verified
            return verified

        def in_job(self, *args: Any) -> Any:
            outcome = self.api.in_job(*args)
            present = ctypes.cast(args[2], ctypes.POINTER(primitive.wintypes.BOOL)).contents.value
            state["membership_verified"] = bool(outcome and present)
            return outcome

        def resume(self, *args: Any) -> Any:
            if (
                not state["limits_query_verified"] or not state["membership_verified"]
                or not state["atomic_job_assignment_verified"]
                or state["cleanup_errors"]
            ):
                raise primitive.SupervisionError(
                    "resume refused without verified cap and assignment"
                )
            outcome = self.api.resume(*args)
            state["resumed"] = outcome != primitive.WAIT_FAILED
            return outcome

        def wait(self, *args: Any) -> Any:
            outcome = self.api.wait(*args)
            if state["job_closed"] and key(args[0]) == key(self.process):
                state["root_exit_after_job_close"] = outcome == primitive.WAIT_OBJECT_0
            return outcome

        def terminate_job(self, *args: Any) -> Any:
            if key(args[0]) != key(self.job):
                raise primitive.SupervisionError("refusing termination outside the private Job")
            try:
                peaks(self, args[0])
            except Exception as error:
                state["peak_sampling_errors"].append(str(error))
            outcome = self.api.terminate_job(*args)
            state["owned_job_termination_called"] = True
            return outcome

        def close(self, handle: Any) -> Any:
            self.remember_created_handles()
            if key(handle) != key(self.job):
                for own, flag in ((self.thread, "thread_handle_closed"),
                                  (self.process, "process_handle_closed")):
                    if own and key(handle) == key(own):
                        if state[flag]:
                            return True  # Already closed only by this adapter.
                        closed = self.api.close(handle)
                        state[flag] = bool(closed)
                        return closed
                return self.api.close(handle)
            try:
                peaks(self, handle)
            except Exception as error:
                state["peak_sampling_errors"].append(str(error))
            try:
                active = primitive._active_processes(self, handle)
                state["active_before_cleanup"] = active
                if active:
                    if not self.terminate_job(handle, primitive.ERROR_TERMINATED):
                        raise primitive.SupervisionError("owned Job cleanup termination failed")
                    primitive._wait_for_empty_job(self, handle, seconds=2.0)
                state["job_empty_before_close"] = primitive._active_processes(self, handle) == 0
                if not state["job_empty_before_close"]:
                    raise primitive.SupervisionError("owned Job emptiness remains unconfirmed")
            except Exception as error:
                state["cleanup_errors"].append(str(error))
            # Closing is still necessary on sensor/query failure: the verified
            # kill-on-close limit is the final owned-tree termination mechanism.
            closed = self.api.close(handle)
            state["job_closed"] = bool(closed)
            if closed and self.process and not state["assignment_step_seen"]:
                # The primitive may still have zero handles if creation was
                # interrupted before it received the native output. Close only
                # these exact recovered handles, preserving the live PID receipt.
                state["creation_bookkeeping_cleanup_called"] = True
                if not state["thread_handle_closed"]:
                    state["thread_handle_closed"] = bool(self.api.close(self.thread))
                status = self.api.wait(self.process, 2000)
                state["root_exit_after_job_close"] = status == primitive.WAIT_OBJECT_0
                if not state["process_handle_closed"]:
                    state["process_handle_closed"] = bool(self.api.close(self.process))
                if not (
                    state["thread_handle_closed"] and state["process_handle_closed"]
                    and state["root_exit_after_job_close"]
                ):
                    state["cleanup_errors"].append("recovered creation handles cleanup unconfirmed")
            # A failed accounting check cannot turn a SUCCESSFUL native close
            # into False: the primitive would retry termination/close on an
            # already closed handle. Attestation is rejected independently.
            return closed

    primitive._WinApi = ObservedApi
    primitive._set_job_limits = limits
    primitive._job_memory_peaks = peaks
