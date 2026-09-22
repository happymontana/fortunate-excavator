# The Excavator Archive

**Status: SPECIFICATION — nothing writes this yet.** Written 2026-09-22.
`schema_version` is `1` and it is *provisional*: it may change without
compatibility guarantees until the spike in [`spike-plan.md`](spike-plan.md)
has run against a real archive. Real output has a way of invalidating a format
designed in the abstract, and this one has not met any.

This document specifies the structured output of Fortunate Excavator: what it
writes to disk, where, and what each field means. The format is named after the
open tool that produces it, not after any program that consumes it; the action
that writes it is **"Export archive"**.

**This repository holds the canonical specification.** Any consumer — including
Fortunate's separate, private importer — reads this format; none co-owns it. See
§9.

> **This is a neutral interchange format, not a Fortunate payload.** It is
> documented here, in the GPL repository, because *this tool's* users need it —
> the archive is theirs, on their disk, and they are entitled to know its shape
> and to write their own consumer. Fortunate's desktop app is one consumer among
> however many exist. If a future field only makes sense to Fortunate, that is a
> defect in this format, and the fix is to generalise it or drop it.

---

## 1 · Layout

```text
<output-dir>/                  # chosen with --output; there is NO default
  excavation/                  # the archive itself; delete this to delete it
    manifest.json              # schema version, source, run date, coverage counts
    people.json                # normalized identities
    conversations.json         # spans, participants, counts
    messages.json              # message metadata
    media/                     # attachment references
    report.html                # the standalone local report (self-contained)
```

Every file is UTF-8 JSON with a trailing newline. Timestamps are **ISO 8601 with
an explicit offset** (`2019-04-07T18:22:04-07:00`), never Apple epoch integers —
a consumer must not need to know Core Data's epoch to read this.

Identifiers (`person_id`, `conversation_id`) are opaque strings, stable across
runs over the same `chat.db`, and meaningless outside one archive. Do not parse
them.

## 2 · `manifest.json`

The file a consumer reads **first**, and the only one it may assume exists.

```json
{
  "schema_version": 1,
  "generator": {
    "name": "fortunate-excavator",
    "version": "0.1.0",
    "upstream": "ReagentX/imessage-exporter",
    "upstream_commit": "0d444ab3220f5940d4632c05da4628009c785a02"
  },
  "source": {
    "kind": "chat.db",
    "db_modified_at": "2026-09-21T23:11:02-07:00"
  },
  "run": {
    "started_at": "2026-09-22T09:04:11-07:00",
    "completed_at": "2026-09-22T09:31:47-07:00"
  },
  "coverage": {
    "messages_in_source": 1483221,
    "messages_exported": 1483221,
    "messages_skipped": 0,
    "skipped_reasons": {},
    "attachments_in_source": 94210,
    "attachment_files_present": 88117,
    "handles_in_source": 3140,
    "people_after_normalization": 1207,
    "complete": true
  },
  "content_included": false,
  "warnings": []
}
```

### No host fingerprints

The archive is the one artefact designed to leave the tool, so it carries **no
information about the machine that produced it**: no username, no hostname, no
OS build, no absolute paths — not the source database's, not the output
directory's, not any attachment's. `source.kind` records *what type* of source
was read (`chat.db`, `ios-backup`), never where it lives. A writer that adds a
field of this kind is defective. The run's destination is printed to the
terminal before writing (§7); it is not recorded in the output.

### `coverage` is the point of the manifest

**A silently partial parse is the failure mode this format exists to make
impossible.** Counts are taken from `chat.db` directly, *not* from what the
exporter produced, and the two are compared.

- `complete` is `true` **only** when `messages_exported + messages_skipped ==
  messages_in_source` **and** every skip is accounted for in `skipped_reasons`.
- Any unexplained shortfall sets `complete: false` and adds a `warnings` entry.
- **A consumer must check `complete` and must surface `false` to the user.**
  Relationship conclusions drawn from a quietly incomplete archive are plausible
  and wrong, which is worse than an error.
- `attachment_files_present < attachments_in_source` is normal and is not
  incompleteness — old attachment files genuinely vanish. It is reported because
  a media count that silently excludes them would otherwise be a mystery.

