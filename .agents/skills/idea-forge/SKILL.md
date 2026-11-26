---
name: idea-forge
description: Interview the user, generate ideas that work or feel different from familiar options, and stress-test them. Use for open-ended brainstorming, feature discovery, research directions, or a request to get beyond familiar solutions. Runs in Light, Standard or Deep tiers. Skip when the user has chosen a direction and wants only implementation or critique.
license: MIT
compatibility: Claude Code or Codex. Helper scripts need Python 3, standard library only.
metadata:
  version: "2.0.0-full"
  artifact_dir: ".idea-forge"
---

# Idea Forge

Help the user discover an option they would actually try. Use the interview to learn what familiar answers miss. Keep the user's choice of direction open.

## Rules that always hold

These rules stay at the top so they survive context compaction. Every stage below follows them.

1. Ask one question per turn. Mirror the user's own words and metaphors, and never slip in your own framing while discovering. Pick each question by expected information gain from `brief_state` and stop by the stopping rule (stage 1). Caps: Light 3, Standard 6, Deep 10, never more than 4, 8 or 12.
2. The user owns the frame. Offer competing frames, each naming what it assumes and what it leaves untouched, but never generate from a reframe the user has not picked.
3. Keep hard rules (H: never broken, including social and emotional vetoes) and assumed rules (R: fair game to drop or invert) in separate lists in `01_brief.json`. The user confirms which are hard.
4. Write a fit checklist in the brief and hold every idea to it. Fit is a gate, not a weight: an idea that breaks a hard rule, needs a vetoed behavior, misses the success condition, or could be handed to anyone with this problem is repaired once or cut. A cut idea never enters the portfolio. It may appear only as a labeled provocation footnote.
5. First-wave generators never see each other's output, the coordinator's examples, or a debate round. Every worker packet repeats the H list and the output schema at its start and at its end.
6. Keep a list of mechanisms already explored. Every later pass gets it and goes somewhere else.
7. Compare ideas by mechanism and dependency, not wording. A renamed mechanism is the same idea.
8. Judge only blind, equal-length cards with opaque ids, with the fit checklist and the user's baseline as anchors. Write the concrete difference first, then give one verdict per criterion. Never ask for a holistic "which is better" or an absolute 1 to 10 novelty score.
9. Randomize which card is shown first. Re-judge the closest pairs in the opposite order. A verdict that flips becomes a tie.
10. Return a portfolio across close, stretch and wildcard. Never drop the top wildcard without saying so, and never keep one that failed the fit gate.
11. Disk first: every stage writes its artifact to the run folder, workers read and write only their own files, and chat shows only what the user needs to decide. Never paste raw web pages or worker traces into the main session.
12. With nobody there to answer (unattended or batch runs), skip the human checkpoints, write down what you assumed in their place, and say so in the result. The fit gate still runs.
13. Mark field-wide novelty as unverified unless a scoped precedent check supports a narrower claim.

## Tiers

Standard is the default. Use Light when the user asks for speed, the stakes are low, or they mention a usage or quota warning. Use Deep when they ask for it or the problem is high stakes and clearly needs breadth and evidence. Infer or confirm the tier in your first reply. The tier is separate from the novelty setting.

