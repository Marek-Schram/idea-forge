# Changelog

## 2.0.0 (2026-11-26)

Targets the two complaints from real use, same-y ideas and ideas that don't fit the situation, plus judging that can be swayed by order and polish.

### Added
- Fit gate before judging: every card is checked against a fit checklist (success condition, hard rules, vetoes, unfair advantage, the episode moment) and passes, gets one repair, or is cut. Generic ideas that could go to anyone, and ideas that match the obvious-answer list, are cut too (one baseline improvement may stay in a close-to-familiar run). Cut ideas never return in the portfolio. Runs unattended as well.
- `grounded_in` field on idea cards: the specific detail of the user's situation an idea relies on.
- Interview probes for an unexamined premise and for contradictions between what the user wants and what they did, a sharper veto question ("what would make you quietly stop after a week"), and a four-slot stop rule that requires at least one veto or advantage.
- Gut-check vetoes rule out the whole mechanism and join the fit checklist.
- Explored-mechanism list: Quick's later passes and wave-two gap fillers are told which mechanisms are already covered.
- Vantage points specific to the brief instead of generic job titles.
- Sharpen pass on finalists: strengthen the weakest "works only if" link without changing the mechanism.
- Judge anchors: the judge gets the fit checklist and the user's baseline with the blind cards.
- `evals/ab-test.md` at the repo root: a six-brief blind A/B check with hidden context cards.
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
- `scripts/diversity_audit.py`: compares structured fields (label, causal path, dependency, change), reports a Vendi score as the effective number of distinct ideas, near-duplicate clusters, shared "works only if" assumptions, a surface-vs-mechanism ratio that catches renamed duplicates, cards missing grounding, each card's unique contribution and up to two taboo targets. Still accepts the 1.x input shape. Stdlib only.
- `scripts/score_matrix.py`: merges swap audits (flips become ties), adds per-criterion points, a Pareto front, a niche-aware portfolio, and a judge card with flip rate, length bias and below-cut keeps. A candidate that loses on fit to most of the field can't take a balance or novelty slot, and `fit_cut` cards are reported and never picked. Still accepts the 1.x input shape. The trailing "Selected winner:" line is replaced by "Decision: left to the user."
- Model guidance per role: Sonnet stays the default for workers, Haiku is offered for cheaper wave-one runs, the main session keeps the interview, frames and synthesis.
- Divergent operators: relational analogy now maps causal roles before searching for a distant setting.

### Not adopted
- Bradley-Terry fits, HodgeRank and cycle diagnostics: with every pair judged, win counts plus the swap audit already show what matters.
- Order-q Vendi profiles and MAP-Elites niches: one Vendi score plus the close/stretch/wildcard tags covers a five to seven idea portfolio.
- A VoI-ranked JSON interview state: the brief file and the one-question-per-turn rule do the same job in prose.
- Swiss or active-boundary tournaments and K-DPP selection: with six to eight finalists, all pairs plus a few swaps costs little and is easier to audit.
- A third effort tier with dollar estimates: the cost figures behind it could not be verified.
