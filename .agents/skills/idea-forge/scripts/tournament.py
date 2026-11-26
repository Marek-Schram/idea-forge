"""Sparse pairwise tournament for Idea Forge: schedule the next round, then score it.

Two subcommands, Python 3 stdlib only.

  schedule  Emit the next batch of pairs to judge. Phases run in order:
            Swiss rounds (4 when there are 14 candidates or fewer, 5 above that,
            never more than n - 1), then one active-boundary round (n // 2 unplayed
            pairs near the cut line with the most Bradley-Terry uncertainty), then
            an order-swap audit (max(6, 20% of judged pairs), the closest pairs,
            shown in the opposite order). Left/right order is a seeded coin flip.
            Pairs are grouped into batches of up to 6 disjoint pairs per judge turn.
            Prints {"phase": "done"} when nothing is left.

  score     Fit Bradley-Terry strengths per criterion and for the weighted
            composite (MM algorithm with a weak Laplace prior, so sparse graphs and
            unbeaten candidates stay finite), observed-Fisher 95% intervals,
            separation probabilities, circular triads and the cycle rate, a
            HodgeRank split into gradient, curl and harmonic parts, position and
            length bias checks, a Pareto front, a MAP-Elites niche grid, and a
            quality-diversity portfolio (Pareto and niche seeding, then greedy
            k-DPP or greedy creative-utility fill). Prints a judge transparency
            card. --output writes the full JSON report.

Pool file (--pool): the cards, as a list or {"candidates": [...]} or {"ids": [...]}.
Per card: id (required); tier_intent or niche (close, stretch, wildcard);
h_gate ("PASS"/"FAIL") or fit_verdict ("pass"/"repaired"/"cut"); words (length of
the blind card) or card/sketch text to count; mechanism, how, depends_on for a
fallback similarity when no audit is given.

Audit file (--audit): diversity_audit.py --output artifact. Supplies the
similarity matrix, leave-one-out uniqueness (delta_vs_1), structural wildcards and
mechanism clusters.

Verdicts file (--verdicts):
  {"weights": {"fit": 3, "plausibility": 2, "originality": 2, "learning": 1},
   "comparisons": [
     {"pair_id": "R1_P01", "phase": "swiss_1", "left_id": "a", "right_id": "b",
      "is_swap_of": null, "evidence_diff": "a needs no second device",
      "verdicts": {"fit": "L", "plausibility": "T", "originality": "R", "learning": "L"}}]}
Verdicts are "L", "R", "T", or a candidate id, or "tie". A swap audit repeats a pair
in the opposite order with "is_swap_of" naming the original pair_id. When the two
orders disagree on a criterion, both games count as a tie there (a flip). The
2.0-lean shape {"ids", "weights", "pairs": [{"a", "b", "votes", "swapped"}]} and
inline "swap_votes" are accepted too. Optional keys: fit_cut {id: reason},
niches {id: niche}, setting (close / stretch / wildcard), portfolio_size.

Exit code 2 on malformed input. Scores describe the judge's votes and the stated
weights, not ground truth. The final choice stays with the user.
"""
import argparse
from itertools import combinations
import json
from math import exp, floor, isfinite, log, sqrt
from pathlib import Path
import random
import re

NICHES = ("close", "stretch", "wildcard")
NICHE_ALIASES = {"close": "close", "close_familiar": "close", "safe": "close", "stretch": "stretch",
                 "wildcard": "wildcard", "wild": "wildcard", "wild_card": "wildcard"}
QUOTAS = {"close": {"close": 2, "stretch": 1}, "stretch": {"close": 1, "stretch": 1, "wildcard": 1},
          "wildcard": {"stretch": 1, "wildcard": 2}}
ROLE_PATTERNS = {"fit": ("fit", "feasib", "viab"), "plausibility": ("plaus", "sound"),
                 "originality": ("orig", "novel", "non_obv", "nonobv"), "learning": ("learn",)}
STOP = set("a an the and or but of to in on at for from by with is are be it its this that they their "
           "you your we our as so if only can could would will may not no who what which how".split())


# ----------------------------------------------------------------------------- linear algebra

def jacobi_eig(matrix, sweeps=100, tol=1e-14):
    """Eigenvalues and eigenvectors (columns of V) of a small symmetric matrix."""
    n = len(matrix)
    a = [row[:] for row in matrix]
    v = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    for _ in range(sweeps):
        if sum(a[i][j] ** 2 for i in range(n) for j in range(n) if i != j) < tol:
            break
        for p in range(n - 1):
            for q in range(p + 1, n):
                if abs(a[p][q]) < 1e-300:
                    continue
                theta = (a[q][q] - a[p][p]) / (2 * a[p][q])
                t = (1 if theta >= 0 else -1) / (abs(theta) + sqrt(theta * theta + 1))
                c = 1 / sqrt(t * t + 1)
                s = t * c
                for k in range(n):
                    akp, akq = a[k][p], a[k][q]
                    a[k][p], a[k][q] = c * akp - s * akq, s * akp + c * akq
                for k in range(n):
                    apk, aqk = a[p][k], a[q][k]
                    a[p][k], a[q][k] = c * apk - s * aqk, s * apk + c * aqk
                for k in range(n):
                    vkp, vkq = v[k][p], v[k][q]
                    v[k][p], v[k][q] = c * vkp - s * vkq, s * vkp + c * vkq
    return [a[i][i] for i in range(n)], v


def pinv_sym(matrix):
    vals, vecs = jacobi_eig(matrix)
    n = len(matrix)
    top = max(abs(x) for x in vals) or 1.0
    out = [[0.0] * n for _ in range(n)]
    for k, lam in enumerate(vals):
        if lam > 1e-9 * top:
            for i in range(n):
                for j in range(n):
                    out[i][j] += vecs[i][k] * vecs[j][k] / lam
    return out


def cg(apply, b, iters=1000, tol=1e-12):
    """Conjugate gradient for a symmetric PSD system with a consistent right-hand side."""
    x = [0.0] * len(b)
    r = b[:]
    p = r[:]
    rs = sum(v * v for v in r)
    for _ in range(iters):
        if rs < tol:
            break
        ap = apply(p)
        denom = sum(pi * api for pi, api in zip(p, ap))
        if denom <= 1e-300:
            break
        alpha = rs / denom
        x = [xi + alpha * pi for xi, pi in zip(x, p)]
        r = [ri - alpha * api for ri, api in zip(r, ap)]
        new = sum(v * v for v in r)
        p = [ri + (new / rs) * pi for ri, pi in zip(r, p)]
        rs = new
    return x