`content_included` records whether any message **bodies** are present. It is
`false` for a metadata-only excavation, which is the default and is sufficient
for every analysis in [`analysis-plan.md`](analysis-plan.md) except topic
extraction.

## 3 · `people.json`

```json
{
  "schema_version": 1,
  "people": [
    {
      "person_id": "p_7f3a91c2",
      "handles": [
        { "kind": "phone", "value": "+14155550123", "raw": "(415) 555-0123" },
        { "kind": "email", "value": "sarah@example.com", "raw": "Sarah@Example.com" }
      ],
      "display_names_seen": ["Sarah", "Sarah M", "Sarah Mitchell"],
      "first_contact": "2011-06-14T10:02:00-07:00",
      "last_contact": "2024-02-03T21:40:11-08:00",
      "message_count": 8412,
      "conversation_ids": ["c_1a2b", "c_9f0e"],
      "merged_from": ["+14155550123", "sarah@example.com"],
      "merge_confidence": "contact-card"
    }
  ],
  "suggested_merges": [
    { "person_ids": ["p_7f3a91c2", "p_02c4d9e1"], "evidence": "same-thread" }
  ]
}
```

**Identity rules — these are the contract, not implementation detail:**

- A **`person_id` is derived from handles, never from a display name.** Display
  names change, collide ("Mom"), and are absent entirely for numbers that were
  never saved to Contacts. `display_names_seen` is there for the UI to *label*
  a person; a consumer must never join on it.
- Phone handles are normalized to **E.164** where a region can be determined;
  `raw` preserves what the database actually held so that a normalization
  mistake is auditable rather than invisible.
- Merging several handles into one person is an **inference**, and
  `merge_confidence` says how it was reached. The values, most to least
  confident: `person-centric-id` (Apple's own `handle.person_centric_id`
  grouping), `exact-handle` (the same normalized identifier), `contact-card`
  (linked by a Contacts card), and `single` (one handle, nothing merged).
  **Nothing weaker than `contact-card` is ever merged.** Weaker evidence —
  handles that behave like one participant across threads, for instance — is a
  *suggestion* the user confirms or rejects, recorded in `suggested_merges`
  below, never folded into a person silently. A consumer may present merges as
  provisional. See
  [`analysis-plan.md`](analysis-plan.md) § *Identity resolution* for the
  known-hard cases; the honest position is that some merges will be wrong.

## 4 · `conversations.json`

```json
{
  "schema_version": 1,
  "conversations": [
    {
      "conversation_id": "c_1a2b",
      "kind": "direct",
      "participant_ids": ["p_7f3a91c2"],
      "display_name": null,
      "service": ["iMessage", "SMS"],
      "first_message_at": "2011-06-14T10:02:00-07:00",
      "last_message_at":  "2024-02-03T21:40:11-08:00",
      "message_count": 8412,
      "sent_count": 4106,
      "received_count": 4306,
      "attachment_count": 311
    }
  ]
}
```

`kind` is `direct` or `group`. A group conversation lists every participant it
could identify; where a participant could not be resolved to a person, that is
recorded in `manifest.warnings` rather than silently dropped.

## 5 · `messages.json`

**Metadata, not content.** One record per message.

```json
{
  "schema_version": 1,
  "content_included": false,
  "messages": [
    {
      "message_id": "m_004a17b3",
      "conversation_id": "c_1a2b",
      "person_id": "p_7f3a91c2",
      "direction": "received",
      "sent_at": "2019-04-07T18:22:04-07:00",
      "service": "iMessage",
      "kind": "text",
      "has_attachments": false,
      "attachment_ids": [],
      "is_reply": false,
      "is_tapback": false,
      "is_edited": false,
      "char_count": 47
    }
  ]
}
```

- `char_count` is a length, not content. It supports "who wrote more" without
  reading anything.
- A `text` field appears **only** when `content_included` is `true`, which
  requires an explicit opt-in flag and applies only to the people the user
  selected. A consumer must handle its absence as the normal case.
