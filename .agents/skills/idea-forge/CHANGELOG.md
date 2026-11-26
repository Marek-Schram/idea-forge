# Changelog

## 2.0.0 (2026-11-26)

Targets three failure points seen in real runs: hidden context the user never states, pools where several ideas share one mechanism under different names, and judging that can be swayed by order and polish.

### Added
- "Rules that always hold" block at the top of SKILL.md. Claude Code re-injects only the first 5,000 tokens of an invoked skill after compaction, so the non-negotiables live first.
- Frame checkpoint before generation: two or three frames (as stated, the tension underneath, an unfair-advantage or rule-drop angle) for the user to pick, edit or combine.
- Hard rules (H) vs assumed rules (R) in the brief, and a rule-drop operator that only touches R.
- Interview probes for unfair advantage and veto, a stop rule, and question caps (Quick 4, Deep 8).
- Gut check between waves: titles only, sparks, vetoes and missing angles in one turn.
- Two-step generation (titles first, then idea cards with mechanism, causal path, dependency and change fields).
- Taboo repair: at most two banned mechanisms per repair wave, with a "does it still work without it" check against renamed duplicates.
- Blind equal-length cards, decomposed pairwise judging with a written difference first, and order-swap audits on close pairs (flips become ties).
- Portfolio selection across close, stretch and wildcard niches, with the top novelty pick protected.
- State folder (`.idea-forge/YYYY-MM-DD-<topic>/`) for stage artifacts, and an unattended-run rule that logs stand-in assumptions.
- CHANGELOG.md.

### Changed
- `scripts/diversity_audit.py`: compares structured fields (label, causal path, dependency, change), reports a Vendi score as the effective number of distinct ideas, near-duplicate clusters, each card's unique contribution and up to two taboo targets. Still accepts the 1.x input shape. Stdlib only.
- `scripts/score_matrix.py`: merges swap audits (flips become ties), adds per-criterion points, a Pareto front, a niche-aware portfolio, and a judge card with flip rate, length bias and below-cut keeps. Still accepts the 1.x input shape. The trailing "Selected winner:" line is replaced by "Decision: left to the user."
- Model guidance per role: Sonnet stays the default for workers, Haiku is offered for cheaper wave-one runs, the main session keeps the interview, frames and synthesis.
- Divergent operators: relational analogy now maps causal roles before searching for a distant setting.

### Not adopted
- Swiss or active-boundary tournaments and K-DPP selection: with six to eight finalists, all pairs plus a few swaps costs little and is easier to audit.
- A third effort tier with dollar estimates: the cost figures behind it could not be verified.
