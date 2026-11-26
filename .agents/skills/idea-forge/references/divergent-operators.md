# Divergent operators

Keep the episode, desired outcome and existing strengths visible. Generate candidates as short sketches of a change and its causal effect. Hold comparisons until the pool is assembled. Give each wave-one generator one operator so the pool comes from different directions.

- **Verbalized sampling.** Ask for several responses from different parts of the response distribution, including unlikely ones. As a variation, ask for responses with estimated probability below 0.10. These estimates are a prompting device, not a measurement. It widens the pool but does not fully undo a model's pull toward typical answers, so pair it with the operators below.
- **Rule drop.** List the brief's assumed rules (R), not its hard rules (H). If R is thin, name the rules everyone assumes for this kind of problem: who pays, when it happens, who has to act, what counts as success. Pick one R and drop it, invert it, or swap in a rule borrowed from another field. Ask what solution becomes possible, then check it against every H. Hidden assumptions count as R: "it has to happen on the phone", "the user has to remember", "it has to be free".
- **Closed-world transformation.** Inventory the resources already present. Try subtraction (remove an element), multiplication (duplicate an element with a changed property), division (move a part in time, place or ownership), task unification (give something already present a second job), or attribute dependency (make one variable depend on another). For a difficult brief, first transform the form, then ask what new function it could serve.
- **Contradiction and dimensions.** Identify two desired outcomes in tension. Vary actor, timing, incentive, or information available. Pick an unexplored combination and explain how it could satisfy both demands.
- **Relational analogy.** First write the problem's causal structure as one sentence with no domain nouns, in plain roles ("someone with no immediate feedback keeps putting off a step whose cost lands later on someone else"). Then find a moderately distant setting with that same structure. Transfer the relationship, not the surface, and name the point where the analogy breaks.

## Two-step generation and idea cards

Each generator first lists 8 to 10 titles of 5 to 8 words. Titles are cheap, they make the gut check possible, and they let you see the spread before anyone writes long sketches. Then it expands its most different titles into cards:

    {"id": "w2-3",
     "title": "Laptop holds the second key",
     "mechanism": "second device holds the key",
     "how": "loosening a rule on the phone needs approval from the paired laptop",
     "depends_on": "the person owns a laptop and keeps it away from bed",
     "changes": "night loosening needs a second device",
     "grounded_in": "the user said the laptop already lives in the office",
     "sketch": "40 to 80 words: what happens, why it could work, what could fail."}

`grounded_in` names the specific detail of the user's situation the idea relies on (an episode moment, an asset, a constraint). If the honest answer is "nothing in particular", the idea is generic and the fit gate will repair or cut it. `mechanism` is a short reusable label. The coordinator normalizes labels across workers after reading the `how` lines, so two cards with the same causal path share one label even when the wording differs.

## Diversity audit

From the installed skill directory, run `python3 scripts/diversity_audit.py pool.json` on a list of cards (only `id`, `mechanism` and `sketch` are required, the other fields make it sharper). It reports:

- `effective_distinct_ideas`: a Vendi score, roughly how many truly different ideas the pool holds. 1 means all the same, N means all different.
- `near_duplicate_clusters`: groups whose mechanism, causal path and dependency overlap.
- `over_40_percent`: any label covering more than 40% of the pool.
- `most_unique` and `most_redundant`: which cards add or barely add to the spread.
- `shared_assumptions`: groups whose "works only if" lines overlap, covering a third of the pool or more. Generate a replacement that works when that assumption is false.
- `surface_vs_mechanism`: how much more varied the sketches look than the mechanisms are. Well above 1.5 means the pool is the same few ideas in different words.
- `taboo_targets`: up to two mechanisms to ban in a repair wave when the pool collapsed.

The similarity is lexical inside each field, so it is only as good as the labels and `how` lines. Check flagged clusters by hand before banning anything, and keep a variant when it changes the trade-off.

## Explored-mechanism list and taboo repair

Keep a running list of the mechanism labels already in the pool, one line each. Quick's later passes and wave-two gap-filling workers get the whole list as ground already covered and must work through a different causal step. This is a pointer away from covered ground, not a ban list to argue with.


For each taboo target (two at most, since longer ban lists make generators strain and drift), brief a fresh generator with the mechanism, two example cards that use it, and this check: "Remove the banned mechanism from your idea. Does it still work? If not, it is the same idea renamed. Name the causal step that is different." Cards that fail the check are dropped before the pool is rebuilt.
