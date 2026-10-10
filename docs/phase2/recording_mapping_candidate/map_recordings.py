"""Compare loader-defined raw filenames and checksums, without signal decoding."""
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from datetime import UTC, datetime
import urllib.request

PKG = Path(__file__).resolve().parent
sys.path.insert(0, str(PKG))
import metadata_reader as reader

PROVIDER_URL = "https://physionet.org/files/eegmmidb/1.0.0/SHA256SUMS.txt"
INVENTORY = "runs/coordination/evaluation_identity_inventory_20261010_v1/candidate/attempt_001/inventory.json"
LOCAL_REGISTRY = ".venv/Lib/site-packages/mne/data/eegbci_checksums.txt"


def checksum_registry(data, *, provider):
    if len(data) > 1024**2:
        raise ValueError("checksum metadata exceeds1MiB")
    values = {}
    for line in data.decode("utf-8", errors="strict").splitlines():
        if not line.strip():
            continue
        pieces = line.split()
        if len(pieces) != 2:
            raise ValueError("two-field checksum metadata required")
        digest, name = pieces if provider else reversed(pieces)
        if not re.fullmatch(r"[a-f0-9]{64}", digest) or name.startswith(("/", "\\")) or ".." in name.split("/") or "\\" in name or name in values:
            raise ValueError("invalid/duplicate checksum path or digest")
        values[name] = digest
    if not values:
        raise ValueError("empty checksum registry")
    return values


def map_subject(dataset, subject):
    number = subject["project_subject_number"]
    limits, digits = {"bci_iv_2a": 9, "cho2017": 52, "mmidb": 109}[dataset], 3 if dataset == "mmidb" else 2
    expected_id = f"{dataset}/subject_{number:0{digits}d}"
    if type(number) is not int or not 1 <= number <= limits or subject["project_subject_id"] != expected_id:
        raise ValueError("fixed project subject identity required")
    groups = subject["project_recording_groups"]
    pairs = [(group["session"], group["run"]) for group in groups]
    if len(pairs) != len(set(pairs)):
        raise ValueError("duplicate project recording group")
    if dataset == "mmidb":
        expected = {("0", run) for run in ("04", "08", "12")}
        paths = {pair: f"data/raw/mmidb/MNE-eegbci-data/files/eegmmidb/1.0.0/S{number:03d}/S{number:03d}R{pair[1]}.edf" for pair in expected}
    elif dataset == "bci_iv_2a":
        expected = {(session, str(run)) for session in ("0train", "1test") for run in range(6)}
        declarations = subject["declared_raw_file_paths"]
        names = {Path(path).name: path for path in declarations}
        if len(names) != 2 or set(names) != {f"A{number:02d}T.mat", f"A{number:02d}E.mat"}:
            raise ValueError("BCI subject-specific T/E source declarations required")
        if any(not path.startswith("data/raw/moabb/MNE-bnci-data/") or ".." in path.split("/") or "\\" in path for path in declarations):
            raise ValueError("BCI declarations outside fixed raw namespace")
        paths = {pair: names[f"A{number:02d}{'T' if pair[0] == '0train' else 'E'}.mat"] for pair in expected}
    else:
        expected = {("0", "0")}
        declarations = subject["declared_raw_file_paths"]
        if len(declarations) != 1 or Path(declarations[0]).name != f"s{number:02d}.mat" or not declarations[0].startswith("data/raw/moabb/cho2017/") or ".." in declarations[0].split("/"):
            raise ValueError("Cho subject-specific source declaration required")
        paths = {("0", "0"): declarations[0]}
    if set(pairs) != expected:
        raise ValueError("stored groups differ from statically traced loader schema")
    return [{"project_subject_id": expected_id, "session": group["session"], "run": group["run"],
             "epoch_count": group["epoch_count"], "loader_defined_raw_file_path": paths[(group["session"], group["run"])],
             "mapping_status": "pinned_loader_filename_relation", "cached_signal_processing_lineage_verified": False} for group in groups]


def hash_raw(root, path):
    path = reader.local_file(root, path)
    before = path.stat()
    if not 0 < before.st_size <= 256 * 1024**2:
        raise ValueError("raw checksum scope requires file below256MiB")
    digest, count = hashlib.sha256(), 0
    with path.open("rb") as stream:
        if reader.stable_stat(os.fstat(stream.fileno())) != reader.stable_stat(before):
            raise ValueError("raw file replaced before hash")
        for chunk in iter(lambda: stream.read(1024**2), b""):
            count += len(chunk)
            if count > 256 * 1024**2:
                raise ValueError("raw file grew beyond checksum bound")
            digest.update(chunk)
        after_handle = os.fstat(stream.fileno())
    if count != before.st_size or reader.stable_stat(before) != reader.stable_stat(after_handle) or reader.stable_stat(before) != reader.stable_stat(path.stat()):
        raise ValueError("raw file changed while hashing")
    return {"path": path.relative_to(root).as_posix(), "bytes": count, "sha256": digest.hexdigest(), "mtime_ns": before.st_mtime_ns,
            "freshly_hashed": True, "signal_or_annotation_decoded": False}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, file, code, message, headers, url):
        raise ValueError("unexpected publisher metadata redirect")


