# Proposed Cho amendment: 51 evaluation targets, unchanged available cohort

12 October 2026 UTC. **Unsigned proposal; not adopted; no execution authority.**
The fresh [readiness review](phase2_readiness_review_20261012.md) found that the
required subject 01/LaBraM-linear/seed11/five-shot case has two failed attempts,
zero remaining and no recoverable success intent. That case is one of the
currently adopted 1,040 rows. The current primary analysis requires every row
and forbids imputation, so the unchanged 52-target plan cannot complete under
its present case rules.

Propose evaluating subjects 02–52, consistently removing all 20 subject 01 rows
across every method and seed. Keep all 52 subjects available to the existing
source-selection protocol: each outer target remains excluded, leaving 51 source
subjects, and each inner validation subject is also excluded from its 50 training
sources. Subject01 may therefore remain a source or inner validation subject for
other outer targets. This changes the evaluation population; it does not claim
to complete the original 52-target study.

| Decision | Current adopted design | Exact proposed amendment |
| --- | --- | --- |
| Available cohort |52 subjects |52 subjects, unchanged |
| Evaluation targets |subjects 01–52 |subjects 02–52, 51 targets |
| Methods |linear, LoRA, full, EEGNet |Unchanged |
| Shots per class |5 |5, unchanged |
| Model seeds |11/23/37/53/71 |Unchanged |
| Complete verified rows |1,040 |1,020 |
| Independent analysis units |52 subjects |51 subjects |
| Student t interval degrees of freedom |51 |50 |
| Selection steps per case |5,253 |5,253, unchanged |
| Total planned selection steps |5,463,120 |5,358,060 |
| Target support steps |1,040 |1,020 |
| Original exhausted case |2 spent, 0 remaining |Preserved, 0 remaining |

The [exact machine-readable proposal](cho_51_target_amendment_proposal_20261012.json)
lists the 1,020 retained rows and20 excluded rows. Every retained case ID and
method-template digest is identical to its existing planned row. No case is
renamed or reset, and no seed, score or subject is substituted for a missing row.
The full original 1,040-row roster and prior decisions remain preserved.

The proposed primary contrast stays LoRA minus linear: exact five-seed means
within each of 51 subjects, one-sided Wilcoxon/Pratt with the existing explicit
settings, and superiority requiring both unrounded p<0.05 and a positive exact
paired mean. The separate95% Student t mean interval uses 51 subjects and df 50;
zero variance retains the point interval rule. The descriptive secondary and90%
exploratory-margin intervals also use 51 subjects/df 50. The superiority family
remains empty, and the existing exploratory margin stays unchanged with no
formal equivalence or interchangeability claim. Exactly1,020 verified rows are
required; no missing-cell imputation is introduced.

This is a **retrospective amendment to the already adopted target scope**, made
after prior engineering history was known. Its reason is the exhausted case and
complete-roster contract, rather than choosing targets by comparative outcomes.
Subject01's historical EEGNet engineering outcome is already known; this proposal
must not be described as a 51-target design specified before that history.
The exclusion changes the evaluation population and can change reported averages.
Any future claims must name the retained51 targets and disclose this decision.

Root recommends this alternative because it preserves the available data,
five-shot question, candidate settings, methods, seeds and original case limits.
The owner can instead keep the adopted 52-target study blocked, or choose a
separately reviewed substantive protocol. Engineering work does not supply that
study-design choice. No extra original attempt or changed repetition is proposed.

Adopting this proposal would still require a versioned route/sweep, complete-cell
collection and inference path for these exact 1,020 rows and51-unit/df 50 fixtures.
The current1,040-row implementation must remain preserved and cannot certify
the revised path. Worker imports passed, but full numerical worker execution,
cached real selection and complete resource/storage/runtime bounds remain
unqualified. Checkpoint-cohort/overlap review, final owner freeze and fresh
compute admission remain separate. No active configuration changed, and no
scientific case, model factory, training, recovery or recorder operation ran.