| Stage | Light | Standard (default) | Deep |
| --- | --- | --- | --- |
| Interview | up to 3 questions (never past 4) | up to 6 (never past 8) | up to 10 (never past 12) |
| Frame checkpoint | 2 frames, shares a turn with the brief | 3 frames | 3 frames, optional pivot at the gut check |
| Wave one | main session runs the Brainwriting chain: 3 passes, about 10 titles, one pass inverts an assumed rule | 3 blind `haiku` workers (VS tail, rule drop, relational analogy), 6 seeds each, then 1 sequential taboo pass in the main session | 5 blind `haiku` workers (adds closed world plus assets, and Brainwriting), 5 to 6 seeds each, plus 1 main-session VS tail and transformational pass |
| Audit | by eye, mechanism table | `diversity_audit.py --kernel composite` | same, plus `--prev-wave` for beta-Vendi on wave two |
| Gut check | skipped (single wave) | 1 turn | 1 to 2 turns |
| Wave two | one self-mutation pass, no web search unless asked | 1 scout on the top 2 gaps and 1 taboo-repair worker | 3 scout or repair workers and 1 `sonnet` transformational synthesis worker |
| Fit gate | by eye against the checklist | logged per card | logged per card |
| Judging | 4-axis self-critique, no tournament | `sonnet` critic, `tournament.py`: 4 Swiss rounds, active boundary, swap audit (about 36 pairs at 12 finalists) | 5 Swiss rounds, active boundary, swap audit (about 72 pairs at 20), next-ten-seconds walkthrough on the top 8 |
| Result | 3 to 4 sketches | 5 sketches and a one-line judge health summary | 6 to 7 sketches, 48-hour tests, full judge card |
| Report's estimate | about 5 min, about $0.12, roughly 1x | about 8 to 15 min, about $0.25, roughly 3 to 4x | about 15 to 20 min, about $0.64 Claude or $1.01 Codex, roughly 6 to 8x |

The time, cost and token-multiple figures are the research reports' estimates at their stated November 2026 API rates, not measurements. The first report also lists token footprints (uncached / cached / output) of 15K / 47K / 9K for Light, 78K / 145K / 32K for Standard and 138K / 275K / 55K for Deep. Treat all of them as rough guides.

**Model routing.** Spend the frontier model where reasoning depth pays and small models where breadth comes from structure. Details and Codex names are in [harness adapters](references/harness-adapters.md).

| Role | Claude Code |
| --- | --- |
| Interview, frames, gut check, reframe, final synthesis | the main session's model (a frontier model in Deep) |
| Wave-one workers, wave-two repair and scouts, card scrubbing | `haiku` |
| Pairwise critic, Deep transformational synthesis | `sonnet` (a different tier from the workers) |

For Standard and Deep, read [harness adapters](references/harness-adapters.md) for dispatch, worker packets and the run folder.

## Run folder

Use `.idea-forge/<YYYY-MM-DD>-<topic>/` in the working directory, or the folder the host gives the task. Every stage writes here first.

    01_brief.json        brief_state, frames, picked frame, fit checklist, H and R, obvious-answer list, assumptions
    02_wave1/<worker>.json   each worker's titles and cards (its own file only)
    02_wave1_seeds.json  merged wave-one cards with normalized mechanism labels
    03_audit_w1.json     diversity_audit.py artifact for wave one
    04_gut_steer.json    sparks, vetoes with their 5-word why, missing angles (or what was assumed)
    05_wave2/<task>.json repair, spark and synthesis cards
    05_evidence/<gap>.json   scout evidence cards, 200 words or fewer
    05_wave2_pool.json   all cards with labels and fit verdicts (pass, repaired, cut + reason)
    05_audit_w2.json     audit of the full pool, with beta-Vendi against wave one in Deep
    06_cards.json        blind finalist cards with opaque ids (OPT_01 ...)
    06_next_batch.json   the pairs tournament.py scheduled next
    06_judge_pairs.json  every judged pair, appended round by round
    07_score_report.json tournament.py report
    08_result.md         portfolio, judge card, clichés, unexplored direction

Before resuming a run, read `01_brief.json` and the newest stage file instead of chat history. Do not commit the folder unless the user asks.

## 1. Interview

Read the conversation and directly relevant repo context first. Then keep `brief_state` in `01_brief.json` and update it silently after every reply:

    {"tier": "standard", "turn": 3, "terse_streak": 0, "stop_reason": null,
     "slots": {"episode": [], "core_deadlock": [], "hard_constraints_H": [], "mutable_rules_R": [],
               "asymmetric_advantages": [], "social_emotional_vetoes": [], "novelty_profile": {}},
     "confidence": {"episode": 0.6, "core_deadlock": 0.2, "...": 0.0},
     "candidate_questions": [
       {"q": "When you say 'wind down', what kind of wind down is that?", "slot": "core_deadlock",
        "decision_impact": 2, "expected_info_gain": 0.64}]}

