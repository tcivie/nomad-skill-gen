# Contributing

Thanks for your interest in improving the Nomad Skill Generator!

## Quick Start

```bash
git clone https://github.com/Tcivie/nomad-skill-gen.git
cd nomad-skill-gen

# Generate a skill locally
python generate_skill.py --version v2.0.x --output /tmp/test
```

## Project Structure

```
generate_skill.py        # Main generator — clone, walk, convert MDX, write CONTENTS.md
ci/generate_all.py       # CI orchestrator — per-version run, hash cache, release output
versions.json            # Tracked versions + script hash (auto-updated by CI)
projects.json            # Source repo + doc root + section labels
templates/skill.md       # SKILL.md template
.github/workflows/       # Daily cron + push triggers
```

## How to Contribute

### Improving the Generator

The most impactful contributions improve output quality:

- **MDX cleanup** — leftover frontmatter or `@include` macros that slip past the regexes in `generate_skill.py`
- **Section indexing** — better logic for the `CONTENTS.md` tree
- **SKILL.md template** — improvements to Core Principles, the Anti-Pattern table, or the "How to Use" section

After making changes, regenerate and compare:

```bash
# Before your change
python generate_skill.py --version v2.0.x --output /tmp/before

# After your change
python generate_skill.py --version v2.0.x --output /tmp/after

# Compare
diff -r /tmp/before /tmp/after
```

### Adding Tracked Versions

Edit `versions.json` and add the new minor (e.g. `"v2.1.x": {"skill_hash": ""}`). CI picks it up on the next run and creates a release.

### Reporting Issues

If you spot bad output (garbled text, missing content, leftover MDX), please open an issue with:

1. The Nomad version
2. The reference file path (e.g. `references/docs/job-specification/template.md`)
3. What's wrong and what it should look like

## Development Notes

- **Python 3.10+** required (`match` statements, `X | Y` union types)
- The generator sparse-clones `hashicorp/web-unified-docs` — first run is slow, repeat runs reuse `--clone-dir`
- Keep MDX→Markdown conversion regex-based; don't pull in heavyweight MDX parsers

## Versioning

Releases are tagged per Nomad minor (`v1.10.x`, `v2.0.x`, …):

- Changing `generate_skill.py`, `templates/`, or `projects.json` bumps the `script_hash` and forces regen of every tracked version
- Each version carries a `skill_hash` of its generated content; the CI only cuts a new release when content actually changes
- Don't manually edit hashes in `versions.json`

## Code Style

- Keep it simple — this is a small script, not a framework
- No `type: ignore` comments — fix the types instead
- Test locally before submitting a PR

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
