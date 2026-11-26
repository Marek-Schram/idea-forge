# Harness adapters

The main session owns the interview, the frame checkpoint, the gut check, user-facing decisions and the run folder. Workers are isolated helpers that read one packet and write one file.

## Model routing

Divergent breadth comes mostly from process structure, not model size, while coherence, abduction and constraint checking still favor stronger models. So small models generate and the frontier model asks, frames and synthesizes.

| Role | Claude Code | Codex | Effort |
| --- | --- | --- | --- |
| Interview, frames, gut check, final synthesis | main session model (frontier, such as `opus`, in Deep, and `sonnet` is enough for Light and Standard per the report) | main session (`gpt-6.2-astra` in Deep, `gpt-6.2-sol` otherwise or on a tight Plus cap) | default |
| Deep extra wave-one pass (VS tail plus transformation) | main session | main session | default |
| Wave-one workers, taboo repair, spark and gap workers | `haiku` (`idea-worker`) | `gpt-6-luna` (`idea_worker`) | low |
| Wave-two scouts | `haiku` (`idea-scout`) | `gpt-6-luna` (`idea_scout`) | low |
| Card scrubbing, fit gate on a large pool | `haiku` | `gpt-6-luna` | low |
| Pairwise critic, Deep transformational synthesis | `sonnet` (`idea-critic`) | `gpt-6.2-sol` (`idea_critic`) | medium |

The Codex model names are the research report's, as of November 2026. Check them against your Codex version, and if the user names other models, use theirs. Select models explicitly when dispatching and keep these choices scoped to Idea Forge workers. If the host cannot select models, run every role on what is available and say so in the result.

## Agent definitions

Ready-made definitions live in this skill's `agents/` folder. Copy them into the project or user configuration once:

- **Claude Code:** copy `agents/claude/*.md` into `.claude/agents/`. Each file sets `model`, the allowed tools and a turn cap. `idea-worker` and `idea-critic` cannot run shell commands, search the web or spawn agents. `idea-scout` can search but cannot edit or spawn.
- **Codex:** copy `agents/codex/*.toml` into `.codex/agents/` and merge `agents/codex/config.toml.example` into `.codex/config.toml`. That file caps concurrency at five threads and registers each agent's `config_file` explicitly, because some Codex builds have been reported to ignore directory discovery and silently run children on the parent's model. Spawn children fresh (`fork_turns = "none"`), leave Fast mode off (it doubles quota burn), and check the resolved child models once with `/subagents` or `/status` before a Deep run.

The skill lives in `.agents/skills/idea-forge/`, which Codex discovers natively. `.claude/skills/idea-forge` is a symlink to it, so both hosts read one copy. Keep SKILL.md frontmatter to the portable fields and Codex extras in `agents/openai.yaml`.

## Worker packets

Follow the packet order in [divergent operators](divergent-operators.md): H and the schema first, the brief, the lens and one operator, the explored list or bans, then H and the schema again. Keep each packet under about 15K tokens, well clear of the price cliff some small models have above 100K input tokens. Workers keep reasoning effort low or medium, since output and thinking tokens cost several times more than input. Single-shot workers should finish in under five minutes and should never turn on long-lived prompt caching, since a cache written once and never reread only adds cost.

Choose lenses for the question at hand. Seek differences in what someone attends to, what they can influence and what failure costs them. A role is a way to pose questions. Treat claims about real people as hypotheses until you have an account or observation from them.

## Give each worker a distinct assignment

**Wave one.** Standard runs three workers (`vs_tail`, `t_uot`, `c_uot_analogy`), six seeds each. Deep runs five (adds `sit_asset` and `brainwriting_ddd`), five or six seeds each, and the main session adds its own VS tail and transformational pass. Each worker writes `02_wave1/<worker>.json` and returns a two-line summary, never its cards in chat. Keep the obvious-answer list in the coordinator. Keep peers' outputs and the coordinator's examples out of every packet.

**Wave two.** Decide assignments from the audit, the gut check and the gaps. Standard: one scout on the top two gaps and one taboo-repair or mutation worker. Deep: three scout or repair workers and one `sonnet` transformational synthesis worker that rebuilds promising seeds under a dropped R. Spark and gap workers get the explored-mechanism list. Repair workers get their one or two banned pathways and the equivalence check. Scouts run at most two targeted queries per gap and write evidence cards of 200 words or fewer to `05_evidence/`: what the source supports, what it leaves open, where the analogy breaks and which card should change. They never return raw page text. Outside sources get only what a general search needs. Keep personal episodes and private repo text in the session.

**Fit gate.** The coordinator runs it, since it holds the checklist and the obvious-answer list. With a large pool, a `haiku` worker can do it, given the checklist, H, the obvious-answer list and the cards.

**Critic.** Receives H, the fit checklist, the user's baseline and the blind cards for its batch only, never worker ids or operator names. It writes its verdicts to disk and returns only the file path and the pair count.

Example lenses for a broken daily routine. Pick others whenever they expose more useful differences.

| Lens | Free-generation question | Possible evidence after wave one |
| --- | --- | --- |
| Engineer responsible for reliability | Where can the system record completion while the intended outcome still fails? | Trace the actual completion event and next state in the repo. |
| Artist designing a participatory experience | What would make the person want to perform the next action even if nobody prompted it? | Examine a documented interaction in which participants voluntarily continued. |
| Parent navigating an interrupted morning | Which part of the routine could survive an interruption and still be easy to rejoin? | Examine a first-person account of a comparable routine. |

## Cross-family option

When the user has both CLIs set up and opts in, route one wave-one worker or the critic to the other model family (`codex exec` from Claude Code, or `claude -p` from Codex). Different families have different blind spots, and a cross-family critic removes self-preference. Only do this when the user asks, since it spends a second subscription.

## Context hygiene

Long, on-topic context degrades every model, and noisy web text is the worst. Write, select, compress and isolate: every stage goes to disk, scouts distill, and the main session reads only summaries. In a single-harness session, compact between wave two and judging (the run folder holds the exact state), aiming to keep the live orchestrator context under about 30K tokens.

## Unattended runs

When nobody can answer (a batch, a scheduled run, or the user said to run it overnight), skip the frame checkpoint and gut check. Pick Frame A unless the brief says otherwise, record the choice and every other stand-in assumption in `01_brief.json`, and list them at the top of the result so the user can redirect. Still write the fit checklist from what the user has said anywhere in the conversation or project notes, mark any veto you had to guess, and run the fit gate. Unattended runs are where bad-fit ideas slip through most, since nobody vetoes titles.

## Run on either host

- **Claude Code.** If available and permitted, dispatch the named agents (or general-purpose agents with the model set per the table) through the Agent tool in one parallel batch per wave. Keep the interview in the parent session.
- **Codex.** If delegation is available and permitted, spawn the registered agents with self-contained packets and fresh contexts. Gather the independent first passes before distributing evidence.
- **Fallback.** Where independent workers are unavailable, run the same distinct assignments as separate passes in the main session and describe the execution accurately. Light uses this path by design. If Python is unavailable, group candidates by hand, compare finalists directly and say the diagnostics were skipped.
