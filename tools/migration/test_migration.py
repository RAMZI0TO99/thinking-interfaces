"""Migration acceptance boundaries, entirely synthetic and stdlib-only."""

from __future__ import annotations

import hashlib
import io
import json
import shutil
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import common
import github
import restore


class MigrationTests(unittest.TestCase):
    def setUp(self):
        parent = common.ROOT / "tmp/migration_tests"
        parent.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=parent)
        self.root = Path(self.temp.name)

    def tearDown(self):
        # Only this test's newly allocated workspace directory is removed.
        # Extended paths are needed even for recursive cleanup on stock Windows.
        if self.root.resolve() != self.root or not self.root.is_relative_to(
            common.ROOT / "tmp/migration_tests"
        ):
            raise ValueError("test cleanup escapes owned scope")
        if common.io_path(self.root).exists():

            def readonly_cleanup(function, path, error):
                import os
                import stat

                target = Path(path)
                if not target.is_relative_to(common.io_path(self.root)):
                    raise ValueError("readonly cleanup escapes owned test tree")
                if not isinstance(error, PermissionError):
                    raise error
                os.chmod(target, stat.S_IREAD | stat.S_IWRITE)
                function(target)

            shutil.rmtree(common.io_path(self.root), onexc=readonly_cleanup)
        self.temp.cleanup()

    def fake_history(self, files=None, extra=None):
        files = files or {
            "runs/attempt.json": b'{"spent":2,"remaining":0}',
            "checkpoints/prior.pt": b"synthetic opaque bytes; never unpickle",
        }
        archive = self.root / "archive.tar.xz"
        with tarfile.open(archive, "w:xz") as stream:
            for name, data in {**files, **(extra or {})}.items():
                info = tarfile.TarInfo(name)
                info.size = len(data)
                stream.addfile(info, io.BytesIO(data))
        part = self.root / "evidence/test/part.001"
        part.parent.mkdir(parents=True)
        archive.rename(part)
        rows = [
            {"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
            for name, data in files.items()
        ]
        manifest = {
            "files": rows,
            "uncompressed_bytes": sum(r["bytes"] for r in rows),
            "archive_bytes": part.stat().st_size,
            "archive_sha256": common.digest(part),
            "parts": [
                {
                    "path": "evidence/test/part.001",
                    "bytes": part.stat().st_size,
                    "sha256": common.digest(part),
                }
            ],
        }
        common.write_json(self.root / restore.HISTORY_MANIFEST, manifest)
        return part, manifest

    def source_fixture(self):
        manifest = common.read_json(common.ROOT / "tools/migration/source-files.json")
        common.write_json(self.root / "tools/migration/source-files.json", manifest)
        for row in manifest["files"]:
            target = self.root / row["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(common.ROOT / row["path"], target)
        return manifest

    def test_source_restores_mixed_and_uniform_endings_exactly(self):
        manifest = self.source_fixture()
        for row in manifest["files"]:
            path = self.root / row["path"]
            path.write_bytes(path.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
        with self.assertRaises(ValueError):
            common.source_check(self.root)
        self.assertEqual(common.source_check(self.root, normalize=True), common.SOURCE_SHA)
        for row in manifest["files"]:
            self.assertEqual(common.digest(self.root / row["path"]), row["sha256"])

    def test_source_semantic_edit_stops_before_normalizing_any_file(self):
        manifest = self.source_fixture()
        first = self.root / manifest["files"][0]["path"]
        changed = first.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
        first.write_bytes(changed)
        last = self.root / manifest["files"][-1]["path"]
        last.write_bytes(last.read_bytes() + b"\n# user edit\n")
        with self.assertRaises(ValueError):
            common.source_check(self.root, normalize=True)
        self.assertEqual(first.read_bytes(), changed)
        self.assertTrue(last.read_bytes().endswith(b"# user edit\n"))

    def test_new_canonical_file_refused(self):
        self.source_fixture()
        (self.root / "core/new_user_module.py").write_text("value = 1\n")
        with self.assertRaises(ValueError):
            common.source_check(self.root)

    def test_extra_hook_prevents_any_source_rewrite(self):
        manifest = self.source_fixture()
        first = self.root / manifest["files"][0]["path"]
        changed = first.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
        first.write_bytes(changed)
        (self.root / ".githooks/user_hook").write_text("user contents\n")
        with self.assertRaises(ValueError):
            common.source_check(self.root, normalize=True)
        self.assertEqual(first.read_bytes(), changed)

    def test_actual_autocrlf_clone_is_clean_after_exact_byte_restoration(self):
        import subprocess

        self.source_fixture()

        def git(*args, cwd=None):
            return subprocess.run(
                ["git", *args], cwd=cwd or self.root, capture_output=True, text=True, check=True
            ).stdout

        git("init", "-q")
        git("config", "core.autocrlf", "true")
        git("config", "user.name", "Synthetic Migration Test")
        git("config", "user.email", "synthetic@example.invalid")
        git("add", ".")
        git(
            "-c",
            "core.hooksPath=.git/unused_test_hooks",
            "commit",
            "-qm",
            "Synthetic exact-source fixture",
        )
        cloned = self.root / "checkout with spaces"
        git(
            "-c",
            "core.autocrlf=true",
            "clone",
            "--no-hardlinks",
            "--config",
            "core.autocrlf=true",
            str(self.root),
            str(cloned),
        )
        restore.normalize(cloned)
        self.assertEqual(common.source_check(cloned), common.SOURCE_SHA)
        self.assertEqual(git("status", "--porcelain", cwd=cloned), "")
        # A user can have a staged edit while the working copy has been restored.
        source = cloned / "core/config.py"
        original = source.read_bytes()
        source.write_bytes(original + b"\n# staged user edit\n")
        git("add", "core/config.py", cwd=cloned)
        staged_before = git("write-tree", cwd=cloned)
        source.write_bytes(original)
        restore.normalize(cloned)
        self.assertEqual(git("write-tree", cwd=cloned), staged_before)

    def test_private_release_redirect_drops_credentials(self):
        import urllib.request

        request = urllib.request.Request(
            "https://api.github.com/repos/test/releases/assets/1",
            headers={"Authorization": "Bearer synthetic-test-token"},
        )
        redirected = github.PrivateRedirect().redirect_request(
            request, None, 302, "Found", {}, "https://release-assets.githubusercontent.com/file"
        )
        self.assertFalse(redirected.has_header("Authorization"))
        with self.assertRaises(ValueError):
            github.PrivateRedirect().redirect_request(
                request, None, 302, "Found", {}, "http://example.invalid/file"
            )

    def test_windows_path_aliases_and_traversal_refused(self):
        for name in (
            "../x",
            "/x",
            "dir/../x",
            "dir//x",
            "C:x",
            "C:/x",
            "dir\\x",
            "CON",
            "con.txt",
            "a.",
            "a ",
            "a:stream",
            "LPT9",
            "dir/./x",
        ):
            with self.subTest(name=name), self.assertRaises(ValueError):
                common.safe_path(self.root, name)

    def test_reparse_ancestor_refused(self):
        target = self.root / "other"
        target.mkdir()
        link = self.root / "linked"
        import subprocess
        import sys

        if sys.platform == "win32":
            result = subprocess.run(
                ["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(target)],
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, "test junction creation failed")
        else:
            link.symlink_to(target, target_is_directory=True)
        try:
            with self.assertRaises(ValueError):
                common.safe_path(self.root, "linked/file.json")
        finally:
            if sys.platform == "win32":
                link.rmdir()
            else:
                link.unlink()

    def test_history_roundtrip_preserves_attempts_and_is_idempotent(self):
        self.fake_history()
        restore.restore_history(self.root)
        self.assertEqual(
            json.loads((self.root / "runs/attempt.json").read_bytes()), {"spent": 2, "remaining": 0}
        )
        restore.restore_history(self.root)
        self.assertEqual(
            (self.root / "checkpoints/prior.pt").read_bytes(),
            b"synthetic opaque bytes; never unpickle",
        )

    def test_conflicting_history_preserved_before_any_restore(self):
        self.fake_history()
        path = self.root / "runs/attempt.json"
        path.parent.mkdir()
        path.write_bytes(b"user contents")
        with self.assertRaises(ValueError):
            restore.restore_history(self.root)
        self.assertEqual(path.read_bytes(), b"user contents")
        self.assertFalse((self.root / "checkpoints/prior.pt").exists())

    def test_corrupted_part_rejected_without_publishing(self):
        part, _ = self.fake_history()
        data = bytearray(part.read_bytes())
        data[20] ^= 1
        part.write_bytes(data)
        with self.assertRaises(ValueError):
            restore.restore_history(self.root)
        self.assertFalse((self.root / "runs/attempt.json").exists())

    def test_outside_history_target_and_case_alias_refused(self):
        for files in ({"README.md": b"x"}, {"runs/A.json": b"x", "runs/a.json": b"x"}):
            manifest = {
                "files": [
                    {"path": n, "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()}
                    for n, b in files.items()
                ],
                "uncompressed_bytes": len(files),
            }
            with self.assertRaises(ValueError):
                restore.history_preflight(self.root, manifest)

    def test_unknown_archive_member_refused(self):
        self.fake_history(extra={"runs/extra.json": b"unlisted"})
        with self.assertRaises(ValueError):
            restore.restore_history(self.root)
        self.assertFalse((self.root / "runs/extra.json").exists())

    def test_long_windows_history_path_restores_exactly(self):
        relative = (
            "runs/"
            + "/".join(["long_history_directory_" + str(i) for i in range(10)])
            + "/receipt.json"
        )
        self.fake_history(files={relative: b"dated inert receipt bytes"})
        restore.restore_history(self.root)
        path = common.io_path(common.safe_path(self.root, relative))
        self.assertGreater(len(str(path)), 260)
        self.assertEqual(path.read_bytes(), b"dated inert receipt bytes")

    def download_row(self):
        data = b"opaque public checkpoint bytes"
        row = {
            "path": "checkpoints/synthetic.pth",
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "url": "https://example.invalid/weights",
        }
        return data, row

    def response(self, data):
        response = io.BytesIO(data)
        response.url = "https://example.invalid/weights"
        return response

    def test_verified_download_and_existing_file_skip(self):
        data, row = self.download_row()
        with patch("urllib.request.urlopen", return_value=self.response(data)) as request:
            self.assertEqual(restore.fetch_one(self.root, row), "downloaded")
            self.assertEqual(restore.fetch_one(self.root, row), "verified")
            self.assertEqual(request.call_count, 1)
            import ssl

            context = request.call_args.kwargs["context"]
            self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
            self.assertTrue(context.check_hostname)

    def test_download_size_or_hash_mismatch_never_published(self):
        data, row = self.download_row()
        for broken in (data + b"extra", data[:-1], b"x" * len(data)):
            with (
                patch("urllib.request.urlopen", return_value=self.response(broken)),
                self.assertRaises(ValueError),
            ):
                restore.fetch_one(self.root, row)
            self.assertFalse((self.root / row["path"]).exists())
            self.assertEqual(list((self.root / "checkpoints").iterdir()), [])

    def test_existing_asset_conflict_is_preserved_without_network(self):
        _, row = self.download_row()
        path = self.root / row["path"]
        path.parent.mkdir()
        path.write_bytes(b"user data")
        with patch("urllib.request.urlopen") as request:
            with self.assertRaises(ValueError):
                restore.fetch_one(self.root, row)
            request.assert_not_called()
        self.assertEqual(path.read_bytes(), b"user data")

    def test_npz_verification_ignores_zip_metadata_but_detects_array_change(self):
        paths = [self.root / f"cache{i}.npz" for i in range(3)]
        for i, path in enumerate(paths):
            with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                info = zipfile.ZipInfo("signals.npy", date_time=(2020 + i, 1, 1, 0, 0, 0))
                archive.writestr(info, b"synthetic array" if i != 2 else b"changed array")
        self.assertNotEqual(common.digest(paths[0]), common.digest(paths[1]))
        self.assertEqual(common.npz_members(paths[0]), common.npz_members(paths[1]))
        self.assertNotEqual(common.npz_members(paths[0]), common.npz_members(paths[2]))

    def test_exclusive_publication_preserves_racing_writer(self):
        temp = self.root / "temp"
        target = self.root / "destination"
        temp.write_bytes(b"new")
        target.write_bytes(b"racing writer")
        with self.assertRaises(FileExistsError):
            common.replace_new(temp, target)
        self.assertEqual(target.read_bytes(), b"racing writer")

    def test_unsigned_science_and_zero_attempts_survive_migration_state(self):
        state = common.read_json(common.ROOT / "tools/migration/state.json")
        self.assertEqual(state["original_case"]["attempts_remaining"], 0)
        self.assertEqual(state["original_case"]["attempts_spent"], 2)
        self.assertFalse(state["scientific"]["gate_a_signed"])
        self.assertFalse(state["scientific"]["experiment_freeze_signed"])
        self.assertIsNone(state["current_machine_admission"])
        self.assertFalse(state["public_maintainer_issue"]["sent"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
