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

2.0-full additions (all optional, the 1.x and 2.0-lean outputs are unchanged):
  --kernel composite   score on the multi-view kernel from the research blueprint:
                       0.45 mechanism (BM25 unigram+bigram cosine blended with
                       char-trigram cosine) + 0.35 assumption-set Jaccard +
                       0.20 causal-slot Jaccard (slots, actor, trigger, frame).
                       The default "lean" kernel reproduces 2.0-lean exactly.
  --prev-wave FILE     earlier wave's cards, for a wave-to-wave beta-Vendi gain
  --embeddings FILE    optional {id: [floats]} blended into the mechanism view
  --output FILE        write the full artifact (with the similarity matrix for
                       tournament.py) and print a compact summary instead
  --matrix             include the similarity matrix in stdout output

Extra input keys accepted: mechanism_signature (used as the mechanism when
"mechanism" is absent, otherwise as the causal path), assumptions (list of
"works only if" items), assumption, slots ({lever_type, primary_actor,
rule_modified, delivery_channel, ...}), actor, trigger, frame, frame_id,
sketch_draft (used when "sketch" is absent), tier_intent, worker_operator.
The input may also be {"candidates": [...]} instead of a bare list.

Extra output keys: kernel, status (COLLAPSE_ALERT / OK / TOO_FEW, from the
pool-size calibrated thresholds), flags, n_candidates, vendi_score,
diversity_efficiency, collapse_warning, vendi_profile (order-q Vendi at
q = 0.5, 1, 2 and infinity, dominant spectral share, surface disguise ratio,
beta-Vendi), clusters (complete linkage), mechanism_clusters,
shared_assumption_alerts, highest_overlap_pairs, lowest_marginal_diversity,
taboo_repair_cards, item_metrics (leave-one-out Vendi anomaly scores and
structural wildcards).
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


def _text(row, key, cid):
    value = row.get(key, "")
    if not isinstance(value, str):
        raise ValueError(f"{cid}: {key} must be text")
    return value


