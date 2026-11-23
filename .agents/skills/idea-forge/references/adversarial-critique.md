# Adversarial critique

For each candidate ask what is new relative to the user's baseline, what assumption could invalidate its mechanism, whether it fits actual constraints, what a failed trial could teach, and who could bear a concrete downside. Give the strongest objection in plain language. If a constraint is unknown, state the dependency. For each cut, keep a one-line reason tied to the brief. Compare a wildcard on learning value before discarding it for uncertainty.

For a close decision, put two sketches side by side with their origin hidden. For each relevant criterion, record which has the advantage and why, allowing ties. Give the user's stated priorities the most weight. Distinguish judgments supplied by the user from provisional judgments supplied by a critic.

For a full comparison, use one judgment per unordered pair per criterion. With six finalists this is 15 pairs. Use the following input shape for `python3 scripts/score_matrix.py comparisons.json` from the skill directory:

    {"ids":["a","b"],"weights":{"feasibility":1,"novelty":2},"pairs":[{"a":"a","b":"b","votes":{"feasibility":"a","novelty":"tie"}}]}

Weights are positive relative priorities. The helper gives each pairwise win one point and a tie half a point. It reports normalized weighted scores and the rank range when each criterion weight moves by ±10% one at a time. These ranges describe sensitivity to stated preferences. They do not quantify statistical uncertainty. Explain the decisive trade-off and leave selection to the user.
