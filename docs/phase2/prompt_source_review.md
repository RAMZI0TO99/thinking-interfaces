# Source-trained support-prompt integration

16 September 2026, milestone 24. The bounded BCI LaBraM selector now fits the
class-conditioned support-prompt generator on permitted source subjects and
carries its learned weights into validation. A new continuation runner also
supports the fixed outer-target role. This is engineering integration; the
remaining selection paths, scientific recording and the measured pilot stay open.

## Contract and implementation

`adaptation.labram_prompt_trained` adds `PromptSourceSettings`,
`PromptContinuationSettings`, `PromptSourceCandidate` and
`TrainedPromptManifestRunner`. The existing `BCILaBraMSourceSelector` accepts
prompt candidates alongside plain tuning, LoRA and adapter candidates. Each
candidate search still evaluates one method; mixed-method rosters are rejected.

Source settings explicitly declare prompt tokens, hidden width, generator seed,
head policy, source steps per subject, class-balanced support/query shots per
class and learning rate. The fixed four-class episode size
`4 * (support + query) shots` must stay within the existing eight-trial batch
ceiling. Continuation settings contain the independent support head policy,
steps, learning rate and query batch size; they carry no replacement generator
dimensions or seed. The supplied backbone remains pinned and the selector creates
the common seeded head exactly as for the other methods. Each source fit installs
a freshly seeded generator beside an owned frozen copy of that initialization,
then trains the generator and the optionally enabled head.

Unlike the LoRA/adapter paths, whose components live inside the classifier, the
trained prompt artifact is a `TrainedPromptSourceModel` container that owns the
plain frozen classifier and the generator together; its state dictionary pins
both for digest and checkpoint identity. Source fitting is episodic: each step
draws distinct class-stratified support/query trials from one subject's retained
pool using the selector's isolated sampling generator, conditions the generator
on batch-one frozen unprompted support features (memoized per subject, identical
by construction to the episode wrapper's values), and takes cross entropy only
on that step's query trials. Prompts enter the verified token path after
position/time assembly and persist through every block. Histories record the
exact support/query trial IDs, per-class wrap counts and state hashes.

Source data is the audited Profile A-retained trial inventory joined to unchanged
Profile B inputs: 22 BCI channels, 800 samples at 200 Hz, stored units of 0.1 mV
and no extra scale. Inner fitting excludes both outer and inner subjects; the
final fit excludes the outer subject. No outer-target signals or outcomes enter
source selection, and the inner subject retains its nested support and fixed
query partition.

## Continuation and structural checks

The new runner checks the trained container's supplied hash, the plain
neural-tokenizer CLS-head classifier (rejecting adapter hybrids and
parametrizations), and the generator's exact two-layer GELU structure, input/
output dimensions, weight shapes, bias shapes, parameter inventory and absence
of buffers. Activation semantics are checked explicitly because they are not
fully represented by tensor state hashes. Parameters must be finite CPU float32
values.

Support continuation reuses `adapt_labram_prompt_support`, whose existing
behavior deep-copies both components, rebuilds the class conditioning from the
held-out subject's permitted support and creates fresh SGD. The new wrapper
asserts the passed generator is the learned one, checks the declared parameter
mask and verifies that frozen classifier tensors remain exact. It never
reinitializes the generator during continuation.

The source and support head policies are independent. Only selected support
signals/labels enter adaptation. All common queries run afterward without
updates; tensor state and generator structure must remain unchanged. Both fixed
outer-target and inner-validation roles use the existing audited episode binder.
An inner runner cannot predict the outer target. Predictions record the source
state, source-settings hash, support mask/losses, adapted state, binding and the
explicit learned-generator continuation policy. The runner does not authenticate
arbitrary prior training history; its history-verification flag remains false.

## Selection and evidence

The selector completes every candidate's eight inner folds, verifies that each
continuation starts from its corresponding source fit, and ranks exact rational
subject-averaged balanced accuracy. Declared candidate order breaks ties. A
failed fold returns no winner; a single diagnostic fold remains incomplete. The
winner gets a fresh eight-source fit from the declared initialization rather than
an inner-fit model. Step ceilings, source/query batch limits and source/runtime
identity checks are unchanged.

Evidence uses immutable engineering envelopes and the existing atomic no-clobber
writer. A saved trained container requires reconstruction of the same classifier
and generator structure before strict safetensors loading; the tensor checkpoint
and source settings together describe that structure. Optimizer resume,
scientific history certification, complete environment validation and scientific
checkpoint/cell publication remain separate work. This path does not admit heavy
training or replace the existing resource guards.

## Verification

The focused suite passed **8 tests / 19 subtests**. It independently replays every
source episode from the Profile B rows, reproducing each step's state hash and
the final fitted digest exactly, with class-balanced support/query coverage and
within-step support/query disjointness checked from the recorded IDs.
Continuation is tested under all four source/support head policy combinations,
asserting the learned generator instance is passed through unchanged, frozen
classifier tensors stay exact and only the declared mask may change.

Other checks cover complete selection with unreadable outer A/B artifacts; both
runner roles at one/five/ten/twenty shots; query changes leaving the support fit
unchanged; altered activation, network structure, width, class count or hybrid
classifier; bad metadata, mixed and duplicate rosters, roles and pins; admission
ceilings; nonfinite source loss; safe container reconstruction from safetensors;
exact repeat and immutable incomplete records. Existing plain, LoRA and adapter
paths are covered by the full regression suite.

The real-data check declares two candidates before selection: two-token,
hidden-eight generators, generator seed 11, head/sampling seed 23, source SGD
rates 0.001 and 0.002, one class-balanced one-plus-one-shot episodic source step
per subject (eight trials per step), one-shot support SGD at 0.0001 and query
batches of eight. Main selection trains the head and has a 136-gradient-step
ceiling. Separate diagnostics freeze the support head only and both source/
support heads. These are bounded engineering settings, not scientific defaults
or convergence claims.

Real checks passed two prompt candidates across all eight inner subjects: 16
folds and 7,924 common-query predictions. Each source fit sampled 56 trials in
seven episodic steps; the fresh final fit sampled 64 trials across eight sources.
The first fold repeated exactly, and both frozen-head diagnostics passed. The
generator trains 10,008 parameters, plus 804 head parameters when enabled
(10,812 total). Including diagnostics and repeat, work totaled **141 source steps
and 19 support steps**, with **zero outer-target predictions**. Safe checkpoint
reconstruction, caller template/RNG and original input/audit hash preservation
all passed.

Full lint and strict types pass. The exact-source suite passes **513 tests / 849
subtests**, with the same four existing warnings; raw results are retained in the
receipt. Evidence directory:
`runs/phase2/prompt_source_checks/20260916_step24/`.
Current source fingerprint:
`79de610c49e2e6eab7fc843ddb3f2cf939d4f1a7406195b757602b77bd8c12a7`.
Only the source selector changed among pre-existing source/config/test files;
the trained-prompt module/tests are new. Other prior source/config/test files
and historical documentation prefixes are preserved, and prior quality status is
saved.

## Next work and unchanged limits

With plain, LoRA, adapter and prompt candidates all continuing learned state
through validation, the bounded BCI LaBraM selection roster is method-complete
at the engineering level. Next are the remaining method selection paths (EEGNet
already exists; EA-tangent and TCPL source-fit paths do not), broader dataset
coverage (Cho2017/MMIDB), and the scientific run/history recorder that the P3
pilot requires. The measured pilot, scientific freeze and full experiment
execution remain pending. P2 is still partial. The RAM-dependent control refresh
stays deferred. No guard, method configuration, scientific comparison or gate
changed, and no full scientific experiment ran.
