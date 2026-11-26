---
name: idea-forge
description: Interview the user, generate ideas that work or feel different from familiar options, and stress-test them. Use for open-ended brainstorming, feature discovery, research directions, or a request to get beyond familiar solutions. Skip when the user has chosen a direction and wants only implementation or critique.
license: MIT
metadata:
  version: "1.2.1"
---

# Idea Forge

Help the user discover an option they would actually try. Use the interview to learn what familiar answers miss. Keep the user's choice of direction open.

## 1. Interview and agree on the brief

In both modes, read the conversation and directly relevant repo context first. Ask one question per turn and wait. Choose the question whose answer could most change what you explore. Follow an unexpected detail. Use these probes selectively:

- **Outcome and episode.** What would change for whom? Reconstruct a recent instance. Locate the moment the outcome became more or less likely, what the person did next, and what they cared about at the time.
- **Current attempts and possible causes.** Find what already works, the workaround, its cost, and where it breaks down. If several explanations fit, ask about an exception or two otherwise similar episodes with different outcomes. Keep plausible causes open when the user cannot distinguish them. Avoid repeated abstract “why” questions.
- **Success and trade-offs.** What observable difference would make this worth using? Over what period? What would spoil a superficially successful outcome? Identify hard constraints, negotiable constraints and strengths worth keeping.
- **Comparison and sources.** Learn which familiar approach the user would pass on and why. Let them keep their own best idea private for a later comparison. Invite a relevant artifact, practitioner account or comparator if they have one. Otherwise propose sources that could resolve the remaining uncertainties. Save external precedent research for after free generation.

**Calibrate novelty for each brief.** Ask what should feel new to this user: how it works, the experience of using it, both, or another dimension they name. If they have already specified this, reflect it in the confirmation. Establish the comparison point (their own attempts, familiar products, or the field). Preserve “either counts” as a valid answer.

Then show the three settings in a single compact chooser. Recommend one with a reason tied to this brief; let the user choose by name or plain language. They can turn it up or down later.

| Setting | What to explore |
| --- | --- |
| Close to familiar | Keep the core approach. Find a concrete improvement on the chosen dimension, within existing resources. |
| A stretch | Change an important part of the mechanism or experience. Explain the departure and offer a plausible first test. |
| A wild card | Challenge a premise about how the goal must be achieved. Speculative dependencies are welcome when named. Keep the user's success condition and hard constraints. |

Summarize the event, desired change, what has failed, any unresolved cause, and the chosen novelty target. Include the planned comparison if it matters. The chooser and brief can share a confirmation turn: accepting the recommended setting can also confirm the brief. Honor a correction before generating. Quick and Deep control effort independently of novelty.

## 2. Generate in two waves

Quick is the default, with short passes in the main session. Use Deep for requested or substantial exploration. Read [divergent operators](references/divergent-operators.md); for Deep, also read [harness adapters](references/harness-adapters.md).

**Free generation.** Use the confirmed brief and known facts. Give each Deep worker a different lens and a different question about the user's situation. In Quick, try a few contrasting lenses as separate passes. Explore before looking up examples, sharing sketches or ranking ideas. The coordinator keeps an obvious-answer list for later comparison.

**Research and mutation.** Group the first sketches by what would change for the user. Preserve genuinely different experiences even when they share machinery. In Deep, the optional diversity helper flags repeated labels for review. Identify a gap or fragile premise. Assign complementary sources and seek evidence that could alter an idea. Record what each source actually shows, where the analogy breaks, and which candidate changed as a result. If access is missing, label the unresolved claim. Generate alternatives for uncovered ground and revise at least one promising seed if the evidence warrants it. Aim for six to eight mutations in a deep run when the brief supports that breadth.

## 3. Stress-test and refine

Use the [critique rubric](references/adversarial-critique.md). Compare both waves against the user's baseline. For each finalist, describe its specific departure on their chosen dimension and judge its feasibility separately. Give preference to ideas that fit the selected setting and success condition. Check earlier suggestions the user passed over. If a stretch or wild-card shortlist leans on the same vivid detail, try one alternative that still works without it. Keep the shared detail only if the departures on the chosen dimension are genuinely different. If every candidate is too familiar, reopen generation around the repeated premise before presenting. In Deep, use an independent critic when available and compare close finalists in pairs.

**Both modes — check shared assumptions.** For each finalist, finish “This works only if …” with the behavior or condition its result depends on. Compare the answers across the shortlist. If several ideas depend on the same doubtful assumption, generate a replacement that can succeed when it is false. Discard any idea that still requires a behavior the user has ruled out for this situation. Shared conditions the user has confirmed can stay.

**Deep Mode — show the next ten seconds.** For each finalist, start at the moment the user says things usually go wrong. Show what the person does next, what the idea changes at that point, and why the outcome could differ. For slower processes, walk through the next consequential decision. If the walkthrough breaks, revise or drop the idea before presenting. Include the surviving scene in the concept sketch and distinguish a predicted action from an observed one.

For a promising idea with a consequential weakness, revise the part that would fail and check whether it still delivers what made it interesting. State the smallest observation that would distinguish the mechanism from its strongest rival. If the user later brings a trial result, start at the first point where prediction and observation diverged. Revise, keep or drop the idea accordingly.

## 4. Return a portfolio and invite selection

Honor the requested count. Otherwise return a short set in Quick or about five to seven distinct candidates in Deep. In each 40–80 word sketch, convey what happens, what makes it different from the named baseline, and what could fail. Order by fit to the user's chosen novelty target; explain any particularly speculative dependency. Mark field-wide novelty as unverified unless a scoped precedent check supports a narrower claim.

In Deep, briefly identify discarded clichés and an unexplored direction. Invite the user to choose a concept or adjust the setting or dimension. On a change, keep the confirmed context, regenerate or revise, and show the difference. Give a recommendation when asked. After selection, save the brief, chosen mechanism, assumptions and next test to docs/ideation/YYYY-MM-DD-<topic>.md when working in a writable project where the user wants the record. Preserve existing notes.
