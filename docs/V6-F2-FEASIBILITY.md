## Executive summary (read this first)

The first V6-F2 implementation matches current events to earlier dated events
in the same unit's text corpus, then samples only panel paths completed before
the current as-of. The public F2 inputs do not contain enough mature, repeated
same-event episodes. The head returns Numeric V3 exactly on all 27 public F2
cards. It is a tested research prototype, **not a submission candidate**.

### What the public inputs actually contain

The 27 F2 cards have 178 indexed documents in total, split into small,
unit-specific corpora. The interpreter's cutoff-safe selection, currentness
filter, and event matcher find a current signal on 11 cards. For those 11,
no card has three independent, same-event documents whose full forecast
horizon is already in that card's input panel before the as-of. Thus the
same-event sleeve has zero actual-asof activations. This is an input coverage
result, not a performance result.

Before deduplication or current-event matching, only three potentially mature
event documents appeared in the entire F2 practice corpus, and all three were
within 14 calendar days on a single card. Treating them as independent worlds
would invent evidence. A valid response for a 63-business-day horizon needs
the panel after the historical document to extend through that full horizon,
while ending before the current cutoff.

### Boundaries enforced by the prototype

- Only this unit's mounted corpus and panel are read. No sibling unit's panel,
  later card, public target outcome, external network, or card-name rule enters
  the runtime route.
- Every historical document is dated before the current as-of. Its response
  is extracted only when the full path fits inside the input panel before
  the current as-of. Overlapping event cycles do not count as independent.
- F1 and F4 retain V5.1 routing, and F3 stays Numeric V3 in `v6-f2` mode.
  A missing or sparse F2 analog returns the original Numeric V3 array.
- The local synthetic tests cover an active same-event path, two insufficient
  episodes, an incomplete later episode, a post-asof document, and family
  preservation. They do not establish a leaderboard improvement.

### Next experiment gate

Obtain a legally usable, independently collected historical document stream
whose publication timestamps and source provenance are verifiable. Build a
training dataset from dated events and the *same training panel's* subsequent
paths, preserving strict rolling cutoffs. Keep raw outcome rows and unit-specific
answers out of the submission image and this public repository. A generic
event-response model can enter a candidate only after older-fit/newer-holdout
evaluation shows enough independent events for each family and horizon.
Published practice cards may inform model development, but overlapping sibling
panels must never become an answer lookup. The official Development budget is
not a substitute for the missing historical training set.
