# Windows boundary provider assessment

28 October 2026. Source research for the diagnostic collector; no positive
provider qualification or current-machine observation is claimed here.

Microsoft distinguishes a full restart from sleep, hibernation and Fast Startup.
Fast Startup preserves kernel state; a restart requests a full shutdown/boot.
That documented behavior does not prove that a particular event occurred on the
host associated with the old failed operation.
[System power states](https://learn.microsoft.com/en-us/windows/win32/power/system-power-states).

QPC supports elapsed-time measurements within the observed execution; it is not
an externally synchronized UTC clock. The collector records QPC and UTC locally
and does not compare the old and current counters as one clock or authenticate
cross-restart ordering.
[Acquiring high-resolution time stamps](https://learn.microsoft.com/en-us/windows/win32/sysinfo/acquiring-high-resolution-time-stamps).

`Win32_OperatingSystem.LastBootUpTime` is an OS boot-time property. A standalone
reading does not provide the missing old host association, persisted-domain
assessment or independently qualified restart-kind and clock evidence. It is
therefore not used as an acceptance shortcut.
[Win32_OperatingSystem](https://learn.microsoft.com/en-us/windows/win32/cimwin32prov/win32-operatingsystem).

The SMBIOS product UUID can be unavailable (all zeros); even a supplied UUID
would need independently supported association with the old operation. This
version does not collect hardware identifiers or treat a machine-name hash as
authentication.
[Win32_ComputerSystemProduct](https://learn.microsoft.com/en-us/windows/win32/cimwin32prov/win32-computersystemproduct).

The implemented collector uses the documented local Event Log APIs to retain
bounded raw XML. `EvtNext` supplies a finite timeout and requires each returned
event handle to be closed. The selected System-channel provider query has a
32-event cap, a sentinel to detect additional rows, 64KiB per XML event and
512KiB total XML. Enumeration errors, time limits, truncation and handle-close
errors remain visible. A supervised child deadline covers blocking API calls.
[EvtNext](https://learn.microsoft.com/en-us/windows/win32/api/winevt/nf-winevt-evtnext).

No event-ID-to-full-restart mapping has been qualified. Query exhaustion is only
exhaustion of that selected retained query; it does not prove completeness of
the event log. Logs may have been cleared, overwritten or restored. Present
computer labels and timestamps cannot bind the old process to this host.
Guest/container persistence and trustworthy cross-boot time ordering remain
unresolved. These are explicit implementation limits, not operator assertions
that can be supplied as `true` to unlock execution.

## Scope of this implementation

The [source package](../../tools/custody_boundary/v1/README.md) separates raw
diagnostics, pure bounded metadata checks and future authenticated evidence.
The collector always reports `UNRESOLVED`, with launch/scientific authority
false. The verifier cannot promote caller-supplied booleans or schemas to a
qualified boundary. No reboot is requested or performed.

This advances the diagnostic and rejection paths. A production positive path
still requires qualified retained artifact identity, actual source/runtime and
review joins, old event-to-host evidence, supported restart/clock/persistence
providers and independent actual-result acceptance. Successor006 remains later
work. The sealed design and its48-case matrix are preserved unchanged; this
implementation's fixture results are reported separately.
