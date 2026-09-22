# Fortunate Excavator — build guide

**Status:** the plan of record. Supersedes the 34-section build spec where they conflict, and
reconciles it with `analysis-plan.md` and `spike-plan.md`, which were written first and were tighter.
Derived from the operator's spec plus two independent reviews (engineering; product and licensing),
with every code claim verified against this repository.

**Product sentence:** *Excavator turns your Messages archive into a history of the people you've
known, entirely on your Mac.*

---

## 1. What V1 is — and what it is not

The spec describes twelve screens. `analysis-plan.md` §6 already committed to something tighter, and
it was right. **V1 is the engine, the archive, one static HTML report, and the MCP server. There is
no desktop application in V1.**

That is not a reduction for its own sake. Three things make it the correct order:

1. **The report is the product's proof.** A tool that can tell you how far your history goes, who you
   have known longest, and who came back is worth installing on its own. Twelve screens of chrome
   around an unproven engine is not.
2. **Standalone usefulness is load-bearing, not marketing.** Until the report exists, "a GPL tool that
   feeds one proprietary product" is the factually accurate description of this repository. **The fix
   is shipping the report, not rewording the README.**
3. **The engine has to be right before anything sits on it.** Every number the UI would render comes
   from identity resolution, which has no ground truth (§3).

