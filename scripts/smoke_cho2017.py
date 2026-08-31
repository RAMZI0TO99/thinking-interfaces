"""Download, load, and structurally verify one Cho2017 subject."""

from __future__ import annotations

import argparse
import json
import tomllib
from pathlib import Path

from data.cho2017 import load_and_summarize_subject

ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--subject", type=int)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    with (ROOT / "configs" / "cho2017.toml").open("rb") as stream:
        config = tomllib.load(stream)
    dataset = config["dataset"]
    smoke = config["smoke_test"]
    subject = int(args.subject if args.subject is not None else smoke["subject"])
    summary = load_and_summarize_subject(
        subject,
        ROOT,
        ROOT / dataset["raw_root"],
        force_update=bool(smoke["force_update"]),
    )
    print(json.dumps(summary.as_dict(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