def logdet_chol(m):
    n = len(m)
    low = [[0.0] * n for _ in range(n)]
    total = 0.0
    for i in range(n):
        for j in range(i + 1):
            s = m[i][j] - sum(low[i][k] * low[j][k] for k in range(j))
            if i == j:
                if s <= 0:
                    return float("-inf")
                low[i][i] = sqrt(s)
                total += 2 * log(low[i][i])
            else:
                low[i][j] = s / low[j][j]
    return total


def pearson(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sx = sqrt(sum((x - mx) ** 2 for x in xs))
    sy = sqrt(sum((y - my) ** 2 for y in ys))
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sx * sy) if sx and sy else 0.0


def logistic(x):
    return 1 / (1 + exp(-max(-50.0, min(50.0, x))))


# ----------------------------------------------------------------------------- inputs

def load_json(path, what):
    if path is None:
        return None
    try:
        return json.loads(Path(path).read_text())
    except json.JSONDecodeError as error:
        raise ValueError(f"{what} is not valid JSON: {error}")


def read_pool(data):
    """Return (ids, cards by id)."""
    if data is None:
        return None, {}
    if isinstance(data, dict) and "candidates" in data:
        data = data["candidates"]
    if isinstance(data, dict) and "ids" in data:
        data = [{"id": i} for i in data["ids"]] if isinstance(data["ids"], list) else None
    if not isinstance(data, list) or not data:
        raise ValueError("pool must be a nonempty list of cards, {\"candidates\": [...]} or {\"ids\": [...]}")
    cards = {}
    for card in data:
        if not isinstance(card, dict) or not isinstance(card.get("id"), str) or not card["id"].strip() or card["id"] in ("tie", "L", "R", "T"):
            raise ValueError("every pool card needs a text id (not tie, L, R or T)")
        if card["id"] in cards:
            raise ValueError(f"duplicate pool id {card['id']}")
        cards[card["id"]] = card
    return list(cards), cards


def gated_out(card):
    gate = str(card.get("h_gate", "")).upper()
    verdict = str(card.get("fit_verdict", "")).casefold()
    return gate == "FAIL" or verdict == "cut"


def niche_of(card, override=None):
    raw = override if override is not None else card.get("niche", card.get("tier_intent"))
    if raw is None:
        return None
    if not isinstance(raw, str) or raw.casefold() not in NICHE_ALIASES:
        raise ValueError(f"unknown niche {raw!r} for {card.get('id')}: use close, stretch or wildcard")
    return NICHE_ALIASES[raw.casefold()]


def read_verdicts(data, ids_hint=None):
    """Normalize every accepted verdict shape to a list of games plus metadata."""
    if data is None:
        return {"weights": None, "games": [], "meta": {}}
    if not isinstance(data, dict):
        raise ValueError("verdicts must be a JSON object")
    weights = data.get("weights")
    if weights is not None and (not isinstance(weights, dict) or not weights or any(
            type(w) not in (int, float) or not isfinite(w) or w <= 0 for w in weights.values())):
        raise ValueError("criterion weights must be finite positive numbers")
    raw = []
    if "comparisons" in data:
        if not isinstance(data["comparisons"], list):
            raise ValueError("comparisons must be a list")
        for c in data["comparisons"]:
            if not isinstance(c, dict):
                raise ValueError("each comparison must be an object")
            raw.append({"pair_id": c.get("pair_id"), "phase": c.get("phase", "unspecified"),
                        "left": c.get("left_id"), "right": c.get("right_id"), "swap_of": c.get("is_swap_of"),
                        "votes": c.get("verdicts"), "evidence": c.get("evidence_diff", "")})
    if "pairs" in data:
        if not isinstance(data["pairs"], list):
            raise ValueError("pairs must be a list")
        primaries = {}
        for k, p in enumerate(data["pairs"]):
            if not isinstance(p, dict):
                raise ValueError("each pair must be an object")
            pid = p.get("pair_id") or f"P{k + 1:02d}"
            key = frozenset((p.get("a"), p.get("b")))
            swapped = p.get("swapped") is True
            entry = {"pair_id": pid, "phase": p.get("phase", "swap" if swapped else "all_pairs"),
                     "left": p.get("a"), "right": p.get("b"), "swap_of": None, "votes": p.get("votes"),
                     "evidence": p.get("evidence", "")}
            if swapped:
                entry["swap_of"] = ("__key__", key)
            else:
                primaries.setdefault(key, pid)
            raw.append(entry)
            if isinstance(p.get("swap_votes"), dict):
                raw.append({"pair_id": pid + "_swap", "phase": "swap", "left": p.get("b"), "right": p.get("a"),
                            "swap_of": pid, "votes": p["swap_votes"], "evidence": ""})
        for entry in raw:
            if isinstance(entry["swap_of"], tuple):
                if entry["swap_of"][1] not in primaries:
                    raise ValueError("swap audit without a primary judgment")
                entry["swap_of"] = primaries[entry["swap_of"][1]]
    meta = {k: data.get(k) for k in ("fit_cut", "niches", "setting", "portfolio_size", "ids",
                                      "fit_criterion", "novelty_criterion") if k in data}
    return {"weights": weights, "games": raw, "meta": meta}


def validate_games(games, ids, weights):
    """Check ids and votes, convert votes to scores for the left card, link swaps."""
    known = set(ids)
    criteria = list(weights) if weights else None
    by_pid, primary_key = {}, {}
    for g in games:
        a, b, votes = g["left"], g["right"], g["votes"]
        if a not in known or b not in known or a == b:
            raise ValueError(f"unknown or invalid pair: {a}, {b}")
        if not isinstance(votes, dict) or not votes:
            raise ValueError(f"pair {a}, {b} needs one verdict per criterion")
        if criteria is None:
            criteria = list(votes)
        if set(votes) != set(criteria):
            raise ValueError(f"pair {a}, {b} needs one verdict per criterion ({', '.join(criteria)})")
        score = {}
        for crit, v in votes.items():
            if v in ("L", a):
                score[crit] = 1.0
            elif v in ("R", b):
                score[crit] = 0.0
            elif v in ("T", "tie"):
                score[crit] = 0.5
            else:
                raise ValueError(f"invalid {crit} verdict {v!r} for {a} versus {b}")
        g["score"] = score
        pid = g["pair_id"]
        if not isinstance(pid, str) or not pid:
            raise ValueError(f"comparison {a} vs {b} needs a pair_id")
        if pid in by_pid:
            raise ValueError(f"duplicate pair_id {pid}")
        by_pid[pid] = g
        if not g["swap_of"]:
            key = frozenset((a, b))
            if key in primary_key:
                raise ValueError(f"duplicate judgment: {a}, {b}")
            primary_key[key] = pid
    swapped_once = set()
    for g in games:
        if g["swap_of"]:
            orig = by_pid.get(g["swap_of"])
            if orig is None or orig["swap_of"]:
                raise ValueError(f"swap audit {g['pair_id']} names no primary judgment")
            if frozenset((g["left"], g["right"])) != frozenset((orig["left"], orig["right"])):
                raise ValueError(f"swap audit {g['pair_id']} is not the same pair as {orig['pair_id']}")
            if orig["pair_id"] in swapped_once:
                raise ValueError(f"duplicate swap audit: {orig['pair_id']}")
            swapped_once.add(orig["pair_id"])
    weights = weights or {c: 1.0 for c in (criteria or [])}
    return weights, primary_key


