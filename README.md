<div align="center">

# Nomad Skill for Claude Code

**Stop Claude from hallucinating Nomad jobspecs.**

Claude's training data is months stale. Without help it confidently writes deprecated HCL, invents stanzas that don't exist, and rebuilds things Nomad already does for you. This skill plugs the **real, version-pinned HashiCorp Nomad docs** into Claude — only the page it needs, only when it needs it.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Latest release](https://img.shields.io/github/v/release/Tcivie/nomad-skill-gen)](../../releases/latest)
[![Auto-updated daily](https://img.shields.io/badge/auto--updated-daily-brightgreen)](.github/workflows/generate.yml)

[Install](#install) · [The problem](#the-problem-claude-hallucinates-nomad) · [Versions](#versions) · [Nomad docs ↗](https://developer.hashicorp.com/nomad)

</div>

---

## The problem: Claude hallucinates Nomad

Real things Claude says when you don't give it the docs:

> 🤖 *"You'll need to spin up Consul for service discovery, then point your jobs at it…"*
> Reality: Nomad has had **native** service discovery since 1.3 — `service { provider = "nomad" }`. No Consul required.

> 🤖 *"Use `raw_exec` to run the binary."*
> Reality: `exec2` exists since 1.6 — better isolation, no root, drop-in replacement. `raw_exec` is the last-resort hack, not the default.

> 🤖 *"Nomad doesn't really do canary deploys, you'd have to script it…"*
> Reality: The `update` block has had `canary`, `max_parallel`, `auto_revert`, and `progress_deadline` since 0.8. Five lines of HCL.

> 🤖 *"Mount the Vault token into the container with an env var."*
> Reality: That's leaking secrets. Use the `vault {}` block + Workload Identity — Nomad signs a JWT for the task, Vault trusts it, no static tokens anywhere.

After install, Claude reads the actual Nomad docs for **your exact version** and stops guessing.

---

## Install

1. Go to [Releases](../../releases) and download the zip for your Nomad version (`v1.9.x`, `v1.10.x`, `v2.0.x`).
2. Unzip into `~/.claude/skills/`.
3. Restart Claude Code.

That's it. The skill auto-loads the moment you open any `.nomad.hcl`, `job.hcl`, agent config, or run a `nomad` command.

**Or two lines in your terminal:**

```bash
gh release download v2.0.x -R Tcivie/nomad-skill-gen
unzip nomad-best-practices.zip -d ~/.claude/skills/
```

(Swap `v2.0.x` for whatever your cluster runs.)

---

## What you get

The full official Nomad reference, sliced for on-demand reading:

| Section | What's inside |
|---------|--------|
| **docs** | Concepts, configuration, deploy, secure, govern, networking, jobs |
| **commands** | Every `nomad` CLI subcommand |
| **api-docs** | HTTP API reference |
| **plugins** | Task drivers + device plugins |
| **tools** | Autoscaler · Pack · Bench |
| **intro** | Getting started |

Claude pulls only the page it needs — `references/docs/job-specification/template.md` for a templating question, `references/docs/job-declare/service-discovery.md` for service routing. The rest of the pack costs zero tokens until accessed.

---

## Versions

| Nomad | Tag | Notes |
|-------|-----|-------|
| 1.9.x | [`v1.9.x`](../../releases/tag/v1.9.x) | older stable |
| 1.10.x | [`v1.10.x`](../../releases/tag/v1.10.x) | LTS |
| 2.0.x | [`v2.0.x`](../../releases/tag/v2.0.x) | latest |

A daily cron rebuilds every release if upstream HashiCorp docs change. You stay current automatically.

Need a different version? Open an issue or PR — adding one is one line in [`versions.json`](versions.json).

---

## What's a Claude Skill, anyway?

A skill is a folder of Markdown the Claude Code CLI can browse on demand. Think of it as a **plug-in brain**: Claude reads only the page that matters for your current question, so the rest doesn't burn your context window.

Read more: [Anthropic — Skills](https://docs.anthropic.com/en/docs/claude-code/skills)

The pack you install looks like this:

```
nomad-best-practices/
├── SKILL.md                  always loaded (principles + section index)
└── references/               loaded only when relevant
    ├── docs/job-specification/template.md
    ├── docs/configuration/server.md
    ├── commands/job-run.md
    ├── api-docs/jobs.md
    └── ...
```

---

## Build it yourself

```bash
git clone https://github.com/Tcivie/nomad-skill-gen.git
cd nomad-skill-gen

# Default → ./output/nomad-best-practices for v2.0.x
python generate_skill.py

# Different version + custom output
python generate_skill.py --version v1.10.x --output ~/.claude/skills

# Reuse a local clone (faster repeat runs)
git clone --depth 1 --filter=blob:none --sparse \
  https://github.com/hashicorp/web-unified-docs.git /tmp/nomad-docs
git -C /tmp/nomad-docs sparse-checkout set content/nomad/v2.0.x
python generate_skill.py --clone-dir /tmp/nomad-docs --version v2.0.x
```

No deps beyond Python 3.10+ and `git`. See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---

## How it works (under the hood)

1. **Sparse-clone** `hashicorp/web-unified-docs` (only the version you want)
2. **Walk** `content/nomad/<version>/content/{docs,commands,api-docs,intro,plugins,tools}/**/*.mdx`
3. **Strip** MDX frontmatter; pull `page_title` + `description`
4. **Strip** `@include` directives (partials not shipped)
5. **Convert** `.mdx → .md` with `# title` + `> description` header
6. **Emit** `CONTENTS.md` at every directory level with topic counts
7. **Render** `templates/skill.md → SKILL.md`

---

## Adding more HashiCorp products

All HashiCorp products live in the same `web-unified-docs` repo. Add an entry to [`projects.json`](projects.json):

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

Vault, Terraform, Boundary, Waypoint — same shape.

---

## Links

- **Nomad** — [nomadproject.io](https://www.nomadproject.io) · [Developer hub](https://developer.hashicorp.com/nomad) · [GitHub](https://github.com/hashicorp/nomad)
- **Claude Code** — [Skills](https://docs.anthropic.com/en/docs/claude-code/skills) · [Authoring guide](https://docs.anthropic.com/en/docs/claude-code/skills-authoring)
- **Sister project** — [`spring-boot-skill-gen`](https://github.com/Tcivie/spring-boot-skill-gen)

---

## Support

If this saves you tokens or headaches, [buy me a coffee on Ko-fi](https://ko-fi.com/tcivie). Stars on GitHub also help.

## License

[MIT](LICENSE) — use it however you want.
