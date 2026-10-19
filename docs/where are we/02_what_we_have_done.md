# Project briefing for our professor and team

Updated **19 October 2026**. Accepted experimental evidence currently ends at the **17 October 2026** checkpoint.

## The project in plain language

We are investigating how to recognise imagined movements from EEG brain signals when a new person provides only a few labelled examples. We use **LaBraM**, a pretrained EEG model, and ask whether **LoRA**, a small-parameter adaptation method, improves on training only the model's final classifier.

Our plan is to prepare trustworthy data, establish reference methods, validate the adaptation pipeline, run a controlled comparison, and report the findings. The immediate study compares classifier-only training, LoRA, full-model tuning and EEGNet on **51 participants, five training seeds and five examples per class: 1,020 evaluations**. Broader experiments and a usable realtime interface are later goals.

## What we have done, and how it went

| Work | What went well | What did not work or remains limited |
| --- | --- | --- |
| Data preparation | Prepared three public datasets covering 170 participants; reproduced their processed data exactly through the current pipeline. | Some acquisition chronology and the pretrained model's exposure to evaluation recordings remain uncertain. |
| Earlier benchmarking | Completed 5,950 validated records across seven variants and five seeds. EEGNet's mean balanced accuracy was 43.83% on BCI IV 2a, 65.69% on Cho2017 and 66.67% on MMIDB. | These experiments use an earlier protocol and do not answer the current LaBraM LoRA-versus-linear question. |
| Baseline and controls | Established an EEGNet reference and passed all 81 original controls. | The reference achieved 75.66% ROC-AUC versus the published 77.15%. Its process-based acceptance was retrospective, not exact score reproduction. |
| Pretrained model | Checked checkpoint correspondence and passed 119 CPU forward comparisons against the reference implementation. | This does not establish every training or hardware path, or prove independence from pretraining data. |
| Adaptation methods | Ran numerical probes and source-fold work for all four methods. Linear and EEGNet progressed further through source selection, saving and restoration. | Complete current workflows remain unfinished. Some attempts encountered memory, import, restoration or integration failures. |
| Earlier adaptation experiment | Ran a real-data EEGNet LoRA probe on one participant. | Balanced accuracy fell from 59.35% to 52.52%. This isolated earlier probe is not the main LaBraM comparison or evidence that LoRA always fails. |
| Latest linear worker | Restored, adapted and queried a model inside the checked recording workflow; verified process cleanup. | The inputs were synthetic, both predictions were wrong, and it produced no final scientific evaluation. |
| Collection and statistics | Built and tested record validation and the 51-participant paired analysis. | Much of this used fabricated records; the complete real study has not passed through it. |
| Realtime demonstration | Replay, buffering, decision gating and display worked on the laptop. | All outputs abstained; useful live brain control was not demonstrated. |

## What have we learned?

The project has produced substantial data and software infrastructure, but component success does not guarantee a complete experiment. The main engineering difficulty is connecting older trained model artifacts with current code while preserving trustworthy records. Several failures have successful successors; some integration gaps remain.

Two scientific matters also remain open: **checkpoint-specific pretraining exposure** and **approval of the final experiment specification**. Unknown exposure is not proof of leakage. The adopted evaluation population is subjects02–52; subject01 remains source-eligible. This was a retrospective scope amendment and must be disclosed.

## What comes next?

First, finish the model-restoration compatibility boundary, then complete the method and result pipeline. In parallel, settle scientific eligibility, final approval, asset restoration and execution cost. Then run the 1,020 evaluations and publish the participant-level analysis.

**Our current achievement is a substantial experimental foundation. Our central scientific question remains unanswered.** A trustworthy negative or inconclusive result would still complete the study correctly; wider research and live deployment would remain separate work.

Sources: [current handoff](../../HANDOFF.md), [adopted scope](../phase2/cho_51_target_amendment_adoption_20261013.md), [earlier benchmark reporting](../benchmark_reporting.md), [earlier adaptation probe](../deviation_log.md), [detailed assessment and evidence](../project_gap_assessment_20261017.md), [realtime limitations](../realtime_system.md).
