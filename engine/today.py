"""
today.py - one list a day, ranked, with every line carrying its reason.

For one person running a business the scarce thing was never data. It was
attention. You can hold thousands of records and speak to a handful of people,
so the only question worth answering each day is: who do I speak to, and why.

This produces one page. Many signals go in, one short list comes out. If it is
longer than a page it will not be read, so it is capped at what you said you can
actually get through.

HOW IT ORDERS

By how perishable the signal is, not by how important the person is. A reply that
arrived this morning goes above a profile change from a fortnight ago, and that
is not a claim that the person who replied matters more. It is a claim that the
reply stops being worth answering much faster.

The evidence behind that is thinner than the industry pretends. The widely quoted
study of lead response time was funded by a company selling lead response
software, and its headline multiple should be read as indicative rather than
settled. But the direction is not seriously disputed, and acting on it costs
nothing: ordering a list you were going to work anyway is free.

WHAT NEVER APPEARS

Anyone you have taken a conversation over with yourself. Friends and family.
Anyone you have marked as not a buyer. The list is what to act on, and acting on
somebody you deliberately picked up by hand is exactly what the hold in Layer 6
exists to prevent.

WHAT PARKS ITSELF

A signal that nobody acted on ages out. It does not pile up, it does not turn
into a backlog, and nobody has to decide to give up on it. That is deliberate:
a list that only grows is a list you stop opening, and the guilt of an unworked
queue is what kills a CRM more reliably than any missing feature.

Nothing here sends, drafts, or decides what to say. It orders.

Use:
    python today.py                 print the list
    python today.py --write         also write Today.md
    python today.py --limit 10

Needs: Python 3.8 or newer. Nothing else.
"""

import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import crm_paths

# What counts as a reason to speak to somebody, in order of how quickly it goes
# off. The number is a priority, not a score: it says which of two people to
# speak to first, and nothing about anybody's worth.
#
#   event              rank  what the line will say        days it stays live
# These names must match exactly what the records layer writes into the log.
# They are not a separate vocabulary: a name invented here that the writer never
# uses produces a list that is permanently empty while every part reports success,
# which is the worst kind of failure because nothing looks broken.
REASONS = [
    ("reply_received",   1,   "replied",                     2),
    ("call_booked",      2,   "booked a call",               7),
    ("details_changed",  3,   "changed role",               14),
    ("they_engaged",     4,   "engaged with something you posted", 7),
    ("comment_made",     5,   "you commented on their work",  3),
    ("joined",           6,   "joined the community",        14),
    ("connected",        7,   "a new connection",             7),
]

DUE_A_TOUCH_RANK = 8

# How long silence lasts before a thread parks itself.
PARK_AFTER_DAYS = 30

# States that are never on the list, whatever else is true about them.
NEVER_ON_THE_LIST = ("held", "suppressed", "personal", "friend", "family",
                     "non-buyer", "not-a-buyer", "parked")

# Front matter fields that might carry one of those.
STATE_FIELDS = ("relationship-state", "contact-type", "category", "relationship")


# ------------------------------------------------------------------ reading in

def read_events(ledger_path=None):
    """Every event, oldest first.

    The event log is one JSON object per line: a timestamp, a type, and the
    person it is about. That is Layer 3's format and this layer only reads it.

    A malformed line is skipped rather than raising. One bad line must never make
    the whole history unreadable, because the history is the only thing here that
    cannot be rebuilt.
    """
    path = Path(ledger_path) if ledger_path else crm_paths.ledger_path()
    if not path.exists():
        return []
    out = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if isinstance(event, dict):
                out.append(event)
    return out


def _age_hours(ts, now=None):
    now = now or datetime.now(timezone.utc)
    try:
        t = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
    if not t.tzinfo:
        t = t.replace(tzinfo=timezone.utc)
    return (now - t).total_seconds() / 3600.0


# --------------------------------------------------------------- who is excluded

def _held_check():
    """Use Layer 6's hold list if it is installed, and say so if it is not.

    Returns a function taking a person and answering whether they are held. If
    Layer 6 is absent the answer is always False, which is correct: there is no
    hold list, so nobody is held. It is reported once rather than assumed
    quietly, because silently ignoring a safety layer is how one stops working.
    """
    try:
        import holds
        return holds.is_held_person, True
    except Exception:
        return (lambda *a: False), False


def _squash(text):
    """Letters and digits only, lower case. So that a name, a filename and an
    identifier that differ only in punctuation still land on the same record."""
    return re.sub(r"[^a-z0-9]+", "", str(text).lower())


def _note_for(person):
    """The record for one person, matched by filename, then by identifier."""
    folder = crm_paths.people_dir()
    if not folder.exists():
        return None
    want = _squash(person)
    if not want:
        return None
    notes = sorted(folder.glob("*.md"))
    for note in notes:
        if _squash(note.stem) == want:
            return note
    for note in notes:
        head = note.read_text(encoding="utf-8", errors="replace")[:2000]
        for line in head.splitlines():
            if ":" not in line:
                continue
            _, _, value = line.partition(":")
            value = value.strip().strip('"\'')
            if value and _squash(value).endswith(want):
                return note
    return None


def marked_off_the_list(person):
    """True if this person's own record says they never belong on the list.

    Read from the record rather than guessed. Somebody being a friend, or having
    told you they are never buying, is a fact about them that belongs on their
    record, not a rule buried in the ordering code.
    """
    note = _note_for(person)
    if not note:
        return False
    text = note.read_text(encoding="utf-8", errors="replace")[:2000]
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return False
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line:
            continue
        field, _, value = line.partition(":")
        field = field.strip().lower()
        value = value.strip().strip('"\'').lower()
        if field == "never-on-the-list" and value in ("true", "yes"):
            return True
        if field in STATE_FIELDS and value in NEVER_ON_THE_LIST:
            return True
    return False


