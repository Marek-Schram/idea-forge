# Changelog

## 2.0.0-full (2026-11-26)

Branch `claude/idea-forge-v2-full`. Built on 2.0.0 (lean) so the two can be A/B tested. It keeps every lean feature (fit gate, grounding, explored-mechanism list, frame checkpoint, H and R, gut check, taboo repair, blind cards, swap audits) and adds everything the two research reports recommend that lean left out, including every item in lean's "Not adopted" list.

### Added
- Three tiers, Light, Standard (default) and Deep, replacing Quick and Deep. A table says what each runs. Question caps follow the second report (3, 6, 10) with the first report's caps as hard ceilings (4, 8, 12). Per-tier time, cost and token figures are shown and labeled as the reports' estimates.
- Model routing per role: `haiku` workers, scouts and scrubbing, a `sonnet` critic and Deep synthesis worker on a different tier from the workers, and the main session's model for the interview, frames and synthesis. Codex mapping: `gpt-6-luna` workers, `gpt-6.2-sol` critic, `gpt-6.2-astra` or `gpt-6.2-sol` main session.
- Value-of-information interview: a JSON `brief_state` in `01_brief.json` with seven slots, per-slot confidence, four silent candidate questions per turn scored for decision impact and expected information gain, and a clarify-or-commit stopping rule (all slots filled and no high-impact question left, two terse replies or impatience, or the cap). New probes: cue and advantage (CDM), anxiety and habit veto (JTBD), counterfactual, ambiguous terms mirrored in the user's words (Clean Language), unexplored alternatives, and laddering capped at three rungs.
- Frames now state what each assumes and what it leaves untouched, stay under 120 words, offer a reorienting frame C, and let the user split wave one across two frames. Light shows two frames.
- Disk-first run folder with numbered stage files (`01_brief.json` to `08_result.md`, plus `02_wave1/`, `05_wave2/`, `05_evidence/`). Workers read one packet and write one file.
- Worker packets repeat H and the output schema at the start and the end, carry one operator block only, and stay under about 15K tokens.
- Operators reorganized into five worker blocks with default practitioner lenses: VS tail (p < 0.10), rule drop and inversion (six modified rule sets filtered by H and realism, contradictions folded in), relational analogy with object mappings, closed world plus assets, and the Brainwriting chain (Deep worker and Light engine). Card schema adds `worker_operator`, `frame_id`, `assumptions`, `slots` and `tier_intent`.
- Taboo repair bans causal pathways plus their shared assumptions, never keywords, and requires a one-sentence equivalence check per card. Gut vetoes join the ban list.
- Gut check shows titles grouped by audit cluster with [WILDCARD] tags, asks for a five-word why on each veto, and saves to `04_gut_steer.json`. Deep allows a frame pivot there.
- Scouts: at most two queries per gap, evidence cards of 200 words or fewer, never raw page text.
- `scripts/tournament.py` (new, stdlib only). `schedule` emits Swiss rounds (4 up to 14 candidates, else 5) with backtracking no-rematch pairing and coin-flip order, then n / 2 active-boundary pairs chosen by Bradley-Terry uncertainty near the cut, then a swap audit of max(6, 20%) closest pairs, in batches of up to six disjoint pairs. `score` fits Bradley-Terry strengths by the MM algorithm with a Laplace prior, per criterion and composite, with observed-Fisher 95% intervals, separation probabilities and virtual ties, counts circular triads with cycle rate, transitivity and sparse Kendall zeta (per criterion too), splits the flow by weighted HodgeRank into gradient, curl and harmonic shares, checks flip rate, first-shown win rate and length bias, builds a 3-axis Pareto front, a MAP-Elites niche grid (niche by mechanism cluster), niche quotas per novelty setting, and fills the portfolio by greedy k-DPP over the audit's similarity matrix (or greedy creative utility with `--selector utility`). It reports rescued wildcards, killed-by-feasibility alerts, unmet niche quotas, fit-gate cuts and rule-breaking provocations in a judge transparency card plus a one-line critique audit. It reads the lean `pairs` format and inline `swap_votes`, keeps lean's fit-cut and weak-fit rules, and exits 2 on malformed input.
- `scripts/diversity_audit.py`: `--kernel composite` (0.45 mechanism view from BM25 unigram and bigram cosine blended with char-trigram cosine, 0.35 assumption-set Jaccard, 0.20 causal-slot Jaccard), order-q Vendi at q = 0.5, 1, 2 and infinity, dominant spectral share, surface disguise ratio, leave-one-out Vendi anomaly scores and structural wildcards, complete-linkage clusters, shared-assumption alerts above 35%, highest-overlap pairs with the views they share, pool-size calibrated collapse thresholds with one or two taboo repair cards, beta-Vendi against `--prev-wave` with a `STAGNANT_WAVE2` flag, optional `--embeddings`, `--output` artifact with the similarity matrix and a compact stdout summary, and the research schema's field names. Every lean output key is unchanged, and the default kernel reproduces lean's numbers exactly.
- Blind cards are four lines (trigger, mechanism, works only if, first cheap test), 40 to 70 words, opaque ids, scrubbed by a `haiku` pass. A non-compensatory hard-rule gate runs before judging. The critic prompt asks for the evidence difference and each option's failure mode before four L/R/T verdicts, in batches of four to six pairs.
- Agent definitions: `agents/claude/idea-worker.md`, `idea-scout.md`, `idea-critic.md` and `agents/codex/idea_worker.toml`, `idea_scout.toml`, `idea_critic.toml` with a `config.toml.example` that caps concurrency at five and registers each agent explicitly. Codex guardrails: fresh children, Fast mode off, check resolved models first.
- Harness notes: optional cross-family worker or critic, cache and cost hygiene, compaction between wave two and judging, frontmatter kept to portable fields plus `compatibility`.
- A short rule recap at the bottom of SKILL.md, so the non-negotiables sit at both ends.
- `evals/full-eval-protocol.md`: the reports' 12-scenario, 30-comparison blind protocol, rubric, ablation, execution proxy and ship gates, as a document only.

