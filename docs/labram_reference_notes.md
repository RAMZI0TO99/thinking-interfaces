# Encoder reference notes

Verified visually against paper pages 17, 21 and 22 on 2026-08-31. Local source:
`runs/references/labram_iclr2024.pdf`; SHA-256 is recorded in
`configs/labram_paper_reference.toml`. These are published references, not locally
reproduced scores.

Appendix D lists MMIDB as 47.3 hours and BCI Competition IV-1 as 8.21 hours within
2534.78 pretraining hours. IV-1 is not IV-2a. MMIDB therefore requires an explicit
pretraining-overlap disclosure in future pretrained-encoder evaluations.
[Paper, Appendix D](https://proceedings.iclr.cc/paper_files/paper/2024/file/47393e8594c82ce8fd83adc672cf9872-Paper-Conference.pdf).

| Fine-tuned part | TUAB balanced accuracy | TUEV balanced accuracy |
|---|---:|---:|
| All parameters | 0.8140 ± 0.0019 | 0.6409 ± 0.0065 |
| Last 12 blocks | 0.8141 ± 0.0022 | 0.6541 ± 0.0250 |
| Last 8 blocks | 0.8134 ± 0.0022 | 0.6611 ± 0.0152 |
| Last 4 blocks | 0.8074 ± 0.0032 | 0.6188 ± 0.0118 |
| Linear probe | 0.7954 ± 0.0059 | 0.3461 ± 0.0225 |

These Table 10 targets distinguish all parameters from transformer-only tuning;
Appendix K sets linear-probe weight decay to zero.
[Paper, Appendix K/Table 10](https://proceedings.iclr.cc/paper_files/paper/2024/file/47393e8594c82ce8fd83adc672cf9872-Paper-Conference.pdf).

The prepared reference config includes Table 5's effective batch 512, AdamW,
cosine learning-rate schedule, 5e-4 peak/1e-6 minimum, beta values, label smoothing,
and Base-model settings. The existing readiness config's shared values agree.
The official example uses eight processes with batch 64 each; this is not a
single-laptop training claim.
[Official fine-tuning example](https://github.com/935963004/LaBraM#4-fine-tune-on-downstream-tasks).

TUAB/TUEV data-use access is still absent. Reproduction and selection of any
hardware-specific accumulation scheme remain Phase II/external work, not hidden
Phase I successes.
