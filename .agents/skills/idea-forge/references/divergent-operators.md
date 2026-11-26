# Divergent operators

Keep the episode, desired outcome and existing strengths visible. Generate candidates as short sketches of a change and its causal effect. Hold comparisons until the pool is assembled. Give each wave-one worker one operator block only, copied from below into its packet, so the pool comes from different directions and the operators do not blur into each other.

## Worker packet

Build every packet in this order, and keep it under about 15K tokens:

1. H (hard rules and vetoes, marked IMMUTABLE) and the output schema below.
2. The confirmed brief, the picked frame, the fit checklist, R (marked MODIFIABLE) and the novelty setting.
3. The worker's practitioner lens and its one operator block.
4. For later passes only: the explored-mechanism list, or up to two banned causal pathways.
5. H and the output schema again, word for word. Models attend least to the middle of a long prompt, so the rules that must hold sit at both ends.

Leave out generic exhortations ("be creative", "think outside the box", "avoid clichés"). They make creative output worse. Leave out celebrity or leader personas. They pull answers toward familiar tropes.

## Practitioner lenses

Each worker gets one horizontal, equal-status lens, made specific to this brief. Defaults to adapt:

| Operator | Default lens to make specific |
| --- | --- |
| VS tail | a scrappy frontline operator who hates overhead |
| Rule drop | a first-principles systems debugger |
| Relational analogy | a field researcher who has worked in non-software settings (triage, stage crews, shipping, utilities) |
| Closed world plus assets | a resource-constrained craftsperson |
| Brainwriting | a small peer group passing one sheet around |

"A night-shift nurse who cannot count on anyone reading instructions" is the right grain. "A nurse" is too generic. A worker may write its own lens from the brief before it starts.

## Operator blocks

**VS tail (`vs_tail`, Standard and Deep).** Sample six distinct approaches from the full range of plausible solutions, each with an estimated probability between 0 and 1. Drop every approach at 0.10 or above and keep only tail candidates that satisfy all of H. The probabilities are a prompting device, not a measurement. This widens the pool but leaves part of a model's pull toward typical answers in place, so it is always paired with the operators below.

**Rule drop and inversion (`t_uot`, Standard and Deep).** Read H (immutable) and R (modifiable). If R is thin, name the rules everyone assumes for this kind of problem: who pays, who starts it, when feedback arrives, what artifact is assumed, what counts as success. Step A: write six modified rule sets, each deleting, inverting or swapping one R, or borrowing a rule from another field. Step B: discard any that break H or physical or social realism (no magic technology, no invented twists). Step C: write one concrete mechanism inside each surviving rule set. This block also covers contradictions: when two desired outcomes pull against each other, treat the rule that forces the trade-off as an R to drop, and vary actor, timing, incentive or information to satisfy both.

**Relational analogy (`c_uot_analogy`, Standard and Deep).** Step A: write the brief's causal structure as two or three relations with no domain nouns ("someone with no immediate feedback keeps putting off a step whose cost lands later on someone else"). Step B: pick six distant source settings that solve part of that structure. Step C: for each, write the object mapping (what plays which role) and the transferable mechanism before adapting it back under H, and name the point where the analogy breaks. Do not just "search another domain": that collapses onto the same few domains.

**Closed world plus assets (`sit_asset`, Deep).** No new tools, budget or headcount. Build only from resources inside the user's episode and their unfair advantages. Try subtraction (remove an element), multiplication (duplicate an element with a changed property), division (move a part in time, place or ownership), task unification (give something already present a second job), or attribute dependency (make one variable depend on another). For a hard brief, transform the form first, then ask what function it could serve.

**Brainwriting chain (`brainwriting_ddd`, Deep worker five and the Light engine).** Three sequential passes before output. Pass 1, bold inventor: four raw, unconventional titles. Pass 2, builder: give each a concrete operational twist that uses the user's advantages. Pass 3, lateral thinker: collide pairs from pass 2 under one rule inversion into six final mechanisms. In Light the main session runs this chain itself, with each pass given the mechanisms the earlier passes used.

