# NOTICE — modifications to imessage-exporter

This repository, **Fortunate Excavator**, is a modified version of
[`ReagentX/imessage-exporter`](https://github.com/ReagentX/imessage-exporter)
by **Christopher Sardegna** (`imessage@reagentx.net`), licensed
**GPL-3.0-or-later**.

This file exists to satisfy **GNU GPL v3 §5(a)**: a modified work must carry
prominent notices stating that it was modified, and the date of the
modification. Every change this project makes to the upstream work is recorded
below with its date. **Keep it current — a change that is not listed here is a
licence defect, not a documentation gap.**

Nothing in this file, and nothing anywhere in this repository, narrows the
licence. **The whole of this repository — upstream code and every Fortunate
addition — is GPL-3.0-or-later.** See [`README.md`](README.md) § *Licence and
provenance*.

---

## Upstream provenance

| | |
|---|---|
| Upstream project | `ReagentX/imessage-exporter` |
| Upstream author | Christopher Sardegna |
| Upstream licence | GPL-3.0-or-later (SPDX, as declared in both crate manifests) |
| Fork created | 2026-09-22, as a GitHub fork (provenance is recorded by GitHub, not merely asserted here) |
| Forked at commit | `0d444ab3220f5940d4632c05da4628009c785a02` — *Merge pull request #810 from ReagentX/feat/cs/fix-null-payload*, 2026-09-18 |
| Upstream branch | `develop` (also this fork's default branch) |
| Upstream remote | `git remote add upstream https://github.com/ReagentX/imessage-exporter.git` |

**`LICENSE` is untouched and must stay untouched.** It is byte-identical to
upstream's (sha256 `3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986`).
Upstream copyright notices, author attributions in `Cargo.toml`, and the
upstream `repository` fields are preserved as found. Do not remove them, do not
rewrite them, and do not add a competing copyright line that displaces them.

> **Observation for anyone auditing this fork:** upstream carries **no per-file
> copyright or SPDX headers** — across 148 `.rs` files there are none. All
> licence signalling lives in the root `LICENSE` and the two `Cargo.toml`
> `license` fields. That makes this file, and the README notice, the load-bearing
> provenance for the fork. Treat them accordingly.

---

## Modifications by Fortunate

Newest first. Each entry: date, what changed, and whether it touched upstream
code or only added files.

### 2026-09-22 — initial fork scaffold (documentation only)

**No upstream source file was modified. No upstream file was renamed, moved, or
deleted.** The Rust workspace is exactly as forked.

| File | Change | Upstream file? |
|---|---|---|
| `NOTICE.md` | Added — this file. | new |
| `README.md` | **Modified** — a fork/provenance notice added near the top, and two sections appended: *What Fortunate adds* and *Licence and provenance*. Upstream's own content is otherwise intact. | **upstream file, modified** |
| `docs/archive-format.md` | Added — specification of the Fortunate Archive Format, the tool's neutral structured output. | new |
| `docs/analysis-plan.md` | Added — specification of the relationship analysis. **Unimplemented.** | new |
| `docs/spike-plan.md` | Added — the gate that must pass before any Fortunate code is written: build upstream *unmodified* and run it against a real archive, with the operator present. | new |

At this date **no analysis code, no archive writer and no HTML report exists.**
The additions above are specifications and obligations, nothing more.

---

## Rules for future modifications

1. **Append to this file in the same commit as the change.** Not afterwards.
2. **Prefer additive change.** New modules beside upstream's, not rewrites of
   upstream's. Where an upstream file must change, say so explicitly in the
   table above and keep the change as small as it can be.
3. **Never rename or restructure upstream modules** to accommodate ours. Renames
   obscure provenance and make upstream sync — which matters, because Apple's
   `chat.db` schema drifts — progressively harder.
4. **Nothing proprietary enters this repository.** No credentials, no private
   API details, no internal infrastructure, hostnames, or paths. This repo is
   public and it is GPL: anything committed here is published under GPL.
5. **Syncing upstream is expected maintenance**, not an event:
   `git fetch upstream && git merge upstream/develop`. Record notable syncs here.
