#!/usr/bin/env python3
"""Nomad Skill Generator.

Sparse-clones `hashicorp/web-unified-docs`, walks `content/nomad/<version>/content/`,
strips MDX frontmatter, converts files to plain Markdown, and writes a tree of
`CONTENTS.md` indexes under `<output>/nomad-best-practices/references/`.

Architecture mirrors `tcivie/spring-boot-skill-gen` but simplified:
- Single repo (no per-project async fetch).
- MDX frontmatter strip in place of AsciiDoc/downdoc conversion.
- Same progressive-disclosure CONTENTS.md tree pattern.

Usage:
    python generate_skill.py --output ../my-plugin/skills
    python generate_skill.py --version v2.0.x --output ./output
    python generate_skill.py --clone-dir /tmp/nomad-docs --version v2.0.x
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
PROJECTS = json.loads((REPO_ROOT / "projects.json").read_text())
TEMPLATE = (REPO_ROOT / "templates" / "skill.md").read_text()

GIT_REPO_URL = "https://github.com/{repo}.git"
SKILL_FOLDER = "nomad-best-practices"

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
INCLUDE_RE = re.compile(r"@include\s+'([^']+)'")
H1_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
H2_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)


@dataclass
class Doc:
    path: Path
    title: str
    description: str
    headings: list[str]


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Pluck YAML frontmatter from MDX. Handles `key: value` and block scalars (`|`, `>`)."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    raw = m.group(1)
    body = text[m.end() :]
    meta: dict[str, str] = {}
    lines = raw.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        i += 1
        if not line or line.lstrip().startswith("#"):
            continue
        if ":" not in line or line.startswith(" "):
            continue
        k, _, v = line.partition(":")
        key = k.strip()
        val = v.strip()
        if val in ("|", "|-", ">", ">-"):
            block: list[str] = []
            while i < len(lines) and (lines[i].startswith(" ") or lines[i] == ""):
                block.append(lines[i].strip())
                i += 1
            sep = " " if val.startswith(">") else "\n"
            meta[key] = sep.join(b for b in block if b)
        else:
            meta[key] = val.strip("'\"")
    return meta, body


def strip_includes(body: str) -> str:
    """MDX `@include 'partial.mdx'` directives reference files we don't ship; drop them."""
    return INCLUDE_RE.sub("", body)


def first_h2_list(body: str, limit: int = 8) -> list[str]:
    return [h.strip() for h in H2_RE.findall(body)[:limit]]


def derive_title(meta: dict, body: str, fallback: str) -> str:
    if t := meta.get("page_title"):
        return t
    if m := H1_RE.search(body):
        return m.group(1).strip()
    return fallback.replace("-", " ").title()


def convert_file(src: Path, out: Path) -> Doc:
    text = src.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(text)
    body = strip_includes(body).strip() + "\n"
    title = derive_title(meta, body, src.stem)
    description = meta.get("description", "").strip()
    headings = first_h2_list(body)

    out.parent.mkdir(parents=True, exist_ok=True)
    parts = [f"# {title}\n"]
    if description:
        parts.append(f"> {description}\n")
    parts.append(body)
    out.write_text("\n".join(parts), encoding="utf-8")

    return Doc(out, title, description, headings)


def write_contents(
    directory: Path, title: str, docs: list[Doc], subdirs: list[tuple[Path, str, int]]
) -> None:
    lines = [f"# {title}", ""]
    if subdirs:
        lines.append("Browse by section:\n")
        for path, child_title, count in sorted(subdirs, key=lambda x: x[1].lower()):
            lines.append(f"- [{child_title}]({path.name}/CONTENTS.md) ({count} topics)")
        lines.append("")
    if docs:
        lines.append("Topics:\n")
        for d in sorted(docs, key=lambda x: x.title.lower()):
            summary = d.description or ", ".join(d.headings[:3]) or ""
            summary = (summary[:120] + "…") if len(summary) > 120 else summary
            if summary:
                lines.append(f"- [{d.title}]({d.path.name}) — {summary}")
            else:
                lines.append(f"- [{d.title}]({d.path.name})")
        lines.append("")
    (directory / "CONTENTS.md").write_text("\n".join(lines), encoding="utf-8")


def build_tree(src_root: Path, out_root: Path) -> dict[Path, list[Doc]]:
    dir_docs: dict[Path, list[Doc]] = {}
    for src in sorted(src_root.rglob("*.mdx")):
        rel = src.relative_to(src_root)
        if rel.parts and rel.parts[0] == "partials":
            continue
        out = out_root / rel.with_suffix(".md")
        doc = convert_file(src, out)
        dir_docs.setdefault(out.parent, []).append(doc)
    return dir_docs


