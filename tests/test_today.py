"""NOTE: the event names below are the ones the records layer actually writes.
An earlier version of this file used names invented here, so every check passed
while the finished system produced a permanently empty list. A fixture that agrees
with the code under test and with nothing else proves only that they agree.

Test: one page, ordered by how quickly the reason goes off, with nobody on it
who should not be there.

What should be true (Layer 7):

- The most perishable reason sorts first. A reply from this morning goes above a
  profile change from a fortnight ago.
- Every line says why it is there. A list without reasons is a list you argue
  with instead of working.
- A person appears once, under their strongest live reason.
- Anyone you picked up by hand, and anyone marked as not a buyer, never appears.
- Old signals age out on their own. Nothing accumulates into a backlog.
- An empty page is a real answer, not a failure.
- The page fits what you said you can actually get through.

Run:  python tests/test_today.py
"""

import json
import shutil
import sys
import tempfile
import types
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine"))

import crm_paths
import today

FAILS = []


def check(label, cond, detail=""):
    ok = bool(cond)
    print(("  PASS  " if ok else "  FAIL  ") + label
          + (("   [" + detail + "]") if detail and not ok else ""))
    if not ok:
        FAILS.append(label)


VAULT = Path(tempfile.mkdtemp(prefix="crm-layer7-today-"))
crm_paths.use_vault(VAULT)
(VAULT / "_layers").mkdir(parents=True)
(VAULT / "_layers" / "config.json").write_text(
    json.dumps({"layer": 6, "daily-capacity": 20, "start-time": "07:30",
                "people_word": "clients"}), encoding="utf-8")
(VAULT / "People").mkdir(parents=True)

LEDGER = VAULT / "_ledger" / "events.jsonl"
LEDGER.parent.mkdir(parents=True)


def ago(hours):
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat(timespec="seconds")


def emit(type_, person, hours_ago):
    with open(LEDGER, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps({"ts": ago(hours_ago), "type": type_,
                             "person": person, "source": "test"}) + "\n")


def names(rows):
    return [r["person"] for r in rows]


print("\n=== 1. the most perishable reason sorts first ===")

emit("they_engaged", "Rowan Ashdown", 20)
emit("call_booked", "Tobias Fenwick", 30)
emit("reply_received", "Mara Quennell", 2)
emit("details_changed", "Delia Marchetti", 100)

rows = today.build(ledger_path=LEDGER)
check("everyone with a live reason is on the page",
      set(names(rows)) == {"Rowan Ashdown", "Tobias Fenwick", "Mara Quennell",
                           "Delia Marchetti"}, str(names(rows)))
check("the reply is first", names(rows)[0] == "Mara Quennell", str(names(rows)))
check("the booked call is second", names(rows)[1] == "Tobias Fenwick", str(names(rows)))
check("every line carries a reason", all(r.get("reason") for r in rows))
check("every line carries how old it is",
      all(r.get("age_hours") is not None for r in rows))

print("\n=== 2. a person appears once, under their strongest reason ===")

emit("details_changed", "Mara Quennell", 6)
rows = today.build(ledger_path=LEDGER)
mara = [r for r in rows if r["person"] == "Mara Quennell"]
check("still only one line for them", len(mara) == 1, str(len(mara)))
check("and it is the reply, not the profile change", mara[0]["reason"] == "replied",
      mara[0]["reason"])

print("\n=== 3. a stale signal ages out on its own ===")

emit("reply_received", "Someone Long Ago", 24 * 40)
rows = today.build(ledger_path=LEDGER)
check("a reply from over a month ago is not on the page",
      "Someone Long Ago" not in names(rows), str(names(rows)))
check("and it is reported as parked rather than vanishing silently",
      today.summary(rows)["parked"] >= 1, str(today.summary(rows)))

print("\n=== 4. somebody you picked up yourself never appears ===")

emit("reply_received", "Held Person", 1)
rows = today.build(ledger_path=LEDGER)
check("with no hold list installed, they are on the page",
      "Held Person" in names(rows), str(names(rows)))
check("and the page says the hold list is not installed",
      today.summary(rows)["holds_installed"] is False)

# Stand in for Layer 6. Layer 6's own tests prove the hold list itself works;
# what is tested here is that this layer asks it, and honours the answer.
fake = types.ModuleType("holds")
fake.is_held_person = lambda *ids: any(str(i) == "Held Person" for i in ids)
sys.modules["holds"] = fake
try:
    rows = today.build(ledger_path=LEDGER)
    check("with the hold list installed, they are gone",
          "Held Person" not in names(rows), str(names(rows)))
    check("even though their reply is the most recent thing that happened",
          any(e["person"] == "Held Person" for e in today.read_events(LEDGER)))
    check("the page says how many were left off",
          today.summary(rows)["held"] == 1, str(today.summary(rows)))
    check("everyone else is still there", "Mara Quennell" in names(rows))
    page = today.render(rows)
    check("and the page explains why in words",
          "picked those conversations up yourself" in page)
finally:
    del sys.modules["holds"]

print("\n=== 5. friends, family and known non-buyers never appear ===")

