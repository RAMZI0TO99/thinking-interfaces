"""Read-only first-tranche Cho case inputs, before source selection or a cell claim."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

from core.config import canonical_config_json, config_digest, load_toml
from evaluation.phase2_cho_60hz_inventory import load_cho_60hz_assets
from evaluation.phase2_profile_binding import CHO_CLASSES, ChoProfileAssets60Hz
from evaluation.phase2_protocol import (
    TrialCatalog,
    nested_episode,
    require_digest,
    source_selection,
)
from evaluation.phase2_records import envelope
from evaluation.phase2_runner import CasePlan
from scripts.audit_phase2_protocol import file_digest, inside, read_catalog, validate_protocol

SELECTED_METHODS = ("labram_linear", "labram_lora", "labram_full", "eegnet")
SELECTED_SEEDS = (11, 23, 37, 53, 71)
SELECTED_SHOTS = 5
CHO_SUBJECTS = tuple(f"subject_{index:02d}" for index in range(1, 53))
_PROFILE_A = "cho_profile_a"
_PROFILE_B_60HZ = "cho_profile_b_60hz_v1"


@dataclass(frozen=True, slots=True)
class ChoCaseInputPins:
    """Reviewed input-byte pins; no source or scientific-freeze approval implied."""

    protocol_config_sha256: str
    threshold_config_sha256: str
    cohort_audit_sha256: str
    variant_config_sha256: str

    def __post_init__(self) -> None:
        for name in self.__dataclass_fields__:
            require_digest(getattr(self, name), name)


@dataclass(frozen=True, slots=True)
class ChoCaseInputs:
    """One planned case with fresh record copies and method-correct asset map."""

    plan: CasePlan
    protocol_config: dict[str, Any]
    catalogs: tuple[TrialCatalog, ...]
    selection_record: dict[str, Any]
    episode_record: dict[str, Any]
    assets: Mapping[str, ChoProfileAssets60Hz] | Mapping[str, str]
    profile: str


@dataclass(frozen=True, slots=True)
class ChoFirstTrancheRoute:
    """The fixed 1,040-case first-tranche inputs; model fitting is separate."""

    plans: tuple[CasePlan, ...]
    catalogs: tuple[TrialCatalog, ...]
    labram_assets: Mapping[str, ChoProfileAssets60Hz]
    protocol_config_json: str
    selection_records_json: Mapping[str, str]
    episode_records_json: Mapping[str, str]

    def inputs_for(self, plan: CasePlan) -> ChoCaseInputs:
        if plan not in self.plans:
            raise ValueError("case is outside the selected Cho first tranche")
        profile = _PROFILE_A if plan.method == "eegnet" else _PROFILE_B_60HZ
        assets: Mapping[str, ChoProfileAssets60Hz] | Mapping[str, str] = (
            MappingProxyType({}) if plan.method == "eegnet" else self.labram_assets
        )
        return ChoCaseInputs(
            plan,
            json.loads(self.protocol_config_json),
            self.catalogs,
            json.loads(self.selection_records_json[plan.target_subject]),
            json.loads(self.episode_records_json[plan.target_subject]),
            assets,
            profile,
        )


def _pinned_file(path: Path, expected_sha256: str, name: str) -> None:
    if not path.is_file() or path.resolve() != path:
        raise ValueError(f"{name} is missing or aliases another path")
    if file_digest(path) != expected_sha256:
        raise ValueError(f"{name} bytes differ from the reviewed pin")


def prepare_cho_first_tranche(root: Path, *, pins: ChoCaseInputPins) -> ChoFirstTrancheRoute:
    """Rebuild typed A catalogs, rehash all B pairs, then enumerate case inputs.

    This does not construct a model, select a candidate, admit compute, or
    publish an evaluation cell. The caller must still resolve selector evidence,
    method settings and checkpoint identity before a case can be claimed.
    """
    root = root.resolve()
    protocol_path = root / "configs/phase2/protocol.toml"
    _pinned_file(protocol_path, pins.protocol_config_sha256, "Phase II protocol config")
    config: dict[str, Any] = load_toml(protocol_path)
    shots = validate_protocol(config)
    cho = config["datasets"]["cho2017"]
    if (
        cho.get("artifact_directory") != "data/processed/cho2017/profile_a"
        or tuple(cho.get("classes", ())) != CHO_CLASSES
        or cho.get("expected_subjects") != 52
        or tuple(config["protocol"].get("model_seeds", ())) != SELECTED_SEEDS
        or SELECTED_SHOTS not in shots
    ):
        raise ValueError("Cho protocol differs from the selected first-tranche roster")
    threshold_relative = config["preparation"]["threshold_config"]
    threshold_lexical = root / threshold_relative
    threshold_path = inside(root, threshold_relative)
    if threshold_path != threshold_lexical:
        raise ValueError("frozen threshold path aliases another file")
    _pinned_file(threshold_path, pins.threshold_config_sha256, "frozen threshold config")
    thresholds: dict[str, Any] = load_toml(threshold_path)
    threshold: float = thresholds["datasets"]["cho2017"][
        "artifact_threshold_volts"
    ]
    preprocessing_sha256 = config_digest({
        "profile_identity": config["preparation"]["profile_identity"],
        "threshold_config_sha256": pins.threshold_config_sha256,
        "dataset": "cho2017",
        "threshold": threshold,
    })
    catalogs_list = []
    for subject in CHO_SUBJECTS:
        artifact_lexical = root / f"data/processed/cho2017/profile_a/{subject}.npz"
        artifact = inside(root, f"data/processed/cho2017/profile_a/{subject}.npz")
        if artifact != artifact_lexical or not artifact.is_file():
            raise ValueError(f"Cho Profile A artifact is missing or aliases: {subject}")
        catalog = read_catalog(
            artifact,
            dataset="cho2017",
            classes=CHO_CLASSES,
            threshold=threshold,
            preprocessing_sha256=preprocessing_sha256,
        )[0]
        catalogs_list.append(catalog)
    catalogs = tuple(catalogs_list)
    if tuple(catalog.subject for catalog in catalogs) != CHO_SUBJECTS:
        raise ValueError("Cho Profile A catalog roster differs")
    assets = load_cho_60hz_assets(
        root,
        catalogs,
        cohort_audit_sha256=pins.cohort_audit_sha256,
        variant_config_sha256=pins.variant_config_sha256,
    )
    if (
        set(assets) != set(CHO_SUBJECTS)
        or any(
            not isinstance(asset, ChoProfileAssets60Hz)
            or asset.variant_config_sha256 != pins.variant_config_sha256
            for asset in assets.values()
        )
    ):
        raise ValueError("complete pinned Cho 60 Hz asset inventory is required")
    protocol_sha256 = config_digest(config)
    selections = MappingProxyType({
        subject: canonical_config_json(envelope(
            "source_selection",
            asdict(source_selection(catalogs, target=subject)),
        ))
        for subject in CHO_SUBJECTS
    })
    catalog_by_subject = {catalog.subject: catalog for catalog in catalogs}
    episodes = MappingProxyType({
        subject: canonical_config_json(envelope(
            "episode_manifest",
            nested_episode(
                catalog_by_subject[subject], shots=shots,
                protocol_sha256=protocol_sha256,
            ).payload(),
        ))
        for subject in CHO_SUBJECTS
    })
    plans = tuple(
        CasePlan("cho2017", subject, method, SELECTED_SHOTS, seed, 1)
        for subject in CHO_SUBJECTS
        for method in SELECTED_METHODS
        for seed in SELECTED_SEEDS
    )
    if len(plans) != 1040 or len({plan.case_id for plan in plans}) != 1040:
        raise ValueError("selected Cho case plan is incomplete or duplicated")
    _pinned_file(protocol_path, pins.protocol_config_sha256, "Phase II protocol config")
    _pinned_file(threshold_path, pins.threshold_config_sha256, "frozen threshold config")
    return ChoFirstTrancheRoute(
        plans,
        catalogs,
        assets,
        canonical_config_json(config),
        selections,
        episodes,
    )
