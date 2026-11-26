# Adversarial critique

For each candidate ask what is new relative to the user's baseline, what assumption could invalidate its mechanism, whether it fits the hard rules, what a failed trial could teach, and who could bear a concrete downside. Give the strongest objection in plain language. If a constraint is unknown, state the dependency. For each cut, keep a one-line reason tied to the brief. Compare a wildcard on learning value before discarding it for uncertainty.

## Blind cards

Before any judging, rewrite every finalist into the same template, 40 to 60 words:

    What happens: ...
    Why it could work: ...
    Works only if: ...

Strip operator names, lens names, worker ids, adjectives that sell, and anything that hints at who wrote it. Keep cards within about 10 words of each other in length. Judges tend to reward length and polish, so equal plain cards keep the comparison about substance. Shuffle the order before handing cards to a judge.

## Decomposed pairwise judging

Use a fresh judge that did not write the candidates. A judge from a different model family is better when one is available, since judges tend to favor text that reads like their own. For each pair:

1. Write the concrete difference between the two cards in 25 words or fewer.
2. Give one verdict per criterion: the winning id or "tie".

Default criteria, reweighted by what the user said matters:

- **Fit:** works inside the hard rules and the user's success condition.
- **Causal plausibility:** the "why it could work" chain holds without a leap.
- **Mechanism originality:** different from the user's baseline and the obvious-answer list in how it works, not just how it sounds.
- **Learning value:** a cheap, quick test would teach something useful even if the idea fails.

Judging criteria separately keeps low feasibility from sinking a genuinely original idea before the portfolio step can protect it. Distinguish judgments the user supplied from provisional judgments by a critic.

## Order and swap audit

Randomize which card appears first in each pair. After the first pass, re-judge every close pair (decided by one criterion or less, or where the two cards are within 0.1 on score) with the order reversed. When a verdict flips, it becomes a tie. With six finalists that is 15 pairs plus a handful of swaps, so there is no need for tournament schemes. With more than eight finalists, cut to eight using the diversity audit and frame fit before judging.

## Score and portfolio

Record judgments for `python3 scripts/score_matrix.py comparisons.json` from the skill directory:

    {"ids": ["a", "b"],
     "weights": {"fit": 3, "plausibility": 2, "originality": 2, "learning": 1},
     "pairs": [
       {"a": "a", "b": "b", "evidence": "a needs no second device",
        "votes": {"fit": "a", "plausibility": "a", "originality": "b", "learning": "tie"}},
       {"a": "b", "b": "a", "swapped": true,
        "votes": {"fit": "a", "plausibility": "a", "originality": "tie", "learning": "tie"}}
     ],
     "niches": {"a": "close", "b": "wildcard"},
     "novelty_criterion": "originality",
     "portfolio_size": 2}

Every unordered pair needs one primary judgment, so a real run with six finalists lists 15 primary pairs. Swap audits, niches, novelty criterion, portfolio size and word counts are optional. The helper reports:

- weighted scores, per-criterion points and the rank range when each weight moves 10% either way (sensitivity to stated preferences, not statistical uncertainty)
- the Pareto front: candidates nobody beats on every criterion
- a suggested portfolio: the best candidate in each niche, the top candidate on the novelty criterion, then the next best scores
- a judge card: swap flip rate, which verdicts flipped, length bias, and any candidate kept below the score cut

Explain the decisive trade-off and leave selection to the user.
