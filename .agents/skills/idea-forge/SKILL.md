---
name: idea-forge
description: Interview the user, generate ideas that work or feel different from familiar options, and stress-test them. Use for open-ended brainstorming, feature discovery, research directions, or a request to get beyond familiar solutions. Skip when the user has chosen a direction and wants only implementation or critique.
license: MIT
metadata:
  version: "2.0.0"
---

# Idea Forge

Help the user discover an option they would actually try. Use the interview to learn what familiar answers miss. Keep the user's choice of direction open.

## Rules that always hold

These rules stay at the top so they survive context compaction. Every stage below follows them.

1. Ask one question per turn. Stop interviewing once the four stop slots are filled (stage 1), or when more answers would not change what you explore (caps: Quick 4, Deep 8).
2. The user owns the frame. Offer competing frames, but never generate from a reframe the user has not picked.
3. Split the brief's rules into hard rules (H: never broken) and assumed rules (R: fair game to drop or invert). The user confirms which are hard.
4. Write a fit checklist in the brief and hold every idea to it. Fit is a gate, not a weight: an idea that breaks a hard rule, needs a vetoed behavior, misses the success condition, or could be handed to anyone with this problem is repaired once or cut, and a cut idea never comes back in the portfolio.
5. First-wave generators never see each other's output, the coordinator's examples, or a debate round.
6. Keep a list of mechanisms already explored. Every later pass gets it and goes somewhere else.
7. Compare ideas by mechanism and dependency, not wording. A renamed mechanism is the same idea.
8. Judge only blind, equal-length cards, with the fit checklist and the user's baseline as anchors. Write the concrete difference first, then give one verdict per criterion.
9. Re-judge close pairs with the order reversed. A verdict that flips becomes a tie.
10. Return a portfolio across close, stretch and wildcard. Never drop the top wildcard without saying so, and never keep one that failed the fit gate.
11. Keep stage artifacts on disk. Chat shows only what the user needs to decide.
12. With nobody there to answer (unattended or batch runs), skip the human checkpoints, write down what you assumed in their place, and say so in the result. The fit gate still runs.
13. Mark field-wide novelty as unverified unless a scoped precedent check supports a narrower claim.

## Effort

Quick is the default. Use Deep when the user asks for it or the problem clearly needs breadth and evidence. Effort is separate from the novelty setting.

| Stage | Quick | Deep |
| --- | --- | --- |
| Interview | up to 4 questions | up to 8 questions |
| Frame checkpoint | yes, shares a turn with the brief | yes |
| Wave one | 3 contrasting passes in the main session, each given the mechanisms already used | 3 to 5 blind workers |
| Gut check | only if the user is clearly around | yes, between waves |
| Diversity audit | by eye, with a mechanism table | `scripts/diversity_audit.py` |
| Fit gate | yes, by eye against the checklist | yes, logged per card in `pool.json` |
| Judging | direct side-by-side of finalists | blind cards, decomposed pairs, swap audit, `scripts/score_matrix.py` |
| Result | 3 to 4 sketches | portfolio of 5 to 7 |

For Deep, read [harness adapters](references/harness-adapters.md) for dispatch, models and the state folder.

## 1. Interview

Read the conversation and directly relevant repo context first. Ask one question per turn and wait. Choose the question whose answer would rule out the most kinds of solutions. Follow an unexpected detail. Ask plain, non-leading questions, and never fill a gap with your own guess about their situation. Use these probes selectively:

- **Outcome and episode.** What would change for whom? Reconstruct a recent instance: the moment the outcome became more or less likely, what the person did next, and what they cared about then.
- **Current attempts and causes.** What already works, the workaround, its cost, and where it breaks. If several causes fit, ask about an exception or two similar episodes with different outcomes. Avoid repeated abstract "why" questions.
- **Success and trade-offs.** What observable difference would make this worth using, over what period? What would spoil a result that looks good on paper?
- **Unfair advantage.** What asset, relationship, skill or shortcut does the user have that an outsider would not?
- **Veto.** Even if an idea solved the problem on paper, what effort, awkwardness or mismatch with who they are would make them quietly stop after a week?
- **Unexamined premise.** What rule in their story are they treating as fixed that might be optional? Answers here feed the R list.
- **Contradiction.** After each answer, check for tension between what they say they want and what they did in the episode. If you find one, ask about it plainly. It usually marks the real constraint.
- **Comparison and sources.** Which familiar approach would the user pass on and why? Let them keep their own best idea private for a later comparison. Invite an artifact or comparator if they have one. Save outside precedent research for after free generation.

