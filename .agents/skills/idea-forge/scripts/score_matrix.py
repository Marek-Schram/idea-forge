"""Summarize complete pairwise judgments and one-at-a-time weight sensitivity."""
import argparse
from itertools import combinations
import json
from math import isfinite
from pathlib import Path


def summarize(data):
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

    remaining = {frozenset(pair) for pair in combinations(ids, 2)}
    points = {i: dict.fromkeys(weights, 0) for i in ids}
    for pair in pairs:
        if not isinstance(pair, dict):
            raise ValueError("each pair must be an object")
        a, b, votes = (pair.get(k) for k in ("a", "b", "votes"))
        if a not in ids or b not in ids or frozenset((a, b)) not in remaining:
            raise ValueError(f"unknown, duplicate or invalid pair: {a}, {b}")
        remaining.remove(frozenset((a, b)))
        if not isinstance(votes, dict) or votes.keys() != weights.keys():
            raise ValueError("each pair needs one vote per criterion")
        for criterion, vote in votes.items():
            if vote == "tie":
                points[a][criterion] += 0.5
                points[b][criterion] += 0.5
            elif vote in (a, b):
                points[vote][criterion] += 1
            else:
                raise ValueError(f"invalid vote for {a} versus {b}")
    if remaining:
        raise ValueError(f"missing {len(remaining)} pair(s)")

    def scores(w):
        denominator = sum(w.values()) * (len(ids) - 1)
        return {i: round(sum(points[i][c] * w[c] for c in w) / denominator, 12) for i in ids}

    base = scores(weights)
    scenarios = [base]
    for c in weights:
        for factor in (0.9, 1.1):
            scenarios.append(scores({**weights, c: weights[c] * factor}))
    lines = ["| Candidate | Weighted score | Rank range |", "|---|---:|---:|"]
    for i in sorted(ids, key=base.get, reverse=True):
        ranks = [1 + sum(other > s[i] for other in s.values()) for s in scenarios]
        label = i.replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {label} | {base[i]:.3f} | {min(ranks)}–{max(ranks)} |")
    return "\n".join([*lines, "", "Selected winner: "]) 


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("comparisons", type=Path)
    args = parser.parse_args()
    try:
        print(summarize(json.loads(args.comparisons.read_text())))
    except (OSError, ValueError) as error:
        parser.exit(2, f"{error}\n")
