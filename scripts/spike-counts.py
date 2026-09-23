#!/usr/bin/env python3
"""Spike steps 2, 5 and 6 — aggregate counts from a COPY of chat.db.

THROWAWAY by design (docs/spike-plan.md step 6: "by hand, or with a throwaway
script — not by starting the analysis crate"). It is not the analysis layer,
its identity grouping is deliberately crude, and it will be deleted when the
real engine exists.

Privacy: it prints and writes **counts only**. No names, no phone numbers, no
email addresses, no message text leave the database. The HTML page it writes
is for the operator's eyes, on this Mac — do not upload or share it.

    cp ~/Library/Messages/chat.db* /tmp/          # copy; never the live file
    python3 scripts/spike-counts.py /tmp/chat.db --html /tmp/spike.html
    rm /tmp/chat.db* /tmp/spike.html              # when the numbers are recorded

GPL-3.0-or-later, like the rest of this repository.
"""

import argparse
import html
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

APPLE_EPOCH = datetime(2001, 1, 1, tzinfo=timezone.utc)
# Throwaway thresholds, mirroring analysis-plan.md / build-guide.md §4.
LONG_YEARS, DORMANT_YEARS, GAP_DAYS = 5, 2, 365
RECONNECT_N, RECONNECT_M_DAYS = 3, 30


def apple_to_dt(v):
    """chat.db stores seconds (old schemas) or nanoseconds (new) since 2001."""
    if not v or v <= 0:
        return None
    secs = v / 1e9 if v > 1e11 else v
    return APPLE_EPOCH + timedelta(seconds=secs)


def one(db, sql):
    return db.execute(sql).fetchone()[0]


def has_column(db, table, col):
    return any(r[1] == col for r in db.execute(f"PRAGMA table_info({table})"))


