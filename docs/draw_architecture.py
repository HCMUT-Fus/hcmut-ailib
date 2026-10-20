"""Render docs/architecture.png (engineering block diagram). Run: python docs/draw_architecture.py"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

# Boxes are placed in three columns so that every cross-layer arrow is vertical.
LAYERS = [
    ("1  Ingestion Layer", "#e8f0fe", "#2a6fdb", {
        0: ("arXiv API\n(Atom feed, CC0 metadata)", "external"),
        1: ("src/ingest.py\nrate limit 1 request / 3 s\nclean + normalize", "module"),
        2: ("data/raw/\narxiv_sample_1000.json", "store"),
    }),
    ("2  Storage / Vector Index Layer", "#fdf0e6", "#e07b39", {
        0: ("ChromaDB (persistent)\ndata/processed/vector_index\nHNSW index, cosine", "store"),
        1: ("all-MiniLM-L6-v2\n384-d sentence embeddings\n(CPU)", "model"),
        2: ("src/indexer.py\nembed \"title. abstract\"\nin batches", "module"),
    }),
    ("3  Core Retrieval Engine", "#e9f6ee", "#3a9d5d", {
        0: ("src/search_engine.py\nANN top-k by cosine\nscore = (1 + cos) / 2", "module"),
        1: ("Metadata filters\nyear · category · author", "module"),
        2: ("Assistant helpers\ncitations (BibTeX/APA/IEEE)\nkeywords · find similar", "module"),
    }),
    ("4  Presentation Layer", "#f6eaf4", "#b8459b", {
        0: ("src/app.py (Streamlit)\nst.cache_resource keeps\nmodel + DB in memory", "module"),
        1: ("Researcher\n(web browser, localhost)", "external"),
    }),
]
STYLES = {"external": dict(ls="--", fc="white"), "store": dict(ls="-", fc="#fffbe6"),
          "model": dict(ls="-", fc="#ededed"), "module": dict(ls="-", fc="white")}
COLS = [0.8, 4.45, 8.1]
BOX_W, BOX_H = 3.1, 1.2
BAND_H, GAP, TOP = 1.85, 0.4, 8.9

fig, ax = plt.subplots(figsize=(12, 9.4), dpi=150)
ax.set_xlim(0, 12)
ax.set_ylim(-0.2, 10)
ax.axis("off")
ax.text(6, 9.65, "HCMUT-AILib — Engineering Block Diagram", ha="center", fontsize=16, weight="bold")
ax.text(6, 9.28, "Local-first, zero-cost semantic retrieval · 4-core CPU, 8 GB RAM, no GPU",
        ha="center", fontsize=10, color="#555")

boxes = []  # boxes[layer][column] -> (x, y)
for i, (name, fill, edge, cells) in enumerate(LAYERS):
    y0 = TOP - (i + 1) * BAND_H - i * GAP
    ax.add_patch(FancyBboxPatch((0.3, y0), 11.4, BAND_H, boxstyle="round,pad=0.02,rounding_size=0.15",
                                fc=fill, ec=edge, lw=1.5))
    ax.text(0.45, y0 + BAND_H - 0.2, name, fontsize=10.5, weight="bold", color=edge, va="center")
    row = {}
    for col, (label, kind) in cells.items():
        x, y = COLS[col], y0 + 0.15
        ax.add_patch(FancyBboxPatch((x, y), BOX_W, BOX_H, boxstyle="round,pad=0.02,rounding_size=0.1",
                                    ec=edge, lw=1.2, **STYLES[kind]))
        ax.text(x + BOX_W / 2, y + BOX_H / 2, label, ha="center", va="center", fontsize=8.6)
        row[col] = (x, y)
    boxes.append(row)


def anchor(layer, col, side, offset=0.0):
    x, y = boxes[layer][col]
    return {"left": (x, y + BOX_H / 2 + offset), "right": (x + BOX_W, y + BOX_H / 2 + offset),
            "top": (x + BOX_W / 2 + offset, y + BOX_H), "bottom": (x + BOX_W / 2 + offset, y)}[side]


def arrow(p, q, label=None, dashed=False, label_dx=0.08, label_dy=0.1, ha="left"):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=13, lw=1.2,
                                 color="#777" if dashed else "#333", ls="--" if dashed else "-"))
    if label:
        ax.text((p[0] + q[0]) / 2 + label_dx, (p[1] + q[1]) / 2 + label_dy, label, fontsize=7.6,
                color="#333", style="italic", ha=ha, va="center")


# Layer 1: fetch and store
arrow(anchor(0, 0, "right"), anchor(0, 1, "left"), "HTTPS", label_dx=-0.2)
arrow(anchor(0, 1, "right"), anchor(0, 2, "left"), "JSON", label_dx=-0.17)
# Layer 1 -> 2 -> index build (right to left)
arrow(anchor(0, 2, "bottom"), anchor(1, 2, "top"), "1,000 records", label_dy=0)
arrow(anchor(1, 2, "left"), anchor(1, 1, "right"), "encode", label_dx=-0.22)
arrow(anchor(1, 1, "left"), anchor(1, 0, "right"), "vectors", label_dx=-0.24)
# Query path
arrow(anchor(3, 1, "left", 0.2), anchor(3, 0, "right", 0.2), "query, filters", label_dx=-0.42)
arrow(anchor(3, 0, "right", -0.2), anchor(3, 1, "left", -0.2), "ranked paper cards",
      label_dx=-0.6, label_dy=-0.13)
arrow(anchor(3, 0, "top", -0.4), anchor(2, 0, "bottom", -0.4), "search()", label_dx=-0.1, ha="right")
arrow(anchor(2, 0, "bottom", 0.4), anchor(3, 0, "top", 0.4), "results", label_dx=0.1)
arrow(anchor(2, 0, "top", -0.4), anchor(1, 0, "bottom", -0.4), "ANN query", label_dx=-0.1, ha="right")
arrow(anchor(1, 0, "bottom", 0.4), anchor(2, 0, "top", 0.4), "neighbours", label_dx=0.1)
arrow(anchor(2, 0, "right"), anchor(2, 1, "left"))
arrow(anchor(2, 1, "right"), anchor(2, 2, "left"))
arrow(anchor(2, 1, "top"), anchor(1, 1, "bottom"), "embed query (same model)", dashed=True)

legend = [("dashed: external actor", "--", "white"), ("yellow: persistent data", "-", "#fffbe6"),
          ("grey: ML model", "-", "#ededed"), ("white: Python module", "-", "white")]
for i, (label, ls, fc) in enumerate(legend):
    x = 0.6 + i * 2.85
    ax.add_patch(FancyBboxPatch((x, -0.1), 0.35, 0.22, boxstyle="round,pad=0.01", ec="#555",
                                fc=fc, ls=ls))
    ax.text(x + 0.45, 0.01, label, fontsize=8, va="center")

out = Path(__file__).resolve().parent / "architecture.png"
fig.savefig(out, bbox_inches="tight", facecolor="white")
print(f"Saved {out}")
