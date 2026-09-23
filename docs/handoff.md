# Handoff — 2026-09-22

Where the work stands, for whoever picks it up next (human or agent). Replace
this file at each handoff rather than appending. **Nothing about the operator's
own archive goes in this file** — this repository is public. Archive-specific
results live with the operator, off-repo.

## State

- **Spike step 1: passed** and recorded in [`spike-plan.md`](spike-plan.md).
- **Steps 2, 5, 6: run once** on a machine with a partial iCloud download (counts
  only). Results are deliberately **not** in this repo. They are being redone on
  the machine with the complete download, and those results are what count.
- **Steps 3–4** (full export, coverage reconciliation), **7** (sign-off) and **8**
  (cleanup) are not done. **Gate still closed:** no engine code yet.
- **PR #1** (`spike/step-1-invariants` → `develop`): CI invariants, Excavator
  Archive rename, `scripts/spike-counts.py`. Its checks had not started when it
  was opened. If they still haven't, enable Actions on the fork.

## What the first real run taught us (general lessons, no figures)

1. **Archive-wide holes exist and are not relationship gaps.** A device whose
   messages never reached iCloud leaves a months-long hole across *every*
   conversation. On the first run, about a third of all per-person gaps and
   reconnections were that hole. Now a rule in
   [`analysis-plan.md`](analysis-plan.md) §3.
2. **`handle.person_centric_id` can be NULL on every row.** Build-guide §3's top
   merge tier may contribute nothing. Identity must work on exact-handle alone.
3. **Contacts names may be absent entirely.** Index by number/email, which the
   design already assumes; names are attached later by the operator.
4. **The same identifier appears as separate SMS and iMessage handle rows**,
   often. Exact-handle normalisation must fold them.
5. **"Dormant 2+ years" is dominated by one-off numbers.** The report headline
   needs a minimum-contact filter (e.g. ≥ N messages or ≥ 2 distinct months)
   before anything counts as a person.
6. **The oldest message can be a cut-off, not a beginning.** Report the archive's
   start as a coverage boundary; never as "when you met".
7. **Attachments may be only partly downloaded** even when message text is fully
   synced. Media counts come from rows; `file_present` distinguishes.
8. **Messages can live on an old phone and nowhere else.** The engine must read
   several sources (Mac `chat.db` and iOS backups, both supported upstream), dedupe
   by message `guid`, and report per-source coverage.
9. **Upstream exporter tests assume `TZ=America/Los_Angeles`.** Use
   `scripts/ci-local.sh`. Worth an upstream issue.

## Next, in order

1. On the machine with the full download: build (`scripts/ci-local.sh`), grant
   Full Disk Access to whatever runs the tools, then run
   `scripts/spike-counts.py` against a **copy** of `chat.db` (+ `-wal`, `-shm`)
   in a private directory. Operator present. Counts only.
2. Back up the other iPhone locally via Finder (Airplane Mode on; never Restore
   or Update). Run the same counts against its `sms.db` to see whether it fills
   the hole.
3. **Operator decisions:** where spike results are recorded (recommended: a local
   file excluded by `.git/info/exclude`, never pushed); go/no-go on steps 3–4.
4. Steps 3–4: full export into a private, non-synced directory; reconcile
   message counts against step 2; delete the export (step 8).
5. Only then: identity resolution (build-guide §10 step 2), with lessons 2–4 and
   8 above as requirements.

## Working rules learned

- **Split sessions.** A session that has read the operator's messages should not
  also commit or push; auto mode blocks it, rightly. Do code and git in a fresh
  session.
- **Never commit archive-derived figures** (counts, dates, sizes) to this repo.
- Open PRs with `--repo happymontana/fortunate-excavator`, because this is a
  fork, and `gh` otherwise targets upstream.
- Rust via Homebrew `rustup` is keg-only: put `$(brew --prefix rustup)/bin` on `PATH`.
