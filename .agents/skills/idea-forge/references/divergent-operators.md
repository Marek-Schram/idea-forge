# Divergent operators

Keep the episode, desired outcome and existing strengths visible. Generate candidates as short sketches of a change and its causal effect. Hold comparisons until the pool is assembled.

- **Verbalized sampling.** Ask for several plausible responses from different parts of the response distribution, including unlikely answers. As a variation, request responses with estimated typicality below 0.10. These model estimates are a prompting device. Judge originality by comparing mechanisms and known precedents.
- **Closed-world transformation.** Inventory the resources already present. Try subtraction (remove an element), multiplication (duplicate an element with a changed property), division (move a part in time, place or ownership), task unification (give something already present a second job), or attribute dependency (make one variable depend on another). For a difficult brief, first transform the form, then ask what new function it could serve.
- **Contradiction and dimensions.** Identify two desired outcomes in tension. Vary actor, timing, incentive, or information available. Pick an unexplored combination and explain how it could satisfy both demands.
- **Relational analogy.** Find a moderately distant setting with the same bottleneck. Identify the roles, the relationship, and the action that resolves it there. Transfer that relationship and name the point where the analogy breaks.

For a large pool, assign consistent mechanism labels after comparing the causal descriptions. From the installed skill directory, run `python3 scripts/diversity_audit.py wave1.json` with a scratch input file shaped like this:

    [{"id":"a","mechanism":"transfer responsibility","sketch":"An existing participant takes over the unfinished step."}]

A label covering over 40% of the pool or a pair with high word overlap is a cue to inspect coverage. Check mislabeled paraphrases by hand. Keep useful variants when they change the trade-off.
