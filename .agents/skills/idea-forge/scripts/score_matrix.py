"""Summarize per-criterion pairwise judgments into scores, a portfolio and a judge card.

Every unordered pair needs one primary judgment ("votes" names the winner per
criterion, or "tie"). Optional swap audits repeat a pair with the cards shown
in the other order and "swapped": true. When the two orders disagree on a
criterion, that verdict becomes a tie and counts as a flip.

Optional keys:
  niches             {id: "close" | "stretch" | "wildcard"} for portfolio slots
  portfolio_size     how many to recommend (default min(5, number of ids))
  novelty_criterion  criterion name whose top candidate is always kept
  words              {id: word count of its judged card} for a length-bias check

Scores describe the stated preferences and the judge's votes. The rank range
shows sensitivity to +/-10% weight moves. Neither is statistical uncertainty.
"""
import argparse
from itertools import combinations
import json
from math import isfinite, sqrt
from pathlib import Path

NICHE_ORDER = ("close", "stretch", "wildcard")


def check_inputs(data):
    if not isinstance(data, dict):
        raise ValueError("expected an object with ids, weights and pairs")
    ids, weights, pairs = (data.get(k) for k in ("ids", "weights", "pairs"))
    if not isinstance(ids, list) or len(ids) < 2 or any(
        not isinstance(i, str) or not i.strip() or i == "tie" for i in ids
    ) or len(set(ids)) != len(ids):
        raise ValueError("supply at least two distinct text ids, excluding 'tie'")
    if not isinstance(weights, dict) or not weights or any(
        type(w) not in (float, int) or not isfinite(w) or w <= 0 for w in weights.values()
    ):
        raise ValueError("criterion weights must be finite positive numbers")
    if not isinstance(pairs, list):
        raise ValueError("pairs must be a list")
    return ids, weights, pairs


def collect_votes(ids, weights, pairs):
    """Return {pair: {criterion: vote}} after merging swap audits, plus flip stats."""
    primary, audits = {}, {}
    for pair in pairs:
        if not isinstance(pair, dict):
            raise ValueError("each pair must be an object")
        a, b, votes = (pair.get(k) for k in ("a", "b", "votes"))
        if a not in ids or b not in ids or a == b:
            raise ValueError(f"unknown or invalid pair: {a}, {b}")
        if not isinstance(votes, dict) or votes.keys() != weights.keys():
            raise ValueError(f"pair {a}, {b} needs one vote per criterion")
        for criterion, vote in votes.items():
            if vote not in (a, b, "tie"):
                raise ValueError(f"invalid {criterion} vote for {a} versus {b}")
        key = frozenset((a, b))
        target = audits if pair.get("swapped") is True else primary
        if key in target:
            raise ValueError(f"duplicate {'swap audit' if target is audits else 'judgment'}: {a}, {b}")
        target[key] = dict(votes)
    missing = {frozenset(p) for p in combinations(ids, 2)} - primary.keys()
    if missing:
        raise ValueError(f"missing {len(missing)} pair(s), e.g. {sorted(next(iter(missing)))}")
    orphan = audits.keys() - primary.keys()
    if orphan:
        raise ValueError("swap audit without a primary judgment")
    flips, checked, flipped_pairs = 0, 0, []
    for key, votes in audits.items():
        for criterion, vote in votes.items():
            checked += 1
            if vote != primary[key][criterion]:
                flips += 1
                primary[key][criterion] = "tie"
                flipped_pairs.append(f"{'/'.join(sorted(key))} on {criterion}")
    return primary, {"audited_pairs": len(audits), "checked": checked, "flips": flips, "flipped": flipped_pairs}


def pearson(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sx = sqrt(sum((x - mx) ** 2 for x in xs))
    sy = sqrt(sum((y - my) ** 2 for y in ys))
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sx * sy) if sx and sy else 0.0


