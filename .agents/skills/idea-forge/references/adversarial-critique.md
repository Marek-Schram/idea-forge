# Adversarial critique

Only cards that passed the fit gate reach this stage. For each candidate ask what is new relative to the user's baseline, what assumption could invalidate its mechanism, whether it fits the hard rules and vetoes, what a failed trial could teach, and who could bear a concrete downside. Give the strongest objection in plain language. If a constraint is unknown, state the dependency. For each cut, keep a one-line reason tied to the brief. Compare a wildcard on learning value before discarding it for uncertainty.

## Hard-rule gate

Before any pairwise judging, check every card on its own against H and the vetoes. This gate is non-compensatory: a card that fails gets `fit_verdict: "cut"` (or `h_gate: "FAIL"`) and leaves the ranking, however original it is. If a failed card is in the top two of the audit's leave-one-out uniqueness, it may be shown once at the end as a labeled "rule-breaking provocation" so the user sees the edge of the space. It is never a pick and never counts toward the portfolio. `tournament.py score` lists these under `gated_provocations`.

## Blind cards

Rewrite every finalist into the same four lines, 40 to 70 words in total, all cards within about 10 words of each other:

    Trigger: what happens in the next ten seconds at the moment things usually go wrong.
    Mechanism: what changes and why it could work, in one sentence.
    Works only if: the key dependency.
    First cheap test: one reversible check, ideally within 48 hours.

Give each card an opaque random id (OPT_01, OPT_02 ...). Strip operator names, lens names, worker ids, adjectives that sell, emphasis, and anything that hints at who wrote it. Judges reward length, polish and text that reads like their own, so equal plain cards keep the comparison about substance. A deterministic edit or a `haiku` scrub pass does the rewrite. Record each card's word count as `words`.

## Decomposed pairwise judging

Use a fresh critic that did not write the candidates, on a different model tier from the workers (`sonnet` critic for `haiku` workers). A judge from a different model family is better when one is available, since self-preference is not reliably smaller in stronger models. Give the critic two anchors with the cards: the fit checklist with H, and the user's baseline (what they do today or the familiar option they would pass on). Concrete anchors make judges more reliable than an open "which is better".

Send pairs in batches of four to six disjoint pairs per critic turn, as `tournament.py schedule` groups them. Prompt pattern:

    You are an independent, skeptical evaluator. Compare each pair (Left vs Right) on substance only.
    Ignore prose polish and length.
    HARD CONTEXT H: <H and vetoes, re-injected>
    For each pair_id output JSON only:
      evidence_diff (25 words or fewer): the sharpest causal difference and each option's
        concrete failure mode, written BEFORE any verdict.
      verdicts, each "L", "R" or "T" (genuine tie):
        fit: fits the user's real constraints, advantages and vetoes without heroic behavior change
        plausibility: survives its own "works only if" with fewer fragile assumptions
        originality: ignoring wording, uses a more non-obvious causal lever than the category's
          clichés and the baseline. Judge this without regard to feasibility.
        learning: can be tested reversibly within 48 hours and teaches something even if it fails
    HARD CONTEXT H again, and the output schema again.

Judging the criteria separately keeps low feasibility from sinking a genuinely original idea before the portfolio step can protect it. Never ask for a holistic verdict or an absolute 1 to 10 novelty score: models compress novelty scores into the safe middle. Distinguish judgments the user supplied from provisional judgments by a critic.

## Tournament schedule

Full all-pairs judging grows with the square of the finalist count, and judging both orders doubles it. `tournament.py schedule` replaces it with:

1. **Swiss rounds.** 4 rounds for 14 finalists or fewer, 5 above that. Each round pairs neighbours in the current standings with no rematches. Which card is shown first is a coin flip, which turns position bias into noise instead of a systematic tilt.
2. **Active boundary.** n / 2 unplayed pairs among the top k + 6 and any structural wildcards, chosen where a Bradley-Terry fit is least certain and the two strengths are closest.
3. **Swap audit.** The closest judged pairs, max(6, 20% of judged pairs), shown again in the opposite order. A criterion verdict that flips becomes a tie for both games.

The report's simulation (20 finalists, top 6) put this at 72 calls instead of 380 for both-order all pairs, with about 0.82 top-6 recall. Treat that as the report's estimate. With 6 finalists the schedule covers nearly every pair anyway.

Run it from the skill directory, appending the critic's verdicts after each call:

    python3 scripts/tournament.py schedule --pool cards.json --verdicts judged.json --audit audit.json --k 5 --output next.json
    python3 scripts/tournament.py score --pool cards.json --verdicts judged.json --audit audit.json --k 5 --novelty-tier stretch

`--help` documents the verdict file shape. Each comparison records `pair_id`, `phase`, `left_id`, `right_id`, `is_swap_of`, `evidence_diff` and `verdicts`. The 2.0-lean `pairs` shape is accepted too. Exit code 2 means malformed input.

## What the score report holds

- **Bradley-Terry strengths** per criterion and for the weighted composite (MM algorithm with a weak prior so sparse Swiss graphs and unbeaten cards stay finite), with observed-Fisher 95% intervals, the probability each card beats the next one down, and virtual ties where that probability is below 0.60.
- **Consistency.** Circular triads (A beats B beats C beats A) among fully observed triangles, the cycle rate, transitivity and a sparse Kendall zeta. Transitivity below 0.85 means the judge cannot separate the finalists, so the user decides directly. A HodgeRank split of the composite flow into gradient (a consistent ranking), local curl (three-way cycles) and global harmonic (longer cycles that triangle counts miss). Warnings fire above 0.35 curl or 0.25 harmonic.
- **Bias checks.** Order-swap flip rate (warning above 20%), first-shown win rate (warning outside 38% to 62%), and the correlation between card length and strength (warning above 0.35).
- **Portfolio.** Three axes on 0 to 1: viability (0.55 fit + 0.45 plausibility), originality (0.65 judged originality + 0.35 audit uniqueness) and learning value. The Pareto front on those axes. A MAP-Elites style niche grid (close, stretch or wildcard by mechanism cluster) whose elites are the strongest viable card per cell. Niche seeding by the novelty setting (close to familiar: 2 close and 1 stretch, a stretch: one of each, a wild card: 1 stretch and 2 wildcards), protection of the top originality pick as in 2.0-lean, then a greedy k-DPP fill over the audit's similarity matrix that trades quality against redundancy. `--selector utility` swaps in the greedy creative-utility rule (quality times one minus half the closest similarity to a pick). A card that loses on fit to more than half its opponents never takes a seeded or protected slot.
- **Judge transparency card.** Topology and call counts, flips, first-shown rate, length bias, cycles, HodgeRank shares, Pareto leads, niche elites, portfolio effective diversity, rescued wildcards (picked although below the scalar top k), killed-by-feasibility alerts (top two on originality or learning but in the bottom half overall), unmet niche quotas, fit-gate cuts and provocations, and a one-line critique audit for Standard results.

## All-pairs fallback

When every pair was judged (a small set the user asked to see exhaustively), `python3 scripts/score_matrix.py comparisons.json` still scores it as in 2.0-lean, with the plus or minus 10% weight sensitivity range. `--help` documents its input. `tournament.py score` reads the same file and adds the diagnostics above.

Explain the decisive trade-off and leave selection to the user.