**In V1:** engine · identity resolution · relationship metrics · archive writer · one static HTML
report · CLI · MCP server · diagnostics.
**Deferred, and nobody will notice:** the conversation viewer (upstream's HTML export already is one),
global search UI, groups, media gallery, the master timeline, and the separate reconnected screen.
When a GUI does arrive, six screens carry it: Welcome, Progress, Story, People, Person history,
Archive/export.

## 2. Architecture

```
chat.db + attachments
        │  (read-only, always)
        ▼
    engine/            upstream imessage_database · normalisation · identity
        │              resolution · relationship metrics · query layer
        ├──────────────┬──────────────┬──────────────┐
        ▼              ▼              ▼              ▼
     report/         cli/           mcp/        archive-format/
   static HTML    text + JSON    read-only      the portable
                                  tools          export
                                                     │
                                          (later, separate repo)
                                                     ▼
                                            any consumer, incl. Fortunate
```

**The query layer is the contract.** It returns plain, already-materialised, already-bounded value
types — `PersonSummary`, `RelationshipStats`, `Page<Message>` — never iterators, connections or
anything transport-shaped. Each surface is a thin adapter over the same functions. **Bounds live in
the engine, not the adapters**: a cap in the MCP layer alone leaves the same unbounded query
available from the CLI, which is the identical hazard wearing a different symptom.

**Rust, and the bet holds — with one correction.** `imessage_database` is a genuine library crate
(`#![forbid(unsafe_code)]`, its own manifest, doc-tested examples) exposing `Handle`, `Chat`,
`Message`, `Attachment` and the `typedstream`/`streamtyped` decoders that absorb fourteen years of
body-encoding drift. **But Contacts matching is not in it** — `imessage-exporter/src/app/contacts.rs`
is 804 lines in the *binary* crate. It must be lifted and reimplemented in our own analysis crate,
not reused. Budget for that; it is the most valuable input to the hardest problem.

**UI, when it comes: Tauri.** Rust engine plus a WebView. SwiftUI pays an FFI cost for a Rust engine;
Electron adds weight this does not need.

## 3. The hard problem, and it is one problem

**Identity resolution has no ground truth, and every statistic sits downstream of it.** A bad merge
does not crash anything — it quietly produces a wrong *"13 years with Mike"* that looks exactly as
credible as a right one. This is the project's central correctness risk.

**Use `Handle.person_centric_id` as the highest-confidence tier.** Apple computes it; upstream already
parses it; its own doc comment reads *"Handles that share `person_centric_id` map to the same combined
string."* The spec builds §30 from scratch without it. Tiers, most to least confident:

1. `person_centric_id` match — Apple's own judgement
2. exact normalised identifier match (E.164 phone, lowercased email)
3. Contacts-card match (once `contacts.rs` is lifted)
4. **everything weaker is a SUGGESTION, never a merge** — surface *"these may be the same person"* and
   let the user decide, per spec §30

Record a confidence tier on every merge and make it visible. A merge the user cannot see is a merge
the user cannot correct.

**Performance is more tractable than feared.** Upstream already builds cheap in-memory index caches
and streams message bodies rather than holding them. What it does not provide is a *derived* index —
cancellable, resumable, incremental re-scan. That is ours to build, and it is ordinary work.

**Schema drift is upstream's strongest area.** typedstream bodies, tapbacks and replies absent from
old schemas, RCS, merged handles. Absorb upstream fixes; do not reimplement.

## 4. Definitions that must exist before any code

The spec's most evocative features are product definitions wearing feature clothes. Each needs a rule,
and `analysis-plan.md` already has some — they conflict with the spec and **`analysis-plan.md` wins**:

| term | rule |
|---|---|
| gap | ≥ 12 months with no message either direction |
| dormant | ≥ 24 months since the last message |
| reconnection | a gap closed by sustained contact — **not one message.** Require ≥ N messages within M days after the gap closes, or a single stray text becomes a "reconnection" |
| "quiet" year | **label the length of the gap, never the mood.** `2019 · no messages` is a fact; `2019 · quiet` asserts a cause the data cannot know |
| lost touch | user-set threshold; `analysis-plan.md`'s 12/24-month defaults, not the spec's 6mo/1y/2y/5y presets |

Pick N and M before writing the reconnection detector, and put them in the manifest so a consumer
knows how the numbers were produced.

## 5. The archive format

**Rename it.** It is currently the "Fortunate Archive Format" in `fortunate-archive/`, produced by an
"Export for Fortunate" button. A GPL tool whose central artefact is branded after the proprietary
product that consumes it hands the derivative-work argument its best sentence. Name it after the open
producer instead: **the Excavator Archive**, directory `excavation/`, and the action is
**"Export archive"** — with "for Fortunate" at most a secondary label on a consumer-specific option.

**This repository holds the canonical specification.** The private importer *consumes* the format; it
does not co-own it. Two copies of one contract drift silently — the writer adds a field, the importer
assumes one, and nothing fails until real data does.

**Strip host fingerprints.** `manifest.json` currently carries `host_os`, `output_dir` and per-item
`media[].source_path`. This is the one artefact designed to leave the tool; it should not carry the
username, the machine or the filesystem layout. Keep `schema_version`, `source` (as a type, not a
path), run date and the coverage counts.

**Keep the coverage contract — it is the real star-earner.** `manifest.coverage` compares counts taken
directly from `chat.db` against what was exported, with `complete: false` on any unexplained
shortfall. Nothing else in this space tells you what it *failed* to read. A silently partial parse is
a FAIL, not a qualified pass.

Ship a JSON Schema and public fixtures so "any application can consume it" is demonstrable.

## 6. Privacy — one invariant, then rules

> **NO NETWORK CODE. EVER.** Not a policy — a testable invariant, enforced in CI.

Every other exclusion in spec §27 needs a socket: no telemetry, no cloud scoring, no account, no
automated outreach. One invariant guards the whole list, and it is the one to defend hardest, because
the exclusion most likely to fall first is "no Fortunate account" arriving as a harmless convenience
sync.

Consequences, all of which correct the spec:

- **Crash reporting: none.** Spec §22's "opt-in *or* clearly disclosed" contradicts the no-network
  promise. There is no version of uploading a crash from this app that is compatible with the
  invariant.
- **The derived cache is a second plaintext copy.** Its location, permissions and deletion must be
  documented wherever the archive's are.
- **Local AI (§23) is local-only** — no download path, no remote inference. "Prefer local" is a hedge;
  this is a hard line.
- **The export artefact is the real exposure.** `--output` is required with no default; refuse
  sync-folder destinations (iCloud Drive, Dropbox, OneDrive, Desktop & Documents Sync); print the
  destination before writing; document deletion, including the Time Machine copy.
- Reading `chat.db` requires **Full Disk Access** — broader than this feature needs. Say so plainly.

### Read-only, by construction

`get_connection` already opens with `SQLITE_OPEN_READ_ONLY`, which SQLite enforces at the file-handle
level — a real mechanism. But `rusqlite` is linked `bundled`, so write-capable APIs are compiled into
every binary; the flag is what stops writes, not the absence of capability. Make it structural:

1. **The engine's public API has no "execute this string" entrypoint.** Every query is a parameterised
   function. With no raw-SQL passthrough there is no path from an argument to a write, whatever the
   connection flags say. This is a stronger guarantee than the flag.
2. Defence in depth: hand the MCP process a read-only file descriptor or a read-only copy.
3. Test that a write against the connection returns `SQLITE_READONLY` — **run it against the MCP
   binary's connection path, not only the engine's.**

## 7. The humane rules — these are requirements, not tone

The app will surface people the user is grieving, escaping, or has deliberately stopped speaking to,
and **it cannot know which.** A cold table reading "last contact: 2019" is neutral; a handwritten
heading inviting you to remember is not. The warmer the register, the worse a misfire lands.

1. **The app never volunteers a name.** The Story screen shows counts. Lists of people open only when
   the user asks for them. "Firsts" is the sharpest edge here — the first message from a dead parent,
   served at random, is the failure case.
2. **"Put away" on every person.** Excluded from every view and statistic, never deleted, reversible
   from one quiet place. Optionally "Remember" for the dead, if it can be done without ceremony.
3. **Label the gap, not the mood** (§4). The data knows a duration. It does not know why.
4. **No photo the user did not open.** Media appears on request, never as decoration.

## 8. MCP — read-only, historical, and shaped by the same query layer

Lives in this repo as its own package. **No `send_message`, ever** — this tool remembers the past;
acting in the present belongs to a different, separately-licensed product.

Tools: `search_messages` · `find_people` · `get_person_history` · `get_first_message` ·
`get_recent_messages` · `get_relationship_stats` · `find_people_not_contacted_since` ·
`find_reconnections` · `list_shared_media` · `search_by_date_range` · `get_archive_summary`.

**Metadata-only by default.** Only three of those touch message bodies — `search_messages`,
`get_recent_messages`, `search_by_date_range` — and they return counts, participants, dates and
message ids unless content is explicitly requested through a separate, named call. This mirrors the
archive's own `content_included: false` default.

**Why that matters, stated honestly:** "your archive stays on this Mac" is true of the *file*. It is
not true of *what the file says* once a cloud-backed agent calls a content-returning tool — that text
goes to whatever model provider is behind the client. The server must disclose at connect time that
it is local, read-only and metadata-only by default, and that enabling content sends message text to
the connected client. A property an operator can audit, not a behaviour discovered by accident.

Every list-shaped tool reports `total_matches` alongside a truncated set, so a caller knows a result
is partial — the same honesty the coverage manifest applies to the archive.

## 9. Upstream discipline — mechanical, not aspirational

"Strongly consider contributing upstream" collapses the first time a deadline meets a fix. Make it
enforceable:

- **CI asserts a zero-diff in `imessage-database/` and `imessage-exporter/`.** This is true today —
  verified, 0 files changed — so the invariant starts green. Our work lives in new crates.
- Parser fixes go upstream first, as pull requests. Ours is the analysis layer.
- A recorded monthly upstream sync, logged in `NOTICE.md`.
- Offer the coverage manifest and the JSON export upstream before treating them as ours.

Beyond the licence, we owe ReagentX the schema-drift findings the spike produces, as issues.

## 10. Build order

1. **Run the spike** (`spike-plan.md`), steps 2, 5 and 6 especially: real coverage counts against a
   `chat.db` row count, real multi-handle behaviour, real onboarding magnitudes. Operator present.
   Nothing below is worth starting until this has run once.
2. **Identity resolution**, with confidence tiers and `person_centric_id` first.
3. **Relationship metrics**, against the §4 definitions.
4. **Archive writer** + the coverage manifest.
5. **MCP server** — before any UI. It forces the query-layer contract into existence under the
   strictest consumer (bounded, serialisable, self-describing) with no pixel work and no design
   review blocking it. A GUI would paper over a wrong return shape with front-end state; MCP cannot.
6. **The static HTML report.** This is the moment the project is genuinely useful to a stranger.
7. Only then, a desktop app.

## 11. What we are not building

No sending. No live messages. No automation. No CRM fields, lead scoring or propensity. No cloud
scoring. No account requirement. No Messages replacement. No Connector functionality.

**Look backward. Understand. Preserve. Export.**