def looks_non_human(handle_id):
    """Short codes and obvious machine senders. A guess, reported as a guess."""
    if "@" in handle_id:
        local = handle_id.split("@", 1)[0].lower()
        return bool(re.match(r"(no-?reply|notifications?|alerts?|info|support|mailer)", local))
    digits = re.sub(r"\D", "", handle_id)
    return 0 < len(digits) <= 6


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("db", help="path to a COPY of chat.db")
    ap.add_argument("--html", help="also write a local, counts-only HTML page here")
    a = ap.parse_args()
    if a.db.rstrip("/").startswith(f"{__import__('os').path.expanduser('~')}/Library/Messages"):
        sys.exit("Refusing to read the live database. Copy it first (see --help).")

    db = sqlite3.connect(f"file:{a.db}?mode=ro", uri=True)

    # ---- Step 2: the source of truth -------------------------------------
    s2 = {
        "messages": one(db, "select count(*) from message"),
        "chats": one(db, "select count(*) from chat"),
        "handles": one(db, "select count(*) from handle"),
        "attachments": one(db, "select count(*) from attachment"),
        "typedstream-only bodies (text null, attributedBody set)":
            one(db, "select count(*) from message where text is null and attributedBody is not null"),
        "tapback/reply rows (associated_message_guid set)":
            one(db, "select count(*) from message where associated_message_guid is not null"),
        "received (is_from_me = 0)": one(db, "select count(*) from message where is_from_me = 0"),
        "messages with no date": one(db, "select count(*) from message where date is null or date <= 0"),
    }
    lo, hi = db.execute("select min(date), max(date) from message where date > 0").fetchone()
    oldest, newest = apple_to_dt(lo), apple_to_dt(hi)

    # ---- Step 5: identifiers ---------------------------------------------
    pcid = has_column(db, "handle", "person_centric_id")
    handles = db.execute(
        f"select rowid, id, {'person_centric_id' if pcid else 'null'} from handle"
    ).fetchall()
    person_of = {}  # handle rowid -> crude person key
    for rowid, hid, pc in handles:
        person_of[rowid] = f"pc:{pc}" if pc else f"id:{(hid or '').strip().lower()}"
    kinds = Counter("email" if "@" in (h or "") else "phone/other" for _, h, _ in handles)
    s5 = {
        "person_centric_id column present": "yes" if pcid else "no",
        "handles with person_centric_id": sum(1 for *_, pc in handles if pc),
        "handles that are email": kinds["email"],
        "handles that are phone/other": kinds["phone/other"],
        "people with 2+ handles (by person_centric_id)":
            len({pc for *_, pc in handles if pc and sum(1 for *_, q in handles if q == pc) > 1}),
        "duplicate handle rows (same identifier, e.g. SMS + iMessage)":
            len(handles) - len({(h or "").strip().lower() for _, h, _ in handles}),
    }

    # ---- Step 6: onboarding magnitudes (crude) ---------------------------
    # A person's contact = messages they sent, plus messages in a direct
    # (one-other-participant) chat with them. Group sends from me are not
    # attributed to anyone; that undercounts, and says so.
    direct = dict(db.execute(
        "select chat_id, min(handle_id) from chat_handle_join group by chat_id having count(*) = 1"
    ).fetchall())
    times = defaultdict(list)
    per_year = Counter()
    rows = db.execute(
        "select m.date, m.handle_id, m.is_from_me, cmj.chat_id from message m "
        "left join chat_message_join cmj on cmj.message_id = m.rowid where m.date > 0"
    )
    for date, handle_id, from_me, chat_id in rows:
        dt = apple_to_dt(date)
        if not dt:
            continue
        per_year[dt.year] += 1
        h = handle_id if handle_id else direct.get(chat_id)
        if not h and chat_id in direct:
            h = direct[chat_id]
        if h and h in person_of:
            times[person_of[h]].append(dt)

    ids_by_person = defaultdict(set)
    for rowid, hid, _ in handles:
        ids_by_person[person_of[rowid]].add(hid or "")
    non_human = {p for p, ids in ids_by_person.items() if all(looks_non_human(i) for i in ids)}

    now = newest or datetime.now(timezone.utc)
    people = [p for p in times]
    humans = [p for p in people if p not in non_human]
    span = {p: (max(times[p]) - min(times[p])) for p in humans}
    long_rel = sum(1 for p in humans if span[p] >= timedelta(days=365.25 * LONG_YEARS))
    dormant = sum(1 for p in humans if now - max(times[p]) >= timedelta(days=365.25 * DORMANT_YEARS))
    gaps = reconnects = 0
    for p in humans:
        ts = sorted(times[p])
        for i in range(1, len(ts)):
            if ts[i] - ts[i - 1] >= timedelta(days=GAP_DAYS):
                gaps += 1
                window = [t for t in ts[i:i + RECONNECT_N] if t - ts[i] <= timedelta(days=RECONNECT_M_DAYS)]
                if len(window) >= RECONNECT_N:
                    reconnects += 1
    years = round((newest - oldest).days / 365.25, 1) if oldest and newest else 0
    s6 = {
        "years of Messages": years,
        "distinct people with any contact (crude grouping)": len(people),
        f"  of which look non-human (short codes, no-reply)": len(people) - len(humans),
        f"relationships spanning {LONG_YEARS}+ years": long_rel,
        f"people not contacted in {DORMANT_YEARS}+ years": dormant,
        f"gaps of {GAP_DAYS}+ days": gaps,
        f"reconnections ({RECONNECT_N}+ msgs within {RECONNECT_M_DAYS} days of a gap)": reconnects,
        "handles with no attributable messages": len(set(person_of.values())) - len(people),
    }

    # ---- Output ------------------------------------------------------------
    def block(title, d):
        print(f"\n{title}")
        for k, v in d.items():
            print(f"  {k:<62} {v:>12,}" if isinstance(v, int) else f"  {k:<62} {v:>12}")

    print(f"oldest message: {oldest:%Y-%m-%d}   newest: {newest:%Y-%m-%d}" if oldest else "no dated messages")
    block("STEP 2 — source counts", s2)
    block("STEP 5 — identifiers", s5)
    block("STEP 6 — magnitudes (crude, throwaway)", s6)
    print("\nMessages per year:")
    top = max(per_year.values() or [1])
    for y in sorted(per_year):
        print(f"  {y}  {per_year[y]:>9,}  {'█' * max(1, round(40 * per_year[y] / top))}")

    if a.html:
        write_html(a.html, oldest, newest, s2, s5, s6, per_year)
        print(f"\nWrote {a.html} — counts only. Open it locally; delete it when done.")


