# LaBraM integration checklist

- [x] Official upstream `labram-base.pth` downloaded (96,612,769 bytes).
- [x] SHA-256 recorded: `7c50583826afac76c4ab18f43d958df40496c8229accc09ed6a227c9bb57c37c`.
- [x] Safe Braindecode safetensors conversion loaded without executing the
  upstream pickle payload.
- [x] Loaded backbone count measured: 5,819,936 parameters.
- [x] Plan's stated count, 5,822,770, checked and found not to match the current
  safe conversion; no parameter was added merely to force equality.
- [x] Temporal embeddings cropped from fifteen to four one-second patches for
  800-sample Profile B epochs while pretrained weights were retained.
- [x] Canonical electrode names mapped to the checkpoint's 128-position table,
  with the class token offset handled explicitly.
- [x] Real forward pass completed on two BCI IV 2a Profile B epochs shaped
  `(2, 22, 800)`.
- [x] Output contained 88 patch features of width 200 and finite four-class logits.
- [x] Partial fine-tuning depths 0, 4, 8, 12, and all are configurable.
- [x] Electrode masking operates by canonical name, never dataset index.
- [x] Appendix D's MMIDB and BCI IV-1 hours recorded, with MMIDB overlap disclosed.
- [x] Appendix K/Table 10 partial-tuning targets recorded separately from local results.
- [x] Complete Table 5 fine-tuning reference prepared in `configs/labram_paper_reference.toml`.

The count mismatch is an upstream/version discrepancy and is recorded in the
deviation log. It prevents the literal Week 0 count check from passing but does
not prevent verified loading or inference.
