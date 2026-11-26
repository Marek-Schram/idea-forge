"""Audit how many genuinely different mechanisms a candidate pool holds.

Compares candidates on structured fields (mechanism label, causal mechanism,
what the idea depends on, what changes for the user), not just shared wording.
Reports a Vendi score (the effective number of distinct ideas), clusters of
near-duplicates, shared assumptions, how much more varied the sketches look
than the mechanisms are, each candidate's unique contribution, and up to two
mechanism-taboo targets for a repair wave.

Input: a JSON list of candidates. Required keys: id, mechanism, sketch.
Optional keys: title, how (the causal path in one line), depends_on (the
"works only if" assumption), changes (what changes for the user),
grounded_in (the detail of the user's situation the idea relies on).

Stdlib only. The similarity is still lexical inside each field, so the
quality of the labels the coordinator writes matters more than the math.
"""
import argparse
from collections import Counter
from itertools import combinations
import json
from math import exp, log, sqrt
from pathlib import Path
import re

STOP = set(
    "a an the and or but of to in on at for from by with into onto over under "
    "is are was were be been being it its this that these those their them they "
    "you your we our he she his her as so than then when while if only can could "
    "would should will may might do does did not no more most less least very "
    "just also each every any some all one two who what which where how why".split()
)

# Field weights for the combined similarity. "label" is the coordinator's
# canonical mechanism label, scored as exact match (a PSD class kernel)
# averaged with token overlap so near-synonym labels still count partly.
FIELDS = {"label": 0.35, "how": 0.25, "depends_on": 0.25, "changes": 0.15}


def stem(word):
    for suffix in ("ingly", "edly", "ing", "ies", "ied", "ers", "er", "ed", "es", "ly", "s"):
        if len(word) > len(suffix) + 2 and word.endswith(suffix):
            return word[: -len(suffix)]
    return word


def tokens(text):
    return {stem(w) for w in re.findall(r"[a-z0-9]+", text.casefold()) if w not in STOP}


def jaccard(a, b):
    union = a | b
    return len(a & b) / len(union) if union else 0.0


def normalize(rows):
    if not isinstance(rows, list) or not rows:
        raise ValueError("expected a nonempty list of candidates")
    seen, out = set(), []
    for row in rows:
        if not isinstance(row, dict) or any(
            not isinstance(row.get(k), str) or not row[k].strip()
            for k in ("id", "mechanism", "sketch")
        ):
            raise ValueError("each candidate needs a text id, mechanism and sketch")
        key = row["id"].strip()
        if key in seen:
            raise ValueError(f"duplicate candidate id {key}")
        seen.add(key)
        for k in ("title", "how", "depends_on", "changes", "grounded_in"):
            if k in row and not isinstance(row[k], str):
                raise ValueError(f"{key}: {k} must be text")
        label = " ".join(row["mechanism"].casefold().split())
        out.append(
            {
                "id": key,
                "label": label,
                "label_tokens": tokens(label),
                "how": tokens(row.get("how", "")),
                "depends_on": tokens(row.get("depends_on", "")),
                "changes": tokens(row.get("changes", "")),
                "sketch": tokens(row["sketch"]),
                "has_grounding_field": "grounded_in" in row,
                "grounded": bool(row.get("grounded_in", "").strip()),
            }
        )
    return out


def similarity(a, b):
    """Weighted mix of per-field kernels, renormalized over fields both rows have."""
    total, weight = 0.0, 0.0
    for field, w in FIELDS.items():
        if field == "label":
            value = 0.5 * (a["label"] == b["label"]) + 0.5 * jaccard(a["label_tokens"], b["label_tokens"])
        elif a[field] and b[field]:
            value = jaccard(a[field], b[field])
        else:
            continue
        total += w * value
        weight += w
    return total / weight if weight else 0.0


def eigenvalues(matrix, sweeps=100, tol=1e-12):
    """Jacobi eigenvalue method for a small symmetric matrix."""
    n = len(matrix)
    a = [row[:] for row in matrix]
    for _ in range(sweeps):
        off = sum(a[i][j] ** 2 for i in range(n) for j in range(n) if i != j)
        if off < tol:
            break
        for p in range(n - 1):
            for q in range(p + 1, n):
                if abs(a[p][q]) < 1e-15:
                    continue
                theta = (a[q][q] - a[p][p]) / (2 * a[p][q])
                t = (1 if theta >= 0 else -1) / (abs(theta) + sqrt(theta * theta + 1))
                c = 1 / sqrt(t * t + 1)
                s = t * c
                for k in range(n):
                    akp, akq = a[k][p], a[k][q]
                    a[k][p] = c * akp - s * akq
                    a[k][q] = s * akp + c * akq
                for k in range(n):
                    apk, aqk = a[p][k], a[q][k]
                    a[p][k] = c * apk - s * aqk
                    a[q][k] = s * apk + c * aqk
    return [a[i][i] for i in range(n)]


