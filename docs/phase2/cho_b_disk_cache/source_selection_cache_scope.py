"""One-use operational Cho selector adapter with explicit cache lifetimes.

The production selector and its evidence/SGD routines remain unchanged. Only
owned instance attributes are temporarily replaced. Progress is written outside
scientific evidence, and the selected model leaves with its original forward.
"""
import hashlib
import json
import time
from adaptation.labram_source import BCILaBraMSourceSelector
from evaluation.phase2_cho_b_input_snapshot import _ChoBInputSnapshot
from disk_backed_snapshot import DiskBackedChoSnapshot
from frozen_feature_cache import FrozenFeatureCache
from owned_cache_cleanup import owned_output, register_owned_cache

_MISSING = object()

class SourceSelectionCacheScope:
    def __init__(self, selector, *, owner_directory, worker_sha256, event_sink):
        if type(selector) is not BCILaBraMSourceSelector or selector._source_device != "cpu" or type(selector._cho_b_inputs) is not _ChoBInputSnapshot:
            raise ValueError("source cache scope requires the pinned CPU Cho B selector")
        if "forward" in selector._initial.__dict__:
            raise ValueError("source cache scope requires an unwrapped initialization")
        if selector._cho_b_inputs._entries or selector._cho_b_inputs._retained_bytes:
            raise ValueError("source cache scope requires no outstanding resident episodes")
        if not callable(event_sink):
            raise ValueError("source cache scope requires an explicit progress sink")
        self.owner_directory = owned_output(owner_directory)
        self.selector = selector
        self.worker_sha256 = worker_sha256
        self.event_sink = event_sink
        self.used = False
        self.sequence = 0
        self.started = None
        self.completed_fits = 0
        self.completed_folds = 0
        self.cache = None
        self.features = None
        self.cleanup_completed = False

    def emit(self, stage, **fields):
        self.sequence += 1
        self.event_sink(dict(sequence=self.sequence, elapsed_seconds=time.perf_counter() - self.started, stage=stage, completed_fits=self.completed_fits, completed_folds=self.completed_folds, **fields))

    def run_selection(self):
        if self.used:
            raise ValueError("source cache scope is one-use")
        self.used = True
        self.started = time.perf_counter()
        selector = self.selector
        selector._check_context()
        original_inputs = selector._cho_b_inputs
        original_retained_limit = original_inputs._maximum_retained_bytes
        namespace = hashlib.sha256(json.dumps(selector.contract, sort_keys=True).encode()).hexdigest()
        features = self.features = FrozenFeatureCache(namespace)
        cache = self.cache = DiskBackedChoSnapshot(selector._root, selector._config, tuple(original_inputs._catalogs.values()), original_inputs._assets, cache_directory=self.owner_directory / "backing", maximum_retained_bytes=min(original_inputs._maximum_retained_bytes, 512 * 1024**2))
        # Preserve every existing original provenance pin, rather than replacing
        # previously observed inputs with a new provenance history.
        cache._snapshot = original_inputs
        try:
            register_owned_cache(self.owner_directory, cache.directory, maximum_bytes=cache._maximum_disk_bytes, worker_sha256=self.worker_sha256)
        except BaseException:
            cache.close()
            raise
        previous = {name: selector.__dict__.get(name, _MISSING) for name in ("_fit", "_fold")}
        original_fit, original_fold = selector._fit, selector._fold
        def fit(*args, **kwargs):
            candidate = args[0] if args else kwargs["candidate"]
            validation = args[1] if len(args) > 1 else kwargs.get("validation_subject")
            began = time.perf_counter()
            self.emit("fit_started", candidate=candidate.name, validation_subject=validation)
            value = original_fit(*args, **kwargs)
            self.completed_fits += 1
            self.emit("fit_completed", candidate=candidate.name, validation_subject=validation, duration_seconds=time.perf_counter() - began)
            return value
        def fold(*args, **kwargs):
            candidate = args[0] if args else kwargs["candidate"]
            validation = args[1] if len(args) > 1 else kwargs["validation_subject"]
            began = time.perf_counter()
            self.emit("fold_started", candidate=candidate.name, validation_subject=validation)
            value = original_fold(*args, **kwargs)
            self.completed_folds += 1
            self.emit("fold_completed", candidate=candidate.name, validation_subject=validation, duration_seconds=time.perf_counter() - began)
            return value
        selected = None
        failure = None
        try:
            original_inputs._maximum_retained_bytes = min(original_retained_limit, 512 * 1024**2)
            selector._cho_b_inputs = cache
            selector._fit, selector._fold = fit, fold
            features.install(selector._initial)
            features.active = True
            self.emit("source_scope_started", source_subjects=list(selector._selection.source_subjects), feature_budget_bytes=features.maximum_bytes, disk_budget_bytes=cache._maximum_disk_bytes)
            selected = selector.run_selection()
            self.emit("selection_completed")
            return selected
        except BaseException as error:
            failure = error
            raise
        finally:
            features.active = False
            features.clear()
            features.remove(selector._initial)
            if selected is not None:
                features.remove(selected.source)
            selector._cho_b_inputs = original_inputs
            original_inputs._maximum_retained_bytes = original_retained_limit
            for name, value in previous.items():
                if value is _MISSING:
                    selector.__dict__.pop(name, None)
                else:
                    setattr(selector, name, value)
            try:
                cache.close()
                self.cleanup_completed = True
            except Exception as cleanup_error:
                # A failing fit's traceback may still own a borrowed mapping.
                # Its registered directory is cleaned only after Job release.
                if failure is None:
                    raise
                failure.add_note("private cache cleanup deferred to owned guard: " + str(cleanup_error))
            try:
                self.emit("source_scope_closed", cleanup_completed=self.cleanup_completed, selection_failed=failure is not None)
            except Exception as progress_error:
                if failure is None:
                    raise
                failure.add_note("source-scope close progress could not be written: " + str(progress_error))
