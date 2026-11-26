# Deep-mode dispatch

The main session owns the interview, user-facing decisions and any files. Choose lenses for the question at hand. Seek differences in what someone attends to, what they can influence and what failure costs them. Professions, crafts, responsibilities and lived situations can all suggest a lens. A role is a way to pose questions. Treat claims about real people as hypotheses until you have an account or observation from them.

## Give each worker a distinct assignment

Share the confirmed brief, baseline, hard constraints, novelty dimension and setting. For wave one, give each worker a perspective, a question only that perspective is being asked, and a divergent operator. Keep peers' outputs and the coordinator's examples out of its context. Ask for a sketch and the assumption it depends on.

For wave two, match a different source or body of evidence to each assignment. Relevant choices include a direct user account, a repo behavior trace, original research, a failed intervention, an analogous practice, and a close competing solution. Decide the assignments from the gaps in wave one. For each, ask what the source supports, what it leaves open, and what to change in the sketch. Cite the artifact or source actually inspected. Outside sources get only the information necessary for a general search; keep personal episodes and private repo text in the session.

For example, these are possible lenses for a broken daily routine. Select others whenever they expose more useful differences.

| Lens | Free-generation question | Possible evidence after wave one |
| --- | --- | --- |
| Engineer responsible for reliability | Where can the system record completion while the intended outcome still fails? | Trace the actual completion event and next state in the repo. |
| Artist designing a participatory experience | What would make the person want to perform the next action even if nobody prompted it? | Examine a documented interaction in which participants voluntarily continued. Identify the transferable choice. |
| Parent navigating an interrupted morning | Which part of the routine could survive an interruption and still be easy to rejoin? | Examine a first-person account of a comparable routine. Identify a workaround and its cost. |

Give a fresh worker a missing dimension to explore or one specific seed to revise. The critic receives the brief and anonymized candidates after generation. A worker can dispute a shared assumption by naming an observation that would resolve it.

## Run on either host

Use a lower-cost model for every delegated role, including research, refinement and critique. Select it explicitly when dispatching. In Codex prefer `gpt-6.2-sol`. In Claude Code prefer `sonnet` for delegated work. Use `haiku` if Sonnet is unavailable or the user requests a lower-cost run. Use another available lower-cost worker if needed. When the host cannot select a lower-cost worker and none is known to be configured, use the in-session fallback below. Keep these choices scoped to Idea Forge workers.

- **Codex.** If delegation is available and permitted, use the host's subagent tool with self-contained prompts and fresh contexts where supported. Gather the independent first passes before distributing evidence.
- **Claude Code.** If available and permitted, dispatch general-purpose workers through the Agent tool in a parallel batch. Keep the interview in the parent session.
- **Fallback.** Where independent workers are unavailable, use the same distinct assignments as separate passes in the main session. Describe the execution accurately. Quick uses this path by design. If Python is unavailable, group candidates and compare finalists directly.
