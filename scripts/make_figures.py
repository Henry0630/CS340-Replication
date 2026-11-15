#!/usr/bin/env python3
"""Generate the report figures from results/tables/*.csv.

Every number plotted here comes from the committed CSVs, so each figure is
traceable to a file in the repository. The paper's published values are
transcribed next to the CSVs for comparison and are labelled as such.

Usage:
    python scripts/make_figures.py [--output report/figures]
"""

import argparse
import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


# Paper values, transcribed from the published tables of
# "Understanding Real-World Concurrency Bugs in Go" (ASPLOS'19).
PAPER_T5 = {
    "Docker": (21, 23, 28, 16),
    "Kubernetes": (17, 17, 20, 14),
    "etcd": (21, 16, 18, 19),
    "CockroachDB": (12, 16, 23, 5),
    "gRPC": (11, 12, 12, 11),
    "BoltDB": (3, 2, 4, 1),
}
PAPER_T6 = {
    "Docker": (9, 0, 3, 5, 2, 2),
    "Kubernetes": (6, 2, 0, 3, 6, 0),
    "etcd": (5, 0, 0, 10, 5, 1),
    "CockroachDB": (4, 3, 0, 5, 0, 0),
    "gRPC": (2, 0, 0, 6, 2, 1),
    "BoltDB": (2, 0, 0, 0, 1, 0),
}

GREY = "#9aa0a6"      # paper
BLUE = "#1a73e8"      # ours
ORANGE = "#e8710a"
GREEN = "#188038"
PURPLE = "#9334e6"
RED = "#d93025"


def read_table(path):
    """Read a CSV into (header, rows) with the trailing Total row removed."""
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    header, body = rows[0], [r for r in rows[1:] if r and r[0] != "Total"]
    return header, body


