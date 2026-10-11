# Required Notice: Copyright Matthew Armstrong (https://github.com/The-Dorkknight)
# Licensed under the PolyForm Noncommercial License 1.0.0. No warranty.
"""Draw the hardpoint STL illustrations in docs/images/ from real data.

    python tools/make_illustrations.py

The part pictures are drawn from an actual hardpoint STL: a CAD solid is built with
OpenCASCADE (tests/cadparts.py), written with src/hstl.py, read back with its reference
reader, and coloured by what the file says. The chart uses the numbers measured for
DESIGN_NOTES.md.

Needs cadquery-ocp, numpy plus matplotlib and Pillow (not needed to run the app).
"""
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "tests"))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle  # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # noqa: E402
from PIL import Image  # noqa: E402

import cadparts  # noqa: E402
import hstl  # noqa: E402

OUT = os.path.join(ROOT, "docs", "images")
SURFACE, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"     # first three categorical slots (validated all-pairs)
SOFT_BLUE, SOFT_ORANGE = "#cde2fb", "#fbd9cb"
MESH_GREY = "#b9bcc4"
REC = np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])

# Measured 4 Oct 2026 (Classic fitter, default settings): STEP faces from the plain STL, from
# the hardpoint STL, and faces in the original CAD model. See DESIGN_NOTES.md, "Measured results".
RESULTS = [("Bracket, 0.05 mm mesh", 21, 17, 16),
           ("Bracket, coarse 0.3 mm mesh", 90, 29, 16),
           ("Knob (cylinder, sphere, rounded edge)", 1103, 8, 4)]

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "text.color": INK,
                     "axes.edgecolor": AXIS, "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": INK2})


def save(fig, name, dpi=160):
    png = os.path.join(tempfile.gettempdir(), name + ".png")
    fig.savefig(png, dpi=dpi, facecolor=SURFACE)
    plt.close(fig)
    Image.open(png).convert("RGB").save(os.path.join(OUT, name + ".webp"), "WEBP", lossless=True)
    os.remove(png)
    print("wrote docs/images/" + name + ".webp")


def shade(rgb, normals, light=(0.35, -0.5, 0.8)):
    light = np.asarray(light) / np.linalg.norm(light)
    k = 0.55 + 0.45 * np.clip(normals @ light, 0, 1)
    return np.clip(np.asarray(rgb)[None, :] * k[:, None] if np.ndim(rgb) == 1 else np.asarray(rgb) * k[:, None], 0, 1)


def hex_rgb(h):
    return np.array([int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)])


def draw_part(ax, tri, colours, edges=False, elev=32, azim=-58):
    v0, v1, v2 = tri[:, 0], tri[:, 1], tri[:, 2]
    n = np.cross(v1 - v0, v2 - v0)
    n /= np.maximum(np.linalg.norm(n, axis=1), 1e-12)[:, None]
    # only triangles that face the viewer: hidden ones would show through (matplotlib
    # paints back to front by triangle centre, which is not exact)
    e, a = np.radians(elev), np.radians(azim)
    front = n @ np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)]) > 0
    full = tri
    tri, n, colours = tri[front], n[front], np.asarray(colours)[front]
    pc = Poly3DCollection(tri, facecolors=shade(colours, n), linewidths=0.35 if edges else 0.0,
                          edgecolors="#5b5f68" if edges else shade(colours, n))
    if not edges:
        pc.set_antialiased(False)
    ax.add_collection3d(pc)
    lo, hi = full.reshape(-1, 3).min(0), full.reshape(-1, 3).max(0)
    ax.set_xlim(lo[0], hi[0]); ax.set_ylim(lo[1], hi[1]); ax.set_zlim(lo[2], hi[2])
    ax.set_box_aspect(hi - lo, zoom=1.02)
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()


