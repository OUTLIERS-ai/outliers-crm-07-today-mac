"""
Outliers CRM - Layer 7 - What Deserves Today

Your CRM is safe and orderly, and it works the queue in the order the queue was
built. Something that arrived an hour ago waits its turn behind a list assembled
long before it.

This layer installs the part that decides what deserves your attention now. One
page, ranked, with every line saying why it is there.

    python install.py

It finds the CRM you built in Layer 1, asks you two questions, and installs the
layer into it.

Nothing here sends, drafts, or decides what to say. It orders.

Needs: Python 3.8 or newer. Nothing else.
"""

import json
import os
import sys
from datetime import date
from pathlib import Path

# The command a member types to start Python: `python3` on a Mac, which has no plain
# `python` command, and `python` everywhere else, as the Windows guides print it.
PY = "python3" if sys.platform == "darwin" else "python"

# The key a member presses. A Mac keyboard's key is Return; Windows keeps Enter, exactly as before
# (Mac build plan V3, wave s1: the Session 7 ruling on the words installers print).
KEY = "Return" if sys.platform == "darwin" else "Enter"

LAYER = 7
LAYER_NAME = "What Deserves Today"
NEEDS_LAYER = 6

HERE = Path(__file__).resolve().parent

MODULES = ["crm_paths.py", "today.py"]

# ---------------------------------------------------------------- small helpers

# No colour codes anywhere. Plenty of terminals print them as literal gibberish
# and a member's first minute with this must not look broken. Plain text works
# everywhere, which is the whole point of the exercise.
BOLD = DIM = OFF = ""


def say(msg=""):
    print(msg, flush=True)


def ask(question, default=None, helptext=None):
    """One plain question. Enter accepts the default."""
    say()
    say(BOLD + question + OFF)
    if helptext:
        say(DIM + "  " + helptext + OFF)
    prompt = "  > " if default is None else "  [%s] > " % default
    try:
        answer = input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        say("\nStopped. Nothing was changed.")
        sys.exit(1)
    return answer or (default or "")


def ask_yes(question, default=True):
    d = "Y/n" if default else "y/N"
    a = ask(question, default=d).strip().lower()
    if a in ("y/n", "y/n".upper(), "y", "yes"):
        return True if a != "y/n" else default
    if a in ("n", "no"):
        return False
    return default