def fetch_provider(output):
    request = urllib.request.Request(PROVIDER_URL, headers={"User-Agent": "Pro3-read-only-checksum-audit/1.0"})
    with urllib.request.build_opener(NoRedirect()).open(request, timeout=15) as response:
        body = response.read(1024**2 + 1)
        if response.status != 200 or response.url != PROVIDER_URL or len(body) > 1024**2:
            raise ValueError("exact bounded HTTP200 publisher checksum metadata required")
        receipt = {"url": PROVIDER_URL, "status": response.status, "retrieved_utc": datetime.now(UTC).isoformat(),
                   "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(),
                   "headers": {key: response.headers.get(key) for key in ("Content-Type", "Content-Length", "Last-Modified", "ETag")}}
    with (output / "publisher_SHA256SUMS.txt").open("xb") as stream:
        stream.write(body)
    with (output / "publisher_metadata_receipt.json").open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(receipt, stream, sort_keys=True, indent=2)
        stream.write("\n")
    return checksum_registry(body, provider=True), receipt


def build_map(root, output):
    value = json.loads(reader.read_small(root, root / INVENTORY))
    local_bytes = reader.read_small(root, root / LOCAL_REGISTRY)
    local = checksum_registry(local_bytes, provider=False)
    provider, provider_receipt = fetch_provider(output)
    records, files, counts = [], {}, {}
    for dataset, item in value["datasets"].items():
        dataset_records = []
        for subject in item["subjects"]:
            mapped = map_subject(dataset, subject)
            for record in mapped:
                relative = record["loader_defined_raw_file_path"]
                if relative not in files:
                    if dataset == "cho2017":
                        old = subject["historical_raw_audit"]
                        if relative != old["raw_file_path"]:
                            raise ValueError("Cho historical path mismatch")
                        files[relative] = {"path": relative, "bytes": old["raw_file_bytes"], "sha256": old["historical_verified_raw_sha256"],
                            "freshly_hashed": False, "historical_audit_receipt": old["audit_receipt"], "signal_or_annotation_decoded": False}
                    else:
                        files[relative] = hash_raw(root, root / relative)
                    if dataset == "mmidb":
                        publisher_name = "/".join(relative.split("/")[-2:])
                        actual = files[relative]["sha256"]
                        if local.get(publisher_name) != actual or provider.get(publisher_name) != actual:
                            raise ValueError("MMIDB actual SHA256 differs from publisher or installed MNE registry")
                        files[relative].update({"publisher_recording_path": publisher_name,
                            "physionet_sha256_match": True, "installed_mne_registry_sha256_match": True})
                dataset_records.append(record)
            records.extend(mapped)
        counts[dataset] = {"subjects": item["subject_count"], "project_session_run_groups": len(dataset_records),
                           "distinct_raw_files": len({record["loader_defined_raw_file_path"] for record in dataset_records})}
    return {"schema": "pro3_loader_defined_recording_mapping_raw_checksum_v1", "datasets": counts, "recording_groups": records,
        "raw_files": files, "prior_inventory": {"path": INVENTORY, "sha256": hashlib.sha256((root / INVENTORY).read_bytes()).hexdigest()},
        "publisher_metadata": provider_receipt, "installed_mne_checksum_registry": {"path": LOCAL_REGISTRY, "sha256": hashlib.sha256(local_bytes).hexdigest()},
        "total_project_groups": len(records), "total_distinct_raw_files": len(files),
        "fresh_raw_files_hashed": sum(item["freshly_hashed"] for item in files.values()),
        "fresh_raw_bytes_hashed": sum(item["bytes"] for item in files.values() if item["freshly_hashed"]),
        "historical_cho_raw_hashes_retained": 52, "mmidb_raw_files_matching_publisher_and_mne": 327,
        "cached_signal_processing_lineage_verified": False, "checkpoint_cohort_or_overlap_verified": False,
        "scientifically_eligible_roster_or_query_freeze": False, "scientific_gate_or_freeze_signed": False,
        "real_training_or_original_case_admission": False, "signal_or_annotation_arrays_decoded": False, "original_case_attempts_remaining": 0}
