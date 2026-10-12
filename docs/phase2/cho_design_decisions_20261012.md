# Four Cho design decisions adopted under explicit user delegation

12 October 2026 UTC. In response to the exact question naming four choices in
the [pinned owner packet](https://github.com/RAMZI0TO99/thinking-interfaces/blob/2aeee666f58b74be35099b103bf5db2c1d07edc8/docs/phase2/cho_owner_decision_packet_20261010.md),
the user replied **"do what you see fit!"**. Root exercised that explicit
delegation by adopting the existing proposed versions of those four choices.
The [new machine-readable decision record](cho_design_decisions_20261012.json)
preserves the exact question/reply, decision maker, prior proposal pins,
13 unchanged configuration pins and full adopted design. It does not infer a
direct human scientific signature or claim the entire packet was reviewed by
the user. The original 10 October packet remains an unchanged historical baseline.

| Decision | Adopted design |
| --- | --- |
| Cho scope and candidates | Cho2017, five shots per class, 52 subjects, four methods (`labram_linear`, `labram_lora`, `labram_full`, `eegnet`), seeds11/23/37/53/71, 1,040 planned cells. Adopt the exact pinned two-candidate template, including method-specific source/support settings and Profile B bindings. EA remains deferred. |
| Primary analysis | Exact five-seed means within each subject, then 52 LoRA-minus-linear differences. Require the complete verified roster with no substitutions or imputation. One-sided Wilcoxon signed ranks, Pratt zeros, asymptotic method, no continuity correction, alpha0.05, exact rank/tie-preserving integer encoding. All-zero differences yield p1; other non-finite results stop analysis. Superiority additionally requires unrounded p<0.05 and a strictly positive exact paired arithmetic mean. Display a separate 95% paired-mean Student t interval, df51; zero variance yields a point interval. |
| Secondary superiority family | Empty. Full-tuning/EEGNet summaries and LoRA-minus-full/EEGNet contrasts are descriptive; any later superiority family requires a new prospective declaration and Holm adjustment. |
| Margin interpretation | Exploratory paired-mean estimate and two-sided90% Student t interval at the existing planning margin +/-0.05202907926797159. No formal TOST, equivalence or clinical interchangeability claim. |

The existing review makes these choices explicit and keeps participant units,
rank/tie handling and claim conditions separate. The
[official SciPy Wilcoxon reference](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.wilcoxon.html)
supports the named Pratt and asymptotic options and warns about subtraction
altering ties. The adopted rule retains the proposal's statistical assumptions
and approximation limits; adoption is not new numerical qualification or proof
that a scientific claim is valid. The installed runtime remains separately pinned.

Historical pilot and Gate A outcomes were known before this adoption. This
record does not claim those earlier cases were prospectively specified or unseen.
The exact candidate proposal SHA remains
`f3dba0643cba2807fbc6e0421c271f260c8cf357a8bc67a19f7456931ca892ef`;
the original owner packet SHA remains
`2a890980541120b4d311078436fe85aac13e77f3f33871739ab62347320ff400`.
Only the successor decision record's adoption metadata changes.

**Three decisions remain pending:** Gate A's explicit retrospective acceptance
rationale; checkpoint-bound cohort evidence, mapping review and permitted claims;
and the final named experiment freeze after scientific and operational conditions
are resolved. The one issue75 capture at12:35:22 UTC had zero comments, so no new
checkpoint training statement or actual recording intersection is available.

All active protocol/configuration bytes remain unchanged. Optimizer/search
implementation and runtime pilot, measured real-worker environment, complete
roster feasibility, resource/storage/runtime bounds and fresh coordination/
admission remain operational prerequisites. The exhausted original case cannot
be reused, reset, renamed or replaced with an invented score to fill the roster.
Its two attempts remain spent, zero remaining. This adoption authorizes no
training, inference, model case, new compute budget or automatic schedule.
Gate A and the experiment freeze remain unsigned.

The decision was recorded in a fresh guarded metadata-only Job,
`20261012T125505Z_f2ca1fc3a3`, which passed, closed and was physically absent.
All13 configuration pins, original proposal/candidate pins and Source3114ec43/432
were verified before recording. No scientific library import, model/raw-data
operation or full-suite replay occurred. The
[portable decision and execution evidence](../../evidence/cho-design-decisions-20261012/README.md)
preserves the decision bytes and receipt. The completed
[reply workflow](provenance_reply_workflow_20261012.md) remains ready for an actual
response; its synthetic checks do not resolve the three pending decisions.
