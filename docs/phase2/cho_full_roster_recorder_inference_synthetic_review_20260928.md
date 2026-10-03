# Cho full-roster synthetic recorder bridge rehearsal

28 September 2026. The [write-once engineering receipt](../../runs/phase2/analysis_inference_checks/20260928_9bf0516c_recorder_bridge_synthetic/receipt.json)
pins a synthetic recorder-format fixture through the [read-only bridge](../../evaluation/phase2_cell_aggregation_bridge.py),
[subject aggregation](../../evaluation/phase2_subject_aggregation.py) and
[pure paired calculation](../../evaluation/phase2_inference.py). It extends
the earlier [ScoreRow-only rehearsal](cho_full_roster_inference_synthetic_review_20260928.md),
which did not read recorder files. This check read no real Cho cell score,
fit no model, admitted no scientific cell and published no scientific report.

The [script](../../runs/phase2/analysis_inference_checks/20260928_9bf0516c_recorder_bridge_synthetic/run_synthetic.py)
required exact equality between the pinned planning crosswalk and the
Cartesian roster of 52 Cho subjects, four selected methods, five fixed seeds
and five shots: **1,040 cases**. It verified source fingerprint `9bf0516c`,
the exact-source full quality bundle and the 1,040/1,040 no-fit route receipt.
It wrote an [external expected-pin manifest](../../runs/phase2/analysis_inference_checks/20260928_9bf0516c_recorder_bridge_synthetic/expected_pin_manifest.json)
before creating the fixture files. The manifest pins each canonical claim,
cell, publication intent and success file by expected byte digest, together
with synthetic cell and selection-evidence digests.

The script created 4,160 canonical recorder-format files in a temporary
directory under `runs/phase2`. The production bridge verified the exact
directory inventory and all 1,040 externally pinned cells. Every returned
cell digest and exact-rational score was compared with its independent
synthetic rule. Aggregation produced **208 five-seed subject-method means**;
those produced **52 exact LoRA-minus-linear subject differences** for the
pure proposed inference calculation. The synthetic Pratt result matched a
separate common-denominator SciPy reference. A self-consistent cell change
after pinning and an unlisted claim were rejected. The fixture files were
removed; the retained manifest, script and receipt permit review without
retaining thousands of synthetic files.

The focused run took 57.8 seconds. Available RAM was 4.975 GiB before and
4.394 GiB after cleanup, with 32.506 GiB disk free afterward. Source and
the [796-test exact-source quality archive](../../runs/phase2/quality_history/20260928_pure_inference_9bf0516c.json)
remain unchanged. This no-fit check does not satisfy the separate 10 GiB
control-fit startup guard.

These files were generated in recorder format; the run did not execute
1,040 `CaseRecorder` writer lifecycles. Fabricated provenance and
selection-evidence digests do not authenticate real cells. A real analysis
still needs independent scientific source, cohort, episode, selection and
configuration pins, ratified executable settings, complete-work resources,
current controls and a report publication contract. The proposed 5,253-step
selection remains above the unchanged 256-step engineering cap. The full
freeze and Gate A remain unsigned. The receipt's numerical results are
**synthetic engineering outputs**, not decoding results or a claim.
