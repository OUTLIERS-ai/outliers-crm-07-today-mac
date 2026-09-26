# What I stole

The ideas in this layer are older than software, mostly. Naming where they came
from is useful because each one carries the conditions under which it works, and
those conditions are easy to lose when a pattern gets copied without its history.

## One page, and no more than one page

**From:** the daily list, in every form it has ever taken. The picking list, the
day book, the operating theatre list, and every productivity system that starts
by saying write down six things.

**Why it is here:** the constraint is not organisational, it is human. A list you
cannot finish stops being a plan and becomes a source of guilt, and the response
to guilt is avoidance. Capping the page at what you said you can do is not
tidiness; it is the only thing that keeps the page getting opened.

## Ordering by perishability rather than importance

**From:** triage, in the medical sense. Also the scheduling idea of earliest
deadline first, which is what a real-time system does when it cannot do
everything.

**Why it is here:** importance is the obvious axis and it is the wrong one for a
daily list, because importance does not change between this morning and this
evening while a reply does. Sorting by what expires soonest is how you lose the
fewest opportunities per unit of attention, and it does not require you to rank
people, which you would get wrong anyway.

## The reason on every line

**From:** the alert that carries its trigger, which is standard practice in
monitoring, and from the difference between a citation and an assertion.

**Why it is here:** a list of names with no reasons attached invites argument
with itself. You look at the third name, cannot remember why they are there, and
either skip them or spend five minutes reconstructing it. Either way the page
stops being a page you work.

## Ageing out rather than accumulating

**From:** the time-to-live, which is how caches, DNS records and message queues
all avoid holding onto things forever. Also the wider observation, in sales
pipeline management, that a stage nobody ever leaves is where deals go to be
counted rather than worked.

**Why it is here:** the alternative to ageing out is a human deciding to give up
on each individual thread, which nobody does, because each individual decision
feels premature. So nothing is ever removed and the queue grows until it is
abandoned wholesale. Ageing out makes giving up automatic and therefore actually
happen.

## Rebuilding the page from scratch every run

**From:** idempotence, and the generated-file convention: never edit the output,
edit the input and regenerate.

**Why it is here:** a page that is partly generated and partly hand-edited is a
page nobody can trust. Rewriting it completely each run means the page and the
event log can never disagree, and a wrong page is always fixed upstream.

## Reading the exclusion off the person's record

**From:** the general principle that data belongs with the entity it describes,
rather than in the logic that happens to use it.

**Why it is here:** somebody being a friend, or having told you they will never
buy, is a fact about that person. Putting it in their record means it is visible
when you open the record, it survives this layer being rewritten, and it applies
everywhere rather than only in the ordering.

## Naming the weakness of the evidence

**From:** ordinary research practice. Declare the funding, then report the
finding.

**Why it is here:** the response-time study everybody quotes was funded by a
company selling response-time software. That does not make it wrong, and it does
mean the headline multiple should not be treated as a measurement. Saying so in
the file rather than in a footnote is deliberate: a reader who later discovers
the funding on their own will discount everything else you told them.

## The atomic write

**From:** write-to-temporary-then-rename, which is how every editor and database
avoids destroying a file when something goes wrong mid-write.

**Why it is here:** the page is regenerated constantly and always in full, which
is exactly the pattern that would truncate the file if a run were interrupted.
It matters less here than in the layers holding your records, and it is the same
three lines of code, so there is no reason to do it any other way.