**Stop slots.** Stop once four things are concrete: (1) a specific episode and the moment it went wrong, (2) the core difficulty, (3) the hard rules plus at least one veto or unfair advantage, and (4) the novelty setting. Also stop when two answers in a row did not change what you would explore.

Use the user's own words for the goal and constraints in the brief. Do not swap in your own metaphors.

**Calibrate novelty.** Ask what should feel new: how it works, the experience of using it, both, or another dimension they name. Establish the comparison point (their own attempts, familiar products, or the field). "Either counts" is a valid answer. Then offer the three settings and recommend one with a reason tied to this brief:

| Setting | What to explore |
| --- | --- |
| Close to familiar | Keep the core approach. Find a concrete improvement on the chosen dimension, within existing resources. |
| A stretch | Change an important part of the mechanism or experience. Explain the departure and offer a plausible first test. |
| A wild card | Challenge a premise about how the goal must be achieved. Named speculative dependencies are welcome. Keep the success condition and hard rules. |

**Fit checklist.** Write five lines or fewer in the brief, in the user's words: the success condition, the hard rules, the vetoes, the unfair advantage, and the episode moment an idea has to change. Also write the obvious-answer list now: the user's current attempts, the familiar products they named, and the first few ideas you would suggest without thinking. Generators never see the obvious-answer list. It is used for the fit gate and judging.

## 2. Frame checkpoint

Before generating, show two or three short frames in one turn, together with the brief summary, the fit checklist and the novelty chooser:

- **Frame A:** the goal as the user stated it.
- **Frame B:** the tension or veto underneath it (what they are really trying to avoid).
- **Frame C:** an angle built on their unfair advantage, or on dropping one assumed rule.

For each frame give one line on what it assumes and what it would rule out. List the H and R rules and ask the user to move anything that is wrongly placed. The user picks, edits, splits or combines frames. Accepting the recommended frame and setting in one reply confirms the brief. Honor a correction before generating.

## 3. Wave one: blind generation

Give each generator the confirmed brief, the picked frame, the fit checklist, the H and R lists, the novelty setting, one vantage point, one operator from [divergent operators](references/divergent-operators.md), and one question only that vantage point is being asked. A vantage point is a specific practitioner or lived situation shaped by this brief (for a forgetful routine, "a night-shift nurse who cannot count on anyone reading instructions"), never a famous person or a generic job title. Keep generators isolated: more interaction and more generators both tend to shrink diversity, so stay at 3 to 5.

Generate in two steps. First list 8 to 10 short titles (5 to 8 words each), dropping any that are the user's current attempt or a familiar product's feature. Then expand the most different ones into idea cards with the fields in the divergent operators reference. Every card names what it is grounded in: the specific detail of the user's situation it relies on.

In Quick, the three passes share a context, so give each later pass the list of mechanisms the earlier passes used and ask it to work through a different causal step.

## 4. Gut check

Between the waves, show the user the titles only, grouped by mechanism, in 20 lines or fewer. Ask for one or two sparks they are curious about, one or two instant vetoes, and any angle that is missing. This takes one turn and they can skip it. Develop sparks in wave two. A veto rules out the mechanism behind the title, not only that card, so add it to the fit checklist. Treat a missing angle as a new assignment.

## 5. Audit and wave two

