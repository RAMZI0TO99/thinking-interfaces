# Current-source control refresh

19 September 2026, milestone 51. The existing RAM-deferred 45-fit refresh is
complete for source `6d01ec59d7323af0fd91f141d1484a419717062b43d7d52dc221d27ea9be19a2`. The owner delegated
autonomous work and GPU use; the previously authorized retry became feasible
when unchanged resource admission passed. No new scientific protocol or
acceptance threshold was chosen.

The unchanged committed configurations specify nine shuffled-label fits
(nine BCI subjects, seed 11) and 36 pre-cue fits (nine subjects, four seeds).
The existing CUDA executor was used. Startup had 12.08 GiB free RAM and
30.70 GiB free disk. The original 10 GiB startup/4 GiB active RAM guards and
cooling policy remained intact; the wrapper additionally monitored the
project's 20 GiB disk floor. Minimum observed active RAM: 10.53 GiB;
minimum monitored disk: 30.70 GiB. No stop or guard override occurred.

| Existing negative control | Fits | Subject-mean balanced accuracy | Precommitted maximum | Result |
| --- | ---: | ---: | ---: | --- |
| Shuffled development labels | 9 | 48.7654% | 60% | Pass |
| One-second pre-cue | 36 | 24.8553% | 35% | Pass |

The independent check-only command verifies **45/45** current-context records,
with zero invalid, missing or unexpected records. It reconstructs the declared
splits, seed/label handling, early stopping and held-out confusion matrices.
Context: `fee460c0a82baffb319afde7edfbe50a13594b6eae258ca67f74d8e028fb13e6`.
Record snapshot: `1c1a273ab4cf18aeb8a2ee3104de153fc7ff45174255852aab2b45f41e220fae`.
Output: `runs/source_bound_controls/fee460c0a82baffb319afde7edfbe50a13594b6eae258ca67f74d8e028fb13e6`.

The worker took 202.84 seconds including orchestration
and loading; saved training/prediction intervals sum to 87.17
seconds. Its atomic completed-fit records are the resume units. A crash during
one unfinished fit would restart that fit; the largest observed fit was
6.86 seconds. The established control implementation was not
modified to add intra-fit checkpoints. Milestone-50 source checkpoints remain
preserved and separately verified.

All **44,968 historical run files** retain
their baseline SHA-256, including frozen Phase I and milestone-50 evidence.
Source/config/test files, the scientific freeze draft, and the fresh milestone-50
quality bundle remain unchanged. The 571-test/935-subtest lint/types/tests bundle
was verified against this exact source and its logs, without rerunning unchanged
tests; the additional verification here is the actual 45-fit control execution
and independent record audit. This reuse is explicitly recorded as an operational
deviation, following the evidence-only milestone pattern.

The RAM-deferred control prerequisite is now closed for this source/environment.
Future source/config/environment changes require a matching refresh. These
negative controls do **not** sign Gate A or resolve the 75.66% versus 77.15%
reproduction rationale. Freeze/EA inclusion, MMIDB policy, Gate A and commit/push
remain owner decisions; complete scientific workload admission is still absent.
No Phase II scientific cell, commit or push occurred.

Final receipt: `runs/phase2/control_refresh_checks/20260919_step51/receipt.json`.