def role_map(weights, fit_name=None, novelty_name=None):
    roles = {}
    for role, pats in ROLE_PATTERNS.items():
        for c in weights:
            if any(p in c.casefold() for p in pats) and c not in roles.values():
                roles[role] = c
                break
    for role, name in (("fit", fit_name), ("originality", novelty_name)):
        if name is not None:
            if name not in weights:
                raise ValueError(f"{role} criterion {name!r} is not one of the weighted criteria")
            roles[role] = name
    return roles


# ----------------------------------------------------------------------------- model fitting

def outcomes(games, ids, weights, criterion=None):
    """Per-game results for one criterion (or the weighted composite), with swap flips turned into ties.

    Returns (results, flips): results is a list of (left, right, score_for_left)."""
    total = sum(weights.values())
    def s(g):
        if criterion:
            return g["score"][criterion]
        return sum(weights[c] * g["score"][c] for c in weights) / total
    by_pid = {g["pair_id"]: g for g in games}
    flipped = set()
    for g in games:
        if g["swap_of"]:
            o = by_pid[g["swap_of"]]
            crits = [criterion] if criterion else list(weights)
            for c in crits:
                # Same winner means the left score of one equals the right score of the other.
                if o["score"][c] != 0.5 or g["score"][c] != 0.5:
                    win_o = o["left"] if o["score"][c] == 1 else o["right"] if o["score"][c] == 0 else "tie"
                    win_g = g["left"] if g["score"][c] == 1 else g["right"] if g["score"][c] == 0 else "tie"
                    if win_o != win_g:
                        flipped.add((o["pair_id"], c))
                        flipped.add((g["pair_id"], c))
    results = []
    for g in games:
        if criterion:
            val = 0.5 if (g["pair_id"], criterion) in flipped else s(g)
        else:
            val = sum(weights[c] * (0.5 if (g["pair_id"], c) in flipped else g["score"][c]) for c in weights) / total
        results.append((g["left"], g["right"], val))
    return results


def bradley_terry(results, ids, alpha=0.25, iters=5000, tol=1e-9):
    n = len(ids)
    idx = {k: i for i, k in enumerate(ids)}
    eps = alpha / (n - 1)
    wins = [[eps if i != j else 0.0 for j in range(n)] for i in range(n)]
    games = [[2 * eps if i != j else 0.0 for j in range(n)] for i in range(n)]
    for a, b, s in results:
        i, j = idx[a], idx[b]
        wins[i][j] += s
        wins[j][i] += 1 - s
        games[i][j] += 1
        games[j][i] += 1
    w = [1.0] * n
    for _ in range(iters):
        new = []
        for i in range(n):
            denom = sum(games[i][j] / (w[i] + w[j]) for j in range(n) if j != i)
            new.append(sum(wins[i]) / denom)
        g = exp(sum(log(x) for x in new) / n)
        new = [x / g for x in new]
        done = max(abs(x - y) for x, y in zip(new, w)) < tol
        w = new
        if done:
            break
    theta = [log(x) for x in w]
    mean = sum(theta) / n
    theta = [t - mean for t in theta]
    hess = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                p = logistic(theta[i] - theta[j])
                v = games[i][j] * p * (1 - p)
                hess[i][j] = -v
                hess[i][i] += v
    cov = pinv_sym(hess)
    return {k: theta[idx[k]] for k in ids}, {(a, b): cov[idx[a]][idx[b]] for a in ids for b in ids}


def pair_net(results):
    """Mean score for the lexically first id of each observed pair, and game counts."""
    net, count = {}, {}
    for a, b, s in results:
        lo, hi = sorted((a, b))
        net[(lo, hi)] = net.get((lo, hi), 0.0) + (s if a == lo else 1 - s)
        count[(lo, hi)] = count.get((lo, hi), 0) + 1
    return {k: net[k] / count[k] for k in net}, count


def cycles(results, ids):
    """Circular triads among fully observed triangles."""
    net, _ = pair_net(results)
    beats = {}
    for (lo, hi), m in net.items():
        if m > 0.5:
            beats[(lo, hi)] = True
        elif m < 0.5:
            beats[(hi, lo)] = True
    tri, found = 0, []
    for a, b, c in combinations(sorted(ids), 3):
        if all(k in net for k in ((a, b), (a, c), (b, c))):
            tri += 1
            for x, y, z in ((a, b, c), (a, c, b)):
                if beats.get((x, y)) and beats.get((y, z)) and beats.get((z, x)):
                    found.append(f"{x} > {y} > {z} > {x}")
    rate = len(found) / tri if tri else 0.0
    return {"observed_triangles": tri, "circular_triads": len(found), "cycle_rate": round(rate, 3),
            "transitivity": round(1 - rate, 3), "sparse_kendall_zeta": round(1 - min(1.0, 4 * rate), 3),
            "cycles": found}


