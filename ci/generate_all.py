#!/usr/bin/env python3
"""CI orchestrator: generate Nomad skill for every version in versions.json,
zip each, and emit GitHub Actions outputs so the workflow can publish releases.

Mirrors the design of tcivie/spring-boot-skill-gen/ci/generate_all.py but
simpler — Nomad is a single product, no companion-library compatibility matrix.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VERSIONS_FILE = REPO_ROOT / "versions.json"
SCRIPT_FILE = REPO_ROOT / "generate_skill.py"
TEMPLATE_FILE = REPO_ROOT / "templates" / "skill.md"
PROJECTS_FILE = REPO_ROOT / "projects.json"
OUTPUT_DIR = REPO_ROOT / "output"
ZIPS_DIR = REPO_ROOT / "zips"
GITHUB_OUTPUT = os.environ.get("GITHUB_OUTPUT", "/dev/null")
SKILL_FOLDER = "nomad-best-practices"


def get_script_hash() -> str:
    """Hash entrypoint + template + projects.json. Template changes count."""
    h = hashlib.sha256()
    for f in (SCRIPT_FILE, TEMPLATE_FILE, PROJECTS_FILE):
        h.update(f.read_bytes())
    return h.hexdigest()[:12]


def hash_skill_dir(path: Path) -> str:
    """Stable hash of generated skill content (excluding `Generated:` line)."""
    h = hashlib.sha256()
    for f in sorted(path.rglob("*")):
        if not f.is_file():
            continue
        rel = f.relative_to(path).as_posix()
        h.update(rel.encode())
        if f.name == "SKILL.md":
            content = "\n".join(
                ln
                for ln in f.read_text().splitlines()
                if not ln.startswith("> **Generated:**")
            )
            h.update(content.encode())
        else:
            h.update(f.read_bytes())
    return h.hexdigest()[:12]


def generate_version(version: str) -> Path:
    """Run generate_skill.py for one version. Returns generated skill dir."""
    version_out = OUTPUT_DIR / version
    if version_out.exists():
        shutil.rmtree(version_out)
    version_out.mkdir(parents=True)

    cmd = [
        sys.executable,
        str(SCRIPT_FILE),
        "--version",
        version,
        "--output",
        str(version_out),
    ]
    print(f"[{version}] $ {' '.join(cmd)}", flush=True)
    subprocess.run(cmd, check=True, cwd=REPO_ROOT)
    skill_dir = version_out / SKILL_FOLDER
    if not skill_dir.exists():
        raise RuntimeError(f"expected {skill_dir} after generation, missing")
    return skill_dir


def zip_skill(skill_dir: Path, version: str) -> Path:
    ZIPS_DIR.mkdir(exist_ok=True)
    zip_path = ZIPS_DIR / f"nomad-best-practices-{version}.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(skill_dir.rglob("*")):
            if f.is_file():
                zf.write(f, f.relative_to(skill_dir.parent))
    return zip_path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--force",
        action="store_true",
        help="Regenerate every version regardless of hash cache",
    )
    args = ap.parse_args()

    versions_data = json.loads(VERSIONS_FILE.read_text())
    cached_script_hash = versions_data.get("script_hash", "")
    current_script_hash = get_script_hash()
    script_changed = cached_script_hash != current_script_hash
    if script_changed:
        print(
            f"script hash changed: {cached_script_hash} -> {current_script_hash}",
            flush=True,
        )

    releases: list[str] = []
    versions_changed = False

    for version, info in versions_data["versions"].items():
        cached_skill_hash = info.get("skill_hash", "")
        needs_regen = args.force or script_changed or not cached_skill_hash

        if not needs_regen:
            print(
                f"[{version}] cached (skill_hash={cached_skill_hash}), skip", flush=True
            )
            continue

        skill_dir = generate_version(version)
        new_skill_hash = hash_skill_dir(skill_dir)

        if new_skill_hash == cached_skill_hash and not args.force:
            print(
                f"[{version}] hash unchanged ({new_skill_hash}), skip release",
                flush=True,
            )
            continue

        zip_path = zip_skill(skill_dir, version)
        print(
            f"[{version}] regenerated, hash {cached_skill_hash} -> {new_skill_hash}",
            flush=True,
        )
        releases.append(f"{version}:{zip_path}")
        versions_data["versions"][version]["skill_hash"] = new_skill_hash
        versions_changed = True

    if script_changed:
        versions_data["script_hash"] = current_script_hash
        versions_changed = True

    if versions_changed:
        VERSIONS_FILE.write_text(json.dumps(versions_data, indent=2) + "\n")

    with open(GITHUB_OUTPUT, "a") as fh:
        fh.write(f"releases={' '.join(releases)}\n")
        fh.write(f"versions_changed={'true' if versions_changed else 'false'}\n")

    print(f"\nreleases queued: {len(releases)}")
    for r in releases:
        print(f"  - {r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