### Changed
- Default tier is Standard (was Quick). Quick is now Light.
- `score_matrix.py` is kept unchanged for all-pairs runs. Its input example moved from the reference into its `--help`, as the second report suggests.

### Checklist of report items not built as written
- Shared `linalg_mini.py` helper: each script stays self-contained, since `python3 -I` does not put the script's folder on the import path.
- Optional numpy acceleration: skipped to stay stdlib only. A 30-card composite audit runs in about a second.
- Restricting leave-one-out scores to 15 candidates above 25 cards: not needed at that speed, so every card gets a score.
- Replacing the plus or minus 10% weight sensitivity with Fisher intervals: done in `tournament.py`. `score_matrix.py` keeps the old range for backward compatibility.
- Second report's kernel with the sketch inside it (0.20): not used, because the sketch must stay outside the mechanism kernel for the surface disguise ratio to mean anything. The first report's 0.45 / 0.35 / 0.20 split is used, with the second report's char trigrams folded into the mechanism view.
- Two-round Swiss and swaps on only the top 3 or 4 pairs (second report): the first report's 4 or 5 rounds and max(6, 20%) swaps are used. At 6 to 12 finalists they land in the second report's 1.5n to 2n pair range.
- Per-tier orchestrator model (mid tier for Light and Standard): a skill cannot switch the main session's model, so this is guidance in the routing table.
- SKILL.md under 3,200 tokens: not met (about 5,500 tokens, 202 lines, under the 25 KB and 320-line limits). The rules, tiers, routing and run folder sit in the first part that survives compaction.
- Deleting deprecated Codex keys and the retired Claude Code agents wizard, and removing fixed minimum interview counts: not applicable, since lean had none of them.
- Unverified figures (costs, token footprints, model names, the 72-call and 81.5% recall simulation): kept and labeled as the reports' estimates.

## 2.0.0 (lean) (2026-11-26)

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