def write(path, content):
    """Write a file without ever damaging one that already exists.

    Writes to a temporary file first, then swaps it into place in a single step.
    If anything goes wrong halfway through, the original is untouched.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(content)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def copy_in(src, dst):
    write(dst, Path(src).read_text(encoding="utf-8"))


def keep_cache_out_of_history(home):
    """Python leaves compiled cache folders beside any code it runs.

    They are noise, they change constantly, and they do not belong in the history
    of your records. Adding two lines to the ignore file costs nothing and saves a
    confusing first look at what changed.
    """
    path = Path(home) / ".gitignore"
    try:
        current = path.read_text(encoding="utf-8") if path.exists() else ""
    except OSError:
        return
    if "__pycache__" in current:
        return
    head = (current.rstrip() + "\n\n") if current.strip() else ""
    write(path, head
          + "# Python leaves these beside any code it runs. Not part of your CRM.\n"
          + "__pycache__/\n"
          + "*.pyc\n")


# -------------------------------------------------------------- finding the CRM

def config_path(home):
    return Path(home) / "_layers" / "config.json"


def looks_like_a_crm(home):
    try:
        return config_path(home).exists()
    except OSError:
        return False


def find_vault():
    """Find the CRM Layer 1 built, by looking for its config file."""
    tried = []
    env = os.environ.get("OUTLIERS_CRM")
    if env:
        tried.append(Path(env).expanduser())
    # Layer 1 leaves a pointer naming wherever the member chose to put their CRM.
    # Without checking it, anyone who declined the default folder is told they have
    # not done Layer 1 when they have, which reads as the series being broken.
    pointer = Path.home() / ".outliers-crm"
    if pointer.exists():
        try:
            noted = pointer.read_text(encoding="utf-8").strip()
            if noted:
                tried.append(Path(noted))
        except OSError:
            pass
    tried.append(Path.home() / "CRM")
    here = Path.cwd()
    tried.append(here)
    tried.extend(here.parents)

    for candidate in tried:
        if looks_like_a_crm(candidate):
            return Path(candidate)

    say()
    say("  Could not find your CRM automatically.")
    raw = ask("Where is it?",
              default=str(Path.home() / "CRM"),
              helptext="The folder Layer 1 built. It has a _layers folder inside it.")
    candidate = Path(raw.strip().strip('"').strip("'")).expanduser()
    return candidate if looks_like_a_crm(candidate) else None


def load_config(home):
    try:
        return json.loads(config_path(home).read_text(encoding="utf-8"))
    except Exception:
        return {}


def refuse_politely(reason):
    say()
    say("=" * 66)
    say("  Not yet.")
    say("=" * 66)
    say()
    say("  " + reason)
    say()
    return 1


# ------------------------------------------------------------------ the interview

def interview(cfg):
    w = cfg.get("people_word", "contacts")
    say()
    say("=" * 66)
    say("  OUTLIERS CRM   LAYER %d   %s" % (LAYER, LAYER_NAME.upper()))
    say("=" * 66)
    say()
    say("  You can hold thousands of records and speak to a handful of people.")
    say("  The scarce thing was never the data. It is your attention.")
    say()
    say("  This builds one page: who to speak to, and why. Short enough to")
    say("  finish, which is the only thing that makes it get read.")
    say()
    say(DIM + "  Two questions. Press %s to accept anything in [brackets]." % KEY + OFF)

    start = ask("What time do you start?",
                default="09:00",
                helptext="Only used to label the page, so it reads like yours. "
                         "Nothing is scheduled and nothing runs on a clock.")

    raw = ask("How many %s can you genuinely speak to in a day?" % w,
              default="10",
              helptext="Be honest rather than ambitious. A page longer than you "
                       "can finish is a page you stop opening, and then the whole "
                       "layer is furniture.")
    try:
        capacity = max(int("".join(c for c in raw if c.isdigit()) or "10"), 1)
    except ValueError:
        capacity = 10

    return {"start": start.strip() or "09:00", "capacity": capacity}


# ------------------------------------------------------------------ what we build

def readme(answers, cfg):
    w = cfg.get("people_word", "contacts")
    return """# What deserves today

**Build the page**

    %s _engine/today.py --write

It prints the list and writes `Today.md`. Open that before you open your inbox,
and work only from it for one morning. That is the whole test of this layer: if
the page is worth working, it is right, and if it is not, the fix is upstream.

**What the page is**

One line per person, ordered by how quickly the reason goes off. A reply from an
hour ago sits above a role change from a fortnight ago. That is not a claim that
one person matters more than the other. It is a claim that the reply stops being
worth answering much faster.

Every line carries its reason. A list without reasons is a list you argue with
instead of working.

**What never appears on it**

- Anyone you have picked a conversation up with yourself. Layer 6's hold list
  decides that, and this layer honours it without exception.
- Anyone whose record says `contact-type: friend`, `relationship-state:
  non-buyer`, or `never-on-the-list: true`. Put that on the record, not in a rule
  somewhere in the code, because it is a fact about them.

**What parks itself**

A signal nobody acted on ages out. It does not become a backlog and nobody has to
decide to give up on it. The page tells you how many parked so that ageing out is
visible rather than silent.

This is the part people find hardest to accept and it is the part that makes the
system survivable. A list that only grows is a list you stop opening.

**It is capped at %d**

You said that is how many %s you can genuinely speak to in a day. Anyone who did
not fit will be there tomorrow if they still matter, and if they do not, that is
the system telling you something.

**It only reads**

This layer never writes to the event log, never writes to a person's record, and
never sends anything. Ordering is a reading job.
""" % (PY, answers["capacity"], w)


def layer_note(answers, cfg):
    return """# Layer {n} - {name}

**What it built.** One ranked page, rebuilt from the event log whenever you ask
for it, with every line carrying the reason it is there.

**What it does.** It turns everything the system knows into one short answer to
the only question that matters on any given day: who do I speak to, and why. It
orders by how perishable the reason is, it leaves off anyone held or marked, and
it lets old signals age out on their own rather than accumulating.

**The idea worth keeping.** For one person running a business the constraint was
never how many records you have. A page you can finish beats a queue you cannot,
and things falling off it quietly is a feature.