- `messages.json` is the large file — millions of records on a long archive. It
  is written as a single JSON document for simplicity in v1; if that proves
  unworkable at real scale the format will move to JSON Lines, and that is
  precisely the kind of change the spike is meant to force before v1 is frozen.

## 6 · `media/`

**References, not a copy of the library.** By default Excavator does not
duplicate gigabytes of photographs.

```json
{
  "schema_version": 1,
  "attachments": [
    {
      "attachment_id": "a_6620fe",
      "message_id": "m_004a17b3",
      "conversation_id": "c_1a2b",
      "mime_type": "image/jpeg",
      "byte_size": 1840221,
      "created_at": "2019-04-07T18:22:04-07:00",
      "file_name": "IMG_0421.JPEG",
      "file_present": true,
      "copied_to": null
    }
  ]
}
```

That index lives at `media/attachments.json`. When a run is asked to copy files,
they land under `media/files/` and `copied_to` is a path relative to the archive
root. `file_present: false` means the database references a file the disk no
longer has — common, expected, and reported rather than hidden. `file_name` is
the base name only; the source path is deliberately not recorded (§2, *No host
fingerprints*).

## 7 · Where the archive goes, and why there is no default

**There is no default output directory. `--output` is required.**

`~/Excavation` is the *suggested* location shown in documentation and
in the tool's own help text. It is a suggestion the user must actually type or
confirm, and it is deliberately **not** a silent fallback.

A default is the whole hazard. Every plausible default on a Mac — `~/Desktop`,
`~/Documents`, the current directory — is a folder that Desktop & Documents
Sync, iCloud Drive or Dropbox may be synchronising. A local-first tool that
writes a plaintext copy of fourteen years of private conversation into a synced
folder has uploaded it, and neither it nor the user will notice.

Therefore:

1. `--output` is explicit and required.
2. Before writing, Excavator **checks the destination for sync markers** —
   iCloud Drive / Mobile Documents paths, Desktop & Documents Sync,
   `.dropbox`-managed trees, OneDrive, Google Drive — and **refuses**, naming
   what it found, unless the user passes an explicit override.
3. Whether or not a marker was found, it **prints the absolute destination and
   what is about to be written** before writing anything.
4. Detection is best-effort and says so. A clean check is not a guarantee that
   no sync client is watching that path.

**Reading `chat.db` requires Full Disk Access** (System Settings → Privacy &
Security → Full Disk Access) for the binary — or for the terminal running it.
That is a much broader grant than this task needs; it is macOS's, not ours.
Excavator states this before it asks for anything and does not attempt to
acquire it silently.

## 8 · Deleting an excavation

An archive you have finished with should be destroyed, and the documentation
says so plainly rather than leaving it to the user to think of.

- **Delete the whole output directory.** Then empty the Trash — a Trashed
  archive is still a plaintext archive.
- **Time Machine and any other backup will have a copy.** Deleting the original
  does not reach it. If the archive was written to a backed-up volume, exclude
  the directory *before* the run (System Settings → General → Time Machine →
  Options), or accept that the copy exists.
- **If it was written into a synced folder despite the checks, deleting it
  locally is not enough** — it must also be removed from the provider, and
  provider version history may retain it longer still.
- Excavator does not encrypt the archive at rest. If that matters for your
  threat model, write it to an encrypted disk image or an encrypted volume.

## 9 · Versioning, and the divergence risk

`schema_version` is a single integer and appears in **every** file, so a
consumer reading one file in isolation can still tell what it is holding.

- Additive fields do **not** bump it. Consumers must ignore unknown fields.
- Removing or re-meaning a field **does** bump it.
- A consumer that finds a `schema_version` it does not know must refuse the
  archive and say so, not guess.

**This document is canonical.** Consumers — Fortunate's private importer among
them — consume the format; they do not co-own it. Two copies of one contract
drift silently: the writer adds a field, the importer assumes one, and nothing
fails until real data does. So there is one copy, here, where this tool's
independent users can read it. A consumer that needs something the format lacks
raises it against this repository; it does not extend a private copy.

A JSON Schema and public, synthetic fixtures will ship beside this document when
the writer does, so that "any application can consume it" is demonstrable rather
than claimed.
