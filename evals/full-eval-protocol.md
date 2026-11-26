# Idea Forge full evaluation protocol

This is the research reports' release test, written down as an evaluation plan. Nothing here runs inside the skill. Use it when you want a result you could defend, not just a gut feel. For a quick afternoon check, `ab-test.md` is enough.

It compares any two arms. The obvious ones on this branch: 2.0-lean vs 2.0-full (Standard), 2.0-full Standard vs 2.0-full Deep, and 1.2.1 vs either 2.0.

## Why a bigger test

- **Proposal-stage judges overrate AI ideas.** In the Ideation-Execution Gap study the first report cites, AI ideas beat human ideas as proposals but dropped about 1.9 points on effectiveness once executed, while human ideas barely moved. So a judge reading proposals is not enough. Add an execution proxy.
- **Small samples are underpowered.** Per the first report's binomial math, 16 paired comparisons give only about 40% power to detect a 75% win rate. 30 paired comparisons give about 80% power at 75%, and 21 of 30 wins (70%) is the two-sided p < 0.05 line.

## Design

1. **Scenarios.** Pick 10 of the 12 below and hold 2 back for regression checks after any later change. Each scenario has an opening line and a hidden card. The person playing the user reveals a hidden item only when a question (or the gut check) points at it.
2. **Arms.** Same backbone model for every arm. Run each arm in a fresh session per scenario. Record wall-clock interview minutes, interview turns, sub-agent calls, and judge calls.
3. **Raters.** Three independent raters per scenario, ideally the scenario's problem owner plus two peers, using the Consensual Assessment Technique. Check agreement: Fleiss' kappa of at least 0.40. 10 scenarios times 3 raters gives 30 paired comparisons.
4. **Blinding.** Strip version labels, judge cards, file paths and formatting tells. Present both portfolios as plain numbered lists of 5 to 6 items, 40 to 80 words each, in random A/B order. Rate the judge transparency card separately, after the portfolio ratings, so it cannot unblind them.
5. **Statistics.** Paired preference win rate with Bonett-Price adjusted Wald 95% intervals and an exact two-sided binomial test. Paired bootstrap 95% intervals (10,000 resamples) for the continuous rubric scores and for composite Vendi diversity.
6. **Ablation.** On 5 scenarios, run the full arm with and without the gut check to isolate what mid-run steering adds.
7. **Execution proxy.** On 3 scenarios, actually run the top pick's 48-hour test and record whether the idea survives.

## Scenarios

| # | Domain | Opening line | Hidden card (advantage / veto / droppable rule) |
| --- | --- | --- | --- |
| 1 | Developer tooling | "Our small engineering team hates code review delays, help me brainstorm fixes." | Senior devs enjoy 5-minute recorded walkthroughs / automated review bots feel insulting and noisy / pull requests must block synchronously |
| 2 | Solo business | "I run a niche B2B newsletter and want new ways to monetize without sponsors." | 400 readers are VPs who privately ask hiring questions / hates live cohorts and sales calls / it has to be a content-only product |
| 3 | Research design | "Help me generate novel experimental designs to test whether onboarding friction hurts retention." | Owns historical support transcripts with timestamped drop-offs / legal blocks dark-pattern tests on live checkout / it has to be a randomized live experiment |
| 4 | Personal workflow | "I read 30 technical papers a month and forget everything two weeks later." | 40-minute daily train commute where they record voice memos / quit spaced-repetition apps twice / reading is passive and solo |
| 5 | Community | "Our neighborhood tool library has high signups but almost nobody returns after visit one." | Retired machinist volunteers every Saturday morning / members are embarrassed to admit they cannot use the tools / it is a self-serve rental desk |
| 6 | Product onboarding | "Trial users sign up for our analytics SaaS, look around for 3 minutes, and churn." | Founders can query public industry datasets / buyers cannot connect production data without a security review / the user's own live data has to come first |
| 7 | Education | "How can I redesign my 2-hour corporate AI workshop so people actually change habits Monday?" | Attendees bring their own messy spreadsheets / employees fear looking incompetent in front of their manager / lecture plus generic prompt templates |
| 8 | Operations | "Our boutique dental clinic loses $8K a month to last-minute cancellations." | Directly above a busy coworking space / cancellation fees trigger one-star reviews / bookings must be made 24 hours ahead |
| 9 | Creative | "I want a fresh podcast or video format about urban architecture that isn't another talking-head interview." | Access to city archive maps and a phone with a depth scanner / only 4 hours a week to edit / weekly 45-minute studio episodes |
| 10 | Career | "I'm a mid-career data scientist trying to stand out in a flooded job market." | Deep fluency in hospital billing edge cases / very uncomfortable with self-promotional posts / resume plus cold applications |
| 11 | Physical product | "Redesign a home composting experience for small city apartments." | Partner runs a coffee roaster with weekly burlap deliveries / zero tolerance for fruit flies or counter clutter / decomposition happens in the apartment |
| 12 | Team rituals | "Our remote 12-person startup feels disconnected and retrospectives have gone stale." | Team spans 4 countries with strong food and music curiosity / mandatory "fun" video games cause eye-rolling / it has to be a live all-hands meeting |

