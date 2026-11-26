# Idea Forge A/B check: 2.0 vs 1.2.1

A small blind test you can run yourself in an afternoon. It checks the two problems 2.0 is meant to fix: ideas that are the same few mechanisms in different words, and ideas that don't fit the situation.

Six briefs is a smoke test, not proof. The Gemini report's own power math says you need about 30 paired ratings to call a 70% win rate real. That only matters if you plan to publish a claim, so start here.

## Setup

1. Keep two copies of the skill: 1.2.1 from `main` and 2.0 from the `claude/idea-forge-v2` branch.
2. For each brief, open a fresh session per version, same model, Quick mode (the default).
3. Someone plays the user. You, a friend, or a separate Claude session given only the brief and its hidden card. A human is better, since a model playing the user tends to volunteer the hidden card too easily.
4. The player answers questions honestly but reveals a hidden card item only when a question points at it. Never volunteer one.

## Briefs

Each brief has an opening line and a hidden card with three items: an unfair advantage, a veto, and an assumed rule that could be dropped.

| # | Opening line | Advantage | Veto | Droppable rule |
| --- | --- | --- | --- | --- |
| 1 | "I scroll my phone in bed for an hour every night and want to stop." | Partner goes to bed earlier and is happy to help. | Won't use anything that fully locks the phone: needs the alarm and on-call texts. | The fix has to live on the phone. |
| 2 | "Trial users of my budgeting app sign up and are gone in a day." | About 300 users came from one subreddit where they're a known poster. | No paid ads, and no email drip that feels spammy. | Onboarding happens inside the app. |
| 3 | "Our campus club gets 40 people at the first meeting and 8 by October." | The club has a free room with a projector and a kitchen. | Officers refuse mandatory attendance or points systems. | Meetings are the main event. |
| 4 | "I need a fresh angle on predicting customer churn for a class project." | Has anonymized check-in logs from a local gym. | Two weeks, no paid compute. | The target has to be "who churns". |
| 5 | "My friend's lawn care side business needs more clients with zero marketing budget." | Already mows 12 lawns on one street. | Hates door-knocking and cold calls. | Sell per mow. |
| 6 | "Our apartment kitchen is chaos when three roommates cook at 6pm." | One roommate works from home and is around at 4pm. | No chore charts, they all ignored the last one. | Everyone cooks their own dinner. |

## Blind rating

After both runs of a brief, copy each final list into a plain numbered list. Strip version numbers, judge cards and file paths, and trim sketches to about the same length. Flip a coin for which one is A. Then rate each list without knowing which is which:

- **Fit (1 to 5):** do the ideas use the hidden advantage and respect the veto, or could they be handed to anyone with this problem?
- **Bad-fit count:** how many ideas break the veto or a stated hard rule.
- **Would try:** how many you'd actually try for a week.
- **Card surfaced (0 to 3):** how many hidden card items the interview uncovered.
- **Distinct ideas:** put each list into the card format and run `python3 scripts/diversity_audit.py` from the 2.0 skill folder on both. Compare `effective_distinct_ideas` divided by the number of ideas.
- **Preference:** which list you'd rather have, A or B.

## Reading the result

2.0 earns the switch if it wins preference on at least 5 of 6 briefs, has zero bad-fit ideas across all six, and does no worse on would-try. If it wins on distinct ideas but loses on fit, the fit gate is too loose. If it wins on fit but the lists feel safe, the gate is too tight or the obvious-answer list is too broad.

Optional: rerun 2.0 on three briefs with the gut check skipped. If those lists are as good, the gut check isn't earning its extra turn for you.
