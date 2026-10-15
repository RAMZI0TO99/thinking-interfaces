# Accepted source publication; detached restore refusal

The v3 source Job `20261015T130336Z_b7198c366e` passed complete selection and
publication:5,253 observed Tensor/autograd backward and SGD calls,102 folds,
5,151 source updates,102 support updates and a fresh51-source winning fit.
It saved real full_v1 EEGNet weights:12,664 bytes, SHA256
`835681c4b38576e2560f836c562e425c5c2505a13a3252cb396edaf6cd9e585d`.
The selected state is `5fb284cea9c1e61dccfbdd96d4d92024973e30641d0ee078ed0be8cd930ddc5b`.

The detached public tensor checker completed with its1MiB weight limit. The
following full public restore factory called the generic store without an
explicit weight bound. Its reader requested4GiB+1 bytes for the tiny file and
raised `MemoryError` under the2GiB process cap. No detached qualification or
parent engineering success was accepted. The parent recorded one linked failure.

Parent `20261015T130307Z_6a387bb981` and detached
`20261015T130635Z_f5bb2b02b2` exited1; the source exited0. All three Jobs closed
empty and were freshly absent, with no cleanup/sampling errors. This is an
accepted source component followed by a failed worker transaction.

The [51-artifact manifest](manifest.json) preserves source/review/pins, all three
native receipts,33 passed checks, production claim/request/failure, source
qualification, complete histories, optimizer observations and publication
metadata. The [summary](summary.json) separates accepted source publication from
failed detached/parent completion. All620 source/context and five runtime pins,
4,719 source module hashes,213 input files and the saved weight hash were
rechecked. Arrays and weights are not copied. Scientific admission remains false;
original attempts remain0.

The next separately reviewed candidate uses the factory's existing supplied-store
API to delegate canonical restoration with a1MiB EEGNet read bound. It leaves
canonical code, model work and resource guards unchanged. The failed v3 case
and its accepted source component remain frozen.