def emit_indexes(
    out_root: Path, dir_docs: dict[Path, list[Doc]], section_title: str
) -> int:
    all_dirs: set[Path] = set()
    for d in dir_docs:
        cur = d
        while cur >= out_root:
            all_dirs.add(cur)
            if cur == out_root:
                break
            cur = cur.parent

    counts: dict[Path, int] = {}
    for d in sorted(all_dirs, key=lambda p: -len(p.parts)):
        docs = list(dir_docs.get(d, []))
        subdirs = []
        topic_count = len(docs)
        for child in sorted(p for p in d.iterdir() if p.is_dir()):
            child_count = counts.get(child, 0)
            topic_count += child_count
            child_title = child.name.replace("-", " ").title()
            subdirs.append((child, child_title, child_count))
        counts[d] = topic_count
        title = section_title if d == out_root else d.name.replace("-", " ").title()
        write_contents(d, title, docs, subdirs)
    return counts.get(out_root, 0)


def sparse_clone(repo: str, version_path: str, dest: Path) -> Path:
    subprocess.run(
        [
            "git",
            "clone",
            "--depth",
            "1",
            "--filter=blob:none",
            "--sparse",
            GIT_REPO_URL.format(repo=repo),
            str(dest),
        ],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(dest), "sparse-checkout", "set", version_path],
        check=True,
        capture_output=True,
    )
    return dest / version_path / "content"


def generate(
    project_id: str,
    version: str,
    output_dir: Path,
    clone_dir: Path | None = None,
    keep_clone: bool = False,
) -> dict:
    cfg = PROJECTS[project_id]
    skill_dir = output_dir / SKILL_FOLDER
    refs_dir = skill_dir / "references"

    if refs_dir.exists():
        shutil.rmtree(refs_dir)
    refs_dir.mkdir(parents=True)

    version_path = f"{cfg['doc_root']}/{version}"
    if clone_dir:
        src_root = Path(clone_dir) / version_path / "content"
        if not src_root.is_dir():
            raise SystemExit(f"missing {src_root}")
        cleanup_dir: Path | None = None
    else:
        tmp = Path(tempfile.mkdtemp(prefix=f"{project_id}-docs-"))
        src_root = sparse_clone(cfg["repo"], version_path, tmp)
        cleanup_dir = None if keep_clone else tmp

    section_totals: list[tuple[str, int, str]] = []
    for section, blurb in cfg["sections"].items():
        section_src = src_root / section
        if not section_src.is_dir():
            continue
        section_out = refs_dir / section
        section_out.mkdir(parents=True, exist_ok=True)
        dir_docs = build_tree(section_src, section_out)
        total = emit_indexes(section_out, dir_docs, f"Nomad — {section}")
        section_totals.append((section, total, blurb))

    section_index = "\n".join(
        f"- [{section}](references/{section}/CONTENTS.md) ({total} topics) — {blurb}"
        for section, total, blurb in section_totals
    )
    grand_total = sum(t for _, t, _ in section_totals)

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_md = TEMPLATE.format(
        version=version,
        generated_at=generated_at,
        section_index=section_index,
    )
    (skill_dir / "SKILL.md").write_text(skill_md)

    if cleanup_dir:
        shutil.rmtree(cleanup_dir, ignore_errors=True)

    print(
        f"Generated {grand_total} topics across {len(section_totals)} sections at {skill_dir}"
    )
    return {
        "project": project_id,
        "version": version,
        "topics": grand_total,
        "sections": len(section_totals),
        "generated_at": generated_at,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate Nomad SKILL from official docs")
    ap.add_argument("--project", default="nomad", choices=list(PROJECTS.keys()))
    ap.add_argument("--version", help="Doc version (default: project's default)")
    ap.add_argument(
        "--output",
        "-o",
        default="./output",
        help="Skill output base dir (parent of <skill>/)",
    )
    ap.add_argument("--clone-dir", help="Reuse existing checkout instead of cloning")
    ap.add_argument("--keep-clone", action="store_true")
    args = ap.parse_args()

    version = args.version or PROJECTS[args.project]["default_version"]
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)

    generate(
        args.project,
        version,
        output,
        clone_dir=Path(args.clone_dir) if args.clone_dir else None,
        keep_clone=args.keep_clone,
    )


if __name__ == "__main__":
    main()