def fig_taxonomy(csv_path, out_path):
    header, rows = read_table(csv_path)
    apps = [r[0] for r in rows]
    ours = {r[0]: tuple(int(x) for x in r[1:]) for r in rows}

    labels = ["blocking", "non-blocking", "shared memory", "message passing"]
    x = range(len(apps))
    width = 0.2

    fig, axes = plt.subplots(1, 4, figsize=(13.5, 3.6), sharey=False)
    for ax, col, label in zip(axes, range(4), labels):
        paper_vals = [PAPER_T5[a][col] for a in apps]
        our_vals = [ours[a][col] for a in apps]
        pos = list(x)
        ax.bar([p - width / 2 for p in pos], paper_vals, width,
               label="Paper", color=GREY)
        ax.bar([p + width / 2 for p in pos], our_vals, width,
               label="Ours", color=BLUE)
        ax.set_xticks(list(pos))
        ax.set_xticklabels(apps, rotation=35, ha="right", fontsize=8)
        ax.set_title(label, fontsize=10)
        ax.set_ylabel("bugs", fontsize=8)
        ax.grid(axis="y", alpha=0.3, linewidth=0.5)
        ax.set_axisbelow(True)
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        ax.tick_params(labelsize=8)
    axes[0].legend(fontsize=8, frameon=False, loc="upper right")
    fig.suptitle("Taxonomy per application: paper vs. ours "
                 "(169 commit-backed records)", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def fig_blocking_causes(csv_path, out_path):
    """Two panels: totals per application, and totals per cause category.

    Bars for the paper and for ours sit side by side so that the three
    differing cause cells are directly visible.
    """
    header, rows = read_table(csv_path)
    apps = [r[0] for r in rows]
    ours = {r[0]: [int(x) for x in r[1:7]] for r in rows}
    causes = ["Mutex", "RWMutex", "Wait", "Chan", "Chan w/", "Messaging Lib"]

    fig, (axl, axr) = plt.subplots(1, 2, figsize=(12.0, 4.3))

    # left: total cause assignments per application
    x = range(len(apps))
    width = 0.36
    paper_tot = [sum(PAPER_T6[a]) for a in apps]
    our_tot = [sum(ours[a]) for a in apps]
    axl.bar([p - width / 2 for p in x], paper_tot, width,
            label="Paper", color=GREY)
    axl.bar([p + width / 2 for p in x], our_tot, width,
            label="Ours", color=BLUE)
    axl.set_xticks(list(x))
    axl.set_xticklabels(apps, fontsize=8, rotation=30, ha="right")
    axl.set_ylabel("cause assignments", fontsize=9)
    axl.set_title("Per application", fontsize=10)
    axl.legend(fontsize=8, frameon=False)
    axl.grid(axis="y", alpha=0.3, linewidth=0.5)
    axl.set_axisbelow(True)

    # right: totals per cause category
    paper_c = [sum(PAPER_T6[a][i] for a in apps) for i in range(6)]
    our_c = [sum(ours[a][i] for a in apps) for i in range(6)]
    y = range(len(causes))
    axr.barh([p - width / 2 for p in y], paper_c, height=width,
             label="Paper", color=GREY)
    axr.barh([p + width / 2 for p in y], our_c, height=width,
             label="Ours", color=BLUE)
    axr.set_yticks(list(y))
    axr.set_yticklabels(causes, fontsize=9)
    axr.invert_yaxis()
    axr.set_xlabel("cause assignments", fontsize=9)
    axr.set_title("Per cause category", fontsize=10)
    axr.legend(fontsize=8, frameon=False)
    axr.grid(axis="x", alpha=0.3, linewidth=0.5)
    axr.set_axisbelow(True)

    for ax in (axl, axr):
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        ax.tick_params(labelsize=8)

    fig.suptitle("Causes of blocking bugs (paper Table 6 vs. ours)", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def fig_nontraditional(out_path, blocking_nt=54, nonblocking_nt=40,
                       total=169, blocking=83, nonblocking=86):
    """Same colour means the same category in both panels."""
    fig, axes = plt.subplots(1, 2, figsize=(9.0, 3.8))

    for ax, nt, tot, title in (
            (axes[0], blocking_nt, blocking, "Blocking"),
            (axes[1], nonblocking_nt, nonblocking, "Non-blocking")):
        ax.pie([nt, tot - nt], labels=["non-traditional", "traditional"],
               colors=[BLUE, GREY], autopct="%1.1f%%", startangle=90,
               textprops={"fontsize": 9})
        ax.set_title("%s: %d of %d non-traditional" % (title, nt, tot),
                     fontsize=10)

    fig.suptitle("Non-traditional label share: %d of %d records (%.1f%%)"
                 % (blocking_nt + nonblocking_nt, total,
                    100.0 * (blocking_nt + nonblocking_nt) / total),
                 fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.90))
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def fig_fix_strategies(csv_path, out_path):
    header, rows = read_table(csv_path)
    causes = [r[0] for r in rows]
    strategies = header[1:]

    fig, ax = plt.subplots(figsize=(9.0, 4.0))
    bottom = [0.0] * len(causes)
    palette = [BLUE, ORANGE, GREEN, PURPLE, RED]
    for i, strat in enumerate(strategies):
        vals = [float(r[1 + i]) for r in rows]
        ax.barh(causes, vals, left=bottom, label=strat,
                color=palette[i % len(palette)])
        bottom = [b + v for b, v in zip(bottom, vals)]
    ax.set_xlabel("blocking bugs (cause assignments)", fontsize=9)
    ax.set_title("Fix strategies for blocking bugs, grouped by cause "
                 "(paper Table 7)", fontsize=11)
    ax.legend(fontsize=8, frameon=False, ncol=5)
    ax.grid(axis="x", alpha=0.3, linewidth=0.5)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.tick_params(labelsize=9)
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    tables = os.path.join(root, "results", "tables")

    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default=os.path.join(root, "report", "figures"))
    args = ap.parse_args()
    os.makedirs(args.output, exist_ok=True)

    made = []
    made.append(("fig_taxonomy.png",
                 fig_taxonomy(os.path.join(tables, "table5.csv"),
                              os.path.join(args.output, "fig_taxonomy.png"))))
    made.append(("fig_blocking_causes.png",
                 fig_blocking_causes(os.path.join(tables, "table6.csv"),
                                     os.path.join(args.output,
                                                  "fig_blocking_causes.png"))))
    made.append(("fig_nontraditional.png",
                 fig_nontraditional(os.path.join(args.output,
                                                "fig_nontraditional.png"))))
    made.append(("fig_fix_strategies.png",
                 fig_fix_strategies(os.path.join(tables, "table7.csv"),
                                    os.path.join(args.output,
                                                 "fig_fix_strategies.png"))))
    for name, _ in made:
        print("wrote", os.path.join(args.output, name))


if __name__ == "__main__":
    main()