def write_html(path, oldest, newest, s2, s5, s6, per_year):
    def table(title, d):
        rows = "".join(
            f"<tr><th>{html.escape(k.strip())}</th><td>{v:,}</td></tr>" if isinstance(v, int)
            else f"<tr><th>{html.escape(k.strip())}</th><td>{html.escape(str(v))}</td></tr>"
            for k, v in d.items())
        return f"<section><h2>{title}</h2><table>{rows}</table></section>"
    top = max(per_year.values() or [1])
    bars = "".join(
        f"<div class=bar><span>{y}</span><i style='width:{100 * n / top:.1f}%'></i><b>{n:,}</b></div>"
        for y, n in sorted(per_year.items()))
    headline = (f"{s6['years of Messages']} years of Messages · "
                f"{s6['distinct people with any contact (crude grouping)'] - s6['  of which look non-human (short codes, no-reply)']:,} people · "
                f"{s6[f'relationships spanning {LONG_YEARS}+ years']:,} relationships spanning {LONG_YEARS}+ years · "
                f"{s6[f'people not contacted in {DORMANT_YEARS}+ years']:,} not contacted in {DORMANT_YEARS}+ years")
    span = f"{oldest:%B %Y} – {newest:%B %Y}" if oldest else ""
    doc = f"""<!doctype html><html lang=en><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Spike counts</title>
<style>
:root{{--bg:#fbfaf7;--fg:#1d1c1a;--mute:#6b6760;--line:#e4e0d8;--bar:#8a7a5c}}
@media (prefers-color-scheme:dark){{:root{{--bg:#171614;--fg:#ece9e2;--mute:#9a958b;--line:#2e2c28;--bar:#b8a57e}}}}
body{{background:var(--bg);color:var(--fg);font:15px/1.5 -apple-system,system-ui,sans-serif;margin:0;padding:32px 16px}}
main{{max-width:760px;margin:auto}} h1{{font-size:22px;margin:0 0 4px}} .sub{{color:var(--mute);margin:0 0 24px}}
.head{{font-size:18px;padding:16px 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}}
h2{{font-size:13px;text-transform:uppercase;letter-spacing:.06em;color:var(--mute);margin:28px 0 8px}}
table{{width:100%;border-collapse:collapse}} th,td{{padding:6px 0;border-bottom:1px solid var(--line);font-weight:400;text-align:left}}
td{{text-align:right;font-variant-numeric:tabular-nums}}
.bar{{display:grid;grid-template-columns:44px 1fr 80px;gap:8px;align-items:center;font-variant-numeric:tabular-nums}}
.bar i{{display:block;height:12px;background:var(--bar);border-radius:2px}} .bar b{{font-weight:400;text-align:right}}
.note{{color:var(--mute);font-size:13px;margin-top:28px}}
</style><main>
<h1>Spike counts</h1><p class=sub>{span} · counts only, no names · throwaway, from scripts/spike-counts.py</p>
<p class=head>{html.escape(headline)}</p>
{table("Step 2 — source counts", s2)}
{table("Step 5 — identifiers", s5)}
{table("Step 6 — magnitudes (crude)", s6)}
<section><h2>Messages per year</h2>{bars}</section>
<p class=note>People are grouped crudely (Apple's person_centric_id, else the exact handle). Group messages you sent
are not attributed to anyone. Non-human detection is a guess. A person reachable on another app reads as dormant here —
this cannot see WhatsApp, Signal, calls or real life. Delete this file when the numbers are recorded.</p>
</main></html>
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(doc)


if __name__ == "__main__":
    main()
