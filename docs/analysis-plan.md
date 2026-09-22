# Analysis plan — what Excavator computes, and how

**Status: SPECIFICATION. None of this is implemented.** Written 2026-09-22.
**Nothing here may be built until [`spike-plan.md`](spike-plan.md) has recorded
results.** Every computation below assumes the upstream parser yields complete,
identifiable output over a long archive, and *nobody has checked that yet*.

This document covers the layer Fortunate adds on top of upstream's export: a
relationship view of the same data. It is part of this GPL repository and it
describes a **standalone local feature** — none of it requires a Fortunate
account, a network connection, or any relationship to Fortunate at all.

---

## 0 · The output it exists to produce

One standalone HTML file, opened from the user's own disk:

> **14 years of Messages · 1,200 people · 68 relationships spanning 5+ years ·
> 31 people you haven't spoken with in 2+ years**

⚠ **Those figures are illustrative, not measured.** They come from a sketch of
what the report should feel like, not from any real run. Producing the real ones
is an exit criterion of the spike, and if reality is an order of magnitude
different in either direction, the report design changes — not the numbers.

## 1 · Where the analysis reads from

**From upstream's parsed data structures inside this workspace** — not by
re-implementing `chat.db` parsing, and not by scraping upstream's `txt`/`html`
output.

That is now a plain engineering choice rather than a licence-driven contortion.
The whole workspace is one GPL program: `imessage-database` already models
handles, chats, messages and attachments correctly, including the parts that are
genuinely hard (`typedstream` bodies, tapbacks, edited messages), and re-deriving
any of it would be both wasteful and less accurate.

The analysis therefore lands as a **new crate beside the existing two**, not as
edits scattered through upstream's:

```text
imessage-database/     # upstream — read from, not modified
imessage-exporter/     # upstream — one new CLI subcommand, minimally
imessage-analysis/     # NEW — identity resolution, metrics, archive writer, report
```

Additive, so that `git merge upstream/develop` keeps working as Apple's schema
drifts — which [`spike-plan.md`](spike-plan.md) argues is the largest real risk
this project carries. Every deviation from that shape gets recorded in
[`../NOTICE.md`](../NOTICE.md).

## 2 · Identity resolution — the load-bearing step

Everything downstream joins on a person. If this step is wrong, every number in
the report is wrong in a way that still looks plausible.

**Rule: a display name is never an identity.** Names change, collide, and do not
exist for handles that were never saved to Contacts — which are exactly the
people a "who have I lost touch with?" report most wants to surface.

### Steps

1. **Collect handles.** Every `handle` row: phone numbers and email addresses.
2. **Normalize.** Phone numbers to E.164 where a region can be inferred; emails
   lowercased. **Keep the raw value** (`handles[].raw` in the archive) so a
   normalization error is auditable instead of invisible.
3. **Merge handles into people.** In descending order of confidence
   (reconciled with [`build-guide.md`](build-guide.md) §3, which wins):
   - `person-centric-id` — handles sharing Apple's own
     `handle.person_centric_id`. Apple's judgement, already parsed upstream
     (`Handle::person_centric_id`); the highest-confidence tier.
   - `exact-handle` — the same normalized handle. Certain.
   - `contact-card` — the Contacts database links them. Strong, and requires
     Contacts access the user must grant separately; without it this tier
     disappears and merge quality drops materially.
   - `same-thread` — handles that behave as one participant across threads.
     **Weak, and the source of most wrong merges — so it is never a merge.** It
     is recorded as a *suggestion* (`suggested_merges` in the archive) for the
     user to confirm or reject.
4. **Record the confidence** on the person, and let the report show a merge as
   provisional rather than asserting it.

### Known-hard cases, stated rather than discovered later

- One person with several numbers over fourteen years, plus two emails.
- Two people who have, at different times, used the **same** number (a recycled
  mobile number, a shared household line, an inherited work handle).
- SMS from `+14155550123` and iMessage from `sarah@example.com` being the same
  person, with nothing in the database linking them but a contact card.
- Short codes, businesses, two-factor senders, delivery and appointment bots.
  These are *not people*, they will inflate any "distinct people" count
  substantially, and the report must be honest about what fraction of the count
  they are. Heuristics (short numeric handles, one-way traffic, no replies ever)
  can *flag* them; they should not silently delete them.

⚠ **There is no ground truth against which to measure merge accuracy.** The only
available check is the operator looking at the merged list and saying whether it
is right. That is a real methodological limit, not a temporary one, and it
belongs in the report's own framing.