def vendi(matrix):
    """exp(Shannon entropy of the eigenvalues of K/n): 1 = all identical, n = all distinct."""
    n = len(matrix)
    if n == 1:
        return 1.0
    lams = [max(l / n, 0.0) for l in eigenvalues(matrix)]
    s = sum(lams) or 1.0
    return exp(-sum((l / s) * log(l / s) for l in lams if l > 1e-12))


def clusters(ids, sim, threshold):
    parent = {i: i for i in ids}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in combinations(ids, 2):
        if sim[(a, b)] >= threshold:
            parent[find(a)] = find(b)
    groups = {}
    for i in ids:
        groups.setdefault(find(i), []).append(i)
    return sorted((g for g in groups.values() if len(g) > 1), key=len, reverse=True)


def audit(rows, threshold=0.5):
    items = normalize(rows)
    ids = [r["id"] for r in items]
    by_id = {r["id"]: r for r in items}
    n = len(items)
    sim = {}
    matrix = [[1.0] * n for _ in range(n)]
    for i, j in combinations(range(n), 2):
        value = similarity(items[i], items[j])
        matrix[i][j] = matrix[j][i] = value
        sim[(ids[i], ids[j])] = sim[(ids[j], ids[i])] = value

    score = vendi(matrix)
    contribution = {}
    if n > 2:
        for k in range(n):
            keep = [i for i in range(n) if i != k]
            contribution[ids[k]] = round(score - vendi([[matrix[i][j] for j in keep] for i in keep]), 3)

    counts = Counter(r["label"] for r in items)
    dominant = [label for label, c in counts.most_common() if c / n > 0.4] if n >= 5 else []
    groups = clusters(ids, sim, threshold)
    ratio = score / n

    # Taboo targets: the labels behind the biggest clusters, at most two.
    taboo = []
    for label in dominant:
        if label not in taboo:
            taboo.append(label)
    for group in groups:
        label = Counter(by_id[i]["label"] for i in group).most_common(1)[0][0]
        if label not in taboo:
            taboo.append(label)
    taboo = taboo[:2]

    similar_wording = [
        {"a": a, "b": b, "word_overlap": round(jaccard(by_id[a]["sketch"], by_id[b]["sketch"]), 3)}
        for a, b in combinations(ids, 2)
        if jaccard(by_id[a]["sketch"], by_id[b]["sketch"]) >= 0.6
    ]
    # Shared assumptions: cards whose "works only if" lines overlap heavily.
    dep_ids = [i for i in ids if by_id[i]["depends_on"]]
    dep_sim = {(a, b): jaccard(by_id[a]["depends_on"], by_id[b]["depends_on"]) for a in dep_ids for b in dep_ids if a != b}
    shared = [
        {"ids": g, "share": round(len(g) / n, 3)}
        for g in clusters(dep_ids, dep_sim, 0.45)
        if n >= 4 and len(g) / n >= 1 / 3
    ]

    # Surface vs mechanism: Vendi on sketch words alone over Vendi on the structured fields.
    # Well above 1 means the sketches read differently while the mechanisms repeat.
    surface = [[1.0 if i == j else jaccard(items[i]["sketch"], items[j]["sketch"]) for j in range(n)] for i in range(n)]
    surface_ratio = round(vendi(surface) / score, 2) if n >= 4 else None

    ungrounded = [r["id"] for r in items if r["has_grounding_field"] and not r["grounded"]]
    if any(r["has_grounding_field"] for r in items):
        ungrounded += [r["id"] for r in items if not r["has_grounding_field"]]

    collapsed = n >= 4 and (bool(dominant) or ratio < 0.5 or any(len(g) / n >= 0.25 for g in groups))
    ranked = sorted(contribution.items(), key=lambda kv: kv[1]) if contribution else []
    return {
        "candidates": n,
        "effective_distinct_ideas": round(score, 2),
        "distinct_ratio": round(ratio, 3),
        "verdict": "collapsed: run a taboo repair wave" if collapsed else ("ok" if n >= 4 else "too few cards to judge spread"),
        "mechanism_counts": dict(counts.most_common()),
        "over_40_percent": dominant,
        "near_duplicate_clusters": groups,
        "most_redundant": [i for i, _ in ranked[:3]],
        "most_unique": [i for i, _ in reversed(ranked[-3:])],
        "shared_assumptions": shared,
        "surface_vs_mechanism": surface_ratio,
        "missing_grounding": ungrounded,
        "taboo_targets": taboo if collapsed else [],
        "similar_wording": similar_wording,
        "note": "Lexical similarity on structured fields. Check flagged clusters by hand before banning a mechanism. "
        "missing_grounding lists cards for the fit gate to repair or cut.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pool", type=Path)
    parser.add_argument("--threshold", type=float, default=0.5, help="cluster similarity cutoff (default 0.5)")
    args = parser.parse_args()
    try:
        print(json.dumps(audit(json.loads(args.pool.read_text()), args.threshold), indent=2))
    except (OSError, ValueError) as error:
        parser.exit(2, f"{error}\n")
