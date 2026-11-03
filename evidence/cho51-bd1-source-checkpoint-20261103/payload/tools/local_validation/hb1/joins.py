"""Pure parent-map and supplied-census conservation. No native observation."""

from dataclasses import dataclass

from .common import (absolute_path, checkpoint, closed, digest, integer, require,
                     sha256_text, strict_json, text, token, uuid_text)

PREFIX = "D:/Aenv/pro3/runs/coordination/cho51_p3_hb1_unadmitted"
PARTITIONS = (("fixtures", 160, 33_554_432), ("supervisor", 40, 8_388_608),
              ("caller", 40, 20_971_520), ("closeout", 16, 4_194_304))
ROLE_CAPS = (("admission", 1_048_576), ("scope", 65_536),
             ("external_return", 65_536), ("raw_tool_return", 1_048_576),
             ("journal_analysis", 131_072), ("actual_review", 131_072),
             ("root_disposition", 131_072), ("source_recheck", 65_536),
             ("runtime_recheck", 65_536), ("output_census", 131_072),
             ("cleanup_assessment", 65_536), ("timing_join", 65_536),
             ("allocation", 65_536), ("source_review", 131_072),
             ("contract_adoption", 16_384), ("closeout", 65_536))
HB_SCENARIO_PIN = "3157f7e0316bee6c141fac04d9794ebdf2550888d04de06d92423d0e7aa733a4"
# Only explicitly native HB design scenarios are representable in this model.
# SC-specific fixture scenarios require their own exact reviewed mapping later.
NATIVE_SCENARIOS = ("HB02", "HB04", "HB08", "HB12", "HB15", "HB16", "HB17",
                    "HB18", "HB20", "HB21")


@dataclass(frozen=True)
class Reservation:
    path: str
    partition: str
    reserved_bytes: int
    publisher_role: object
    transaction_id: str


@dataclass(frozen=True)
class ParentMap:
    raw: bytes
    sha256: str
    parent_operation_id: str
    metadata_transaction_id: str
    stage: str
    authority_sha256: str
    producer_domain_sha256: str
    reservations: tuple
    charges: tuple
    fixture_transaction_id: object
    fixture_scenario_id: object

    @property
    def evidence_kind(self):
        return "UNAUTHENTICATED"

    @property
    def authenticated(self):
        return False


@dataclass(frozen=True)
class CensusModel:
    join_sha256: str
    census_sha256: str
    charges: tuple
    metadata_paths: tuple
    fixture_paths: tuple
    other_paths: tuple
    present_paths: tuple
    absent_paths: tuple
    fixture_scenario_pin: object

    @property
    def evidence_kind(self):
        return "MODEL_ONLY"

    @property
    def authenticated(self):
        return False

    @property
    def fixture_purpose(self):
        return "NATIVE_FIXTURE" if self.fixture_paths else None


def root_path(parent):
    return PREFIX + "/" + uuid_text(parent)


def role_path(parent, transaction, role, *, fixture=False):
    require(role in dict(ROLE_CAPS), "unknown role")
    uuid_text(transaction)
    base = root_path(parent)
    part = "/fixtures/publication_" + transaction if fixture else "/closeout"
    return base + part + "/" + role + "_" + transaction + ".json"