def hodgerank(results, ids):
    """Weighted HodgeRank split of the net edge flow into gradient, curl and harmonic parts."""
    net, count = pair_net(results)
    edges = sorted(net)
    if not edges:
        return None
    eidx = {e: k for k, e in enumerate(edges)}
    idx = {k: i for i, k in enumerate(sorted(ids))}
    y = [2 * net[e] - 1 for e in edges]
    w = [count[e] for e in edges]
    n = len(ids)

    def lap(s):
        out = [0.0] * n
        for (a, b), we in zip(edges, w):
            d = we * (s[idx[a]] - s[idx[b]])
            out[idx[a]] += d
            out[idx[b]] -= d
        return out
    rhs = [0.0] * n
    for (a, b), we, ye in zip(edges, w, y):
        rhs[idx[a]] += we * ye
        rhs[idx[b]] -= we * ye
    s = cg(lap, rhs)
    grad = [s[idx[a]] - s[idx[b]] for a, b in edges]
    resid = [ye - ge for ye, ge in zip(y, grad)]
    tris = [t for t in combinations(sorted(ids), 3) if (t[0], t[1]) in eidx and (t[0], t[2]) in eidx and (t[1], t[2]) in eidx]
    rt = [sqrt(we) * r for we, r in zip(w, resid)]
    curl = [0.0] * len(edges)
    if tris:
        cols = [((eidx[(a, b)], 1.0), (eidx[(b, c)], 1.0), (eidx[(a, c)], -1.0)) for a, b, c in tris]

        def a_mul(phi):
            out = [0.0] * len(edges)
            for col, f in zip(cols, phi):
                for e, sign in col:
                    out[e] += sign * f / sqrt(w[e])
            return out

        def at_mul(v):
            return [sum(sign * v[e] / sqrt(w[e]) for e, sign in col) for col in cols]
        phi = cg(lambda p: at_mul(a_mul(p)), at_mul(rt))
        curl = a_mul(phi)
    harm = [r - c for r, c in zip(rt, curl)]
    yt = [sqrt(we) * ye for we, ye in zip(w, y)]
    gt = [sqrt(we) * ge for we, ge in zip(w, grad)]
    total = sum(v * v for v in yt)
    if total <= 1e-12:
        return {"gradient": None, "curl": None, "harmonic": None, "note": "every judged pair was a tie"}
    parts = [sum(v * v for v in gt), sum(v * v for v in curl), sum(v * v for v in harm)]
    norm = sum(parts) or 1.0
    return {"gradient": round(parts[0] / norm, 3), "curl": round(parts[1] / norm, 3),
            "harmonic": round(parts[2] / norm, 3), "edges": len(edges), "triangles": len(tris)}


# ----------------------------------------------------------------------------- schedule

def default_rounds(n):
    return min(n - 1, 4 if n <= 14 else 5)


def batch_pairs(pairs, size=6):
    batches = []
    for p in pairs:
        for b in batches:
            if len(b["ids"]) < size * 2 and len(b["pairs"]) < size and not ({p["left_id"], p["right_id"]} & b["ids"]):
                b["pairs"].append(p["pair_id"])
                b["ids"] |= {p["left_id"], p["right_id"]}
                break
        else:
            batches.append({"pairs": [p["pair_id"]], "ids": {p["left_id"], p["right_id"]}})
    return [b["pairs"] for b in batches]


def swiss_pairs(order, played, budget=20000):
    """Pair neighbours in standing order with no rematches. Backtracks to avoid needless byes."""
    calls = [0]

    def solve(rest):
        if len(rest) <= 1:
            return [], list(rest)
        calls[0] += 1
        if calls[0] > budget:
            return None
        a, tail = rest[0], rest[1:]
        for b in tail:
            if frozenset((a, b)) in played:
                continue
            found = solve([x for x in tail if x != b])
            if found is not None and not found[1][1:]:
                return [(a, b)] + found[0], found[1]
        # Odd count: let the lowest-ranked open candidate sit out.
        if len(rest) % 2 == 1:
            found = solve(rest[:-1])
            if found is not None and not found[1]:
                return found[0], [rest[-1]]
        return None

    result = solve(list(order))
    if result is not None:
        return result
    pairs, byes, open_ = [], [], list(order)
    while len(open_) > 1:
        a = open_.pop(0)
        partner = next((b for b in open_ if frozenset((a, b)) not in played), None)
        if partner is None:
            byes.append(a)
            continue
        open_.remove(partner)
        pairs.append((a, partner))
    return pairs, byes + open_