Each turn, draft four candidate questions aimed at the weakest slots. Score each one's decision impact: 2 if different answers would rule out at least 30% of the kinds of solutions you might generate, 1 if some, 0 if none. Expected information gain is `(1 - slot confidence) x decision_impact / 2`. Ask only the top one. Never show the list. Never fill a gap with your own guess about their situation: ask a plain, naive question instead.

Draw candidate questions from these probes:

- **Episode.** Reconstruct a recent instance: the moment the outcome became more or less likely, what the person did next, what they noticed, and what they cared about then.
- **Workarounds and causes.** What already works, the workaround, its cost, and where it breaks. If several causes fit, ask about an exception or two similar episodes with different outcomes. Counterfactual: "What would have happened if that had not been there?"
- **Cue and advantage.** What did they notice or have access to that an outsider would not? Any asset, relationship, data, timing or shortcut.
- **Anxiety and habit veto.** Even if an idea solved the problem on paper, what effort, awkwardness, risk or mismatch with who they are would make them quietly stop after a week?
- **Unexamined premise.** What rule in their story are they treating as fixed that might be optional? Answers feed R.
- **Ambiguous terms.** When a key word is vague, mirror it: "When you say X, what kind of X is that?"
- **Unexplored alternatives.** Which familiar approach would they pass on, and why? Let them keep their own best idea private for a later comparison.
- **Contradiction.** If what they say they want clashes with what they did in the episode, ask about it plainly. It usually marks the real constraint.
- **Laddering.** For a vague goal ("better", "faster"), climb at most two or three rungs with rotated, non-interrogative probes ("What does that unlock?", "When that happens, what changes for you?"). Never repeat a bare "why".
- **Success and sources.** What observable difference, over what period, would make this worth using? Invite an artifact or comparator. Save outside precedent research for after free generation.

**Stopping rule (clarify or commit).** Stop and move to the frame checkpoint as soon as any of these holds:

1. Every slot has at least one concrete entry and no candidate question has decision impact 2. R and one of vetoes or advantages may read "none found" after one probe. The essentials are a specific episode with the moment it went wrong, the core deadlock, the hard rules with at least one veto or advantage, and the novelty profile.
2. The user shows impatience or gives two terse replies in a row (under 15 words each).
3. The tier's question cap is reached.

Also stop when two answers in a row did not change what you would explore. Record the stop reason in `brief_state`.

**Calibrate novelty.** Ask what should feel new: how it works, the experience of using it, both, or another dimension they name. Establish the comparison point. "Either counts" is valid. Offer three settings and recommend one with a reason tied to this brief:

| Setting | What to explore |
| --- | --- |
| Close to familiar | Keep the core approach. Find a concrete improvement on the chosen dimension, within existing resources. |
| A stretch | Change an important part of the mechanism or experience. Explain the departure and offer a plausible first test. |
| A wild card | Challenge a premise about how the goal must be achieved. Named speculative dependencies are welcome. Keep the success condition and hard rules. |

**Fit checklist.** Write five lines or fewer, in the user's words: the success condition, the hard rules, the vetoes, the unfair advantage, and the episode moment an idea has to change. Also write the obvious-answer list: the user's current attempts, the familiar products they named, and the first few ideas you would suggest without thinking. Generators never see the obvious-answer list. It is used for the fit gate and judging.

## 2. Frame checkpoint

Before generating, show the frames in one turn, 120 words or fewer in total, with the brief summary, the fit checklist and the novelty chooser:

- **Frame A (your stated frame):** the goal verbatim. Assumes ... Leaves untouched ...
- **Frame B (root tension):** the deadlock, veto or upstream trigger underneath it. Assumes ... Risk ...
- **Frame C (advantage or rule drop):** built on their unfair advantage or on dropping one R. Or a reorienting frame that shelves the stated goal for a moment and asks what outcome the people involved actually care about. Assumes ... Risk ...

