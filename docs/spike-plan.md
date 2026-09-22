# Spike plan — prove upstream parses a real archive before writing a line of our own

**Status: NOT STARTED** (2026-09-22). **This gate blocks the build.**

No Fortunate code — no identity resolution, no metrics, no archive writer, no
report — may be written until the steps below have **recorded results** in this
file. The question is simple and unanswered: *does this parser, on this machine,
read fourteen years of `chat.db` completely?* Everything in
[`analysis-plan.md`](analysis-plan.md) assumes the answer is yes.

---

## Rules for running this

- ⛔ **The operator must be present for every step that touches the real
  archive** (step 3 onward). It is their message history: years of private
  conversation with real people who did not consent to an agent reading it. **No
  agent runs an export unattended, on a schedule, or "just to check something".**
  A step that needs the archive and cannot have the operator is **not started** —
  it is not blocked, and it is not skipped.
- **Build upstream UNMODIFIED first.** The point of the first two steps is to
  measure the thing we inherited, not the thing we changed. Do not add a crate,
  do not touch a `Cargo.toml`, do not "just fix" a warning until step 7.
- **Record every result, including failures and "worked, but…".** The qualifier
  is usually the real content: *worked, but 4% of messages had empty bodies*;
  *worked, but took 40 minutes*.
- **Record what each result was tested against** — macOS version, commit SHA,
  archive size, date. A true-at-the-time claim with no version attached stays
  green forever.
- **A step that cannot be completed is a result.** Write down why.
- ### A silently partial parse is a FAIL, not a pass with an asterisk.
  This is the most important line in this document. A crash is honest. A clean
  exit code over a partial parse produces relationship numbers that are wrong
  and *plausible*, and nothing downstream would ever catch it. Coverage is
  measured against a `chat.db` row count, every time, or the step has not been
  done.

## The risk this is actually testing

**Not** macOS compatibility. Upstream claims support through macOS 27 and this
box is **macOS 14.8.9 Sonoma (23J631)** — comfortably inside that, and the
claim is upstream's own, freely given.

The real risk is **fourteen years of `chat.db` schema drift**:

- `typedstream`-encoded message bodies from older macOS releases, where `text`
  is null and the content lives in `attributedBody`.
- Attachments whose files no longer exist on disk, or whose paths point into
  long-gone directory layouts.
- Reactions/tapbacks, replies/threads, edited and unsent messages — features
  that **only exist in recent schemas**, so old rows lack the columns entirely.
- SMS/MMS rows alongside iMessage, with different conventions.
- Merged, duplicated and orphaned `handle` rows accumulated across devices and
  Apple ID changes.

Any of these can produce a clean run with missing data. That is the failure this
plan is built to catch.

---

## Step 1 — Build upstream, unmodified · ⬜ NOT STARTED

- [ ] Confirm the working tree is upstream-clean apart from documentation:
      `git diff --stat upstream/develop -- ':!*.md'` should be empty.
- [ ] `cargo build --release` in the workspace root.
- [ ] Record the toolchain: `rustc --version`, `cargo --version`, whether Xcode
      Command Line Tools were needed, and total build time.
- [ ] Run `./target/release/imessage-exporter --help`.

**Exit criterion:** the binary builds from this fork's source and prints help.
Not "it builds with a few warnings we ignored" — record the warnings.

```
commit built:
rustc / cargo:
build time:
warnings of note:
binary runs:            yes / no
```

## Step 2 — Baseline the source of truth · ⬜ NOT STARTED

**Operator present.** This step only *reads counts* — it does not export
anything — but it touches the real database, so the rule applies.

Full Disk Access is required. Grant it, note what you granted it to.

- [ ] Record `chat.db` size and last-modified date.
- [ ] Take the counts directly, with `sqlite3` against a **copy** of the
      database, never the live file:

```sh
cp ~/Library/Messages/chat.db /tmp/chatdb-baseline.db
sqlite3 /tmp/chatdb-baseline.db \
  "select count(*) from message;
   select count(*) from chat;
   select count(*) from handle;
   select count(*) from attachment;
   select datetime(min(date)/1000000000 + 978307200,'unixepoch','localtime') from message where date > 0;
   select datetime(max(date)/1000000000 + 978307200,'unixepoch','localtime') from message;"
```

- [ ] Also count the hard cases, because these are the ones that go missing:

```sh
sqlite3 /tmp/chatdb-baseline.db \
  "select count(*) from message where text is null and attributedBody is not null;
   select count(*) from message where associated_message_guid is not null;
   select count(*) from message where is_from_me = 0;"
```

- [ ] **Delete `/tmp/chatdb-baseline.db` when the numbers are written down.**

**Exit criterion:** a written set of counts to measure the export against. Without
this, step 4 cannot be performed at all — it can only be *claimed*.

```
chat.db size / modified:
messages:               chats:            handles:          attachments:
oldest message:                       newest message:
typedstream-only bodies (text null, attributedBody set):
tapback/reply rows (associated_message_guid set):
FDA granted to:                       (revoked after? yes / no)
```

## Step 3 — Run a full export · ⬜ NOT STARTED

**Operator present.**

- [ ] Choose the output path **explicitly and deliberately**, and confirm it is
      **not** inside iCloud Drive, Dropbox, or a Desktop/Documents folder under
      Desktop & Documents Sync. See [`archive-format.md`](archive-format.md) §7 —
      this is the hazard the whole `--output` design exists for, and the spike is
      the first time it becomes concrete rather than theoretical.
