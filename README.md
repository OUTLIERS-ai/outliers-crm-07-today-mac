**This is the Mac version.** On Windows, use [outliers-crm-07-today](https://github.com/OUTLIERS-ai/outliers-crm-07-today).

# Outliers CRM - Layer 7 - What Deserves Today

Your CRM is safe and orderly. It also works the queue in the order the queue was
built, which means something that arrived an hour ago waits its turn behind a
list assembled long before it.

This layer fixes that. One page, ranked, with every line saying why it is there.

## Install it

    python3 install.py

One command. It finds the CRM you built in Layer 1, installs into it, and builds
your page once so you can see what it looks like. Two questions:

- **What time do you start?** Only used to label the page so it reads like yours.
  Nothing here is scheduled and nothing runs on a clock.
- **How many people can you genuinely speak to in a day?** Be honest rather than
  ambitious. A page longer than you can finish is a page you stop opening, and
  then the whole layer is furniture.

## What it needs beneath it

Layer 6. The installer checks and stops politely if it is not there. This layer
honours Layer 6's hold list without exception, and a ranked list of people to
contact, built without the thing that stops it contacting the wrong people, is
worse than no list.

## Build the page

In Terminal, from your CRM folder (if your CRM is not at `~/CRM`, put your own folder in the `cd` line):

    cd ~/CRM
    python3 _engine/today.py --write

It prints the list and writes `Today.md` into your CRM. The page is rebuilt from
scratch every run, so it is never edited by hand and never gets out of date.

## How it orders

By how quickly the reason goes off. Not by how important the person is.

| Why they are here | Stays live for |
|---|---|
| Replied | 2 days |
| Booked a call | 7 days |
| Changed role | 14 days |
| Engaged with something you posted | 7 days |
| You commented on their work | 3 days |
| Joined the community | 14 days |
| A new connection | 7 days |
| Quiet, and due a word | until they park |

A reply at the top is not more important than the person below it. It is more
perishable.

**On the evidence for that.** The much-quoted study of lead response time was
funded by a company selling lead response software, which is a reason to treat
its headline multiple as indicative rather than settled. The direction is not
seriously disputed, and acting on it is free: you were going to work the list
anyway, and ordering it costs nothing.

## What never appears

- **Anyone you have picked a conversation up with yourself.** Layer 6's hold list
  decides that. This layer asks it every time and honours the answer.
- **Friends, family, and anyone you know is not buying.** Marked on their own
  record: `contact-type: friend`, `relationship-state: non-buyer`, or
  `never-on-the-list: true`. It belongs on the record, because it is a fact about
  them, not a rule buried in the ordering code.

The page reports how many it left off and why, so an exclusion is visible rather
than a person mysteriously never appearing.

## What parks itself

A signal nobody acted on ages out. It does not become a backlog, and nobody has
to decide to give up on it.

This is the part people find hardest to accept, and it is the part that makes the
system survivable. A list that only grows is a list you stop opening, and the
guilt of an unworked queue kills a CRM more reliably than any missing feature.

## Now use it

Open `Today.md` before you open your inbox, and work only from it for one
morning. Nothing else.

That is the entire test of this layer. If the page is worth working, it is right.
If it is not, the fix is upstream in what is being captured, not in the ordering.

## Run the tests

From the folder you downloaded:

    cd ~/outliers-crm-07-today-mac
    python3 tests/test_today.py

It prints a line per assertion and exits non-zero on any failure. Standard
library only.

## It only reads

This layer never writes to the event log, never writes to a person's record, and
never sends anything. Ordering is a reading job. The only file it writes is the
page itself.

## What this layer leaves for the next one

You are fast now, and running on assumptions about which signals actually matter.
The table above is a guess with a plausible story attached, and nothing here has
tested it. You also still cannot tell whether the machine is working or quietly
doing nothing, because a system that produces nothing exits just as cleanly as
one that produces everything. Layer 8.

This repo is made automatically from outliers-crm-07-today@266dc18. To report a problem or suggest a change, use that repo, not this one.