def parse_join(raw, *, check):
    value = strict_json(raw, 65_536, check)
    closed(value, ("schema", "parent_operation_id", "metadata_transaction_id", "stage",
                   "authority_sha256", "producer_domain_sha256", "partitions",
                   "fixture_publication", "reservations"))
    require(value["schema"] == "cho51_hb1_parent_join_v1", "join schema")
    parent = uuid_text(value["parent_operation_id"])
    metadata = uuid_text(value["metadata_transaction_id"])
    require(parent != metadata, "distinct parent/metadata UUIDs")
    stage = text(value["stage"], 32)
    require(stage in ("COMPONENT_MODEL", "COMPONENT_NATIVE", "Q"), "P/unrecognized stage")
    authority = sha256_text(value["authority_sha256"])
    producer = sha256_text(value["producer_domain_sha256"])
    parts = value["partitions"]
    closed(parts, (p[0] for p in PARTITIONS))
    for name, count, size in PARTITIONS:
        closed(parts[name], ("files", "bytes"))
        require(integer(parts[name]["files"]) == count
                and integer(parts[name]["bytes"]) == size, "unchanged partition caps")
    fixture = value["fixture_publication"]
    fixture_id = scenario = None
    fixture_roles = {}
    if fixture is not None:
        require(stage == "COMPONENT_NATIVE", "inner publication is native-component only")
        closed(fixture, ("transaction_id", "scenario_id", "roles"))
        fixture_id = uuid_text(fixture["transaction_id"])
        require(fixture_id not in (parent, metadata), "distinct inner transaction")
        scenario = text(fixture["scenario_id"], 16)
        require(scenario in NATIVE_SCENARIOS, "unmapped native scenario")
        closed(fixture["roles"], (r[0] for r in ROLE_CAPS))
        for role, size in ROLE_CAPS:
            row = fixture["roles"][role]
            closed(row, ("path", "reserved_bytes"))
            path = role_path(parent, fixture_id, role, fixture=True)
            require(row["path"] == path and integer(row["reserved_bytes"]) == size,
                    "exact native-fixture role/path/cap")
            fixture_roles[path] = (role, size)
    rows = value["reservations"]
    require(type(rows) is list and 16 <= len(rows) <= 256, "complete finite reservations")
    charges = {name: [0, 0] for name, _, _ in PARTITIONS}
    seen, main_roles, inner_roles = set(), set(), set()
    reservations = []
    auxiliary_files = auxiliary_bytes = 0
    for row in rows:
        checkpoint(check)
        closed(row, ("path", "partition", "reserved_bytes", "publisher_role", "transaction_id"))
        path = absolute_path(row["path"])
        partition = text(row["partition"], 16)
        require(partition in charges, "unknown partition")
        lower = path.casefold()
        require(lower not in seen, "duplicate/Windows case alias")
        require(all(not lower.startswith(other + "/") and not other.startswith(lower + "/")
                    for other in seen), "file/directory collision")
        seen.add(lower)
        size = integer(row["reserved_bytes"], 1, 8_388_608)
        role = row["publisher_role"]
        transaction = uuid_text(row["transaction_id"])
        if partition == "closeout":
            require(type(role) is str and role in dict(ROLE_CAPS), "main metadata role")
            require(role not in main_roles and transaction == metadata, "main role/transaction")
            require(path == role_path(parent, metadata, role)
                    and size == dict(ROLE_CAPS)[role], "main fixed slot/cap")
            main_roles.add(role)
        elif path in fixture_roles:
            expected_role, expected_size = fixture_roles[path]
            require(partition == "fixtures" and role == expected_role
                    and transaction == fixture_id and size == expected_size, "inner correspondence")
            inner_roles.add(role)
        else:
            require(role is None and transaction == parent, "ordinary reservation ownership")
            require(path.startswith(root_path(parent) + "/" + partition + "/"),
                    "fixed ordinary namespace")
            # No ordinary path may occupy any publication subtree, even absent.
            relative = path[len(root_path(parent) + "/" + partition + "/"):]
            require(not any(part.casefold().startswith("publication_")
                            for part in relative.split("/")), "reserved inner namespace")
            if partition == "fixtures" and fixture_id is not None:
                auxiliary_files += 1
                auxiliary_bytes += size
        charges[partition][0] += 1
        charges[partition][1] += size
        reservations.append(Reservation(path, partition, size, role, transaction))
    require(main_roles == {r[0] for r in ROLE_CAPS}, "all main slots charged")
    require(inner_roles == ({r[0] for r in ROLE_CAPS} if fixture_id else set()),
            "all inner slots charged")
    if fixture_id:
        require(auxiliary_files <= 16 and auxiliary_bytes <= 901_120,
                "inner fixture auxiliary budget")
        require(charges["fixtures"][0] <= 32 and charges["fixtures"][1] <= 4_194_304,
                "inner combined fixture budget")
    for name, count, size in PARTITIONS:
        require(charges[name][0] <= count and charges[name][1] <= size, "partition overflow")
    require(sum(x[0] for x in charges.values()) <= 256
            and sum(x[1] for x in charges.values()) <= 67_108_864, "parent overflow")
    checkpoint(check)
    return ParentMap(raw, digest(raw, check), parent, metadata, stage, authority, producer,
                     tuple(reservations), tuple((n, *charges[n]) for n, _, _ in PARTITIONS),
                     fixture_id, scenario)


