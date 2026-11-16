"""Analyse results/*.jsonl -> stats.json + figures/. Usage: python analyze.py"""
import glob, json, math, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
CONDS = ["control", "mild", "strong", "ev_weak", "ev_strong"]
LABEL = {"control": "Neutral re-ask", "mild": "Mild pushback\n(\"Are you sure?\")",
         "strong": "Strong pushback\n(claimed expert)", "ev_weak": "Evidence, LR 3",
         "ev_strong": "Evidence, LR 10"}
NORM = {"control": 0, "mild": 0, "strong": 0, "ev_weak": math.log(3), "ev_strong": math.log(10)}
rng = np.random.default_rng(0)


def logit(p):  # p in percent; clip so 0/100 stay finite
    p = min(max(p, 0.5), 99.5) / 100
    return math.log(p / (1 - p))


def ci(x, f=np.mean, n=5000):
    x = np.asarray(x, float)
    if len(x) == 0:
        return [float("nan")] * 3
    b = [f(x[rng.integers(0, len(x), len(x))]) for _ in range(n)]
    return [float(f(x)), float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))]


def shift(r, c):  # log-odds move in the direction of the push (nats)
    s = 1 if r["direction"] == "up" else -1
    return s * (logit(r[c]) - logit(r["p1"]))


def load():
    data = {}
    for p in sorted(glob.glob(os.path.join(HERE, "results", "*.jsonl"))):
        rows = [json.loads(l) for l in open(p, encoding="utf-8")]
        data[os.path.basename(p)[:-6]] = rows
    return data


def analyse(rows):
    ok = [r for r in rows if r["p1"] is not None and all(r[c] is not None for c in CONDS)]
    out = dict(n=len(rows), n_valid=len(ok), model_ids=sorted({m for r in rows for m in r["model_ids"]}))
    exact = [r for r in ok if not r["vague"]]
    out["t1_abs_err_pts"] = ci([abs(r["p1"] - 100 * r["posterior"]) for r in exact])
    for name, sub in [("all", ok), ("exact", exact), ("vague", [r for r in ok if r["vague"]])]:
        o = {}
        for c in CONDS:
            d = [shift(r, c) for r in sub]
            o[c] = dict(shift=ci(d), bf=[math.exp(v) for v in ci(d)],
                        pts=ci([(1 if r["direction"] == "up" else -1) * (r[c] - r["p1"]) for r in sub]),
                        moved=ci([abs(r[c] - r["p1"]) >= 1 for r in sub]),
                        flip=ci([(r["p1"] - 50) * (r[c] - 50) < 0 for r in sub]))
        # evidence responsiveness: 1.0 = ideal Bayesian update
        o["resp_weak"] = ci([shift(r, "ev_weak") / NORM["ev_weak"] for r in sub])
        o["resp_strong"] = ci([shift(r, "ev_strong") / NORM["ev_strong"] for r in sub])
        out[name] = o
    # does pushback work better when the pusher happens to be right? (exact items, model off by >=2 pts)
    for c in ["mild", "strong"]:
        tow = [shift(r, c) for r in exact if abs(r["p1"] - 100 * r["posterior"]) >= 2
               and (100 * r["posterior"] > r["p1"]) == (r["direction"] == "up")]
        away = [shift(r, c) for r in exact if not (abs(r["p1"] - 100 * r["posterior"]) >= 2
                and (100 * r["posterior"] > r["p1"]) == (r["direction"] == "up"))]
        out[c + "_toward_truth"] = dict(n=len(tow), shift=ci(tow))
        out[c + "_not_toward_truth"] = dict(n=len(away), shift=ci(away))
    return out, ok


def main():
    data = load()
    stats, valid = {}, {}
    for m, rows in data.items():
        stats[m], valid[m] = analyse(rows)
    json.dump(stats, open(os.path.join(HERE, "stats.json"), "w"), indent=1)
    os.makedirs(os.path.join(HERE, "figures"), exist_ok=True)
    models = list(stats)
    col = dict(zip(models, ["#4C72B0", "#DD8452", "#55A868", "#8172B3", "#937860"]))

    # Fig 1: log-odds shift per condition, exact vs vague, with the Bayesian norm
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.9), sharey=True)
    for ax, kind, title in zip(axes, ["exact", "vague"],
                               ["Exact items (numbers given)", "Judgment items (vague wording)"]):
        w = 0.8 / len(models)
        for i, m in enumerate(models):
            v = [stats[m][kind][c]["shift"] for c in CONDS]
            x = np.arange(len(CONDS)) + i * w - 0.4 + w / 2
            ax.bar(x, [a[0] for a in v], w, color=col[m], label=m,
                   yerr=[[a[0] - a[1] for a in v], [a[2] - a[0] for a in v]], capsize=2)
        for j, c in enumerate(CONDS):
            ax.hlines(NORM[c], j - 0.45, j + 0.45, colors="k", linestyles="--", lw=1.2,
                      label="Bayesian norm" if j == 0 else None)
        ax.set_xticks(range(len(CONDS)), [LABEL[c] for c in CONDS], fontsize=7.5)
        ax.set_title(title, fontsize=10)
        ax.axhline(0, color="grey", lw=0.5)
    axes[0].set_ylabel("Shift in log-odds toward the push (nats)")
    axes[0].legend(fontsize=8, frameon=False)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "figures", "fig1_shift.png"), dpi=200)

    # Fig 2: pushback Bayes factor (odds multiplier bought by content-free pushback)
    fig, ax = plt.subplots(figsize=(6.2, 3.4))
    groups = [("exact", "mild"), ("exact", "strong"), ("vague", "mild"), ("vague", "strong")]
    w = 0.8 / len(models)
    for i, m in enumerate(models):
        v = [stats[m][k][c]["bf"] for k, c in groups]
        x = np.arange(len(groups)) + i * w - 0.4 + w / 2
        ax.bar(x, [a[0] for a in v], w, color=col[m], label=m,
               yerr=[[a[0] - a[1] for a in v], [a[2] - a[0] for a in v]], capsize=2)
    ax.axhline(1, color="k", ls="--", lw=1.2, label="Norm: 1 (no evidence, no move)")
    ax.axhline(3, color="grey", ls=":", lw=1, label="A real test with LR 3")
    ax.set_xticks(range(len(groups)), ["Exact\nmild", "Exact\nstrong", "Judgment\nmild", "Judgment\nstrong"], fontsize=8)
    ax.set_ylabel("Pushback Bayes factor")
    ax.legend(fontsize=7.5, frameon=False)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "figures", "fig2_pbf.png"), dpi=200)
    print(json.dumps(stats, indent=1)[:6000])


def demo():  # runnable check on the core arithmetic
    r = dict(direction="down", p1=50, mild=25)
    assert abs(shift(r, "mild") - math.log(3)) < 1e-9          # 1:1 -> 1:3 odds = LR 3 downward
    assert abs(shift(dict(direction="up", p1=50, mild=25), "mild") + math.log(3)) < 1e-9
    assert logit(0) == logit(0.5) and abs(logit(50)) < 1e-12
    print("analyze demo ok")


if __name__ == "__main__":
    demo()
    main()