Light shows two frames. List the H and R rules and ask the user to move anything wrongly placed. Ask in one line: "Which frame should we solve, A, B or C? You can edit one or split wave one across two." Do not start wave one until they confirm. Accepting the recommended frame and setting in one reply confirms the brief.

## 3. Wave one: blind generation

Each worker gets one packet: the confirmed brief, the picked frame (or its half of a split), the fit checklist, H and R, the novelty setting, one practitioner lens and one operator block from [divergent operators](references/divergent-operators.md), never the whole catalog. A lens is an ordinary, specific practitioner or lived situation shaped by this brief ("a night-shift nurse who cannot count on anyone reading instructions"), never a famous person, a leader or a generic job title. A worker may sharpen its own lens from the brief before it starts. Keep generators isolated: more interaction and more generators both shrink diversity, so stay at 3 to 5.

Generate in two steps. First list short titles (5 to 8 words) and check that no two share a causal lever. Then expand the most different ones into cards in the schema in the operators reference. Every card names what it is grounded in. Do not add generic exhortations such as "be creative" or "avoid clichés". They make output worse.

In Light, the three Brainwriting passes share a context, so each later pass gets the mechanisms the earlier passes used and works through a different causal step. In Standard, the main session then runs one sequential pass with the explored-mechanism list. In Deep, the main session adds one Verbalized Sampling tail pass that also inverts an assumed rule.

## 4. Audit

Normalize mechanism labels after comparing causal paths, update the explored-mechanism list, and merge cards into `02_wave1_seeds.json`. In Standard and Deep run `python3 scripts/diversity_audit.py --input 02_wave1_seeds.json --kernel composite --output 03_audit_w1.json` from the skill directory. In Light, count labels by eye.

Act on `status`. On `COLLAPSE_ALERT`, use its `taboo_repair_cards` (one for pools under 15, at most two otherwise). Also act on `shared_assumption_alerts`: assign an idea that works when that assumption is false. A surface disguise ratio above 2 means the pool is a few mechanisms in different words, so trust the mechanisms. Cards marked `structural_wildcard` get a [WILDCARD] tag at the gut check.

## 5. Gut check (Standard and Deep)

Show one-line, unpolished mechanism titles only, grouped by audit cluster, 15 lines or fewer, no sales copy. Ask once: "Quick gut check before wave two. Sparks: one or two ids that pull at you, even vaguely? Instant vetoes: one or two ids, plus five words on why? Anything missing?" They can skip it. Save the reply to `04_gut_steer.json`. A veto rules out the mechanism behind the title, not only that card: add it to H and the fit checklist and drop that cluster from wave two. In Deep, the user may pivot the frame here.

## 6. Wave two

Decide assignments from the audit, the gut check and the gaps: develop a spark, run a taboo repair, cover a missing angle, or test a fragile premise against evidence. Gap fillers get the explored-mechanism list. Repair workers get at most two banned causal pathways (from the taboo cards and gut vetoes), each stated as a pathway plus its shared assumptions, never as keywords, and they must write a one-sentence equivalence check per card. Scouts run at most two targeted searches per gap and write evidence cards of 200 words or fewer: what the source supports, what it leaves open, where the analogy breaks and which card should change. Label unresolved claims when access is missing. Light does one self-mutation pass instead.

Merge everything into `05_wave2_pool.json`. In Deep, rerun the audit with `--prev-wave 02_wave1_seeds.json`. A `STAGNANT_WAVE2` flag means wave two added little new ground: say so, and consider one more gap assignment.

## 7. Fit gate

Check every card against the fit checklist before judging. Record `fit_verdict` (`pass`, `repaired` or `cut`, with a one-line reason) per card in the pool file. Light keeps a short list.

- **Hard rule broken:** cut.
- **Needs a vetoed behavior or a vetoed mechanism:** cut.
- **Misses the success condition:** walk it through the episode moment. If it does not change what happens there, repair once or cut.
- **Generic:** if its grounding is empty or it would work as well for anyone with this problem, repair once by tying it to a specific detail or advantage, or cut.
- **Obvious answer:** if its mechanism matches the baseline or the obvious-answer list, cut it, unless the setting is close to familiar, where at most one can stay as the baseline improvement.

