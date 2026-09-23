# Fortunate Excavator

> ### A fork of [`ReagentX/imessage-exporter`](https://github.com/ReagentX/imessage-exporter) by **Christopher Sardegna**, licensed **GPL-3.0-or-later**.
>
> Upstream wrote the hard part: a comprehensive, accurate parser for Apple's
> `chat.db`. This fork adds **local relationship analysis** on top of it, and
> tracks upstream as Apple's schema drifts.
>
> **The entire Excavator is GPL-3.0-or-later — upstream's code and every
> Fortunate addition alike.** Nothing here is proprietary, nothing is
> dual-licensed, and nothing added here narrows what you may do with it. This
> fork exists to *comply* with the GPL by releasing its modifications under the
> same licence — not to route around it.
>
> Modifications and their dates are recorded in [`NOTICE.md`](NOTICE.md), as
> GPL §5(a) requires. [`LICENSE`](LICENSE) is upstream's, unmodified.
>
> **Status: scaffold.** The analysis described in *What Fortunate adds* is
> specified and **not implemented**. What works today is everything upstream
> does — which is a lot; read on.

---

This crate provides both a library to interact with iMessage data as well as a binary that can perform some useful read-only operations using that data. The aim of this project is to provide the most comprehensive and accurate representation of iMessage data available.

This free and open-source software can:

- Save, export, backup, and archive iMessage data to open, portable formats
- Preserve multimedia content (images, videos, audio) from conversations
- Facilitate easy migration of message history between devices and platforms
- Run diagnostics on the iMessage database
- Give you full ownership and control over your communication history
- Support compliance with data retention policies or legal requirements
- Run on macOS, Linux, and Windows

## Example Export

![HTML Export Sample](/docs/hero.png)

## Binary

The `imessage-exporter` binary exports iMessage data to `txt` or `html` formats. It can also run diagnostics to find problems with the iMessage database.

Installation instructions for the binary are located [here](imessage-exporter/README.md).

## Library

The `imessage_database` library provides models that allow us to access iMessage information as native, cross-platform data structures.

Documentation for the library is located [here](imessage-database/README.md).

### Supported Features

This crate supports every iMessage feature as of macOS Golden Gate 27.0 (26A428) and iOS 27.0 (24A437):

- iMessage, RCS, SMS, and MMS
- Multi-part messages
- Replies/Threads
- Formatted text
- Attachments
- Expressives
- Tapbacks
- Stickers
- Apple Pay
- Group chats
- Digital Touch
- URL Previews
- Audio messages
- App Integrations
- Edited messages
- Business messages
- Handwritten messages

See more detail about supported features [here](docs/features.md).

## What Fortunate adds

Upstream answers *"what was said?"* — it exports conversations faithfully to
`txt` and `html`. Excavator adds a second question on top of the same parser:
***"who has been in my life, and for how long?"***

All of it is computed **on your Mac**. There is no account, no server, no
network call, and no telemetry. These features work for anyone who clones this
repository, with no relationship to Fortunate whatsoever.

**Planned capability (specified in [`docs/analysis-plan.md`](docs/analysis-plan.md), not yet implemented):**

- **Durable identities.** Phone numbers and emails normalized into stable person
  identifiers, with multiple handles for one person merged. *A display name is
  never an identity* — it changes, it collides, and it is absent for numbers you
  never saved.
- **First and last contact, per person**, and the span between them.
- **Message and conversation counts over time**, and years active.
- **Long gaps and reconnections** — the silences, and who broke them.
- **Media exchanged**, counted per relationship.
- **A relationship timeline** per person.
- **A standalone local HTML report** presenting all of the above. This is the
  main output: open it in a browser, read it, delete it. No further tooling
  required.
- **A structured archive** on disk — the [Excavator
  Archive](docs/archive-format.md): plain JSON, documented, and deliberately
  neutral. Anything can read it.

Fortunate's own desktop app is *one* consumer of that archive. Writing it is an
optional "Export archive" step; it is one button among these features, it is not
required, and the format is not shaped around it — see
[`docs/archive-format.md`](docs/archive-format.md), which is written so that
someone can build a completely different consumer.

### ⚠ Read this before you run an excavation

**The output is a copy of your message history in plain text.** Treat it like
one.

- **There is no default output directory.** `--output` is explicit, on purpose.
  A local-first tool that quietly writes an archive into iCloud Drive, Dropbox,
  or a Desktop/Documents folder under Desktop & Documents Sync has *uploaded
  your message history by accident*. Excavator will refuse a destination it
  detects as synced unless you override it deliberately, and it names the
  destination out loud before it writes a byte.
- **Delete the archive when you are done with it.** Guidance, including Time
  Machine's copy of it, is in [`docs/archive-format.md`](docs/archive-format.md)
  § *Deleting an excavation*.
- **Reading `chat.db` requires Full Disk Access** in System Settings → Privacy
  & Security. That is a broad grant. Give it to the binary, use it, and consider
  revoking it afterwards.

## Licence and provenance

This repository is **GPL-3.0-or-later**, in whole.

- It is a fork of [`ReagentX/imessage-exporter`](https://github.com/ReagentX/imessage-exporter),
  © Christopher Sardegna, and that project's `LICENSE` governs this one
  unchanged. Upstream's copyright notices are preserved throughout.
- **Fortunate's additions are GPL-3.0-or-later too.** They are modifications of
  a GPL work and they are released as the licence requires. You may use, study,
  modify and redistribute the whole thing under those terms, commercially
  included, so long as you pass the same freedoms along.
- Modifications made by Fortunate, with dates, are listed in
  [`NOTICE.md`](NOTICE.md) (GPL §5(a)).
- Fortunate's own desktop application is separate, proprietary software that is
  not in this repository and is not built from it. It reads an archive **a user
  chose to generate and chose to hand over** — the same archive any other
  program could read, in a format documented here for exactly that reason. It
  does not link this code, embed it, or ship it.

If you believe any part of this fork falls short of its GPL obligations, please
open an issue. That is a bug in this project and it will be fixed.

## Frequently Asked Questions

The FAQ document is located [here](/docs/faq.md).

## Special Thanks

- All of my friends, for putting up with me sending them random messages to test things
- [SQLiteFlow](https://www.sqliteflow.com), the SQL viewer I used to explore and reverse engineer the iMessage database
- [Xplist](https://github.com/ic005k/Xplist), an invaluable tool for reverse engineering the `payload_data` plist format
- [Compart](https://www.compart.com/en/unicode/), an amazing resource for looking up esoteric unicode details
- [GNU Project](https://github.com/gnustep/libobjc) and [Archive.org](https://archive.org/details/darwin_0.1), for hosting source code referenced to reverse engineer the `typedstream` format
