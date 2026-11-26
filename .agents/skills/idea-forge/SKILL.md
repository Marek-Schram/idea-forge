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

1. Ask one question per turn. Stop interviewing as soon as more answers would not change what you explore (caps: Quick 4, Deep 8).
2. The user owns the frame. Offer competing frames, but never generate from a reframe the user has not picked.
3. Split the brief's rules into hard rules (H: never broken) and assumed rules (R: fair game to drop or invert). The user confirms which are hard.
4. First-wave generators never see each other's output, the coordinator's examples, or a debate round.
5. Compare ideas by mechanism and dependency, not wording. A renamed mechanism is the same idea.
6. Judge only blind, equal-length cards. Write the concrete difference first, then give one verdict per criterion.
7. Re-judge close pairs with the order reversed. A verdict that flips becomes a tie.
8. Return a portfolio across close, stretch and wildcard. Never drop the top wildcard without saying so.
9. Keep stage artifacts on disk. Chat shows only what the user needs to decide.
10. With nobody there to answer (unattended or batch runs), skip the human checkpoints, write down what you assumed in their place, and say so in the result.
11. Mark field-wide novelty as unverified unless a scoped precedent check supports a narrower claim.

## Effort

Quick is the default. Use Deep when the user asks for it or the problem clearly needs breadth and evidence. Effort is separate from the novelty setting.

| Stage | Quick | Deep |
| --- | --- | --- |
| Interview | up to 4 questions | up to 8 questions |
| Frame checkpoint | yes, shares a turn with the brief | yes |
| Wave one | 3 contrasting passes in the main session | 3 to 5 blind workers |
| Gut check | only if the user is clearly around | yes, between waves |
| Diversity audit | by eye, with a mechanism table | `scripts/diversity_audit.py` |
| Judging | direct side-by-side of finalists | blind cards, decomposed pairs, swap audit, `scripts/score_matrix.py` |
| Result | 3 to 4 sketches | portfolio of 5 to 7 |

For Deep, read [harness adapters](references/harness-adapters.md) for dispatch, models and the state folder.

## 1. Interview

Read the conversation and directly relevant repo context first. Ask one question per turn and wait. Choose the question whose answer would rule out the most kinds of solutions. Follow an unexpected detail. Stop when the success condition, the hard rules and the novelty target are clear, or when two answers in a row did not change what you would explore. Use these probes selectively:

- **Outcome and episode.** What would change for whom? Reconstruct a recent instance: the moment the outcome became more or less likely, what the person did next, and what they cared about then.
- **Current attempts and causes.** What already works, the workaround, its cost, and where it breaks. If several causes fit, ask about an exception or two similar episodes with different outcomes. Avoid repeated abstract "why" questions.
- **Success and trade-offs.** What observable difference would make this worth using, over what period? What would spoil a result that looks good on paper?
- **Unfair advantage.** What asset, relationship or observation does the user have that an outsider would not?
- **Veto.** What would make a clever answer socially awkward, risky or too annoying to actually adopt?
- **Comparison and sources.** Which familiar approach would the user pass on and why? Let them keep their own best idea private for a later comparison. Invite an artifact or comparator if they have one. Save outside precedent research for after free generation.

Use the user's own words for the goal and constraints in the brief. Do not swap in your own metaphors.

**Calibrate novelty.** Ask what should feel new: how it works, the experience of using it, both, or another dimension they name. Establish the comparison point (their own attempts, familiar products, or the field). "Either counts" is a valid answer. Then offer the three settings and recommend one with a reason tied to this brief:

| Setting | What to explore |
| --- | --- |
| Close to familiar | Keep the core approach. Find a concrete improvement on the chosen dimension, within existing resources. |
| A stretch | Change an important part of the mechanism or experience. Explain the departure and offer a plausible first test. |
| A wild card | Challenge a premise about how the goal must be achieved. Named speculative dependencies are welcome. Keep the success condition and hard rules. |

## 2. Frame checkpoint

Before generating, show two or three short frames in one turn, together with the brief summary and the novelty chooser:

- **Frame A:** the goal as the user stated it.
- **Frame B:** the tension or veto underneath it (what they are really trying to avoid).
- **Frame C:** an angle built on their unfair advantage, or on dropping one assumed rule.

For each frame give one line on what it assumes and what it would rule out. List the H and R rules and ask the user to move anything that is wrongly placed. The user picks, edits, splits or combines frames. Accepting the recommended frame and setting in one reply confirms the brief. Honor a correction before generating.

## 3. Wave one: blind generation

Give each generator the confirmed brief, the picked frame, the H and R lists, the novelty setting, one lens, one operator from [divergent operators](references/divergent-operators.md), and one question only that lens is being asked. Lenses are practitioners and lived situations, not famous people. Keep generators isolated: more interaction and more generators both tend to shrink diversity, so stay at 3 to 5.

Generate in two steps. First list 8 to 10 short titles (5 to 8 words each). Then expand the most different ones into idea cards with the fields in the divergent operators reference. Keep an obvious-answer list in the coordinator for later comparison.

## 4. Gut check

Between the waves, show the user the titles only, grouped by mechanism, in 20 lines or fewer. Ask for one or two sparks they are curious about, one or two instant vetoes, and any angle that is missing. This takes one turn and they can skip it. Develop sparks in wave two, drop vetoes, and treat a missing angle as a new assignment.

## 5. Audit and wave two

Give every card a consistent mechanism label after comparing causal descriptions. In Deep, run `python3 scripts/diversity_audit.py pool.json` from the skill directory. In Quick, count labels by eye. If the pool collapsed (one mechanism over 40% of cards, or near-duplicate clusters), write a taboo repair card for at most two mechanisms. Each repair idea must say how it differs from the banned mechanism and must still work with that mechanism removed. Otherwise it is the same idea renamed.

Then do the evidence work. Group cards by what would change for the user. Identify a gap or fragile premise. Assign complementary sources and record what each one actually shows, where the analogy breaks, and which card changed as a result. Label unresolved claims when access is missing. Generate for uncovered ground and revise at least one promising seed when evidence warrants it.

## 6. Stress-test

Use the [critique reference](references/adversarial-critique.md). Compare both waves against the user's baseline and the obvious-answer list.

- **Shared assumptions.** Finish "This works only if ..." for each finalist. If several depend on the same doubtful condition, generate a replacement that survives it being false. Drop anything that needs a behavior the user ruled out.
- **Vivid detail check.** If a stretch or wildcard shortlist leans on the same vivid detail, try one alternative that works without it.
- **Next ten seconds (Deep).** Start at the moment things usually go wrong. Show what the person does next, what the idea changes, and why the outcome could differ. If the walkthrough breaks, revise or drop the idea.
- **Cheapest test.** For each survivor, name the smallest observation, ideally doable within 48 hours, that would tell its mechanism apart from its strongest rival.

If every candidate is too familiar, reopen generation around the repeated premise before judging.

## 7. Judge and build the portfolio

Rewrite each finalist as a blind card (format in the critique reference). In Quick, compare finalists side by side on the user's priorities. In Deep, judge every pair with the decomposed method and swap audit in the critique reference, using a fresh judge that did not write the ideas, and run `python3 scripts/score_matrix.py comparisons.json`. Tag each finalist close, stretch or wildcard so the portfolio keeps one of each where possible.

## 8. Return the result

Honor a requested count. Otherwise return 3 to 4 sketches in Quick or a 5 to 7 idea portfolio in Deep. Each 40 to 80 word sketch says what happens, how it differs from the named baseline, what it depends on, and its cheapest test. Tag each one close, stretch or wildcard. In Deep, add one line from the judge card (flip rate, any wildcard kept below the cut), the discarded clichés, an unexplored direction, and where the run's files are. List every assumption made in place of a skipped checkpoint.

Invite the user to pick a concept or change the setting, frame or dimension. On a change, keep the confirmed context, regenerate or revise, and show the difference. Give a recommendation when asked. After selection, save the brief, chosen mechanism, assumptions and next test to `docs/ideation/YYYY-MM-DD-<topic>.md` when working in a writable project where the user wants the record. Preserve existing notes. If the user later brings a trial result, start at the first point where prediction and observation diverged.