# ------------------------------------------------------------------- the ordering

def build(limit=None, ledger_path=None, now=None):
    """Return the ranked list. One row per person, under their strongest reason.

    A person appears once. If they replied AND changed role, the reply is what
    the line says, because that is the one that goes off fastest.
    """
    now = now or datetime.now(timezone.utc)
    limit = int(limit or crm_paths.config().get("daily-capacity", 20) or 20)
    events = read_events(ledger_path)
    is_held, have_holds = _held_check()

    best = {}
    last_seen = {}
    parked = 0

    for event in events:
        person = event.get("person")
        if not person:
            continue                       # an event nobody can attribute is a gap
        age = _age_hours(event.get("ts"), now)
        if age is not None:
            prev = last_seen.get(person)
            if prev is None or age < prev:
                last_seen[person] = age
        for etype, rank, label, window in REASONS:
            if event.get("type") != etype:
                continue
            if age is None or age > window * 24:
                continue
            row = {"person": person, "rank": rank, "reason": label,
                   "age_hours": age, "ts": event.get("ts")}
            current = best.get(person)
            if not current or (row["rank"], row["age_hours"]) < \
                    (current["rank"], current["age_hours"]):
                best[person] = row

    # A cadence touch is a real reason, and it never outranks a live signal.
    for person, age in last_seen.items():
        if person in best:
            continue
        if age is None:
            continue
        if age > PARK_AFTER_DAYS * 24:
            parked += 1                    # it aged out on its own; nobody decided
            continue
        best[person] = {"person": person, "rank": DUE_A_TOUCH_RANK,
                        "reason": "quiet, and due a word", "age_hours": age,
                        "ts": None}

    rows = []
    left_off = {"held": 0, "marked": 0}
    for person, row in best.items():
        if is_held(person):
            left_off["held"] += 1
            continue
        if marked_off_the_list(person):
            left_off["marked"] += 1
            continue
        rows.append(row)

    rows.sort(key=lambda r: (r["rank"], r["age_hours"]))
    kept = rows[:limit]
    for row in kept:
        row["left_off"] = left_off
        row["parked"] = parked
        row["holds_installed"] = have_holds
        row["over_capacity"] = max(len(rows) - limit, 0)
    if not kept:
        return []
    return kept


def summary(rows):
    """The counts a reader needs to trust the page, taken off the first row."""
    if not rows:
        return {"held": 0, "marked": 0, "parked": 0, "over": 0, "holds_installed": True}
    first = rows[0]
    return {"held": first["left_off"]["held"],
            "marked": first["left_off"]["marked"],
            "parked": first["parked"],
            "over": first["over_capacity"],
            "holds_installed": first["holds_installed"]}


def _age_words(hours):
    if hours is None:
        return ""
    if hours < 1:
        return "%d minutes ago" % max(int(hours * 60), 1)
    if hours < 48:
        return "%d hours ago" % int(hours)
    return "%d days ago" % int(hours / 24)


def render(rows, start_time=None):
    """The page. Plain markdown, rewritten from scratch every run."""
    stamp = datetime.now(timezone.utc).date().isoformat()
    if not rows:
        return ("# Today\n\n"
                "Nothing is waiting.\n\n"
                "That is a real answer, not an empty page. Every signal has either\n"
                "been acted on or aged out on its own. Nothing is sitting in a pile\n"
                "waiting for you to feel guilty about it.\n")

    counts = summary(rows)
    out = ["# Today", ""]
    if start_time:
        out.append("_Built for %s. Open this before you open your inbox._" % start_time)
    else:
        out.append("_Open this before you open your inbox._")
    out += ["",
            "_Generated %s from the event log. Do not edit by hand: this page is "
            "rewritten from scratch every run._" % stamp,
            "",
            "| # | Who | Why they are here | When |",
            "|---|---|---|---|"]
    for i, row in enumerate(rows, 1):
        out.append("| %d | %s | %s | %s |"
                   % (i, row["person"], row["reason"], _age_words(row.get("age_hours"))))
    out += ["",
            "Ordered by how quickly the reason goes off, not by how much anybody is",
            "worth. A reply at the top is not more important than the person below",
            "it. It is more perishable."]

    notes = []
    if counts["held"]:
        notes.append("%d person(s) left off because you picked those conversations "
                     "up yourself." % counts["held"])
    if counts["marked"]:
        notes.append("%d left off because their record says they never belong here."
                     % counts["marked"])
    if counts["parked"]:
        notes.append("%d parked themselves after %d days of silence. Nobody had to "
                     "decide to give up on them." % (counts["parked"], PARK_AFTER_DAYS))
    if counts["over"]:
        notes.append("%d more had a live reason and did not fit. They will be here "
                     "tomorrow if they still matter, which is the point of a page "
                     "you can finish." % counts["over"])
    if not counts["holds_installed"]:
        notes.append("Layer 6 is not installed, so nobody could be checked against a "
                     "hold list. Everyone with a live signal is on this page.")
    if notes:
        out += ["", "---", ""] + ["- " + n for n in notes]
    out.append("")
    return "\n".join(out)


def _atomic_write(path, content):
    """Write without ever damaging the file already there."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(content)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)
    return path


def main(argv):
    limit = None
    if "--limit" in argv:
        try:
            limit = int(argv[argv.index("--limit") + 1])
        except (IndexError, ValueError):
            print("--limit needs a number after it")
            return 2
    cfg = crm_paths.config()
    rows = build(limit=limit)
    text = render(rows, start_time=cfg.get("start-time"))
    print(text)
    if "--write" in argv:
        path = _atomic_write(crm_paths.today_page(), text)
        print("")
        print("written: %s" % path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