## 3 · The metrics

Each with what it needs and where it can mislead. All are computable from
metadata alone — no message bodies — except the one that is explicitly marked.

| Metric | Needs | Caveat |
|---|---|---|
| First contact, per person | earliest timestamp per `person_id` | Bounded by the archive, not by the friendship. A relationship predating this Mac's history looks like it began the day the database did. |
| Last contact, per person | latest timestamp | A relationship that moved to Signal, WhatsApp or real life reads as dormant. **The tool cannot see this and must not imply otherwise.** |
| Years connected | span between the two | Same bounding problem at both ends. |
| Message / conversation counts over time | counts bucketed by month and year | Volume is not closeness. Group chats inflate; a single close friend can be quiet. |
| Long gaps and reconnections | ordered timestamps per person, gap threshold | Threshold is a judgement call, not a fact. Default: a gap ≥ 12 months. A *reconnection* is that gap closed by **sustained** contact — ≥ N messages within M days — never one stray message ([`build-guide.md`](build-guide.md) §4). **N and M are an open decision for the operator**, taken before the detector is written and recorded in the manifest. Make both configurable and *show* them in the report. |
| Dormant relationships | last contact + dormancy threshold | Default 24 months. Same caveat: a person may simply be reachable elsewhere. |
| Media exchanged | attachment counts per person | Missing attachment files are counted from the database rows, not the disk; the archive's `file_present` distinguishes them. |
| Relationship timeline | all of the above, per person | Only as good as the identity merge behind it. |
| Frequently discussed topics | **message bodies** | **Out of scope for v1.** It is materially different from every other row: it requires reading content, which is a far larger privacy surface and a separate processing problem. It gets its own opt-in and its own stage, or it does not ship. |

### Deliberately not computed

- **Sentiment, tone, or relationship "health" scores.** Metadata does not support
  them and a number like that would be believed.
- **Anything ranking people against each other.** The report describes; it does
  not rate the user's friends.
- **Anything about the other party's behaviour** beyond what is symmetric with
  the user's own.

## 4 · The standalone report

One self-contained HTML file. No external requests, no CDN, no fonts fetched, no
analytics — it must render correctly on a machine with the network off, because
that is exactly how a cautious person will open it.

Sections, in order:

1. **The headline** — years, people, long relationships, dormant relationships,
   with the thresholds used stated inline.
2. **Coverage and honesty** — messages parsed vs messages in `chat.db`, taken
   from `manifest.coverage`. **If coverage is incomplete, this sits at the top,
   not in a footnote.** A report drawn from a partial parse says so before it
   says anything else.
3. **Timeline** — messages per year across the whole archive.
4. **People** — sortable: longest relationship, most recent, longest dormant,
   most messages. Merge confidence visible. Probable non-humans flagged and
   filterable, not deleted.
5. **Relationships worth noticing** — spanning 5+ years; dormant 2+ years;
   reconnections after a long gap.
6. **Per-person detail** — first and last contact, span, counts by year, gaps,
   media.
7. **What this cannot know** — the caveats above, in the report itself rather
   than only in this file. A user reading "you haven't spoken to Sarah in three
   years" deserves to see, on the same page, that the tool cannot see WhatsApp.

## 5 · Export archive

One optional step: write the [Excavator Archive](archive-format.md) to the
chosen `--output` directory. It is a button beside the others.

It is worth being exact about what it is and is not:

- It writes **a documented, neutral JSON archive to the user's own disk.**
- It **sends nothing.** Excavator has no network code and will not acquire any.
- What the user subsequently does with that directory — including handing it to
  Fortunate's separate, proprietary desktop app, or to any other program, or to
  nothing — is the user's decision, taken after the fact, with the archive in
  their possession.
- The format is specified in this repository precisely so that the second
  sentence of that list is verifiable rather than promised.

## 6 · Order of work

Nothing starts until the spike passes.

1. **Spike** ([`spike-plan.md`](spike-plan.md)) — upstream, unmodified, against
   a real archive, with the operator present.
2. **Identity resolution** — and hand-verification of the merged list with the
   operator. Before any metric is computed on top of it.
3. **Metrics** over resolved identities.
4. **Archive writer** — `manifest.json` coverage counts first, because coverage
   is what makes everything else trustworthy.
5. **HTML report.**
6. **Export archive** — last, because it is the least important of these
   and the tool must be worth running without it.