emit("reply_received", "A Friend", 1)
emit("reply_received", "Not Buying", 1)
emit("reply_received", "Kept Private", 1)
(VAULT / "People" / "A Friend.md").write_text(
    "---\nname: A Friend\ncontact-type: friend\n---\n", encoding="utf-8")
(VAULT / "People" / "Not Buying.md").write_text(
    "---\nname: Not Buying\nrelationship-state: non-buyer\n---\n", encoding="utf-8")
(VAULT / "People" / "Kept Private.md").write_text(
    "---\nname: Kept Private\nnever-on-the-list: true\n---\n", encoding="utf-8")

rows = today.build(ledger_path=LEDGER)
check("a friend is not on the page", "A Friend" not in names(rows), str(names(rows)))
check("a known non-buyer is not on the page", "Not Buying" not in names(rows))
check("somebody marked off the list is not on the page",
      "Kept Private" not in names(rows))
check("they are counted, not silently dropped",
      today.summary(rows)["marked"] == 3, str(today.summary(rows)))

print("\n=== 6. the page fits what you can get through ===")

for i in range(30):
    emit("connected", "Person %02d" % i, 5)
rows = today.build(limit=5, ledger_path=LEDGER)
check("the list is capped", len(rows) == 5, str(len(rows)))
check("and it says how many did not fit", today.summary(rows)["over"] > 0,
      str(today.summary(rows)))
page = today.render(rows)
check("the page explains that the rest will be there tomorrow if they still matter",
      "still matter" in page)

check("the cap comes from your config when you do not pass one",
      len(today.build(ledger_path=LEDGER)) <= 20)

print("\n=== 7. an empty page is an answer ===")

empty = today.render([])
check("it says nothing is waiting", "Nothing is waiting" in empty)
check("it explains that this is a real answer", "not an empty page" in empty)
check("and that things aged out rather than piling up", "aged out" in empty)
check("it does not pretend there is a table", "|" not in empty)

print("\n=== 8. the page is readable, and rewritten rather than appended ===")

rows = today.build(limit=5, ledger_path=LEDGER)
page = today.render(rows, start_time="07:30")
check("it names the time you said you start", "07:30" in page)
check("it warns against editing it by hand", "rewritten from scratch" in page)
check("it explains the ordering in plain words", "perishable" in page)
check("every row is a table line", page.count("\n|") >= len(rows))

path = today._atomic_write(VAULT / "Today.md", page)
first = Path(path).read_text(encoding="utf-8")
today._atomic_write(VAULT / "Today.md", today.render([]))
second = Path(path).read_text(encoding="utf-8")
check("writing again replaces the page rather than adding to it",
      "Nothing is waiting" in second and first != second)
check("no temporary file is left behind",
      not list(Path(path).parent.glob("Today.md.tmp")))

print("\n=== 9. a damaged event log does not take the page with it ===")

with open(LEDGER, "a", encoding="utf-8") as fh:
    fh.write("this line is not json at all\n")
    fh.write('{"ts": "not a date", "type": "reply_received", "person": "Broken Time"}\n')
    fh.write('{"ts": "%s", "type": "reply_received"}\n' % ago(1))
rows = today.build(ledger_path=LEDGER)
check("the page is still built", len(rows) > 0)
check("the unreadable line is skipped rather than raising", True)
check("an event with an unreadable date does not appear",
      "Broken Time" not in names(rows), str(names(rows)))
check("an event that names nobody does not appear as a blank row",
      all(r["person"] for r in rows))

print("\n=== 10. this layer only reads ===")

src = (ROOT / "engine" / "today.py").read_text(encoding="utf-8")
writes = []
for i, line in enumerate(src.splitlines(), 1):
    s = line.strip()
    if s.startswith("#"):
        continue
    if "open(" in s and any(m in s for m in ('"a"', "'a'")):
        writes.append("%d: %s" % (i, s[:60]))
check("it never appends to the event log", not writes, "; ".join(writes[:3]))
before = LEDGER.read_text(encoding="utf-8")
today.build(ledger_path=LEDGER)
check("building the page leaves the event log untouched",
      LEDGER.read_text(encoding="utf-8") == before)

print("\n=== 11. installing this layer does not break the one below ===")

# Every layer from 6 upward ships the same crm_paths.py, because each installer
# copies it into the same folder. If this repository shipped a narrower version,
# installing Layer 7 would quietly remove functions Layer 6 depends on, and the
# hold list would stop working the moment the ordering was installed.
NEEDED_BY_LAYER_6 = ("vault", "use_vault", "state_dir", "people_dir", "outbox_dir")
NEEDED_BY_LAYER_7 = ("config", "ledger_path", "today_page")
NEEDED_BY_LAYER_8 = ("schema_dir", "reports_dir")
for group, names_needed in (("6", NEEDED_BY_LAYER_6), ("7", NEEDED_BY_LAYER_7),
                            ("8", NEEDED_BY_LAYER_8)):
    missing = [n for n in names_needed if not hasattr(crm_paths, n)]
    check("the shared paths file still serves Layer %s" % group, not missing,
          ", ".join(missing))

shutil.rmtree(VAULT, ignore_errors=True)

print("\n%s" % ("ALL PASS" if not FAILS else "FAILURES: " + ", ".join(FAILS)))
sys.exit(1 if FAILS else 0)