Give every card a consistent mechanism label after comparing causal descriptions, and update the explored-mechanism list. In Deep, run `python3 scripts/diversity_audit.py pool.json` from the skill directory. In Quick, count labels by eye. If the pool collapsed (one mechanism over 40% of cards, or near-duplicate clusters), write a taboo repair card for at most two mechanisms. Each repair idea must say how it differs from the banned mechanism and must still work with that mechanism removed. Otherwise it is the same idea renamed. If a third or more of the pool shares one "works only if" assumption, assign an idea that works when that assumption is false. If the sketches look far more varied than the mechanisms (the audit's surface ratio well above 1.5), trust the mechanisms. Gap-filling workers get the whole explored-mechanism list as ground already covered.

Then do the evidence work. Group cards by what would change for the user. Identify a gap or fragile premise. Assign complementary sources and record what each one actually shows, where the analogy breaks, and which card changed as a result. Label unresolved claims when access is missing. Generate for uncovered ground and revise at least one promising seed when evidence warrants it.

## 6. Fit gate

Check every card in the pool against the fit checklist before any judging. Record a verdict per card (`pass`, `repaired` or `cut`, with a one-line reason) in `pool.json` in Deep, or in a short list in Quick.

- **Hard rule broken:** cut.
- **Needs a vetoed behavior or a vetoed mechanism:** cut.
- **Misses the success condition:** walk it through the episode moment. If it does not change what happens there, repair once or cut.
- **Generic:** if its grounding is empty, or it would work just as well for anyone with this problem, repair once by tying it to a specific detail or advantage, or cut.
- **Obvious answer:** if its mechanism matches the user's baseline or the obvious-answer list, cut it, unless the setting is close to familiar, where at most one can stay as the baseline improvement.

A repair keeps the mechanism and changes how it lands in the user's situation. If the repaired card fails the same check, cut it. Report how many cards were cut and why in the result. If more than half the pool is cut, generate again around the fit checklist before judging.

## 7. Stress-test

Use the [critique reference](references/adversarial-critique.md). Compare the survivors against the user's baseline and the obvious-answer list.

- **Shared assumptions.** Finish "This works only if ..." for each finalist. If several depend on the same doubtful condition, generate a replacement that survives it being false.
- **Vivid detail check.** If a stretch or wildcard shortlist leans on the same vivid detail, try one alternative that works without it.
- **Next ten seconds (Deep).** Start at the moment things usually go wrong. Show what the person does next, what the idea changes, and why the outcome could differ. If the walkthrough breaks, revise or drop the idea.
- **Sharpen.** For each finalist, find the weakest link in its "works only if" line and revise once to make it stronger or cheaper to check, without changing the mechanism.
- **Cheapest test.** For each survivor, name the smallest observation, ideally doable within 48 hours, that would tell its mechanism apart from its strongest rival.

If every candidate is too familiar, reopen generation around the repeated premise before judging.

## 8. Judge and build the portfolio

Rewrite each finalist as a blind card (format in the critique reference). In Quick, compare finalists side by side on the user's priorities. In Deep, judge every pair with the decomposed method and swap audit in the critique reference, using a fresh judge that did not write the ideas and that gets the fit checklist and the user's baseline, and run `python3 scripts/score_matrix.py comparisons.json`. Tag each finalist close, stretch or wildcard so the portfolio keeps one of each where possible. A candidate that loses on fit to most of the field is not kept for balance.

## 9. Return the result

Honor a requested count. Otherwise return 3 to 4 sketches in Quick or a 5 to 7 idea portfolio in Deep. Each 40 to 80 word sketch says what happens, which part of the user's situation it builds on, how it differs from the named baseline, what it depends on, and its cheapest test. Tag each one close, stretch or wildcard. Add one line on the fit gate (how many cards were cut and the most common reason). In Deep, also add one line from the judge card (flip rate, any wildcard kept below the cut), the discarded clichés, an unexplored direction, and where the run's files are. List every assumption made in place of a skipped checkpoint.

Invite the user to pick a concept or change the setting, frame or dimension. On a change, keep the confirmed context, regenerate or revise, and show the difference. Give a recommendation when asked. After selection, save the brief, chosen mechanism, assumptions and next test to `docs/ideation/YYYY-MM-DD-<topic>.md` when working in a writable project where the user wants the record. Preserve existing notes. If the user later brings a trial result, start at the first point where prediction and observation diverged.
