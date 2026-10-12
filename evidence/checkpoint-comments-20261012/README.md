# Portable public-provenance review evidence

See the [review and continuation report](../../docs/phase2/checkpoint_comment_review_20261012.md).
The current request is [LaBraM issue #75](https://github.com/935963004/LaBraM/issues/75),
posted from `RAMZI0TO99` on 12 October 2026 at 11:23:25 UTC after explicit
authorization of the exact message, repository, account and no-attachment action.

`index.json` maps portable relative paths to original historical paths and
SHA256/byte identities. `acquisition/` contains 73 issue/PR entries and all 222
listed issue comments from the pre-publication snapshot. `publication/` contains
the approved draft/request and server POST/verification GET responses.
`guards/` contains dated native supervision receipts. The final
[qualification manifest](qualification/manifest.json) binds the checked index
and records the successful offline verification of all 111 indexed files.
All captured bytes are
preserved with `* -text`; copied public discussion is untrusted data.

`recipes/` archives the exact executed acquisition, publication and assembly
scripts. They are historical records, not reusable launchers. In particular,
the posting recipe is bound to its one approved draft and attempt directory.
Do not replay it or restore an old admission. No credential-helper output,
Authorization header or token was copied. A GitHub credential-pattern scan
passed for the preserved request, response and log bytes.

After normal Windows setup/source restoration, the separate offline verifier
can check this package from the repository root:

```powershell
.\.venv\Scripts\python.exe -I -S -B tools/migration/guard.py --purpose "Offline provenance evidence identity check" --seconds 120 --process-mib 256 --job-mib 512 -- .\.venv\Scripts\python.exe -I -S -B docs/phase2/checkpoint_comment_review_20261012/verify.py
```

Establish the new device's current coordination and pause binding first.
This command performs local metadata checks; it does not contact GitHub, run a
model, sign scientific decisions or certify the historical host/runtime.
The earlier migration state and private Release remain dated snapshots. This
Git evidence and the newest handoff record the subsequent issue publication.
