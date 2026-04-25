# nomad-skill-gen

Generates a [Claude Code skill](https://docs.anthropic.com/en/docs/claude-code/skills) from official HashiCorp Nomad docs.

Sister to [`spring-boot-skill-gen`](https://github.com/Tcivie/spring-boot-skill-gen) — same progressive-disclosure CONTENTS.md tree, MDX pipeline instead of AsciiDoc.

## Use

```bash
# Default — Nomad v2.0.x → ./output/nomad-best-practices
python generate_skill.py

# Pick version + output dir
python generate_skill.py --version v1.10.x --output ~/.claude/skills

# Reuse local clone (faster iteration)
git clone --depth 1 --filter=blob:none --sparse https://github.com/hashicorp/web-unified-docs.git /tmp/nomad-docs
git -C /tmp/nomad-docs sparse-checkout set content/nomad/v2.0.x
python generate_skill.py --clone-dir /tmp/nomad-docs --version v2.0.x
```

No deps beyond Python 3.10+ stdlib and `git`.

## Output

```
nomad-best-practices/
├── SKILL.md          # always loaded — principles, anti-patterns, section index
└── references/       # loaded on demand via CONTENTS.md drilldown
    ├── docs/
    ├── commands/
    ├── api-docs/
    ├── plugins/
    ├── tools/
    └── intro/
```

`SKILL.md` ships with `paths` frontmatter so Claude auto-loads when editing `*.nomad`, `*.nomad.hcl`, `job.hcl`, `nomad-server.hcl`, `*.sentinel`, etc.

## How it works

1. Sparse-clone `hashicorp/web-unified-docs` (only requested Nomad version)
2. Walk `content/nomad/<version>/content/{docs,commands,api-docs,intro,plugins,tools}/**/*.mdx`
3. Strip MDX frontmatter (handles YAML block scalars `|` `>`); pull `page_title` + `description`
4. Strip `@include` directives (partials not shipped)
5. Convert `.mdx → .md` with `# title` + `> description` header
6. Emit `CONTENTS.md` at every directory level with topic counts
7. Render `templates/skill.md` → `SKILL.md`

## Files

```
generate_skill.py    # CLI + pipeline
projects.json        # registry — extensible to consul/vault/terraform
templates/skill.md   # SKILL.md template ({version}, {generated_at}, {section_index})
```

## Adding HashiCorp products

All HashiCorp products live in the same docs repo. Add to `projects.json`:

```json
{
  "consul": {
    "repo": "hashicorp/web-unified-docs",
    "doc_root": "content/consul",
    "default_version": "v1.21.x",
    "sections": { "docs": "...", "commands": "...", "api-docs": "..." }
  }
}
```

## License

MIT