The six briefs in `ab-test.md` also work as a smaller set: personal habit, product feature, community, research direction, small business and physical logistics.

## Rubric (each 1 to 5 unless noted)

1. **Tacit grounding and fit.** Do the ideas use the hidden advantage and respect the unspoken veto, or are they generic category advice?
2. **Mechanism originality.** Ignoring surface wording, how far do the top ideas move away from category clichés through distinct causal levers or a dropped rule?
3. **Structural non-redundancy.** Are the items different bets or cosmetic variants? Pair the human score with `diversity_audit.py --kernel composite` run identically on both portfolios: report VS1 divided by the portfolio size and the surface disguise ratio.
4. **Execution readiness.** Does the lead idea say what happens in the next ten seconds, name its load-bearing dependency, and give an honest test of 48 hours or less?
5. **Wildcard upside.** Is at least one non-obvious wildcard kept that stays inside the hard rules?
6. **Frame shift (0, 1 or 2).** Did at least one viable idea reframe the problem rather than optimize inside the opening premise?
7. **Would actually try.** How many items pass the rater's gut check for a real one-week trial?
8. **Hidden card surfaced (0 to 3).** How many hidden items the interview or gut check uncovered, and how many the portfolio used.
9. **Judge health and efficiency** (full arms only). Interview minutes, sub-agent calls, judge calls, order-swap flip rate, cycle rate and HodgeRank harmonic share, from the score report.

## Ship gates

The reports' bar for making the new version the default:

| Axis | Metric | Gate |
| --- | --- | --- |
| Human preference (primary) | blind paired win rate, 30 comparisons | at least 70% (21 of 30), two-sided p < 0.05, Bonett-Price lower bound above 50%, no regression on fit or execution readiness |
| Tacit context discovery | share of hidden-card items surfaced and used | +25 percentage points over the comparison arm |
| Mechanism diversity | portfolio VS1 / size, composite kernel | at least 0.80 (4.8 of 6) and surface disguise ratio below 1.5 |
| Wildcard preservation | runs with at least one hard-rule-valid Pareto wildcard | at least 90% |
| Judge observability and cost | flip rate, harmonic share, judge calls | flip rate at most 20%, harmonic share at most 15%, at least 70% fewer judge calls than both-order all pairs |
| Practical budget | interview length, report's cost estimate | interview at most 15 min (Standard) or 20 min (Deep), Deep at most about $1.10 API-equivalent on either host |

The cost line uses the first report's November 2026 rate card, which this repo has not verified. If the full version misses the preference gate but wins on diversity, check whether the extra machinery is costing fit. If it wins on fit and loses on would-try, the fit gate or the obvious-answer list may be too tight.
