---
name: nomad-best-practices
description: Official HashiCorp Nomad {version} reference docs and best practices. Loaded automatically when editing .nomad / .nomad.hcl / job.hcl files, Nomad agent config, ACL/Sentinel policies, autoscaler configs, or running `nomad` CLI commands. Use when deploying or scheduling workloads on Nomad, writing job specs (group/task/network/service/template/vault/identity blocks), choosing task drivers (docker, exec2, raw_exec, podman, java, qemu), wiring Consul Connect / Vault integration / Workload Identity, configuring update/canary/rolling deploys, CSI volumes, host_volume, constraint/affinity/spread placement, or troubleshooting allocations / evaluations / deployments. Trigger phrases: "Nomad", "job spec", "task driver", "allocation", "evaluation", "Consul Connect", "Vault integration", "workload identity", "CSI", "host_volume", "scheduler", "bin packing", "node pool", "canary", "rolling deploy", "nomad job run", "nomad alloc", "nomad node", "raw_exec", "exec2", "Sentinel policy", "namespace".
paths:
  - "**/*.nomad"
  - "**/*.nomad.hcl"
  - "**/jobs/**/*.hcl"
  - "**/nomad/**/*.hcl"
  - "**/job.hcl"
  - "**/nomad.hcl"
  - "**/nomad-server.hcl"
  - "**/nomad-client.hcl"
  - "**/sentinel/**/*.sentinel"
  - "**/*.sentinel"
---

# Nomad {version} — Reference SKILL

> **Source:** Official Nomad {version} docs (`hashicorp/web-unified-docs`)
> **Generated:** {generated_at}
> Regenerate: `python .gen/generate_skill.py --output ../.. --version {version}` (from skill dir) — see `.gen/README.md`.

---

## Core Principles

Before writing HCL, ask: *does Nomad already model this?*

1. **Job → Group → Task is the contract.** Don't model orchestration in scripts; let groups + restart/reschedule blocks do it.
2. **Constraints over scripted placement.** `constraint` and `affinity` are first-class — declare requirements, let scheduler decide.
3. **Workload Identity over static secrets.** Tasks get a signed JWT (`identity` block); use it to auth to Vault/Consul instead of long-lived tokens.
4. **`template` block over baked configs.** Render Vault/Consul/env data at runtime; restart/signal on change.
5. **Task drivers are pluggable.** Pick `docker`/`exec2`/`raw_exec`/`java`/`podman` per workload — don't shoehorn everything into Docker.
6. **Update strategy is declarative.** `update` block (canary, max_parallel, healthy_deadline) replaces deploy scripts.
7. **CSI for stateful, host_volume for node-pinned.** Don't bind-mount paths from `raw_exec`.
8. **ACLs + namespaces from day one.** Bootstrap ACLs before exposing API; namespaces isolate tenants.

---

## Anti-Pattern Quick Reference

| Avoid | Nomad way |
|---|---|
| Hardcoded IPs in env vars | `template` with Consul service discovery, or `NOMAD_ADDR_<label>` |
| Static Vault tokens in job | `vault {{}}` block + workload identity |
| `raw_exec` for everything | Pick `exec2`, `docker`, `podman`, `java` per fit |
| Bash retry loops in tasks | `restart` block + `reschedule` block |
| Manual rolling deploy scripts | `update` block (canary, max_parallel, auto_revert) |
| Bind-mounting host dirs ad-hoc | `host_volume` (node-local) or `csi_plugin` (cluster-wide) |
| `count = N` for HA without anti-affinity | `spread` block across datacenter / node_pool |
| Logging to files inside task | Driver `logging` config + `nomad alloc logs` / log shipper |
| Secrets in `env {{}}` | `template` rendering to `${{NOMAD_SECRETS_DIR}}` (tmpfs) |
| Polling `nomad job status` in CI | `nomad job run -detach=false` blocks until healthy |
| Long-running batch in `service` job type | Use `batch` or `sysbatch` job type |
| One job = one task | Group related tasks; share network namespace + lifecycle |
| Manual port assignment | `network {{ port "x" {{}} }}` + dynamic ports |
| Skipping `resources {{}}` | Always set `cpu`/`memory`; scheduler needs it for bin packing |
| Plain HTTP between tasks | Consul Connect sidecar (`connect {{ sidecar_service {{}} }}`) |

---

## Reference Sections

Load only the section/topic you need. Do **not** load everything at once.

{section_index}

---

## How to Use These References

1. Check anti-pattern table above first — answer may already be there.
2. Job-spec questions → [`docs/job-specification/CONTENTS.md`](references/docs/job-specification/CONTENTS.md). One topic per HCL block (`task`, `group`, `network`, `service`, `template`, `vault`, `identity`, `update`, `migrate`, `reschedule`, `volume`, `affinity`, `constraint`, `spread`, …).
3. CLI questions → [`commands/CONTENTS.md`](references/commands/CONTENTS.md).
4. HTTP API questions → [`api-docs/CONTENTS.md`](references/api-docs/CONTENTS.md).
5. Agent/cluster config (server, client, telemetry, ACL, TLS) → [`docs/configuration/CONTENTS.md`](references/docs/configuration/CONTENTS.md).
6. Task drivers → [`docs/job-declare/task-driver/CONTENTS.md`](references/docs/job-declare/task-driver/CONTENTS.md) and [`plugins/CONTENTS.md`](references/plugins/CONTENTS.md).
7. Before writing custom orchestration in a `script` check, look for equivalent block in `job-specification/` first.
