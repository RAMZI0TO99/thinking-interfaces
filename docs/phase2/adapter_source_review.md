# Source-trained adapter integration

9 September 2026, milestone 23. The bounded BCI LaBraM selector now fits post-block
adapters on permitted source subjects and carries their learned weights into
validation. A new continuation runner also supports the fixed outer-target role.
This is engineering integration; source-trained prompt generators remain next.

## Contract and implementation

`adaptation.labram_adapter_trained` adds `AdapterSourceSettings`,
`AdapterContinuationSettings`, `AdapterSourceCandidate` and
`TrainedAdapterManifestRunner`. The existing `BCILaBraMSourceSelector` accepts
adapter candidates alongside plain tuning and LoRA candidates. Each candidate
search still evaluates one method; mixed-method rosters are rejected.

Source settings explicitly declare target blocks, bottleneck width, adapter seed,
head policy, source steps per subject, batch size and learning rate. Continuation
settings contain the independent support head policy, steps, learning rate and
query batch size. They contain no replacement adapter dimensions or initialization
seed. The supplied backbone remains pinned and the selector creates a common
seeded head. Each source fit installs freshly seeded adapters into its owned
initial model, then trains those adapters and the optionally enabled head.

The method uses the established serial residual adapter after a complete LaBraM
block: `h + up(GELU(down(h)))`. Up-projection weights and bias start at zero.
Original block/backbone parameters and normalization buffers remain frozen.
All modules stay in evaluation mode, without adapter dropout or extra normalization.
The source loop retains fresh SGD, fixed steps, finite-loss/gradient checks,
permitted-source sampling and exact trial/state histories from the existing selector.

Source data is the audited Profile A-retained trial inventory joined to unchanged
Profile B inputs: 22 BCI channels, 800 samples at 200 Hz, stored units of 0.1 mV
and no extra scale. Inner fitting excludes both outer and inner subjects; the final
fit excludes the outer subject. All retained trials of permitted source subjects
are eligible training data. The inner subject retains its nested support and fixed
query partition. No outer-target signals or outcomes enter source selection.

## Continuation and structural checks

The new runner checks the trained state's supplied hash and exact adapter target
inventory, wrapper type, installed original block, bottleneck dimensions, linear
weights/biases, GELU behavior and zero-dropout configuration. It rejects hybrid
parametrizations and unexpected adapter parameters/buffers. Activation/dropout
settings are checked explicitly because they are not fully represented by tensor
state hashes. Parameters must be finite CPU float32 values.

An owned plain copy unwraps adapters solely for the existing cohort/architecture
admission checks. Prediction always uses a separate copy with learned adapters
intact. The original caller is neither unwrapped nor modified. Support continuation
reuses `adapt_labram_adapter_support`, whose existing behavior clones learned
components and creates fresh SGD. The new wrapper checks the declared parameter
mask and verifies that frozen tensors remain exact. It never injects or resets
adapters during continuation.

The source and support head policies are independent. Only selected support
signals/labels enter adaptation. All common queries run afterward without updates;
tensor state and adapter structure must remain unchanged. Both fixed outer-target
and inner-validation roles use the existing audited episode binder. An inner
runner cannot predict the outer target. Predictions record the source state,
source-settings hash, support mask/losses, adapted state, binding and explicit
learned-component continuation policy. The general runner does not authenticate
arbitrary prior training history; its history-verification flag remains false.

## Selection and evidence

The selector completes every candidate's eight inner folds, verifies that each
continuation starts from its corresponding source fit, and ranks exact rational
subject-averaged balanced accuracy. Declared candidate order breaks ties. A failed
fold returns no winner; a single diagnostic fold remains incomplete. The winner
gets a fresh eight-source fit from the declared initialization, rather than an
inner-fit model. Step ceilings, source/query batch limits and source/runtime
identity checks are unchanged.

Evidence uses immutable engineering envelopes and the existing atomic no-clobber
writer. A saved trained model requires reconstruction of the same adapter wrappers
and dimensions before strict safetensors loading. The tensor checkpoint and source
settings together describe that structure. Optimizer resume, scientific history
certification, complete environment validation and scientific checkpoint/cell
publication remain separate work. This path does not admit heavy training or
replace the existing resource guards.

## Verification

The focused suite passed **8 tests / 20 subtests**. It independently reconstructs
source batches from Profile B rows and replays all seven source updates, reproducing
every state hash. Down/up projections learn while frozen tensors and caller
template/RNG remain unchanged. Continuation is tested under all four source/support
head policies, with injection patched to fail and a first-forward state observation
that must equal the trained source exactly.

Other checks cover complete selection with unreadable outer A/B artifacts; both
roles at one/five/ten/twenty shots; query changes leaving the support fit unchanged;
altered activation, dropout, width or block structure; query tensor mutation; bad
metadata, roles and pins; nonfinite source loss; safe wrapper reconstruction;
exact repeat and immutable incomplete records. Existing plain and LoRA paths are
covered by the full regression suite.

The real-data check declares two candidates before selection: last-block width-four
adapters, adapter seed 11, head/sampling seed 23, source SGD rates 0.001 and 0.002,
one two-trial source step per subject, one-shot support SGD at 0.0001 and query
batches of eight. Main selection trains the head and has a 136-gradient-step ceiling.
Separate diagnostics freeze the support head only and both source/support heads.
These are bounded engineering settings, not scientific defaults or convergence claims.

Real checks passed two adapter candidates across all eight inner subjects: 16
folds and 7,924 common-query predictions. Each source fit sampled 14 trials in
seven steps; the fresh final fit sampled 16 trials across eight sources. The
first fold repeated exactly, and both frozen-head diagnostics passed. Width-four
adapters train 1,804 parameters, plus 804 head parameters when enabled (2,608 total).
Including diagnostics and repeat, work totaled **141 source steps and 19 support
steps**, with **zero outer-target predictions**. Safe checkpoint reconstruction,
caller template/RNG and original input/audit hash preservation all passed.

Full lint and strict types pass. The exact-source suite passes **505 tests / 830
subtests**, with four existing warnings; raw results are retained in the receipt.
Evidence directory: `runs/phase2/adapter_source_checks/20260909_step23/`.
Current source fingerprint:
`a416fe551ecfd2924d31987619690a3a30b2b02ef154b7872632e8ed35754561`.
The source selector is the only pre-existing source file changed. Its reviewed
diff adds adapter handling; the trained-adapter module/tests are new. Other prior
source/config/test files and historical documentation prefixes are preserved,
and prior quality status is saved.

## Next work and unchanged limits

Next is the source-trained support-prompt generator, preserving learned generator
weights while rebuilding support conditioning for each validation subject. Other
method selection, broader dataset coverage, scientific run/history recording,
the measured P3 pilot and scientific freeze remain open. P2 is still partial.
The RAM-dependent control refresh stays deferred. No guard, method configuration,
scientific comparison or gate changed, and no full scientific experiment ran.
