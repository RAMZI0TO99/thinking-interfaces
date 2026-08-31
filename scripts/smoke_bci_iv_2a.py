"""Download and structurally inspect the configured BCI IV 2a subject."""

from __future__ import annotations

import json
import tomllib
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from data.bci_iv_2a import dataset_metadata, load_and_summarize_subject

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    with (ROOT / "configs" / "bci_iv_2a.toml").open("rb") as stream:
        config = tomllib.load(stream)

    dataset_config = config["dataset"]
    smoke_config = config["smoke_test"]
    metadata = dataset_metadata()
    expected_events = set(dataset_config["expected_events"])
    if set(metadata.events) != expected_events:
        raise ValueError(f"event mismatch: {metadata.events}")
    if len(metadata.subjects) != int(dataset_config["expected_subject_count"]):
        raise ValueError(f"subject count mismatch: {len(metadata.subjects)}")
    if not bool(smoke_config["download"]):
        print(json.dumps(asdict(metadata), indent=2))
        return 0

    summaries = []
    for subject in dataset_config["subjects"]:
        summary = load_and_summarize_subject(
            int(subject),
            ROOT,
            ROOT / dataset_config["raw_root"],
            force_update=bool(smoke_config["force_update"]),
        )
        if summary.sampling_rates_hz != (float(dataset_config["expected_sampling_rate_hz"]),):
            raise ValueError(f"sampling-rate mismatch: {summary.sampling_rates_hz}")
        channel_counts = Counter(summary.channel_types)
        expected_channel_counts = {
            "eeg": int(dataset_config["expected_eeg_channels"]),
            "eog": int(dataset_config["expected_eog_channels"]),
            "stim": int(dataset_config["expected_stim_channels"]),
        }
        if channel_counts != expected_channel_counts:
            raise ValueError(f"channel-type mismatch: {dict(channel_counts)}")
        summaries.append(summary.as_dict())
    print(json.dumps({"metadata": asdict(metadata), "subjects": summaries}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