def verify_supplied_census(join_raw, census_raw, *, check):
    """Verify all supplied rows before deriving any view; no completeness witness."""
    join = parse_join(join_raw, check=check)  # Never trust a caller-constructed ParentMap.
    census = strict_json(census_raw, 131_072, check)
    closed(census, ("schema", "parent_operation_id", "join_sha256", "authority_sha256",
                    "producer_domain_sha256", "barrier", "entries"))
    require(census["schema"] == "cho51_hb1_supplied_census_v1", "model census schema")
    for key in ("parent_operation_id", "authority_sha256", "producer_domain_sha256"):
        require(census[key] == getattr(join, key), "census identity join")
    require(census["join_sha256"] == join.sha256, "exact join-byte pin")
    barrier = census["barrier"]
    closed(barrier, ("kind", "sequence", "producers_closed", "lost_events"))
    require(barrier["kind"] == "SUPPLIED_ONLY" and barrier["producers_closed"] is True,
            "model barrier required; not a real producer seal")
    integer(barrier["sequence"], 1)
    require(integer(barrier["lost_events"]) == 0, "loss/overflow refuses")
    entries = census["entries"]
    require(type(entries) is list and len(entries) == len(join.reservations), "complete parent census")
    expected = {r.path: r for r in join.reservations}
    seen, native_ids, present, absent = set(), set(), [], []
    for row in entries:
        checkpoint(check)
        closed(row, ("path", "state", "actual_bytes", "native_identity", "sha256", "links", "reparse"))
        path = absolute_path(row["path"])
        require(path in expected and path not in seen, "unknown/duplicate/copy census path")
        seen.add(path)
        size = integer(row["actual_bytes"], 0, expected[path].reserved_bytes)
        state = text(row["state"], 32)
        require(state in ("RESERVED_ABSENT", "FAILED_ABSENT", "PARTIAL", "PRESENT", "FAILED_PRESENT"),
                "unknown custody state")
        if state.endswith("ABSENT"):
            require(size == 0 and all(row[k] is None for k in
                    ("native_identity", "sha256", "links", "reparse")), "absence fields")
            absent.append(path)
        else:
            identity = row["native_identity"]
            closed(identity, ("volume", "file_id"))
            volume = text(identity["volume"], 16)
            file_id = text(identity["file_id"], 32)
            require(len(volume) == 16 and len(file_id) == 32
                    and all(c in "0123456789abcdef" for c in volume + file_id), "native identity text")
            require(int(volume, 16) != 0 and int(file_id, 16) != 0, "unknown zero native identity")
            native = (volume, file_id)
            require(native not in native_ids, "duplicate physical identity")
            native_ids.add(native)
            sha256_text(row["sha256"])
            require(integer(row["links"], 1, 1) == 1 and row["reparse"] is False,
                    "alias/reparse refusal")
            present.append(path)
    require(seen == set(expected), "no omitted failed/unused reservations")
    # Only after full supplied-parent conservation are partition views derived.
    main = tuple(r.path for r in join.reservations if r.partition == "closeout")
    inner = tuple(r.path for r in join.reservations if r.transaction_id == join.fixture_transaction_id)
    other = tuple(r.path for r in join.reservations if r.path not in main and r.path not in inner)
    checkpoint(check)
    return CensusModel(join.sha256, digest(census_raw, check), join.charges, main, inner, other,
                       tuple(present), tuple(absent), HB_SCENARIO_PIN if inner else None)