**What it leaves for Layer {nxt}.** You are fast now, and running on assumptions
about which signals actually matter. The ordering above is a guess with a
plausible story attached. You also still cannot tell whether the machine is
working or quietly doing nothing, because a system that produces nothing exits
just as cleanly as one that produces everything. Counting properly, and noticing
silence, is the next layer.
""".format(n=LAYER, name=LAYER_NAME, nxt=LAYER + 1)


def build(home, answers, cfg):
    say()
    say("Installing Layer %d into %s" % (LAYER, home))
    say()

    def note(path, what):
        say("  built  %-34s %s" % (str(Path(path).relative_to(home)), what))

    for name in MODULES:
        copy_in(HERE / "engine" / name, home / "_engine" / name)
    say("  built  %-34s %s" % ("_engine/today.py", "builds the page from the event log"))

    p = home / "_today" / "README.md"
    write(p, readme(answers, cfg))
    note(p, "what the page is, and what never appears on it")

    p = home / "_layers" / ("Layer %d - %s.md" % (LAYER, LAYER_NAME))
    write(p, layer_note(answers, cfg))
    note(p, "what this layer did, for when you forget")

    keep_cache_out_of_history(home)

    cfg["layer"] = max(int(cfg.get("layer", 0) or 0), LAYER)
    cfg["start-time"] = answers["start"]
    cfg["daily-capacity"] = answers["capacity"]
    cfg["layer-%d-installed" % LAYER] = date.today().isoformat()
    write(config_path(home), json.dumps(cfg, indent=2) + "\n")


def first_run(home, cfg):
    """Build the page once, so nobody has to wonder what it looks like."""
    say()
    say("Building your page for the first time.")
    say()
    sys.path.insert(0, str(home / "_engine"))
    try:
        import crm_paths
        import today
        crm_paths.use_vault(home)
        rows = today.build()
        text = today.render(rows, start_time=cfg.get("start-time"))
        today._atomic_write(home / "Today.md", text)
    except Exception as err:
        say("  Could not build it yet (%s)." % err)
        say("  Nothing is broken. Run it yourself when you are ready:")
        say("      %s _engine/today.py --write" % PY)
        return 0
    say("  written: %s" % (home / "Today.md"))
    if not rows:
        say()
        say("  It is empty, and that is the right answer today: there are no live")
        say("  signals in your event log yet. The page fills as Layer 4 captures.")
    else:
        say()
        say("  %d line(s) on it." % len(rows))
    return len(rows)


def finish(home, answers, cfg, count):
    say()
    say("=" * 66)
    say("  Done. Your CRM now tells you where to start.")
    say("=" * 66)
    say()
    say("  Rebuild it any time, from inside %s:" % home)
    say()
    say("      %s _engine/today.py --write" % PY)
    say()
    say("  What to do now: open Today.md before you open your inbox, and work")
    say("  only from it for one morning. Nothing else. If the page is worth")
    say("  working, this layer is right. If it is not, the fix is upstream in")
    say("  what is being captured, not in the ordering.")
    say()
    say("  Two things people find odd at first, and should not:")
    say("    - Things drop off the page on their own. That is deliberate. A list")
    say("      that only grows is a list you stop opening.")
    say("    - The page is capped at %d. Anyone who did not fit will be back" % answers["capacity"])
    say("      tomorrow if they still matter, and if they do not, that is the")
    say("      system telling you something.")
    say()


def main():
    home = find_vault()
    if not home:
        return refuse_politely(
            "Layer %d needs Layer 1 first. Run that one and come back." % LAYER)

    cfg = load_config(home)
    have = int(cfg.get("layer", 0) or 0)
    if have < NEEDS_LAYER:
        return refuse_politely(
            "Layer %d needs Layer %d first. Run that one and come back.\n\n"
            "  Your CRM at %s is on Layer %d."
            % (LAYER, NEEDS_LAYER, home, have))

    answers = interview(cfg)
    say()
    say("  Installing into:  %s" % home)
    say("  You start at:     %s" % answers["start"])
    say("  Page capped at:   %d" % answers["capacity"])
    if not ask_yes("Go ahead?", default=True):
        say("\nStopped. Nothing was changed.")
        return 1
    build(home, answers, cfg)
    count = first_run(home, cfg)
    finish(home, answers, cfg, count)
    return 0


if __name__ == "__main__":
    sys.exit(main())