def schedule(pool_ids, cards, verdicts, audit, k, rounds, seed):
    ids = [i for i in pool_ids if not gated_out(cards.get(i, {}))]
    if len(ids) < 2:
        raise ValueError("need at least two candidates that passed the fit gate")
    games = verdicts["games"]
    weights, played = validate_games(games, ids, verdicts["weights"]) if games else ({}, {})
    rounds = default_rounds(len(ids)) if rounds is None else rounds
    if rounds < 1:
        raise ValueError("rounds must be at least 1")
    rng = random.Random(seed)
    phases = [g["phase"] for g in games]
    swiss_done = max([int(p.split("_")[1]) for p in phases if re.fullmatch(r"swiss_\d+", str(p))] or [0])
    composite = outcomes(games, ids, weights) if games else []
    score = {i: 0.0 for i in ids}
    for a, b, s in composite:
        score[a] += s
        score[b] += 1 - s
    out = {"phase": None, "pairs": [], "byes": []}

    while swiss_done < rounds:
        r = swiss_done + 1
        order = ids[:]
        rng.shuffle(order)
        order.sort(key=lambda i: -score[i])
        pairs, byes = swiss_pairs(order, played)
        unpaired = []
        if not pairs:
            # Every remaining pair was already judged: Swiss is exhausted, move on to the next phase.
            swiss_done = rounds
            break
        out["byes"] = byes + unpaired
        out["phase"], out["round"] = f"swiss_{r}", r
        for n_, (a, b) in enumerate(pairs, 1):
            left, right = (a, b) if rng.random() < 0.5 else (b, a)
            out["pairs"].append({"pair_id": f"R{r}_P{n_:02d}", "phase": f"swiss_{r}", "left_id": left,
                                 "right_id": right, "is_swap_of": None})
        out["batches"] = batch_pairs(out["pairs"])
        return out

    theta, cov = bradley_terry(composite, ids) if composite else ({i: 0.0 for i in ids}, {(a, b): 0.0 for a in ids for b in ids})
    has_active = any(p == "active" for p in phases)
    has_swap = any(g["swap_of"] for g in games)
    if not has_active:
        wild = {m["id"] for m in (audit or {}).get("item_metrics", []) if m.get("structural_wildcard")}
        ranked = sorted(ids, key=lambda i: (-theta[i], i))
        contenders = set(ranked[:k + 6]) | (wild & set(ids))
        options = []
        for a, b in combinations(sorted(contenders), 2):
            if frozenset((a, b)) in played:
                continue
            var = cov[(a, a)] + cov[(b, b)] - 2 * cov[(a, b)]
            options.append((var * exp(-abs(theta[a] - theta[b])), a, b))
        options.sort(key=lambda t: (-t[0], t[1], t[2]))
        chosen = options[:len(ids) // 2]
        if chosen:
            out["phase"] = "active"
            for n_, (info, a, b) in enumerate(chosen, 1):
                left, right = (a, b) if rng.random() < 0.5 else (b, a)
                out["pairs"].append({"pair_id": f"A_P{n_:02d}", "phase": "active", "left_id": left,
                                     "right_id": right, "is_swap_of": None, "info": round(info, 4)})
            out["batches"] = batch_pairs(out["pairs"])
            return out
    if not has_swap:
        primaries = [g for g in games if not g["swap_of"]]
        count = min(len(primaries), max(6, floor(0.2 * len(primaries))))
        closest = sorted(primaries, key=lambda g: (abs(theta[g["left"]] - theta[g["right"]]), g["pair_id"]))[:count]
        out["phase"] = "swap"
        for n_, g in enumerate(closest, 1):
            out["pairs"].append({"pair_id": f"S_P{n_:02d}", "phase": "swap", "left_id": g["right"],
                                 "right_id": g["left"], "is_swap_of": g["pair_id"]})
        out["batches"] = batch_pairs(out["pairs"])
        return out
    return {"phase": "done", "pairs": [], "byes": [], "note": "Swiss, active-boundary and swap phases are complete. Run score."}


# ----------------------------------------------------------------------------- score

def text_tokens(card):
    text = " ".join(str(card.get(k, "")) for k in ("mechanism", "mechanism_signature", "how", "depends_on"))
    return {w for w in re.findall(r"[a-z0-9]+", text.casefold()) if w not in STOP}


def similarity_lookup(ids, cards, audit):
    sim = (audit or {}).get("similarity_matrix")
    if sim and isinstance(sim.get("ids"), list) and set(ids) <= set(sim["ids"]):
        pos = {k: i for i, k in enumerate(sim["ids"])}
        mat = sim.get("K_composite")
        return (lambda a, b: 1.0 if a == b else float(mat[pos[a]][pos[b]])), "audit similarity matrix"
    toks = {i: text_tokens(cards.get(i, {})) for i in ids}
    if any(toks.values()):
        def jac(a, b):
            if a == b:
                return 1.0
            u = toks[a] | toks[b]
            return len(toks[a] & toks[b]) / len(u) if u else 0.0
        return jac, "word overlap of pool mechanism fields (no audit matrix given)"
    return (lambda a, b: 1.0 if a == b else 0.0), "none (no audit or mechanism text): diversity unchecked"


def word_count(card):
    if type(card.get("words")) in (int, float):
        return card["words"]
    for k in ("card", "blind_card", "sketch", "sketch_draft"):
        if isinstance(card.get(k), str):
            return len(card[k].split())
    return None


def score(pool_ids, cards, verdicts, audit, k, tier, selector, lam, beta, fit_name, novelty_name):
    meta = verdicts["meta"]
    games = verdicts["games"]
    if not games:
        raise ValueError("no judgments to score")
    ids = pool_ids or meta.get("ids")
    if ids is None:
        seen = []
        for g in games:
            for x in (g["left"], g["right"]):
                if x not in seen:
                    seen.append(x)
        ids = seen
    fit_cut = meta.get("fit_cut") or {}
    if not isinstance(fit_cut, dict) or any(not isinstance(v, str) for v in fit_cut.values()):
        raise ValueError("fit_cut must map ids to a text reason")
    gated = {i: "failed the fit gate (h_gate FAIL or fit_verdict cut)" for i in ids if gated_out(cards.get(i, {}))}
    gated.update({i: r for i, r in fit_cut.items()})
    judged_ids = [i for i in ids if i not in gated or any(i in (g["left"], g["right"]) for g in games)]
    if len(judged_ids) < 2:
        raise ValueError("supply at least two judged candidates")
    weights, primary = validate_games(games, judged_ids, verdicts["weights"])
    roles = role_map(weights, fit_name or meta.get("fit_criterion"), novelty_name or meta.get("novelty_criterion"))
    n = len(judged_ids)

    comp = outcomes(games, judged_ids, weights)
    theta, cov = bradley_terry(comp, judged_ids)
    per = {c: bradley_terry(outcomes(games, judged_ids, weights, c), judged_ids)[0] for c in weights}
    order = sorted(judged_ids, key=lambda i: (-theta[i], i))

    # Bias telemetry.
    swaps = [g for g in games if g["swap_of"]]
    by_pid = {g["pair_id"]: g for g in games}
    checked, flips, flipped = 0, 0, []
    for g in swaps:
        o = by_pid[g["swap_of"]]
        for c in weights:
            checked += 1
            win_o = o["left"] if o["score"][c] == 1 else o["right"] if o["score"][c] == 0 else "tie"
            win_g = g["left"] if g["score"][c] == 1 else g["right"] if g["score"][c] == 0 else "tie"
            if win_o != win_g:
                flips += 1
                flipped.append(f"{'/'.join(sorted((o['left'], o['right'])))} on {c}")
    flip_rate = flips / checked if checked else None
    decisive = [s for _, _, s in comp if abs(s - 0.5) > 1e-9]
    first_pos = sum(1 for s in decisive if s > 0.5) / len(decisive) if decisive else None
    words = {i: word_count(cards.get(i, {})) for i in judged_ids}
    if not all(type(words[i]) in (int, float) for i in judged_ids) and isinstance(meta.get("words"), dict):
        words = {i: meta["words"].get(i) for i in judged_ids}
    length_r = pearson([words[i] for i in judged_ids], [theta[i] for i in judged_ids]) \
        if n >= 4 and all(type(words[i]) in (int, float) for i in judged_ids) else None
    cyc = cycles(comp, judged_ids)
    per_cycles = {c: cycles(outcomes(games, judged_ids, weights, c), judged_ids)["circular_triads"] for c in weights}
    hodge = hodgerank(comp, judged_ids)
    warnings = []
    if flip_rate is not None and flip_rate > 0.20:
        warnings.append(f"WARN_JUDGE_BRITTLE: {flip_rate:.0%} of swap-audited verdicts flipped (above 20%)")
    if (flip_rate is not None and flip_rate > 0.25) or (first_pos is not None and len(decisive) >= 8 and not 0.38 <= first_pos <= 0.62):
        warnings.append("WARN_POSITION_BIAS: the first-shown card wins too often or swaps flip too often")
    if length_r is not None and length_r > 0.35:
        warnings.append(f"WARN_LENGTH_BIAS: longer cards are winning (r = {length_r:+.2f}). Re-trim cards to one length")
    if cyc["observed_triangles"] and cyc["transitivity"] < 0.85:
        warnings.append("WARN_INTRANSITIVE: transitivity below 0.85. The judge cannot separate these finalists, so let the user decide directly")
    if hodge and hodge.get("harmonic") is not None and hodge["harmonic"] > 0.25:
        warnings.append("GLOBAL_INCOHERENCE: harmonic share above 0.25 (cycles longer than three)")
    if hodge and hodge.get("curl") is not None and hodge["curl"] > 0.35:
        warnings.append("LOCAL_NOISE: curl share above 0.35 (many local three-way cycles)")

    # Confidence and separation.
    table = []
    for rank, i in enumerate(order, 1):
        se = sqrt(max(cov[(i, i)], 0.0))
        row = {"id": i, "scalar_rank": rank, "theta": round(theta[i], 3), "se": round(se, 3),
               "ci95": [round(theta[i] - 1.96 * se, 3), round(theta[i] + 1.96 * se, 3)],
               "criteria_theta": {c: round(per[c][i], 3) for c in weights}}
        if rank < n:
            j = order[rank]
            var = cov[(i, i)] + cov[(j, j)] - 2 * cov[(i, j)]
            row["p_beats_next"] = round(logistic(theta[i] - theta[j]), 3)
            row["z_vs_next"] = round((theta[i] - theta[j]) / sqrt(var), 2) if var > 1e-12 else None
        table.append(row)
    virtual_ties = [f"{r['id']} vs {order[r['scalar_rank']]} (P = {r['p_beats_next']:.2f})"
                    for r in table if r.get("p_beats_next") is not None and r["p_beats_next"] < 0.60]

    # Portfolio axes on [0, 1].
    audit_items = {m["id"]: m for m in (audit or {}).get("item_metrics", []) if isinstance(m, dict) and "id" in m}
    dvs = {i: audit_items[i].get("delta_vs_1") for i in judged_ids if i in audit_items}
    if dvs and len(dvs) == n:
        lo, hi = min(dvs.values()), max(dvs.values())
        uniq = {i: (dvs[i] - lo) / (hi - lo) if hi > lo else 0.5 for i in judged_ids}
    else:
        uniq = None
    lg = {c: {i: logistic(per[c][i]) for i in judged_ids} for c in weights}
    comp_l = {i: logistic(theta[i]) for i in judged_ids}

    def mix(parts):
        parts = [(w, v) for w, v in parts if v is not None]
        return (lambda i: sum(w * v[i] for w, v in parts) / sum(w for w, _ in parts)) if parts else None
    viability = mix([(0.55, lg.get(roles.get("fit"))), (0.45, lg.get(roles.get("plausibility")))]) or (lambda i: comp_l[i])
    orig_base = lg.get(roles.get("originality"))
    originality = mix([(0.65, orig_base), (0.35, uniq)]) if orig_base else (mix([(1.0, uniq)]) if uniq else None)
    learning = mix([(1.0, lg.get(roles.get("learning")))])
    axes = {"viability": viability}
    if originality:
        axes["originality"] = originality
    if learning:
        axes["learning_value"] = learning
    axis_val = {i: {a: round(f(i), 3) for a, f in axes.items()} for i in judged_ids}

    eligible = [i for i in order if i not in gated]
    if not eligible:
        raise ValueError("every judged candidate failed the fit gate")
    pareto = [i for i in eligible if not any(
        all(axis_val[j][a] >= axis_val[i][a] for a in axes) and any(axis_val[j][a] > axis_val[i][a] for a in axes)
        for j in eligible if j != i)]

    # Weak fit (2.0-lean rule): lost on the fit criterion in more than half of its games.
    weak_fit = set()
    fit_c = roles.get("fit")
    if fit_c and n >= 3:
        res = outcomes(games, judged_ids, weights, fit_c)
        for i in judged_ids:
            played_n = [(a, b, s) for a, b, s in res if i in (a, b)]
            losses = sum(1 for a, b, s in played_n if (s < 0.5 if a == i else s > 0.5))
            if played_n and losses > len(played_n) / 2:
                weak_fit.add(i)

    niche_override = meta.get("niches") or {}
    if not isinstance(niche_override, dict):
        raise ValueError("niches must map ids to close, stretch or wildcard")
    niche = {i: niche_of(cards.get(i, {"id": i}), niche_override.get(i)) for i in judged_ids}
    cluster = {i: audit_items.get(i, {}).get("cluster_id", "-") for i in judged_ids}
    structural_wild = {i for i in judged_ids if audit_items.get(i, {}).get("structural_wildcard")}

    # MAP-Elites grid: niche x mechanism cluster, elite = strongest viable candidate in the cell.
    grid = {}
    for i in eligible:
        if niche[i] is None or axis_val[i]["viability"] < 0.35 or i in weak_fit:
            continue
        cell = (niche[i], cluster[i])
        if cell not in grid or theta[i] > theta[grid[cell]]:
            grid[cell] = i
    tier = tier or meta.get("setting") or "stretch"
    tier = NICHE_ALIASES.get(str(tier).casefold())
    if tier not in QUOTAS:
        raise ValueError("novelty tier must be close, stretch or wildcard")
    size = meta.get("portfolio_size", k)
    if type(size) is not int or size < 1:
        raise ValueError("portfolio size must be a positive whole number")
    size = min(size, len(eligible))

    sim, sim_source = similarity_lookup(judged_ids, cards, audit)
    quality = {i: sum(axis_val[i].values()) / len(axes) for i in judged_ids}
    picks, reasons, unfilled = [], {}, []
    for nk in NICHES:
        quota = QUOTAS[tier].get(nk, 0)
        elites = sorted((e for (cn, _), e in grid.items() if cn == nk),
                        key=lambda e: (e not in pareto, -theta[e], e))
        if len(elites) < quota:
            unfilled.append(f"{nk}: wanted {quota}, found {len(elites)} viable elite(s)")
        for e in elites[:quota]:
            if len(picks) < size:
                picks.append(e)
                reasons[e] = f"{nk} niche elite" + (" (Pareto)" if e in pareto else "")
    # Protect the top originality pick, as 2.0-lean does.
    orig_c = roles.get("originality")
    passed_over = []
    if orig_c:
        ranked = sorted(eligible, key=lambda i: (-per[orig_c][i], -theta[i], i))
        if ranked and ranked[0] in weak_fit:
            passed_over.append(f"{ranked[0]} (top on {orig_c})")
        top_novel = next((i for i in ranked if i not in weak_fit), None)
        if top_novel and top_novel not in picks and len(picks) < size:
            picks.append(top_novel)
            reasons[top_novel] = f"top on {orig_c}"

    def kdpp_gain(i):
        q = {x: exp(beta * quality[x]) * (1.2 if x in pareto else 1.0) for x in picks + [i]}
        sub = picks + [i]
        m = [[q[a] * q[b] * sim(a, b) + (1e-10 if a == b else 0.0) for b in sub] for a in sub]
        return logdet_chol(m)

    def utility_gain(i):
        return quality[i] * (1 - lam * max((sim(i, s) for s in picks), default=0.0))
    gain = kdpp_gain if selector == "kdpp" else utility_gain
    while len(picks) < size:
        rest = [i for i in eligible if i not in picks]
        if not rest:
            break
        best = max(rest, key=lambda i: (gain(i), theta[i], i))
        picks.append(best)
        reasons[best] = "greedy k-DPP fill" if selector == "kdpp" else "greedy creative-utility fill"
    sub = [[sim(a, b) for b in picks] for a in picks]
    vals, _ = jacobi_eig(sub)
    lams = [max(v / len(picks), 0.0) for v in vals]
    tot = sum(lams) or 1.0
    port_vs = exp(-sum((x / tot) * log(x / tot) for x in lams if x / tot > 1e-12))

    scalar_top = eligible[:size]
    rescued = [{"id": i, "scalar_rank": order.index(i) + 1, "qd_slot": reasons[i],
                "reason": ("Pareto-optimal" if i in pareto else "") + (" and " if i in pareto and i in structural_wild else "")
                + ("structural wildcard in the audit" if i in structural_wild else "")}
               for i in picks if i not in scalar_top and (i in pareto or i in structural_wild)]
    half = n / 2
    killed = []
    for c in (roles.get("originality"), roles.get("learning")):
        if not c:
            continue
        for i in sorted(judged_ids, key=lambda x: (-per[c][x], x))[:2]:
            if order.index(i) + 1 > half and i not in gated:
                killed.append({"id": i, "axis": c, "scalar_rank": order.index(i) + 1, "kept": i in picks})
    provocations = []
    if audit_items:
        top_unique = sorted(audit_items.values(), key=lambda m: -(m.get("delta_vs_1") or 0))[:2]
        provocations = [{"id": m["id"], "delta_vs_1": m.get("delta_vs_1"), "reason": gated[m["id"]]}
                        for m in top_unique if m["id"] in gated]

    phase_counts = {}
    for g in games:
        key = "swap" if g["swap_of"] else re.sub(r"_\d+$", "", str(g["phase"]))
        phase_counts[key] = phase_counts.get(key, 0) + 1
    swiss_rounds = len({g["phase"] for g in games if re.fullmatch(r"swiss_\d+", str(g["phase"]))})
    health = {
        "total_pairs_evaluated": len(games), "primary_pairs": len(primary), "swap_pairs_audited": len(swaps),
        "phases": phase_counts, "swiss_rounds": swiss_rounds, "all_pairs_would_be": n * (n - 1) // 2,
        "bidirectional_all_pairs_would_be": n * (n - 1),
        "order_swap_flip_rate": None if flip_rate is None else round(flip_rate, 3), "flipped": flipped,
        "first_position_win_rate": None if first_pos is None else round(first_pos, 3),
        "length_bias_r": None if length_r is None else round(length_r, 3),
        **{k2: cyc[k2] for k2 in ("observed_triangles", "circular_triads", "cycle_rate", "transitivity", "sparse_kendall_zeta", "cycles")},
        "circular_triads_by_criterion": per_cycles, "hodge_ratios": hodge, "warnings": warnings,
    }
    report = {
        "judge_health_card": health,
        "portfolio_selection": {
            "k": size, "novelty_tier": tier, "selector": selector, "similarity_source": sim_source,
            "selected_ids": picks, "reasons": reasons, "portfolio_vendi_vs1": round(port_vs, 2),
            "scalar_top_k": scalar_top, "pareto_front_ids": pareto,
            "map_elites_grid": [{"niche": a, "cluster": b, "elite": e} for (a, b), e in sorted(grid.items())],
            "rescued_wildcards": rescued, "killed_by_feasibility_alerts": killed,
            "passed_over_for_weak_fit": passed_over, "gated_provocations": provocations,
            "fit_gate_cut": gated, "virtual_ties": virtual_ties, "unfilled_niche_quotas": unfilled,
        },
        "candidate_table": [dict(r, axes=axis_val[r["id"]], niche=niche[r["id"]], cluster=cluster[r["id"]],
                                 pareto_optimal=r["id"] in pareto, h_gate="FAIL" if r["id"] in gated else "PASS",
                                 weak_fit=r["id"] in weak_fit) for r in table],
        "roles": roles, "weights": weights,
    }
    return report


def render(report):
    h, p = report["judge_health_card"], report["portfolio_selection"]
    lines = ["| Candidate | BT strength | 95% CI | P(beats next) | " + " | ".join(report["roles"].get(r, r) for r in ("fit", "plausibility", "originality", "learning") if r in report["roles"]) + " | Axes (viability / originality / learning) |",
             "|---|---:|---:|---:|" + "---:|" * len([r for r in ("fit", "plausibility", "originality", "learning") if r in report["roles"]]) + "---|"]
    for r in report["candidate_table"]:
        crits = " | ".join(f"{r['criteria_theta'][report['roles'][x]]:+.2f}" for x in ("fit", "plausibility", "originality", "learning") if x in report["roles"])
        axes = " / ".join(f"{v:.2f}" for v in r["axes"].values())
        pn = f"{r['p_beats_next']:.2f}" if r.get("p_beats_next") is not None else "-"
        lines.append(f"| {r['id']} | {r['theta']:+.2f} | {r['ci95'][0]:+.2f} to {r['ci95'][1]:+.2f} | {pn} | {crits} | {axes} |")
    ph = h["phases"]
    topo = ", ".join(f"{v} {k}" for k, v in ph.items())
    lines += ["", "Judge transparency card:",
              f"- Topology: {h['swiss_rounds']} Swiss round(s); {h['total_pairs_evaluated']} judged pairs ({topo}). "
              f"All pairs would be {h['all_pairs_would_be']}, both orders {h['bidirectional_all_pairs_would_be']}."]
    if h["order_swap_flip_rate"] is None:
        lines.append("- No order-swap audit was run, so position bias is unmeasured.")
    else:
        lines.append(f"- Order swaps: {h['swap_pairs_audited']} pair(s) re-judged in reverse, "
                     f"{h['order_swap_flip_rate']:.0%} of verdicts flipped and were counted as ties."
                     + (f" Flipped: {'; '.join(h['flipped'])}." if h["flipped"] else ""))
    if h["first_position_win_rate"] is not None:
        lines.append(f"- First-shown card won {h['first_position_win_rate']:.0%} of decisive verdicts.")
    if h["length_bias_r"] is not None:
        lines.append(f"- Card length vs strength: r = {h['length_bias_r']:+.2f}.")
    lines.append(f"- Consistency: {h['circular_triads']} circular triad(s) in {h['observed_triangles']} observed triangle(s), "
                 f"cycle rate {h['cycle_rate']:.0%}, transitivity {h['transitivity']:.0%}, sparse Kendall zeta {h['sparse_kendall_zeta']:.2f}."
                 + (f" Cycles: {'; '.join(h['cycles'])}." if h["cycles"] else ""))
    hr = h["hodge_ratios"]
    if hr and hr.get("gradient") is not None:
        lines.append(f"- HodgeRank: gradient {hr['gradient']:.0%}, local curl {hr['curl']:.0%}, global harmonic {hr['harmonic']:.0%}.")
    near_cut = p["virtual_ties"][:p["k"] + 1]
    if near_cut:
        more = len(p["virtual_ties"]) - len(near_cut)
        lines.append("- Virtual ties near the top (P below 0.60): " + "; ".join(near_cut)
                     + (f", plus {more} lower down (see the JSON report)." if more else "."))
    lines.append("- Pareto front (viability, originality, learning): " + ", ".join(p["pareto_front_ids"]) + ".")
    if p["map_elites_grid"]:
        lines.append("- Niche grid elites: " + "; ".join(f"{c['niche']}/{c['cluster']}: {c['elite']}" for c in p["map_elites_grid"]) + ".")
    lines.append(f"- Portfolio ({p['selector']}, {p['novelty_tier']} setting, similarity from {p['similarity_source']}): "
                 + "; ".join(f"{i} ({p['reasons'][i]})" for i in p["selected_ids"])
                 + f". Effective distinct ideas in the portfolio: {p['portfolio_vendi_vs1']:.2f} of {len(p['selected_ids'])}.")
    if p["unfilled_niche_quotas"]:
        lines.append("- Niche quota not met (no candidate in that niche had viability 0.35 or more without losing on fit to most opponents): "
                     + "; ".join(p["unfilled_niche_quotas"]) + ".")
    for r in p["rescued_wildcards"]:
        lines.append(f"- Wildcard rescue: {r['id']} sits at scalar rank {r['scalar_rank']} but was kept ({r['reason']}).")
    for r in p["killed_by_feasibility_alerts"]:
        lines.append(f"- Killed-by-feasibility alert: {r['id']} is top two on {r['axis']} but ranks {r['scalar_rank']} overall"
                     + (", kept in the portfolio." if r["kept"] else ", not kept. Say so to the user."))
    for item in p["passed_over_for_weak_fit"]:
        cid = item.split(" ")[0]
        lines.append(f"- Not given the protected novelty slot because it lost on fit to most opponents: {item}"
                     + (". It still made the portfolio on the fill step." if cid in p["selected_ids"] else "."))
    if p["fit_gate_cut"]:
        lines.append(f"- Fit gate cut {len(p['fit_gate_cut'])} card(s): " + "; ".join(f"{k}: {v}" for k, v in p["fit_gate_cut"].items()) + ".")
    for g in p["gated_provocations"]:
        lines.append(f"- Rule-breaking provocation (failed the fit gate, footnote only, never a pick): {g['id']}.")
    for w in h["warnings"]:
        lines.append(f"- {w}.")
    wild = [r["id"] for r in p["killed_by_feasibility_alerts"]]
    lines += ["", f"Critique audit: {h['total_pairs_evaluated']} pairs evaluated ({h['swap_pairs_audited']} swapped); "
              + (f"{h['order_swap_flip_rate']:.0%} position flips, " if h["order_swap_flip_rate"] is not None else "flips unmeasured, ")
              + f"{h['transitivity']:.0%} transitivity; {len(p['pareto_front_ids'])} Pareto-optimal leads"
              + (f"; wildcard(s) {', '.join(sorted(set(wild)))} flagged for high novelty or learning despite a low overall rank." if wild else "."),
              "", "Decision: left to the user."]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("schedule", "score"):
        sp = sub.add_parser(name)
        sp.add_argument("--pool", type=Path, help="cards JSON (ids, niches, fit gate verdicts, words)")
        sp.add_argument("--ids", help="comma-separated ids, instead of --pool")
        sp.add_argument("--verdicts", type=Path, help="judged comparisons so far")
        sp.add_argument("--audit", type=Path, help="diversity_audit.py --output artifact")
        sp.add_argument("--k", type=int, default=5, help="portfolio size (Standard 5, Deep 6)")
        sp.add_argument("--seed", type=int, default=0, help="random seed for order flips and tiebreaks")
        sp.add_argument("--output", type=Path, help="also write the JSON result here")
    sp = sub.choices["schedule"]
    sp.add_argument("--rounds", type=int, help="Swiss rounds (default 4 up to 14 candidates, else 5)")
    sp = sub.choices["score"]
    sp.add_argument("--novelty-tier", help="close, stretch or wildcard (default from verdicts 'setting', else stretch)")
    sp.add_argument("--selector", choices=("kdpp", "utility"), default="kdpp", help="portfolio fill rule")
    sp.add_argument("--lambda", dest="lam", type=float, default=0.5, help="creative-utility redundancy penalty")
    sp.add_argument("--beta", type=float, default=2.0, help="k-DPP quality sharpness")
    sp.add_argument("--fit-criterion", help="criterion that guards balance slots (default: name containing fit)")
    sp.add_argument("--novelty-criterion", help="criterion for the originality axis (default: name containing orig)")
    sp.add_argument("--json", action="store_true", help="print the JSON report instead of the card")
    args = parser.parse_args()
    try:
        if args.k < 1:
            raise ValueError("--k must be at least 1")
        pool_ids, cards = read_pool(load_json(args.pool, "pool"))
        if args.ids:
            pool_ids = [x.strip() for x in args.ids.split(",") if x.strip()]
            if len(set(pool_ids)) != len(pool_ids) or any(x in ("tie", "L", "R", "T") for x in pool_ids):
                raise ValueError("--ids must be distinct and not tie, L, R or T")
        verdicts = read_verdicts(load_json(args.verdicts, "verdicts")) if args.verdicts and args.verdicts.exists() else read_verdicts(None)
        audit = load_json(args.audit, "audit")
        if audit is not None and not isinstance(audit, dict):
            raise ValueError("audit must be the JSON object diversity_audit.py writes")
        if args.cmd == "schedule":
            if not pool_ids:
                raise ValueError("schedule needs --pool or --ids")
            result = schedule(pool_ids, cards, verdicts, audit, args.k, args.rounds, args.seed)
            text = json.dumps(result, indent=2)
        else:
            result = score(pool_ids, cards, verdicts, audit, args.k, args.novelty_tier, args.selector,
                           args.lam, args.beta, args.fit_criterion, args.novelty_criterion)
            text = json.dumps(result, indent=2) if args.json else render(result)
        if args.output:
            args.output.write_text(json.dumps(result, indent=2))
        print(text)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(2, f"{error}\n")


if __name__ == "__main__":
    main()
