# Where are we in the project?

Updated **19 October 2026**, using the latest accepted checkpoint from **17 October 2026**.

## 1. What is the plan?

Find out whether a pretrained EEG model can recognise imagined movements using very little labelled data from a new person. EEG measures the brain's electrical activity.

The main question is whether **LoRA**, which adapts a small number of model parameters, works better than training only the final classifier of the pretrained **LaBraM** model.

The current study compares four methods: LaBraM with classifier-only training, LaBraM with LoRA, LaBraM with full tuning, and EEGNet as a reference. It uses **51 Cho2017 participants × four methods × five training seeds = 1,020 evaluations**, with five labelled examples per class. Seeds repeat training with different randomness; they are not extra participants.

## 2. Where are we on that plan?

| Stage | Position |
| --- | --- |
| Prepare and check the data | Completed locally. |
| Establish earlier benchmarks and reference methods | Completed, with documented limitations. |
| Implement and connect the adaptation pipeline | **Current stage:** components work, but complete integration remains. Linear is furthest along. |
| Run the main study | Pending: **0/1,020 accepted final scientific evaluations**. |
| Analyze and write the scientific findings | Pending the main study. |

## 3. What are the results so far?

- **Earlier experiments:** 170 participants across three public datasets; 5,950 validated benchmark records. For example, EEGNet's earlier Cho2017 mean balanced accuracy was **65.69%**. This is a different protocol from the planned main study.
- **Reference reproduction:** EEGNet achieved **75.66% ROC-AUC**, compared with the published **77.15%**. Its procedure was accepted as a reference; exact numerical reproduction was not established.
- **Engineering:** all four methods have executed component checks. The latest linear worker successfully restored a model, updated its classifier and made predictions. Its 38 focused checks passed separately.
- **Latest predictions:** **0/2 correct on synthetic inputs**. This tiny artificial test verifies execution, not real-data performance. We have not yet shown a LaBraM LoRA advantage.

## 4. How much is left?

Four substantial milestones remain:

1. Finish connecting model restoration, all four methods, recording and analysis into one validated workflow.
2. Resolve the pretrained checkpoint's data-exposure evidence or claim limits, obtain final experiment approval, and establish realistic runtime and asset-restoration plans.
3. Run all **1,020** eligible real-data evaluations.
4. Analyze the participant-level comparison and write the report, including negative findings and limitations.

**The foundation is substantial, but most of the main scientific validation remains. We need integration and scientific decisions as well as results.** There is no reliable completion percentage or finish date yet; complete-case runtime measurements are still needed. Wider dataset comparisons and useful realtime operation are separate later goals.

Sources: [current handoff](../../HANDOFF.md), [adopted study](../phase2/cho_51_target_amendment_adoption_20261013.md), [earlier benchmark reporting](../benchmark_reporting.md), [latest numerical result](../phase2/cho51_linear_numerical_worker_qualification_20261017.md), [detailed gaps](../project_gap_assessment_20261017.md).