def normalize(rows):
    if isinstance(rows, dict) and "candidates" in rows:
        rows = rows["candidates"]
    if not isinstance(rows, list) or not rows:
        raise ValueError("expected a nonempty list of candidates")
    seen, out = set(), []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("each candidate needs a text id, mechanism and sketch")
        # 2.0-full schema aliases: mechanism_signature and sketch_draft stand in when
        # the lean keys are absent, so lean inputs are read exactly as before.
        mech_key = "mechanism" if "mechanism" in row else "mechanism_signature"
        sketch_key = "sketch" if "sketch" in row else "sketch_draft"
        if any(not isinstance(row.get(k), str) or not row[k].strip() for k in ("id", mech_key, sketch_key)):
            raise ValueError("each candidate needs a text id, mechanism and sketch")
        key = row["id"].strip()
        if key in seen:
            raise ValueError(f"duplicate candidate id {key}")
        seen.add(key)
        for k in ("title", "how", "depends_on", "changes", "grounded_in", "assumption", "actor",
                  "trigger", "frame", "frame_id", "tier_intent", "worker_operator", "mechanism_signature"):
            _text(row, k, key)
        assumptions = row.get("assumptions", [])
        if not isinstance(assumptions, list) or any(not isinstance(a, str) for a in assumptions):
            raise ValueError(f"{key}: assumptions must be a list of text")
        slots = row.get("slots", {})
        if not isinstance(slots, dict) or any(not isinstance(v, str) for v in slots.values()):
            raise ValueError(f"{key}: slots must map names to text")
        label = " ".join(row[mech_key].casefold().split())
        how_text = row.get("how", "")
        if mech_key == "mechanism" and "mechanism_signature" in row:
            how_text = (how_text + " " + row["mechanism_signature"]).strip()
        dep_text = " ".join([row.get("depends_on", ""), row.get("assumption", "")] + assumptions).strip()
        slot_set = {f"{k.casefold()}:{' '.join(v.casefold().split())}" for k, v in slots.items() if v.strip()}
        for k in ("actor", "trigger"):
            if row.get(k, "").strip():
                slot_set.add(f"{k}:{' '.join(row[k].casefold().split())}")
        frame = row.get("frame", "") or row.get("frame_id", "")
        if frame.strip():
            slot_set.add(f"frame:{' '.join(frame.casefold().split())}")
        out.append(
            {
                "id": key,
                "label": label,
                "label_tokens": tokens(label),
                "how": tokens(how_text),
                "depends_on": tokens(dep_text),
                "changes": tokens(row.get("changes", "")),
                "sketch": tokens(row[sketch_key]),
                "has_grounding_field": "grounded_in" in row,
                "grounded": bool(row.get("grounded_in", "").strip()),
                # Raw text for the composite kernel.
                "mech_text": (label + " " + how_text).strip(),
                "sketch_text": row[sketch_key],
                "dep_text": dep_text,
                "slot_set": slot_set,
                "tier_intent": row.get("tier_intent", ""),
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


# ---------------------------------------------------------------------------
# 2.0-full: multi-view composite kernel, order-q Vendi, leave-one-out anomaly
# scores, complete-linkage clusters, beta-Vendi and calibrated collapse rules.
# ---------------------------------------------------------------------------

# (pool size floor, VS1/n floor, VS_inf ceiling, dominant cluster share, taboo cards)
CALIBRATION = ((25, 0.32, 2.8, 0.30, 2), (15, 0.42, 2.5, 0.35, 2), (0, 0.55, 2.2, 0.40, 1))
COMPOSITE = {"mechanism": 0.45, "assumption": 0.35, "slot": 0.20}


def term_list(text):
    words = [stem(w) for w in re.findall(r"[a-z0-9]+", text.casefold()) if w not in STOP]
    return words + [a + "_" + b for a, b in zip(words, words[1:])]


def unit(vec):
    norm = sqrt(sum(v * v for v in vec.values()))
    return {k: v / norm for k, v in vec.items()} if norm else {}


def bm25_vectors(docs, k1=1.2, b=0.75):
    n = len(docs)
    df = Counter(t for d in docs for t in set(d))
    avg = (sum(len(d) for d in docs) / n) or 1.0
    out = []
    for d in docs:
        tf = Counter(d)
        out.append(unit({
            t: log(1 + (n - df[t] + 0.5) / (df[t] + 0.5)) * c * (k1 + 1) / (c + k1 * (1 - b + b * len(d) / avg))
            for t, c in tf.items()
        }))
    return out


def trigram_vectors(texts):
    grams = []
    for text in texts:
        g = Counter()
        for w in re.findall(r"[a-z0-9]+", text.casefold()):
            if w in STOP:
                continue
            padded = f"#{w}#"
            g.update(padded[i:i + 3] for i in range(len(padded) - 2))
        grams.append(g)
    n = len(texts)
    df = Counter(t for g in grams for t in g)
    return [unit({t: c * (log((1 + n) / (1 + df[t])) + 1) for t, c in g.items()}) for g in grams]


def cosine_gram(vecs):
    n = len(vecs)
    return [[1.0 if i == j else sum(v * vecs[j].get(t, 0.0) for t, v in vecs[i].items()) for j in range(n)] for i in range(n)]


def jaccard_gram(sets):
    n = len(sets)
    return [[1.0 if i == j else jaccard(sets[i], sets[j]) for j in range(n)] for i in range(n)]


def composite_kernel(items, embeddings=None):
    """K = 0.45 K_mech + 0.35 K_assumption + 0.20 K_slot, weights renormalized over views the pool has.

    Every view is a unit-diagonal PSD Gram or Jaccard kernel, and weights are global (never per pair),
    so the convex mix stays PSD. Cards without slots fall back to their "changes" words as the slot view.
    """
    docs = [term_list(r["mech_text"]) for r in items]
    k_mech = cosine_gram(bm25_vectors(docs))
    k_tri = cosine_gram(trigram_vectors([r["mech_text"] for r in items]))
    n = len(items)
    mech = [[0.5 * k_mech[i][j] + 0.5 * k_tri[i][j] for j in range(n)] for i in range(n)]
    if embeddings:
        vecs = []
        for r in items:
            e = embeddings.get(r["id"])
            if not isinstance(e, list) or not e or any(type(x) not in (int, float) for x in e):
                raise ValueError(f"embeddings need a list of numbers for {r['id']}")
            vecs.append(unit(dict(enumerate(e))))
        k_emb = cosine_gram(vecs)
        # max(0, cos) as in the blueprint; any tiny negative eigenvalue is clipped by the Vendi step.
        mech = [[0.5 * mech[i][j] + 0.5 * max(0.0, k_emb[i][j]) for j in range(n)] for i in range(n)]
    views = {"mechanism": mech}
    if any(r["depends_on"] for r in items):
        views["assumption"] = jaccard_gram([r["depends_on"] for r in items])
    slot_sets = [r["slot_set"] for r in items]
    if not any(slot_sets):
        slot_sets = [{"change:" + t for t in r["changes"]} for r in items]
    if any(slot_sets):
        views["slot"] = jaccard_gram(slot_sets)
    total = sum(COMPOSITE[v] for v in views)
    matrix = [[sum(COMPOSITE[v] * views[v][i][j] for v in views) / total for j in range(n)] for i in range(n)]
    return matrix, views


def lean_views(items):
    n = len(items)
    views = {}
    for field in FIELDS:
        rows = [[0.0] * n for _ in range(n)]
        for i, j in combinations(range(n), 2):
            a, b = items[i], items[j]
            if field == "label":
                v = 0.5 * (a["label"] == b["label"]) + 0.5 * jaccard(a["label_tokens"], b["label_tokens"])
            else:
                v = jaccard(a[field], b[field])
            rows[i][j] = rows[j][i] = v
        views[field] = rows
    return views


def spectrum(matrix):
    n = len(matrix)
    if n == 1:
        return [1.0]
    lams = [max(l / n, 0.0) for l in eigenvalues(matrix)]
    s = sum(lams) or 1.0
    return [l / s for l in lams if l / s > 1e-12]


def vendi_q(p, q):
    """Order-q Vendi score from normalized eigenvalues p."""
    if q == "inf":
        return 1.0 / max(p)
    if q == 1:
        return exp(-sum(x * log(x) for x in p))
    return sum(x ** q for x in p) ** (1.0 / (1.0 - q))


def complete_linkage(ids, matrix, floor):
    groups = [[k] for k in range(len(ids))]
    while True:
        best, pair = floor, None
        for a, b in combinations(range(len(groups)), 2):
            link = min(matrix[i][j] for i in groups[a] for j in groups[b])
            if link >= best:
                best, pair = link, (a, b)
        if pair is None:
            break
        a, b = pair
        groups[a] += groups.pop(b)
    return sorted(groups, key=lambda g: (-len(g), min(g)))


def full_metrics(items, matrix, views, prev_items=None, kernel="lean", embeddings=None, lean_collapse=None, dominant_labels=()):
    ids = [r["id"] for r in items]
    by_id = {r["id"]: r for r in items}
    n = len(items)
    p = spectrum(matrix)
    vs = {q: vendi_q(p, q) for q in (0.5, 1, 2, "inf")}

    # Leave-one-out Vendi anomaly scores (VAS-LOO).
    loo = []
    for k in range(n):
        if n <= 2:
            loo.append((0.0, 0.0))
            continue
        keep = [i for i in range(n) if i != k]
        pk = spectrum([[matrix[i][j] for j in keep] for i in keep])
        loo.append((vs[1] - vendi_q(pk, 1), vs[0.5] - vendi_q(pk, 0.5)))
    deltas = sorted(d for d, _ in loo)
    quartile = deltas[n - max(1, n // 4)] if n >= 4 else float("inf")

    # Complete-linkage clusters (no single-linkage chaining).
    groups = complete_linkage(ids, matrix, 0.55)
    cluster_of, cluster_rows = {}, []
    for c, g in enumerate(groups):
        members = [ids[k] for k in g]
        for m in members:
            cluster_of[m] = f"C{c}"
        rep = max(g, key=lambda k: (sum(matrix[k][j] for j in g), -k))
        common_dep = set.intersection(*(by_id[m]["depends_on"] for m in members)) if members else set()
        slot_counts = Counter(s for m in members for s in by_id[m]["slot_set"])
        cluster_rows.append({
            "cluster_id": f"C{c}",
            "member_ids": members,
            "share": round(len(members) / n, 3),
            "representative_id": ids[rep],
            "shared_assumptions": sorted(common_dep) if len(members) > 1 else [],
            "dominant_slots": dict(sorted(s.split(":", 1) for s, c2 in slot_counts.items() if c2 > len(members) / 2))
            if len(members) > 1 else {},
        })

    item_metrics = []
    for k, r in enumerate(items):
        d1, d05 = loo[k]
        mean_sim = sum(matrix[k][j] for j in range(n) if j != k) / (n - 1) if n > 1 else 0.0
        item_metrics.append({
            "id": r["id"], "cluster_id": cluster_of[r["id"]], "delta_vs_1": round(d1, 3),
            "delta_vs_05": round(d05, 3), "mean_similarity": round(mean_sim, 3),
            "structural_wildcard": n >= 4 and d1 >= quartile and d1 > 0.25,
        })

    # Shared assumption alerts: single linkage above 0.45 covering more than 35% of the pool.
    dep_ids = [i for i in ids if by_id[i]["depends_on"]]
    dep_sim = {(a, b): jaccard(by_id[a]["depends_on"], by_id[b]["depends_on"]) for a in dep_ids for b in dep_ids if a != b}
    alerts = [
        {"cluster": g, "share": round(len(g) / n, 3), "sample_assumption": by_id[g[0]]["dep_text"]}
        for g in clusters(dep_ids, dep_sim, 0.45) if len(g) / n > 0.35
    ]

    # Highest-overlap pairs and the views they share.
    pairs = sorted(combinations(range(n), 2), key=lambda ij: (-matrix[ij[0]][ij[1]], ij))[:3]
    overlap = [
        {"pair": [ids[i], ids[j]], "sim": round(matrix[i][j], 3),
         "shared_slots": [v for v in views if views[v][i][j] >= 0.5]}
        for i, j in pairs
    ]

    # Surface disguise ratio: BM25 Vendi on the sketch prose over Vendi on the mechanism kernel.
    surf = cosine_gram(bm25_vectors([term_list(r["sketch_text"]) for r in items]))
    surface_vs1 = vendi_q(spectrum(surf), 1)
    disguise = surface_vs1 / vs[1]

    # Pool-size calibrated collapse rule.
    floor_n, eff_floor, inf_ceiling, share_alert, max_cards = next(c for c in CALIBRATION if n >= c[0])
    flags = []
    status = "TOO_FEW" if n < 4 else "OK"
    if n >= 4:
        if vs[1] / n < eff_floor:
            flags.append(f"VS1/n {vs[1] / n:.2f} below the {eff_floor} floor for this pool size")
        if vs["inf"] < inf_ceiling:
            flags.append(f"VS_inf {vs['inf']:.2f} below {inf_ceiling}: one mode holds {1 / vs['inf']:.0%} of the spectrum")
        if groups and len(groups[0]) / n > share_alert:
            flags.append(f"cluster C0 holds {len(groups[0]) / n:.0%} of the pool (alert above {share_alert:.0%})")
        if lean_collapse:
            flags.append(lean_collapse)
        if flags:
            status = "COLLAPSE_ALERT"
        if disguise > 2.0:
            flags.append(f"surface disguise ratio {disguise:.2f}: sketches vary far more than mechanisms")

    taboo_cards, used = [], set()
    if status == "COLLAPSE_ALERT":
        # Dominant labels first (over 40% of the pool), then the biggest complete-linkage clusters.
        for label in dominant_labels:
            members = [r["id"] for r in items if r["label"] == label]
            common = set.intersection(*(by_id[m]["depends_on"] for m in members))
            summary = label + (" | assumes {" + ", ".join(sorted(common)[:6]) + "}" if common else "")
            taboo_cards.append({"target_cluster": cluster_of[members[0]], "banned_pathway_summary": summary,
                                "example_ids": members[:2], "max_allowed_overlap": 1})
            used.add(label)
        for row in [c for c in cluster_rows if len(c["member_ids"]) > 1]:
            label = Counter(by_id[m]["label"] for m in row["member_ids"]).most_common(1)[0][0]
            if label in used:
                continue
            used.add(label)
            parts = [label]
            if row["dominant_slots"]:
                parts.append("via " + ", ".join(f"{k}={v}" for k, v in row["dominant_slots"].items()))
            if row["shared_assumptions"]:
                parts.append("| assumes {" + ", ".join(row["shared_assumptions"][:6]) + "}")
            taboo_cards.append({"target_cluster": row["cluster_id"], "banned_pathway_summary": " ".join(parts),
                                "example_ids": row["member_ids"][:2], "max_allowed_overlap": 1})
        taboo_cards = taboo_cards[:max_cards]

    beta = None
    if prev_items is not None:
        clash = set(ids) & {r["id"] for r in prev_items}
        if clash:
            raise ValueError(f"--prev-wave repeats ids from this wave: {sorted(clash)[:3]}")
        union = prev_items + items
        if kernel == "composite":
            um, _ = composite_kernel(union, embeddings)
        else:
            m = len(union)
            um = [[1.0 if i == j else similarity(union[i], union[j]) for j in range(m)] for i in range(m)]
        m1 = len(prev_items)
        sub = lambda rng: [[um[i][j] for j in rng] for i in rng]
        v_u = vendi_q(spectrum(um), 1)
        v1 = vendi_q(spectrum(sub(range(m1))), 1)
        v2 = vendi_q(spectrum(sub(range(m1, len(union)))), 1)
        beta = v_u - (m1 / len(union)) * v1 - (n / len(union)) * v2
        if beta < 0.5:
            flags.append(f"STAGNANT_WAVE2: beta-Vendi {beta:.2f} below 0.50, wave two added little new ground")

    ranked = sorted(item_metrics, key=lambda r: (r["delta_vs_1"], r["id"]))
    return {
        "kernel": kernel,
        "status": status,
        "flags": flags,
        "n_candidates": n,
        "vendi_score": round(vs[1], 2),
        "diversity_efficiency": round(vs[1] / n, 3),
        "collapse_warning": status == "COLLAPSE_ALERT",
        "vendi_profile": {
            "vs_05": round(vs[0.5], 3), "vs_1": round(vs[1], 3), "vs_2": round(vs[2], 3), "vs_inf": round(vs["inf"], 3),
            "vs_1_ratio": round(vs[1] / n, 3), "dominant_spectral_share": round(1 / vs["inf"], 3),
            "surface_vs_1": round(surface_vs1, 3), "surface_disguise_ratio": round(disguise, 2),
            "beta_vendi_vs_prev_wave": None if beta is None else round(beta, 3),
        },
        "clusters": cluster_rows,
        "mechanism_clusters": [c["member_ids"] for c in cluster_rows if len(c["member_ids"]) > 1],
        "shared_assumption_alerts": alerts,
        "highest_overlap_pairs": overlap,
        "lowest_marginal_diversity": [r["id"] for r in ranked[:2]] if n > 2 else [],
        "taboo_repair_cards": taboo_cards,
        "item_metrics": item_metrics,
        "similarity_matrix": {"ids": ids, "K_composite": [[round(x, 4) for x in row] for row in matrix]},
    }


def audit(rows, threshold=0.5, kernel="lean", prev_rows=None, embeddings=None, include_matrix=False):
    if kernel not in ("lean", "composite"):
        raise ValueError("kernel must be lean or composite")
    items = normalize(rows)
    ids = [r["id"] for r in items]
    by_id = {r["id"]: r for r in items}
    n = len(items)
    sim = {}
    if kernel == "composite":
        matrix, views = composite_kernel(items, embeddings)
        for i, j in combinations(range(n), 2):
            sim[(ids[i], ids[j])] = sim[(ids[j], ids[i])] = matrix[i][j]
    else:
        matrix = [[1.0] * n for _ in range(n)]
        for i, j in combinations(range(n), 2):
            value = similarity(items[i], items[j])
            matrix[i][j] = matrix[j][i] = value
            sim[(ids[i], ids[j])] = sim[(ids[j], ids[i])] = value
        views = lean_views(items)

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
    prev_items = normalize(prev_rows) if prev_rows is not None else None
    lean_collapse = None
    if collapsed:
        lean_collapse = ("a mechanism label covers over 40% of the pool" if dominant else
                         "Vendi ratio below 0.5" if ratio < 0.5 else "a near-duplicate cluster holds 25% or more")
    extra = full_metrics(items, matrix, views, prev_items, kernel, embeddings, lean_collapse, dominant)
    if not include_matrix:
        extra.pop("similarity_matrix")
    result = {
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
    result.update(extra)
    return result



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pool", type=Path, nargs="?", help="cards JSON (list or {\"candidates\": [...]})")
    parser.add_argument("--input", type=Path, help="same as the positional pool argument")
    parser.add_argument("--threshold", type=float, default=0.5, help="cluster similarity cutoff (default 0.5)")
    parser.add_argument("--kernel", choices=("lean", "composite"), default="lean",
                        help="lean (2.0-lean field mix, default) or composite (multi-view research kernel)")
    parser.add_argument("--prev-wave", type=Path, help="earlier wave's cards, for beta-Vendi")
    parser.add_argument("--embeddings", type=Path, help="optional {id: [floats]} blended into the mechanism view")
    parser.add_argument("--output", type=Path, help="write the full artifact here and print a compact summary")
    parser.add_argument("--matrix", action="store_true", help="include the similarity matrix in stdout output")
    args = parser.parse_args()
    try:
        path = args.input or args.pool
        if path is None:
            raise ValueError("give the pool file as an argument or with --input")
        prev = json.loads(args.prev_wave.read_text()) if args.prev_wave else None
        emb = json.loads(args.embeddings.read_text()) if args.embeddings else None
        if emb is not None and not isinstance(emb, dict):
            raise ValueError("embeddings must map ids to lists of numbers")
        report = audit(json.loads(path.read_text()), args.threshold, args.kernel, prev, emb,
                       include_matrix=bool(args.output or args.matrix))
        if args.output:
            args.output.write_text(json.dumps(report, indent=2))
            keep = ("status", "flags", "kernel", "n_candidates", "vendi_score", "diversity_efficiency", "verdict",
                    "mechanism_clusters", "shared_assumption_alerts", "taboo_repair_cards", "missing_grounding")
            summary = {k: report[k] for k in keep}
            summary["structural_wildcards"] = [m["id"] for m in report["item_metrics"] if m["structural_wildcard"]]
            summary["full_report"] = str(args.output)
            print(json.dumps(summary, indent=2))
        else:
            print(json.dumps(report, indent=2))
    except (OSError, ValueError) as error:
        parser.exit(2, f"{error}\n")