def part_figure():
    """One real hardpoint STL, drawn three ways."""
    c, t, tf, ftype, hard = cadparts.tessellate(cadparts.bracket(), 0.05, 15.0)
    data, info = hstl.encode(c, t, tf, ftype, hard, units="mm", tol=0.05, angle=15, by="illustration")
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "bracket.stl")
        open(p, "wb").write(data)
        doc = hstl.read(p)
    dec = hstl.decode(doc)
    arr = np.frombuffer(doc["facets"], REC)
    tri = arr["v"].astype(float)
    col_idx = arr["a"] & 0x1F
    typ = (arr["a"] >> 8) & 7

    fig = plt.figure(figsize=(13.5, 4.5))
    fig.patch.set_facecolor(SURFACE)
    titles = ["1. What a slicer sees", "2. Face colours stored in the file", "3. Surface types and hardpoints"]
    subs = [f"{len(tri):,} triangles. The labels are in bytes it ignores.",
            f"{len(dec['type'])} faces told apart with {info['colours']} colours:\nfaces that touch never share one.",
            "Each face says what it is. Dots are the CAD corners\n(all 25 shown, including those on the far side)."]
    palette = [hex_rgb(BLUE), hex_rgb(ORANGE), hex_rgb(AQUA)]
    tcol = {hstl.T_PLANE: hex_rgb(BLUE), hstl.T_CYL: hex_rgb(AQUA), hstl.T_CONE: hex_rgb(ORANGE)}
    for k in range(3):
        ax = fig.add_axes([0.005 + 0.333 * k, 0.0, 0.325, 0.86], projection="3d", computed_zorder=False)
        ax.set_facecolor(SURFACE)
        if k == 0:
            draw_part(ax, tri, np.tile(hex_rgb(MESH_GREY), (len(tri), 1)), edges=True)
        elif k == 1:
            draw_part(ax, tri, np.array([palette[i % 3] for i in col_idx]))
        else:
            draw_part(ax, tri, np.array([tcol.get(int(x), hex_rgb(MESH_GREY)) for x in typ]))
            hp = np.array(dec["hardpoints"])
            ax.scatter(hp[:, 0], hp[:, 1], hp[:, 2], s=34, c=INK, edgecolors=SURFACE, linewidths=1.3,
                       depthshade=False, zorder=10)
        fig.text(0.02 + 0.333 * k, 0.93, titles[k], fontsize=14, fontweight="bold", color=INK)
        fig.text(0.02 + 0.333 * k, 0.905, subs[k], fontsize=10.5, color=INK2, va="top")
    # legends
    def key(x, y, colour, text):
        fig.patches.append(Rectangle((x, y), 0.012, 0.022, transform=fig.transFigure, color=colour))
        fig.text(x + 0.017, y + 0.011, text, fontsize=10, color=INK2, va="center")
    for i, (colour, text) in enumerate(((BLUE, "colour 0"), (ORANGE, "colour 1"), (AQUA, "colour 2"))):
        key(0.36 + 0.085 * i, 0.03, colour, text)
    for i, (colour, text) in enumerate(((BLUE, "plane"), (AQUA, "cylinder"), (ORANGE, "cone"))):
        key(0.69 + 0.075 * i, 0.03, colour, text)
    fig.text(0.925, 0.041, "●  hardpoint", fontsize=10, color=INK2, va="center")
    save(fig, "hardpoint-part")