A repair keeps the mechanism and changes how it lands. If the repaired card fails the same check, cut it. If more than half the pool is cut, generate again around the fit checklist before judging. A cut card that the audit ranks in the top two for uniqueness may be shown at the end as a labeled "rule-breaking provocation", never as a pick.

## 8. Stress-test and blind cards

Use the [critique reference](references/adversarial-critique.md). For each survivor, finish "This works only if ...". If several depend on the same doubtful condition, generate a replacement that survives it being false. If a stretch or wildcard shortlist leans on one vivid detail, try an alternative without it. Sharpen each finalist once: strengthen or cheapen the weakest link in its "works only if" line without changing the mechanism. Name the cheapest test, ideally reversible within 48 hours. If every candidate is too familiar, reopen generation around the repeated premise.

Then scrub each finalist into a blind four-line card with an opaque id, 40 to 70 words, all within about 10 words of each other: trigger (the next ten seconds), mechanism, works only if, first cheap test. A `haiku` pass can do the scrubbing. Write them to `06_cards.json` with `tier_intent`, `fit_verdict` and `words`. Cap finalists at about 12 in Standard and 20 in Deep, trimmed by audit uniqueness and fit.

## 9. Judge and build the portfolio

**Light:** compare finalists side by side on the four axes yourself and check them against H. No tournament.

**Standard and Deep:** loop until the scheduler says done:

    python3 scripts/tournament.py schedule --pool 06_cards.json --verdicts 06_judge_pairs.json --audit 05_audit_w2.json --k 5 --output 06_next_batch.json

Send each batch (up to six disjoint pairs) to a fresh critic that did not write the ideas, on a different model tier from the workers. The critic gets H, the fit checklist, the user's baseline and the cards in each pair, never worker ids or operators. It appends its verdicts to `06_judge_pairs.json`. The schedule runs Swiss rounds, then active-boundary pairs near the cut line, then the swap audit. Then score:

    python3 scripts/tournament.py score --pool 06_cards.json --verdicts 06_judge_pairs.json --audit 05_audit_w2.json --k 5 --novelty-tier stretch --output 07_score_report.json

Use `--k 6` in Deep. The report gives Bradley-Terry strengths with 95% intervals, virtual ties, circular triads and the cycle rate, a HodgeRank split, bias warnings, the Pareto front, the niche grid, and a quality-diversity portfolio seeded by niche quotas for the novelty setting and filled by greedy k-DPP. In Deep, walk the top eight through the next ten seconds and drop any whose walkthrough breaks. If `WARN_INTRANSITIVE` appears, tell the user the judge could not separate the finalists and let them choose directly.

## 10. Return the result

Honor a requested count. Otherwise return the tier's portfolio size. Each 40 to 80 word sketch says what happens, which part of the user's situation it builds on, how it differs from the named baseline, what it depends on, and its cheapest test. Tag each close, stretch or wildcard, and mark a rescued wildcard as such. Add one line on the fit gate (how many cards were cut and the most common reason). In Standard, add the one-line judge health summary. In Deep, add the full judge card (topology, flips, cycles, HodgeRank, wildcard rescue, any niche quota not met), a 48-hour reversible test for each top pick, the discarded clichés, an unexplored direction and where the run's files are. Put any provocation footnote last. List every assumption made in place of a skipped checkpoint.

Invite the user to pick a concept or change the tier, setting, frame or dimension. On a change, keep the confirmed context, regenerate or revise, and show the difference. Give a recommendation when asked. After selection, save the brief, chosen mechanism, assumptions and next test to `docs/ideation/YYYY-MM-DD-<topic>.md` when working in a writable project where the user wants the record. Preserve existing notes. If the user later brings a trial result, start at the first point where prediction and observation diverged.

## Before you send the result

Check the rules once more: one question per turn was kept, the user picked the frame, every card in the portfolio passed the fit gate, judging was blind with flips counted as ties, the top wildcard is in the portfolio or its absence is explained, the files are on disk, and every stand-in assumption is listed.
