---
name: idea-forge
description: Interview the user, generate ideas that work in different ways, and stress-test the options. Use for open-ended brainstorming, feature discovery, research directions, or a request to get beyond familiar solutions. Skip when the user has chosen a direction and wants only implementation or critique.
license: MIT
metadata:
  version: "1.0.0"
---

# Idea Forge

Help the user discover options they would consider trying. Start with their experience, explore alternatives before ranking them, and preserve their say in what moves forward.

## 1. Interview and agree on the brief

Read the conversation and any directly relevant project context first. In a repository, check applicable instructions and look for the existing feature, design notes, or constraints. Use what you find to ask a better question.

Interview before generating in both Quick and Deep modes. Ask one short question per turn and wait. Follow the answer. For a vague request, invite the user to walk through a real episode, then locate the moment they wish had gone differently. If they are unsure why, ask about a time it went well. Distinguish what already works from the gap. Clarify the kind of idea they want, what would count as success, and any consequential trade-off, constraint, or anti-goal. Avoid leading them toward a feature or insisting they already know the answer.

Stop asking when you can describe the situation and distinguish a useful idea from an obvious miss. Summarize the brief in the user's language and ask whether to use it. A sufficiently detailed initial request can go straight to this confirmation. A correction updates the brief. An explicit invitation to generate against the agreed framing opens the next phase. Carry that brief forward across turns.

## 2. Generate in two waves

Quick is the default. Run both waves as short passes in the current conversation. Deep is for requested or substantial exploration. For independent workers, use [harness adapters](references/harness-adapters.md).

Use the [divergent operators](references/divergent-operators.md). In wave one, vary how the proposed change would produce the desired outcome. Use a few complementary operators in Quick or cover all four pathways in Deep. Defer ranking. Keep a coordinator-side list of obvious answers and things the user already tried so independent workers can start from the episode itself.

After wave one, describe each candidate's mechanism in plain language. Group ideas that depend on the same causal change, even when their names differ. In Deep, the optional diversity helper flags repeated mechanism labels and wording for review. In wave two, explore an uncovered dimension and push a promising mechanism one step further. Bring in one or two uncommon analogies when stuck. For a deep run aim for six to eight mutations when the brief supports that breadth. If claiming novelty in a field matters, check the nearest precedents and describe the specific difference.

## 3. Stress-test and prune

Use the [critique rubric](references/adversarial-critique.md). Pool both waves first. Remove duplicates and solutions the user already has. Test remaining ideas against the confirmed brief and record a specific reason for pruning. Let a promising idea survive with a clearly identified uncertainty. In Deep, use an independent critic when available and compare closely matched finalists in pairs. In Quick, make a separate critique pass. Scope and code come after selection when requested.

## 4. Return a portfolio and invite selection

Honor the requested count. Otherwise show a short set in Quick or about five to seven in Deep if enough distinct candidates survive. Give each a concrete 40–80 word sketch explaining what happens, why it could help, and where it could fail. When useful, give the smallest observable test of the riskiest assumption. Combine related ideas only when the combination changes what the user can do.

In Deep, briefly identify discarded clichés and a worthwhile unexplored direction. Invite the user to choose a direction, challenge a constraint, or ask for another wave. Give a recommendation if asked and explain the trade-off. After selection, save the confirmed brief, chosen mechanism, assumptions and next test to docs/ideation/YYYY-MM-DD-<topic>.md when working in a writable project where the user wants the record. Keep it in chat otherwise. Preserve existing notes.
