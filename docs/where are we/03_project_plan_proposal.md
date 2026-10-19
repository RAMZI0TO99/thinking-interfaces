# Project proposal: adapting an EEG model with very little labelled data

*A proposal-style explanation of the intended project, without progress updates or results.*

## 1. What problem will we study?

EEG records the brain's electrical activity. We want to recognise **imagined movements**, such as imagining movement of the left or right hand, from these signals.

The practical challenge is adapting a model to a new person using only a few labelled examples. Our goal is to investigate whether a pretrained EEG model can reduce this calibration burden while maintaining useful prediction performance.

## 2. What is our main idea?

We will use **LaBraM**, a model pretrained on EEG, as the starting point. Instead of retraining all its parameters, we will investigate **LoRA**: a method that learns small additional parameter matrices while keeping the pretrained backbone weights fixed.

Our main research question will be:

> With five labelled examples per class from a new person, does LoRA improve prediction performance compared with training only LaBraM's final classifier?

We will also examine the computational cost. Improvement is a hypothesis to test, not an assumed outcome.

## 3. Which methods will we compare?

| Method | What we will train | Purpose |
| --- | --- | --- |
| LaBraM linear | Only the final classifier; the pretrained backbone stays fixed. | Simple reference for using pretrained features. |
| LaBraM LoRA | Small added parameter matrices and the classifier. | Main proposed adaptation approach. |
| LaBraM full tuning | The full model. | Reference for adapting all parameters. |
| EEGNet | A smaller EEG-specific neural network under the study protocol. | Conventional reference method. |

## 4. How will the project proceed?

1. **Prepare the data.** Use public EEG datasets: BCI Competition IV 2a, Cho2017 and MMIDB. Standardize processing, check labels and signal quality, and define reproducible training/evaluation splits.
2. **Establish reference experiments.** Benchmark conventional methods so we understand the datasets and have meaningful comparison points.
3. **Verify the pretrained model.** Check model loading and behavior, and review whether its pretraining data could overlap with evaluation participants or recordings.
4. **Build the adaptation pipeline.** Connect source training, selection of training settings, new-person calibration, prediction and result recording. Check each method before running the complete study.
5. **Run the focused comparison.** Evaluate the four methods under the same declared calibration and query rules.
6. **Analyze and report.** Compare participant-level performance, uncertainty and computational cost. Report favorable, negative and inconclusive findings transparently.

## 5. What will the first focused experiment look like?

| Design choice | Plan |
| --- | --- |
| Dataset | Cho2017. |
| Evaluation population | 51 participants; the available source cohort contains 52. |
| Calibration data | Five labelled examples per class from each evaluation participant. |
| Methods and repetitions | Four methods, each repeated with five training seeds. |
| Total | **51 × 4 × 5 = 1,020 evaluations.** |
| Main performance measure | Balanced accuracy, which gives each class equal weight. |

For each evaluation participant, source training and selection of training settings will use other participants. The small calibration set will support adaptation; separate query trials will measure performance and will not guide training or model selection. We will use the same support/query partitions across methods, with the declared fixed support partition across training seeds.

We will average the five seeds within each participant before the main comparison. The primary question will be **LoRA versus linear** using a paired statistical test and a separate confidence interval. Full tuning and EEGNet will provide descriptive context. Before scientific execution, the final protocol, pretraining-exposure limitations and resource plan will need to be settled.

## 6. What will we deliver?

- A reproducible data-processing and evaluation pipeline.
- A controlled comparison of adaptation methods, including performance and resource costs.
- A research report explaining the findings, limitations and conditions under which the approach is useful.
- As a later extension, a realtime prototype that can abstain when confidence is insufficient. Live operation will require its own validation.

## A short explanation to say aloud

“We plan to test whether an existing EEG model can adapt to a new person with just five labelled examples per class. Our main approach is LoRA, which trains a small number of added parameters. We will compare it with simpler and more expensive alternatives, evaluate performance fairly across participants, and report both prediction quality and computational cost.”

Design references: [focused study scope](../phase2/cho_51_target_amendment_adoption_20261013.md), [method and analysis choices](../phase2/cho_design_decisions_20261012.md), [support-partition design](../phase2/decision_analysis.md).
