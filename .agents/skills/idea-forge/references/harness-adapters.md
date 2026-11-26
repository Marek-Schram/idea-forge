# Deep-mode dispatch

The main session owns the interview, the frame checkpoint, the gut check, user-facing decisions and any files. Choose vantage points for the question at hand. Seek differences in what someone attends to, what they can influence and what failure costs them. Make each one specific to this brief ("a night-shift nurse who cannot count on anyone reading instructions", not "a nurse"), since a generic job title pulls the worker back toward the typical answer. A worker may also write its own vantage point from the brief before it starts. A role is a way to pose questions. Treat claims about real people as hypotheses until you have an account or observation from them.

## Give each worker a distinct assignment

**Wave one.** Share the confirmed brief, picked frame, fit checklist, H and R lists, baseline, novelty dimension and setting. Give each worker a vantage point, a question only that vantage point is being asked, and one operator. Keep the obvious-answer list in the coordinator. Keep peers' outputs and the coordinator's examples out of its context. Ask for titles first, then cards (see divergent operators).

**Wave two.** Decide assignments from the audit, the gut check and the gaps in wave one: develop a spark, run a taboo repair, cover a missing angle, or test a fragile premise against evidence. Spark and gap-filling workers get the explored-mechanism list. Repair workers get their one or two banned mechanisms. Relevant sources include a direct user account, a repo behavior trace, original research, a failed intervention, an analogous practice, and a close competing solution. For each, ask what the source supports, what it leaves open, and what to change in the card. Cite the artifact or source actually inspected. Outside sources get only what a general search needs. Keep personal episodes and private repo text in the session.

**Fit gate.** The coordinator runs it, since it holds the checklist and the obvious-answer list. In Deep, a sonnet worker can do it instead when the pool is large, given the checklist, the obvious-answer list and the cards.

**Critic and judge.** The judge receives the brief, the fit checklist, the user's baseline and the blind cards only, never worker ids or operator names.

For example, these are possible vantage points for a broken daily routine. Select others whenever they expose more useful differences.

| Vantage point | Free-generation question | Possible evidence after wave one |
| --- | --- | --- |
| Engineer responsible for reliability | Where can the system record completion while the intended outcome still fails? | Trace the actual completion event and next state in the repo. |
| Artist designing a participatory experience | What would make the person want to perform the next action even if nobody prompted it? | Examine a documented interaction in which participants voluntarily continued. |
| Parent navigating an interrupted morning | Which part of the routine could survive an interruption and still be easy to rejoin? | Examine a first-person account of a comparable routine. |

## Models

Bigger models do not clearly beat smaller ones at raw divergent thinking, so spend the expensive model where reasoning matters.

- **Wave-one generators:** a lower-cost model. In Claude Code use `sonnet`. Use `haiku` when the user asks for a cheaper run, since raw idea generation loses little on a smaller model.
- **Evidence work, taboo repair, critic and judge:** a mid-tier model. In Claude Code use `sonnet`, falling back to `haiku` if Sonnet is unavailable.
- **Interview, frames, final synthesis:** the main session's model.
- **Codex:** prefer `gpt-6.2-sol` for delegated roles unless the user names another.

Select models explicitly when dispatching and keep these choices scoped to Idea Forge workers. If the host cannot select models, run every role on what is available and say so.

## State folder

Write each stage to disk so the chat stays short and a compacted or resumed session can pick up where it left off. Use `.idea-forge/YYYY-MM-DD-<topic>/` in the working directory, or the working folder the host already provides for the task.

    brief.md          frames, picked frame, fit checklist, H and R lists, obvious-answer list, novelty setting, assumptions
    wave1/<worker>.json   titles and cards per worker
    gut-check.md      sparks, vetoes, missing angles (or what was assumed)
    pool.json         all cards with normalized labels and fit verdicts (pass, repaired, cut + reason)
    audit.json        diversity_audit.py output
    wave2/<task>.json repair, spark and evidence cards
    cards.md          blind finalist cards
    comparisons.json  pairwise judgments and swap audits
    result.md         portfolio, judge card, clichés, unexplored direction

Workers write only their own files. Before resuming a run, read `brief.md` and the newest stage file instead of relying on chat history. Do not commit the folder unless the user asks.

## Unattended runs

When nobody can answer (a batch, a scheduled run, or the user said to run it overnight), skip the frame checkpoint and gut check. Pick Frame A unless the brief says otherwise, record the choice and every other stand-in assumption in `brief.md`, and list them at the top of the result so the user can redirect. Still write the fit checklist from what the user has said anywhere in the conversation or project notes, mark any veto you had to guess, and run the fit gate. Unattended runs are where bad-fit ideas slip through most, since nobody vetoes titles.

## Run on either host

- **Claude Code.** If available and permitted, dispatch general-purpose workers through the Agent tool in one parallel batch with the model set per role above. Keep the interview in the parent session.
- **Codex.** If delegation is available and permitted, use the host's subagent tool with self-contained prompts and fresh contexts. Gather the independent first passes before distributing evidence.
- **Fallback.** Where independent workers are unavailable, run the same distinct assignments as separate passes in the main session and describe the execution accurately. Quick uses this path by design. If Python is unavailable, group candidates and compare finalists directly.