def layout_figure():
    """Where the labels live in a binary STL."""
    fig, ax = plt.subplots(figsize=(13.5, 6.6))
    fig.patch.set_facecolor(SURFACE)
    ax.set_xlim(0, 100); ax.set_ylim(0, 60); ax.axis("off")
    ax.set_position([0.02, 0.02, 0.96, 0.96])

    def box(x, y, w, h, text, fill=SURFACE, sub=None, bold=False, fs=10.5):
        ax.add_patch(Rectangle((x, y), w, h, facecolor=fill, edgecolor=INK2, linewidth=1.0))
        ax.text(x + w / 2, y + h / 2 + (0.9 if sub else 0), text, ha="center", va="center", fontsize=fs,
                fontweight="bold" if bold else "normal", color=INK)
        if sub:
            ax.text(x + w / 2, y + h / 2 - 1.3, sub, ha="center", va="center", fontsize=9, color=INK2)

    ax.text(1, 57.5, "Where the labels live", fontsize=15, fontweight="bold")
    ax.text(1, 54.6, "A binary STL, byte for byte. Shaded = bytes every STL already has and slicers ignore. "
                     "Nothing is added to the file.", fontsize=10.5, color=INK2)

    # row 1: the file
    y = 44
    ax.text(1, y + 7.2, "The file", fontsize=11, fontweight="bold", color=INK2)
    box(1, y, 20, 6, "Header", SOFT_BLUE, "80 bytes", bold=True)
    box(21, y, 9, 6, "Count", sub="4 bytes")
    box(30, y, 17, 6, "Triangle 1", sub="50 bytes")
    box(47, y, 17, 6, "Triangle 2", sub="50 bytes")
    box(64, y, 17, 6, "Triangle 3", sub="50 bytes")
    box(81, y, 18, 6, "…  Triangle n", sub="50 bytes each")
    ax.text(1, y - 2.2, "HARDPOINT-STL 1 u=mm tol=0.05 ang=15 crc=1a2b3c4d by=freecad", family="DejaVu Sans Mono",
            fontsize=10, color=INK)
    ax.text(1, y - 4.6, "marker and version · units · mesh tolerance and angle · checksum of the triangles · who wrote it",
            fontsize=9.5, color=INK2)

    # row 2: one triangle
    y2 = 26
    ax.plot([30, 20], [y, y2 + 6], color=AXIS, lw=1); ax.plot([47, 86], [y, y2 + 6], color=AXIS, lw=1)
    ax.text(1, y2 + 2.4, "One triangle", fontsize=11, fontweight="bold", color=INK2)
    box(20, y2, 15, 6, "Normal", sub="12 bytes")
    box(35, y2, 15, 6, "Corner 1", sub="12 bytes")
    box(50, y2, 15, 6, "Corner 2", sub="12 bytes")
    box(65, y2, 15, 6, "Corner 3", sub="12 bytes")
    box(80, y2, 6, 6, "Attr.", SOFT_ORANGE, "2 bytes", bold=True, fs=9.5)

    # row 3: the 16 bits
    y3, bw, x0 = 8, 5.6, 5.5
    ax.plot([80, x0], [y2, y3 + 6.5], color=AXIS, lw=1); ax.plot([86, x0 + 16 * bw], [y2, y3 + 6.5], color=AXIS, lw=1)
    ax.text(1, y3 + 10.2, "The 2 attribute bytes, bit by bit", fontsize=11, fontweight="bold", color=INK2,
            bbox=dict(facecolor=SURFACE, edgecolor="none", pad=2.5))
    groups = [(15, 15, "0", "always 0", SURFACE), (14, 14, "0", "spare", SURFACE),
              (13, 11, "c3 c2 c1", "hardpoint flags:\nis corner 3 / 2 / 1\na CAD vertex?", SOFT_ORANGE),
              (10, 8, "type", "surface type:\nplane, cylinder, sphere,\ncone, torus, freeform…", SOFT_ORANGE),
              (7, 7, "1", "labelled", SOFT_ORANGE), (6, 5, "0 0", "spare", SURFACE),
              (4, 0, "face colour", "which face: 0 to 31.\nFaces that touch\nnever share a colour", SOFT_ORANGE)]
    for hi, lo, text, note, fill in groups:
        x = x0 + (15 - hi) * bw
        w = (hi - lo + 1) * bw
        ax.add_patch(Rectangle((x, y3), w, 6, facecolor=fill, edgecolor=INK2, linewidth=1.0))
        ax.text(x + w / 2, y3 + 3, text, ha="center", va="center", fontsize=10.5,
                fontweight="bold" if fill != SURFACE else "normal")
        ax.text(x + w / 2, y3 - 1.2, note, ha="center", va="top", fontsize=9, color=INK2, linespacing=1.25)
        for b in range(hi, lo - 1, -1):
            ax.text(x0 + (15 - b) * bw + bw / 2, y3 + 6.9, str(b), ha="center", va="bottom", fontsize=8, color=MUTED)
    ax.text(x0 - 0.6, y3 + 6.9, "bit", ha="right", va="bottom", fontsize=8, color=MUTED)
    save(fig, "hardpoint-layout")