## Two-step output and the card schema

Each worker first lists short titles of 5 to 8 words, checks that no two share a causal lever, and only then writes cards. Titles are cheap, they reduce early anchoring, and they make the gut check possible. Then it writes a JSON array to its own file:

    {"id": "W1_T1",
     "worker_operator": "t_uot",
     "frame_id": "B",
     "title": "Laptop holds the second key",
     "mechanism": "second device holds the key",
     "how": "loosening a rule on the phone needs approval from the paired laptop",
     "depends_on": "the person owns a laptop and keeps it away from bed",
     "assumptions": ["owns a laptop", "laptop stays out of the bedroom"],
     "slots": {"lever_type": "second_key", "primary_actor": "user", "rule_modified": "phone acts alone",
               "delivery_channel": "paired device", "trigger": "late-night loosening"},
     "changes": "night loosening needs a second device",
     "grounded_in": "the user said the laptop already lives in the office",
     "tier_intent": "stretch",
     "sketch": "40 to 80 words: what happens, why it could work, what could fail."}

`mechanism` is a short reusable label, and the coordinator normalizes labels across workers after reading the `how` lines. `assumptions` splits the "works only if" line into atomic conditions, and `slots` records the causal structure. Both feed the audit's composite kernel, which compares cards on mechanism, assumptions and slots rather than on wording. `grounded_in` names the specific detail of the user's situation the idea relies on. If the honest answer is "nothing in particular", the idea is generic and the fit gate will repair or cut it. `tier_intent` is the worker's guess at close, stretch or wildcard. The audit also accepts the research schema's names (`mechanism_signature`, `sketch_draft`, `actor`, `trigger`, `assumption`).

## Diversity audit

Run `python3 scripts/diversity_audit.py --input pool.json --kernel composite --output audit.json` from the skill directory. `--help` lists every input and output key. The short version: `status` (`COLLAPSE_ALERT`, `OK` or `TOO_FEW`, using thresholds that tighten as the pool grows), `vendi_profile` (order-q Vendi scores: `vs_1` is the effective number of distinct ideas, small q stays sensitive to rare wildcards, `vs_inf` exposes one dominant mode), `clusters`, `shared_assumption_alerts`, `taboo_repair_cards`, `item_metrics` (each card's leave-one-out uniqueness and whether it is a structural wildcard), and the similarity matrix the tournament reuses. With `--prev-wave` it adds a beta-Vendi gain and flags `STAGNANT_WAVE2`. Without `--kernel composite` it reproduces the 2.0-lean output exactly.

The similarity is still lexical inside each field, so it is only as good as the labels, `how` lines and slots. Check flagged clusters by hand before banning anything, and keep a variant when it changes the trade-off.

## Explored-mechanism list and taboo repair

Keep a running list of mechanism labels already in the pool, one line each. Light's later passes, Standard's sequential pass and wave-two gap fillers get the whole list as ground already covered and must work through a different causal step. It is a pointer away from covered ground, not a ban list to argue with.

A taboo repair worker gets at most two banned causal pathways, since longer ban lists make generators strain, drift and lose accuracy. State each one as a pathway plus its shared assumptions, never as surface keywords:

    BANNED CAUSAL PATHWAYS (at most 2, do not disguise under a new metaphor or brand name):
    [Cluster C0] reminder nudge via the app, relying on {user checks app, trusts reminders}
    [Gut veto] anything that needs public social posting
    EQUIVALENCE CHECK (one sentence per card, before you write it): say why this card's core
    causal lever is not a renamed version of a banned pathway. Remove the banned mechanism from
    your idea: does it still work? If not, discard it and write another.

Models routinely reapply a banned method under a new name, so the check is mandatory. Cards that fail it are dropped before the pool is rebuilt.
