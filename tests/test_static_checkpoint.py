from __future__ import annotations

import json
import pickle
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from evaluation.static_checkpoint import (
    Descriptor,
    GlobalName,
    float_tensor_slice,
    inspect_metadata,
)
from scripts.audit_labram_checkpoint import compare_checkpoints, original_key, safe_tensor_bytes


class StaticCheckpointTests(unittest.TestCase):
    def test_builtins_and_shared_memo(self):
        shared = [1, 2, None, True, 2.5]
        original = {"a": shared, "b": shared, "tuple": (1, 2, 3)}
        result = inspect_metadata(pickle.dumps(original, protocol=2))
        self.assertEqual(result, original)
        self.assertIs(result["a"], result["b"])

    def test_reduce_is_inert_even_for_dangerous_global(self):
        payload = b"\x80\x02cos\nsystem\nX\x04\x00\x00\x00echo\x85R."
        with patch("os.system", side_effect=AssertionError("must never execute")) as execute:
            result = inspect_metadata(payload)
        execute.assert_not_called()
        self.assertEqual(result.target, GlobalName("os system"))
        self.assertEqual(result.arguments, ("echo",))

    def test_newobj_and_build_are_inert(self):
        result = inspect_metadata(b"\x80\x02cargparse\nNamespace\n)\x81}b.")
        self.assertEqual(result.kind, "NEWOBJ")
        self.assertEqual(result.state, {})

    def test_invalid_metadata_fails_closed(self):
        for payload in (
            b"\x80\x04N.",
            b"\x80\x02N.trailing",
            b"\x80\x02h\x01.",
            b"\x80\x02R.",
            b"\x80\x02u.",
            b"\x80\x02N0.",
            b"\x80\x02NN.",
            b"\x80\x02N",
            b"\x80\x02}K\x01K\x02sK\x01K\x03s.",
        ):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                inspect_metadata(payload)

    def tensor(self, *, shape=(2, 3), stride=(3, 1), offset=0, size=6, key="0"):
        storage = Descriptor(
            "BINPERSID",
            None,
            (
                "storage",
                GlobalName("torch FloatStorage"),
                key,
                "cuda:0",
                size,
            ),
        )
        hooks = Descriptor("REDUCE", GlobalName("collections OrderedDict"), ())
        return Descriptor(
            "REDUCE",
            GlobalName("torch._utils _rebuild_tensor_v2"),
            (
                storage,
                offset,
                shape,
                stride,
                False,
                hooks,
            ),
        )

    def test_contiguous_tensor_and_scalar(self):
        result = float_tensor_slice(self.tensor())
        self.assertEqual(result.elements, 6)
        self.assertEqual(result.storage_key, "0")
        self.assertEqual(float_tensor_slice(self.tensor(shape=(), stride=(), size=1)).elements, 1)

    def test_invalid_storage_or_stride(self):
        for settings in (
            {"key": "../0"},
            {"size": 5},
            {"offset": 1},
            {"stride": (1, 2)},
            {"shape": (True, 3)},
            {"shape": (0, 3)},
            {"stride": (3,)},
        ):
            with self.subTest(settings=settings), self.assertRaises(ValueError):
                float_tensor_slice(self.tensor(**settings))

    def safe_payload(self, header, data=b"\x00" * 8):
        encoded = json.dumps(header).encode()
        return len(encoded).to_bytes(8, "little") + encoded + data

    def test_safe_slice_and_explicit_name_mapping(self):
        header = {"value": {"dtype": "F32", "shape": [2], "data_offsets": [0, 8]}}
        self.assertEqual(
            safe_tensor_bytes(self.safe_payload(header)),
            {
                "value": ((2,), b"\x00" * 8),
            },
        )
        pairs = {
            "position_embedding": "student.pos_embed",
            "temporal_embedding": "student.time_embed",
            "patch_embed.temporal_conv.conv1.weight": "student.patch_embed.conv1.weight",
            "blocks.3.mlp.0.weight": "student.blocks.3.mlp.fc1.weight",
            "blocks.3.mlp.2.bias": "student.blocks.3.mlp.fc2.bias",
        }
        for safe, original in pairs.items():
            self.assertEqual(original_key(safe), original)

    def test_safe_header_bad_ranges_and_types_rejected(self):
        for override in (
            {"dtype": "I32"},
            {"shape": [True]},
            {"shape": [3]},
            {"data_offsets": [-1, 7]},
            {"data_offsets": [0, 12]},
            {"data_offsets": [1, 9]},
            {"data_offsets": [False, 8]},
        ):
            header = {"value": {"dtype": "F32", "shape": [2], "data_offsets": [0, 8], **override}}
            with self.subTest(override=override), self.assertRaises(ValueError):
                safe_tensor_bytes(self.safe_payload(header))

    def test_safe_overlap_gap_trailing_and_duplicate_rejected(self):
        entry = {"dtype": "F32", "shape": [1], "data_offsets": [0, 4]}
        for header in (
            {"a": entry, "b": entry},
            {"a": entry},
            {"a": {**entry, "data_offsets": [4, 8]}},
        ):
            with self.subTest(header=header), self.assertRaises(ValueError):
                safe_tensor_bytes(self.safe_payload(header))
        duplicate = b'{"a": 1, "a": 2}'
        with self.assertRaises(ValueError):
            safe_tensor_bytes(len(duplicate).to_bytes(8, "little") + duplicate)

    def test_safe_truncation_and_empty_rejected(self):
        for payload in (b"", b"\xff" * 8, self.safe_payload({}, data=b"")):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                safe_tensor_bytes(payload)

    def checkpoint_pair(self, directory, *, changed=False, wrong_shape=False):
        def text(value):
            encoded = value.encode()
            return b"X" + len(encoded).to_bytes(4, "little") + encoded

        ordered = b"ccollections\nOrderedDict\n)R"
        metadata = (
            b"\x80\x02}"
            + text("model")
            + ordered
            + text("student.cls_token")
            + b"ctorch._utils\n_rebuild_tensor_v2\n(("
            + text("storage")
            + b"ctorch\nFloatStorage\n"
            + text("0")
            + text("cpu")
            + b"K\x02tQ"
            + b"K\x00K\x02\x85K\x01\x85\x89"
            + ordered
            + b"tRss."
        )
        original, safe = Path(directory) / "original.pth", Path(directory) / "model.safetensors"
        with zipfile.ZipFile(original, "w") as archive:
            archive.writestr("checkpoint/data.pkl", metadata)
            archive.writestr("checkpoint/data/0", b"\x00" * 8)
        header = {
            "cls_token": {
                "dtype": "F32",
                "shape": [1, 2] if wrong_shape else [2],
                "data_offsets": [0, 8],
            }
        }
        safe.write_bytes(
            self.safe_payload(header, data=(b"\x01" if changed else b"\x00") + b"\x00" * 7)
        )
        return original, safe

    def test_full_comparison_detects_value_and_shape_changes(self):
        settings = {
            "expected_safe_tensors": 1,
            "expected_safe_elements": 2,
            "expected_plan_parameters": 3,
            "omitted_student_keys": [],
        }
        for changed, wrong_shape in ((False, False), (True, False), (False, True)):
            with (
                self.subTest(changed=changed, wrong_shape=wrong_shape),
                tempfile.TemporaryDirectory() as directory,
            ):
                original, safe = self.checkpoint_pair(
                    directory, changed=changed, wrong_shape=wrong_shape
                )
                report = compare_checkpoints(original, safe, settings)
                self.assertEqual(
                    report["all_retained_weights_identical"], not (changed or wrong_shape)
                )
                self.assertFalse(report["parameter_count_matches_plan"])
                self.assertFalse(report["pickle_executed"])
                self.assertFalse(report["inference_parity_established"])


if __name__ == "__main__":
    unittest.main()
