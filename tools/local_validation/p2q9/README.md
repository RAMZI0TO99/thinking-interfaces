# P2Q revision9 cooperative artifact consumer

Only the exact operation-specific mapping, diagnostic and helper may use a read
handle sharing READ|WRITE, after mandatory byte/hash/native-ID authorization.
Original caller RW/ShareRead handles remain live until all consumers close;
other writers and deleters remain denied. Ordinary readers stay strict.

Both receivers report exact capabilities. After reaping consumers the caller
rehashes/reidentifies its original writers, then closes them. Q qualification
must bind that actual handoff plus three native sharing tests. The exact roster
is195, with unchanged resource/time/file/output caps. See the R9 contract.

No source was imported, compiled, tested or executed in authoring. Failed Q8
mapping artifacts remain unqualified; independent review/admission is required.
