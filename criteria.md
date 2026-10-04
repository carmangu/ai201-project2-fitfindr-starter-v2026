# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**
The happy path is the baseline. Pick 4 of 5 rather than 5 of 5 because the search is a keyword overlap match, and some phrasings will fall just under the threshold even when a human would say the listing matches.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
This is the branch. If it fails, the agent is a list of function calls, not a loop.
Pick 5 of 5 because the check is mechanical: either `suggest_outfit` was called or
it wasn't, and the message either names a change or it doesn't.
There is no fuzziness to allow for.

---

## 3. State carries the item through

The item `search_listings` returns is the same item `suggest_outfit`
receives. When I run 5 queries that match at least one listing, in all
5 the `session["selected_item"]["id"]` equals the `id` of the first
listing in `session["search_results"]`.

**Why this target:**
The state criterion exists to catch a loop that
re-searches or re-parses instead of reading what the previous tool
returned. I pick 5 of 5 because the id comparison is exact — the loop
either passes the same dict or it doesn't. There is no fuzziness to
allow for, so any failure is a real bug.

---

## 4. Fit card is specific and varies

The fit card is non-empty and mentions the item's price and platform at
least once. When I run `create_fit_card` 5 times on the same item, all
5 outputs mention both, and at least 3 of the 5 are different from each
other word-for-word.

**Why this target:**
The fit card calls a model, so identical wording
across runs would suggest the cache or temperature is wrong — the brief
calls this out. I pick 3 of 5 different because two runs occasionally
landing on the same phrasing is normal, but if all five come back
identical something is frozen. The price and platform requirement is
separate: it is what makes the caption read like a real post rather
than a generic description, and it is something a reader can check
without judgment.

---

## 5. Agent responds within 30 seconds

Given a query that matches at least one listing, the agent returns a
fit card within 30 seconds — in at least 4 of 5 tries.

**Why this target:**
This one is about latency, which none of the
other four cover. The agent makes three tool calls and two of them hit
the model; if the pacing adapter is misconfigured or the loop retries,
a query can take minutes. 30 seconds is generous for two model calls
under the starter's pacing, and 4 of 5 allows one slow run without
calling the whole thing broken.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