def workflow_figure():
    fig, ax = plt.subplots(figsize=(13.5, 4.4))
    fig.patch.set_facecolor(SURFACE)
    ax.set_xlim(0, 100); ax.set_ylim(0, 34); ax.axis("off")
    ax.set_position([0.02, 0.02, 0.96, 0.96])

    def node(x, y, w, h, title, sub, fill=SURFACE):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.2", facecolor=fill,
                                    edgecolor=INK2, linewidth=1.1))
        ax.text(x + w / 2, y + h - 2.6, title, ha="center", va="center", fontsize=11.5, fontweight="bold")
        ax.text(x + w / 2, y + h / 2 - 1.6, sub, ha="center", va="center", fontsize=9.5, color=INK2, linespacing=1.3)

    def arrow(a, b, text=None, dy=1.2):
        ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=14, color=INK2, lw=1.3,
                                     shrinkA=2, shrinkB=2))
        if text:
            ax.text((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, text, ha="center", va="center", fontsize=9.5, color=INK2,
                    bbox=dict(facecolor=SURFACE, edgecolor="none", pad=3))

    ax.text(1, 31.6, "One file, two readers", fontsize=15, fontweight="bold")
    node(1, 9.5, 21, 11, "CAD model", "FreeCAD or Fusion\nknows its real faces")
    node(38, 9.5, 24, 11, "Hardpoint STL", "an ordinary .stl\n+ faces, types, corners", SOFT_ORANGE)
    node(76, 17, 23, 10, "Slicer", "reads the triangles,\nignores the labels")
    node(76, 2, 23, 10, "Mesh-to-CAD converter", "reads the labels, checks\nthem, builds the solid")
    arrow((22, 15), (38, 15), "Export hardpoint STL")
    arrow((62, 17), (76, 22), "prints as usual")
    arrow((62, 12.5), (76, 7), "STEP with real faces", dy=-3.4)
    save(fig, "hardpoint-workflow")


def results_figure():
    """Dumbbell on a log axis: three values per part differ by up to 250 times."""
    fig, ax = plt.subplots(figsize=(11.5, 4.3))
    fig.patch.set_facecolor(SURFACE); ax.set_facecolor(SURFACE)
    fig.subplots_adjust(left=0.30, right=0.97, top=0.74, bottom=0.17)
    ys = list(range(len(RESULTS)))[::-1]
    for y, (name, plain, hard, cad) in zip(ys, RESULTS):
        ax.plot([hard, plain], [y, y], color=AXIS, lw=2, solid_capstyle="round", zorder=1)
        ax.plot([cad, cad], [y - 0.17, y + 0.17], color=INK, lw=2, zorder=2)
        ax.scatter([plain], [y], s=110, color=ORANGE, edgecolors=SURFACE, linewidths=2, zorder=3)
        ax.scatter([hard], [y], s=110, color=BLUE, edgecolors=SURFACE, linewidths=2, zorder=3)
        ax.annotate(f"{plain:,}", (plain, y), xytext=(9, 0), textcoords="offset points", va="center", fontsize=10.5, color=INK)
        ax.annotate(f"{hard:,}", (hard, y), xytext=(4, 13), textcoords="offset points", ha="center", fontsize=10.5, color=INK)
        ax.annotate(f"{cad}", (cad, y), xytext=(0, -24), textcoords="offset points", ha="center", fontsize=9.5, color=INK2)
    ax.set_xscale("log"); ax.set_xlim(2.5, 2600); ax.set_ylim(-0.6, len(RESULTS) - 0.4)
    ax.set_yticks(ys); ax.set_yticklabels([r[0] for r in RESULTS], fontsize=10.5)
    ax.set_xticks([3, 10, 30, 100, 300, 1000]); ax.set_xticklabels(["3", "10", "30", "100", "300", "1,000"])
    ax.minorticks_off()
    ax.grid(axis="x", color=GRID, lw=1); ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="y", length=0); ax.tick_params(axis="x", length=0)
    ax.set_xlabel("Faces in the STEP result (log scale)", fontsize=10)
    fig.text(0.02, 0.93, "Fewer, truer faces from the same triangles", fontsize=14, fontweight="bold")
    fig.text(0.02, 0.865, "STEP faces after converting a plain STL and its hardpoint twin. Classic fitter, default settings.",
             fontsize=10, color=INK2)
    from matplotlib.lines import Line2D
    handles = [Line2D([], [], marker="o", ls="", ms=9, mfc=ORANGE, mec=SURFACE, mew=1.5, label="Plain STL"),
               Line2D([], [], marker="o", ls="", ms=9, mfc=BLUE, mec=SURFACE, mew=1.5, label="Hardpoint STL"),
               Line2D([], [], marker="|", ls="", ms=14, mew=2, color=INK, label="Faces in the original CAD model")]
    ax.legend(handles=handles, loc="lower left", bbox_to_anchor=(-0.01, 1.0), ncol=3, frameon=False, fontsize=10,
              labelcolor=INK2, handletextpad=0.3, columnspacing=1.8)
    save(fig, "hardpoint-results")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    layout_figure()
    workflow_figure()
    results_figure()
    part_figure()
