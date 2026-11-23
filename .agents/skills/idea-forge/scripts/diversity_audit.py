"""Inspect mechanism coverage and lexical overlap in a candidate pool."""
import argparse
from collections import Counter
from itertools import combinations
import json
from pathlib import Path
import re


def audit(rows):
    if not isinstance(rows, list) or not rows:
        raise ValueError("expected a nonempty list of candidates")
    counts = Counter()
    tokens = {}
    for row in rows:
        if not isinstance(row, dict) or any(
            not isinstance(row.get(k), str) or not row[k].strip()
            for k in ("id", "mechanism", "sketch")
        ):
            raise ValueError("each candidate needs a text id, mechanism and sketch")
        key = row["id"].strip()
        if key in tokens:
            raise ValueError(f"duplicate candidate id {key}")
        counts[" ".join(row["mechanism"].casefold().split())] += 1
        tokens[key] = set(re.findall(r"\w+", row["sketch"].casefold()))
    similar = []
    for a, b in combinations(tokens, 2):
        vocabulary = tokens[a] | tokens[b]
        overlap = len(tokens[a] & tokens[b]) / len(vocabulary) if vocabulary else 0
        if overlap >= 0.6:
            similar.append({"a": a, "b": b, "word_overlap": round(overlap, 3)})
    return {
        "mechanism_counts": dict(counts),
        "over_40_percent": [k for k, n in counts.items() if n / len(rows) > 0.4],
        "similar_wording": similar,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pool", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(audit(json.loads(args.pool.read_text())), indent=2))
    except (OSError, ValueError) as error:
        parser.exit(2, f"{error}\n")