- [ ] Run a full export to `html` and note wall-clock time.
- [ ] Capture **all** stderr. Warnings here are findings, not noise.

**Exit criterion:** the export completes, or it fails, and either way the failure
mode is written down.

```
output path:                          (synced folder? yes / no — how verified:)
wall clock:
exit status:
stderr warnings (verbatim, or a count by type):
output size (with / without attachments):
peak memory / machine usable during run:
```

## Step 4 — Reconcile coverage against step 2 · ⬜ NOT STARTED

The step that decides whether any of this is trustworthy.

- [ ] Count messages in the export. Compare to step 2's `chat.db` count.
- [ ] **Quantify every shortfall and explain it.** An explained skip (a row type
      deliberately not exported) is fine and gets named. An unexplained one is a
      FAIL of this step regardless of exit code.
- [ ] Spot-check the **oldest** year and the **newest** year by eye with the
      operator. Middle years are not where this breaks.
- [ ] Check specifically: did `typedstream`-only bodies come through, or are they
      empty? Compare against step 2's count of them.
- [ ] Check how tapbacks, replies, attachments and group chats survived.

**Exit criterion:** an export whose message count reconciles with `chat.db`, with
any shortfall quantified and explained.

```
messages in chat.db:            messages in export:           delta:        (   %)
unexplained losses:
oldest-year spot-check:
newest-year spot-check:
typedstream bodies recovered:   (of            )
tapbacks / replies:
attachments (references resolving? files present on disk?):
group chats:
```

## Step 5 — Confirm durable identifiers exist · ⬜ NOT STARTED

A hard gate: without a durable join key there is no analysis layer, and
[`analysis-plan.md`](analysis-plan.md) §2 collapses.

- [ ] Confirm a **durable identifier** per person is available — phone number
      (in what format?) or email. **A display name is not one.**
- [ ] Check a person with **several handles** (two numbers, or a number plus an
      email): can they be merged, and on what evidence?
- [ ] Group chats: is each participant individually identified, or only the
      thread?
- [ ] Unsaved numbers — people never in Contacts. These matter most: they are
      exactly who a "lost touch" report should surface.
- [ ] Estimate, with the operator, what fraction of distinct handles are **not
      people**: short codes, businesses, 2FA senders, delivery bots.

**Exit criterion:** a named field, in real output, that can serve as the join
key — plus a recorded answer on multi-handle people and a rough non-human count.

```
identifier field(s) / format:
stable across years:            yes / no / qualified
multi-handle people:
group-chat participants:
unsaved numbers:
non-human fraction (operator's estimate):
```

## Step 6 — Produce the real onboarding numbers · ⬜ NOT STARTED

By hand, or with a throwaway script — **not** by starting the analysis crate.
The point is to learn the magnitudes before designing around them.

- [ ] total years of Messages
- [ ] distinct people (and how many are plausibly human)
- [ ] relationships spanning 5+ years
- [ ] people not contacted in 2+ years
- [ ] Compare against the illustrative *14 years · 1,200 people · 68 · 31*. The
      point is **not** that they match; it is that
      [`analysis-plan.md`](analysis-plan.md) assumes their order of magnitude.

**Exit criterion:** four real numbers and an honest note on how much of the
"people" count is noise.

```
years:                          distinct people:        (of which human:        )
5+ year relationships:          dormant 2+ years:
vs the illustrative figures:
```

## Step 7 — Confirm the additive shape holds · ⬜ NOT STARTED

Only after 1–6 have results. This is the last cheap moment to discover that the
plan in [`analysis-plan.md`](analysis-plan.md) §1 does not fit.

- [ ] Confirm `imessage-database` exposes the handles, chats, messages and
      attachments a separate crate can consume **without modifying upstream
      files**. Name the types.
- [ ] Confirm a new CLI subcommand can be added to `imessage-exporter` with a
      minimal upstream diff — and record how minimal.
- [ ] Confirm `git fetch upstream && git merge upstream/develop` is clean today,
      so that the sync path is known to work *before* we depend on it.

**Exit criterion:** either the additive plan is confirmed against real APIs, or
it is revised here and in `analysis-plan.md` **before** any code is written.

```
types the analysis crate will consume:
upstream diff required (files, lines):
upstream merge clean:           yes / no
plan revised?                   no / yes — what changed:
```

## Step 8 — Clean up · ⬜ NOT STARTED

Not optional, and not "later".

- [ ] Delete the export produced in step 3, and any database copy from step 2.
- [ ] Empty the Trash.
- [ ] Note whether Time Machine or any backup captured either, and what was done
      about it ([`archive-format.md`](archive-format.md) §8).
- [ ] Decide with the operator whether Full Disk Access is revoked.

```
export deleted:                 trash emptied:
backup copies:                  FDA revoked:
```

---

## Verdict · ⬜ NOT REACHED

Fill in only when steps 1–8 have results.

```
Parses a 14-year archive completely on this machine:     PASS / FAIL / QUALIFIED —
Durable identifiers derivable:                           PASS / FAIL / QUALIFIED —
Onboarding figures representative in magnitude:          PASS / FAIL / QUALIFIED —
Additive crate shape holds:                              PASS / FAIL / QUALIFIED —

recorded by / date:
```

**A FAIL is the gate working, not a setback to route around.** If coverage does
not reconcile, the correct next move is upstream — an issue, or a fix contributed
back under the same licence — not a workaround in our own layer that papers over
missing data.

Whether message metadata is even a good proxy for which relationships matter is
**not testable here.** It needs a real person looking at real output and saying
whether the right people came back. Do not mark it settled by this spike.