def summarize(data):
    ids, weights, pairs = check_inputs(data)
    votes, flip_stats = collect_votes(ids, weights, pairs)

    points = {i: dict.fromkeys(weights, 0.0) for i in ids}
    for key, pair_votes in votes.items():
        a, b = sorted(key)
        for criterion, vote in pair_votes.items():
            if vote == "tie":
                points[a][criterion] += 0.5
                points[b][criterion] += 0.5
            else:
                points[vote][criterion] += 1

    def scores(w):
        denominator = sum(w.values()) * (len(ids) - 1)
        return {i: round(sum(points[i][c] * w[c] for c in w) / denominator, 12) for i in ids}

    base = scores(weights)
    scenarios = [base]
    for c in weights:
        for factor in (0.9, 1.1):
            scenarios.append(scores({**weights, c: weights[c] * factor}))
    order = sorted(ids, key=lambda i: (-base[i], i))

    def clean(i):
        return i.replace("|", "\\|").replace("\n", " ")

    criteria = list(weights)
    lines = ["| Candidate | Weighted score | Rank range | " + " | ".join(criteria) + " |",
             "|---|---:|---:|" + "---:|" * len(criteria)]
    for i in order:
        ranks = [1 + sum(other > s[i] for other in s.values()) for s in scenarios]
        per = " | ".join(f"{points[i][c]:g}" for c in criteria)
        lines.append(f"| {clean(i)} | {base[i]:.3f} | {min(ranks)}–{max(ranks)} | {per} |")

    # Pareto front on per-criterion points: nobody else is at least as good everywhere and better somewhere.
    front = [
        i for i in order
        if not any(
            all(points[j][c] >= points[i][c] for c in criteria) and any(points[j][c] > points[i][c] for c in criteria)
            for j in ids if j != i
        )
    ]
    lines += ["", "Pareto front (no candidate beats these on every criterion): " + ", ".join(map(clean, front))]

    # Portfolio: best per niche first, then protect the top novelty pick, then fill by score.
    niches = data.get("niches") or {}
    if not isinstance(niches, dict) or any(v not in NICHE_ORDER for v in niches.values()) or not set(niches) <= set(ids):
        raise ValueError("niches must map known ids to close, stretch or wildcard")
    size = data.get("portfolio_size", min(5, len(ids)))
    if type(size) is not int or not 1 <= size <= len(ids):
        raise ValueError("portfolio_size must be a whole number between 1 and the number of ids")
    novelty = data.get("novelty_criterion")
    if novelty is not None and novelty not in weights:
        raise ValueError("novelty_criterion must name one of the weighted criteria")

    picks, reasons = [], {}
    for niche in NICHE_ORDER:
        members = [i for i in order if niches.get(i) == niche]
        if members and len(picks) < size:
            picks.append(members[0])
            reasons[members[0]] = f"best {niche}"
    if novelty:
        top_novel = max(order, key=lambda i: (points[i][novelty], base[i]))
        if top_novel not in picks:
            if len(picks) >= size:
                picks.pop()
            picks.append(top_novel)
            reasons[top_novel] = f"top on {novelty}"
    for i in order:
        if len(picks) >= size:
            break
        if i not in picks:
            picks.append(i)
            reasons[i] = "next best score"
    lines += ["", f"Suggested portfolio ({len(picks)}):"]
    lines += [f"- {clean(i)} ({reasons[i]}, score {base[i]:.3f})" for i in picks]

    # Judge card.
    lines += ["", "Judge card:"]
    if flip_stats["audited_pairs"]:
        rate = flip_stats["flips"] / flip_stats["checked"]
        lines.append(
            f"- Order swaps: {flip_stats['audited_pairs']} pair(s) re-judged in reverse, "
            f"{flip_stats['flips']} of {flip_stats['checked']} verdicts flipped ({rate:.0%}) and were counted as ties."
        )
        if flip_stats["flipped"]:
            lines.append("- Flipped: " + "; ".join(flip_stats["flipped"]))
        if rate > 0.25:
            lines.append("- High flip rate: treat close scores as ties and lean on the written evidence lines.")
    else:
        lines.append("- No order-swap audit was run, so position bias is unmeasured.")
    words = data.get("words")
    if isinstance(words, dict) and set(words) >= set(ids) and len(ids) >= 4:
        if any(type(words[i]) not in (int, float) for i in ids):
            raise ValueError("words must be numbers")
        r = pearson([words[i] for i in ids], [base[i] for i in ids])
        flag = " Longer cards are winning: re-trim cards to the same length." if r > 0.5 else ""
        lines.append(f"- Card length vs score correlation: {r:+.2f}.{flag}")
    kept = [i for i in picks if i not in order[:size]]
    if kept:
        lines.append(
            "- Kept for balance, though below the weighted-score cut: "
            + ", ".join(f"{clean(i)} ({reasons[i]})" for i in kept)
        )
    top = [i for i in order if base[i] == base[order[0]]]
    if len(top) > 1:
        lines.append("- Tied at the top: " + ", ".join(map(clean, top)) + ". The judge did not separate them.")
    lines += ["", "Decision: left to the user."]
    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("comparisons", type=Path)
    args = parser.parse_args()
    try:
        print(summarize(json.loads(args.comparisons.read_text())))
    except (OSError, ValueError) as error:
        parser.exit(2, f"{error}\n")
