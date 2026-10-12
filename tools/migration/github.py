"""Private release transport using Git's existing credential helper. Never log tokens."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, digest, read_json, safe_path

REPOSITORY = "RAMZI0TO99/thinking-interfaces"
TAG = "windows-portable-20261012"
API = "https://api.github.com/repos/" + REPOSITORY


class PrivateRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        result = super().redirect_request(req, fp, code, msg, headers, newurl)
        if (
            result is not None
            and urllib.parse.urlsplit(newurl).hostname
            != urllib.parse.urlsplit(req.full_url).hostname
        ):
            result.remove_header("Authorization")
        if not newurl.startswith("https://"):
            raise ValueError("insecure release redirect refused")
        return result


def token():
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="Never")
    result = subprocess.run(
        ["git", "-c", "credential.interactive=never", "credential", "fill"],
        input="protocol=https\nhost=github.com\npath=" + REPOSITORY + ".git\n\n",
        cwd=ROOT,
        text=True,
        capture_output=True,
        env=env,
        timeout=30,
        check=False,
    )
    values = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
    if result.returncode or not values.get("password"):
        raise ValueError("Sign in to GitHub through Git Credential Manager, then rerun setup.")
    return values["password"]


def request(
    url, credential, *, data=None, method=None, accept="application/vnd.github+json", headers=None
):
    if urllib.parse.urlsplit(url).hostname not in {"api.github.com", "uploads.github.com"}:
        raise ValueError("credential use restricted to GitHub API/upload hosts")
    values = {
        "Authorization": "Bearer " + credential,
        "Accept": accept,
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "thinking-interfaces-migration",
    }
    values.update(headers or {})
    req = urllib.request.Request(url, data=data, headers=values, method=method)
    return urllib.request.build_opener(PrivateRedirect()).open(req, timeout=60)


def api(path, credential, payload=None, method=None):
    data = None if payload is None else json.dumps(payload).encode()
    with request(
        API + path,
        credential,
        data=data,
        method=method,
        headers={} if data is None else {"Content-Type": "application/json"},
    ) as response:
        return json.load(response)


def release_by_tag(credential):
    try:
        return api("/releases/tags/" + TAG, credential)
    except urllib.error.HTTPError as exc:
        if exc.code != 404:
            raise
    # Draft releases may not yet have a Git tag. Do not create a duplicate draft.
    candidates = [r for r in api("/releases?per_page=100", credential) if r["tag_name"] == TAG]
    if len(candidates) > 1:
        raise ValueError("duplicate release drafts; preserve them for review")
    return candidates[0] if candidates else None


def download_asset(root: Path, row: dict):
    # Resolve the pinned asset id on the private release, then verify all bytes.
    credential = token()
    destination = safe_path(root, row["path"])
    destination.parent.mkdir(parents=True, exist_ok=True)
    if row["github_asset"].get("repository") != REPOSITORY:
        raise ValueError("unexpected private asset repository")
    asset = row["github_asset"]
    if asset["tag"] != TAG:
        raise ValueError("unexpected release tag")
    release = release_by_tag(credential)
    if release is None or release["draft"]:
        raise ValueError("published private evidence release is unavailable")
    matches = [a for a in release["assets"] if a["name"] == asset["name"]]
    if len(matches) != 1 or matches[0]["size"] != row["bytes"]:
        raise ValueError("private release asset identity differs")
    url = API + "/releases/assets/" + str(matches[0]["id"])
    import hashlib
    import uuid

    from common import replace_new

    temp = destination.with_name(destination.name + ".download-" + uuid.uuid4().hex)
    count = 0
    h = hashlib.sha256()
    try:
        with (
            request(url, credential, accept="application/octet-stream") as source,
            temp.open("xb") as target,
        ):
            while block := source.read(1024**2):
                count += len(block)
                if count > row["bytes"]:
                    raise ValueError("release asset exceeds expected bytes")
                target.write(block)
                h.update(block)
        if count != row["bytes"] or h.hexdigest() != row["sha256"]:
            raise ValueError("release asset digest differs")
        replace_new(temp, destination)
        print("Verified private history asset: " + asset["name"], flush=True)
    finally:
        if temp.exists():
            temp.unlink()


def publish(mode: str, name: str | None):
    credential = token()
    manifest = read_json(ROOT / "evidence/portable-20261012-v2/manifest.json")
    release = release_by_tag(credential)
    if release is None:
        if mode != "create":
            raise ValueError("release draft has not been created")
        revision = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True
        ).stdout.strip()
        release = api(
            "/releases",
            credential,
            {
                "tag_name": TAG,
                "target_commitish": revision,
                "name": "Windows continuation evidence - 12 October 2026",
                "draft": True,
                "prerelease": False,
                "body": (
                    "Hash-verified, inert historical run evidence and trained checkpoints "
                    "for Windows continuation. Public raw data and original weights use "
                    "separate pinned downloads; processed caches are rebuilt. Old launchers/"
                    "admissions remain expired. Gate A/freeze unsigned; original case attempts "
                    "remain zero. See WINDOWS_SETUP.md and the committed archive manifest."
                ),
            },
            "POST",
        )
    if mode == "upload":
        rows = [r for r in manifest["parts"] if r["github_asset"]["name"] == name]
        if len(rows) != 1:
            raise ValueError("unknown archive part")
        row = rows[0]
        path = ROOT / "runs/migration_export/release_assets" / name
        if path.stat().st_size != row["bytes"] or digest(path) != row["sha256"]:
            raise ValueError("upload bytes differ from committed manifest")
        matches = [a for a in release["assets"] if a["name"] == name]
        if matches:
            if (
                len(matches) != 1
                or matches[0]["size"] != row["bytes"]
                or matches[0].get("digest") not in {None, "sha256:" + row["sha256"]}
            ):
                raise ValueError("existing asset conflicts; preserve it")
            print("Existing release asset retained: " + name)
            return
        url = release["upload_url"].split("{")[0] + "?" + urllib.parse.urlencode({"name": name})
        with (
            path.open("rb") as stream,
            request(
                url,
                credential,
                data=stream,
                method="POST",
                headers={
                    "Content-Type": "application/octet-stream",
                    "Content-Length": str(row["bytes"]),
                },
            ) as response,
        ):
            uploaded = json.load(response)
        if uploaded["size"] != row["bytes"] or uploaded.get("digest") not in {
            None,
            "sha256:" + row["sha256"],
        }:
            raise ValueError("server upload identity differs")
        print("Uploaded: " + name)
    elif mode == "finish":
        expected = {r["github_asset"]["name"]: r for r in manifest["parts"]}
        if {a["name"] for a in release["assets"]} != set(expected):
            raise ValueError("release assets incomplete or unexpected")
        for asset in release["assets"]:
            row = expected[asset["name"]]
            if asset["size"] != row["bytes"] or asset.get("digest") not in {
                None,
                "sha256:" + row["sha256"],
            }:
                raise ValueError("release asset identity differs")
        release = api("/releases/" + str(release["id"]), credential, {"draft": False}, "PATCH")
        print(release["html_url"])
    else:
        print("Draft release prepared: " + TAG)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("create", "upload", "finish"))
    parser.add_argument("--asset")
    args = parser.parse_args()
    publish(args.mode, args.asset)
