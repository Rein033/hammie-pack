"""Hammie's original sticker drawing as vector shapes, for a Kode Dot face pack (Lottie).

The four parts hamorig.py cuts out of out/reference.png (body, head, pliers arm, scope arm) are
each reduced to a fixed palette and traced colour by colour: every fill region is grown a little
under the black ink and painted first, the ink with its holes last. Contours are simplified
(Douglas-Peucker) and given smooth tangents except at corners, so a part costs a few KB of JSON.

    vectorize.py OUT.json [--scale S] [--eps-fill E] [--eps-ink E]
writes {part: {"bbox": [x0, y0, x1, y1] (reference px), "shapes": [lottie group, ...]}, "unit": U}
Coordinates are reference pixels divided by U (integers).
"""
import json
import math
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hamorig as H  # noqa: E402

PARTS = ("body", "head", "pliers", "scope")


def opt(name, default):
    if name in sys.argv:
        return float(sys.argv[sys.argv.index(name) + 1])
    return default


SCALE = opt("--scale", 0.5)        # trace resolution, of reference px
EPS_FILL = opt("--eps-fill", 1.6)  # simplification, trace px
EPS_INK = opt("--eps-ink", 0.9)
GROW = int(opt("--grow", 1))       # fills grow this far under the ink, trace px
MIN_AREA = opt("--min-area", 10)   # smaller islands are dropped, trace px^2
NCOL = int(opt("--colors", 9))
UNIT = 1.0 / SCALE                  # output coordinates = reference px / UNIT = trace px


# The sticker's own colours (out/reference.png's histogram); index 0 is the ink.
PALETTE = np.array([
    (36, 36, 36),     # ink
    (246, 134, 26),   # orange fur, goggle lenses
    (230, 104, 24),   # fur shade
    (248, 248, 246),  # white fur
    (112, 112, 110),  # grey: meter, scope
    (72, 72, 72),     # dark grey
    (54, 134, 60),    # scope screen
    (182, 232, 72),   # the trace on it
], dtype=np.uint8)


def palette(images):
    """One palette for all parts: k-means over their opaque pixels."""
    px = []
    for im in images:
        a = np.asarray(im)
        m = a[:, :, 3] > 160
        px.append(a[m][:, :3])
    px = np.concatenate(px).astype(np.float32)
    rng = np.random.default_rng(1)
    px = px[rng.choice(len(px), min(len(px), 60000), replace=False)]
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 0.5)
    _, _, centres = cv2.kmeans(px, NCOL, None, crit, 4, cv2.KMEANS_PP_CENTERS)
    centres = centres.astype(np.uint8)
    # the darkest is the ink
    lum = centres.astype(np.float32) @ np.array([0.3, 0.59, 0.11])
    order = np.argsort(lum)
    return centres[order]


def smooth_path(pts, closed=True):
    """Bezier tangents by Catmull-Rom, none at corners (turn > 50 degrees)."""
    n = len(pts)
    ins, outs = [], []
    for k in range(n):
        p0, p1, p2 = pts[(k - 1) % n], pts[k], pts[(k + 1) % n]
        d1 = p1 - p0
        d2 = p2 - p1
        l1, l2 = np.hypot(*d1), np.hypot(*d2)
        if l1 == 0 or l2 == 0:
            ins.append([0, 0]); outs.append([0, 0]); continue
        cosang = float(np.dot(d1, d2) / (l1 * l2))
        if cosang < math.cos(math.radians(50)):
            ins.append([0, 0]); outs.append([0, 0]); continue
        t = (p2 - p0) / np.hypot(*(p2 - p0))
        outs.append((t * l2 / 3).tolist())
        ins.append((-t * l1 / 3).tolist())
    return ins, outs


def r(v):
    return int(round(v))


def path_of(cnt, eps):
    c = cv2.approxPolyDP(cnt, eps, True).reshape(-1, 2).astype(np.float64)
    if len(c) < 3:
        return None
    ins, outs = smooth_path(c)
    return {"ty": "sh", "ks": {"a": 0, "k": {
        "c": True,
        "v": [[r(x), r(y)] for x, y in c],
        "i": [[r(a), r(b)] for a, b in ins],
        "o": [[r(a), r(b)] for a, b in outs],
    }}}


def group(paths, rgb):
    return {"ty": "gr", "it": paths + [
        {"ty": "fl", "c": {"a": 0, "k": [round(c / 255, 3) for c in rgb] + [1]}, "o": {"a": 0, "k": 100}, "r": 2},
        {"ty": "tr", "p": {"a": 0, "k": [0, 0]}, "a": {"a": 0, "k": [0, 0]}, "s": {"a": 0, "k": [100, 100]},
         "r": {"a": 0, "k": 0}, "o": {"a": 0, "k": 100}},
    ]}


def contours(mask, eps):
    cnts, _ = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    out = []
    for c in cnts:
        if abs(cv2.contourArea(c)) < MIN_AREA:
            continue
        p = path_of(c, eps)
        if p:
            out.append(p)
    return out


# Colours a part may use (indices into PALETTE): the head has no metal, only the scope has a screen.
ALLOWED = {"head": [0, 1, 2, 3], "body": [0, 1, 2, 3, 4, 5], "pliers": [0, 1, 2, 3, 4, 5],
           "scope": [0, 1, 2, 3, 4, 5, 6, 7]}
# Greys are where the antialiasing of a black line lands: only big pieces of them are kept.
MIN_AREA_GREY = opt("--min-grey", 60)


def trace(im, pal, off, allowed):
    """im: the part, cropped and scaled to trace px. Returns Lottie groups, back to front."""
    a = np.asarray(im)
    alpha = (a[:, :, 3] > 128).astype(np.uint8)
    rgb = a[:, :, :3].astype(np.int32)
    sub = pal[allowed].astype(np.int32)
    d = ((rgb[:, :, None, :] - sub[None, None, :, :]) ** 2).sum(-1)
    lab = np.array(allowed)[d.argmin(-1)]
    lab[alpha == 0] = -1
    # a 3x3 mode filter takes the antialiasing seams away
    lab = cv2.medianBlur((lab + 1).astype(np.uint8), 3).astype(np.int32) - 1
    lab[alpha == 0] = -1
    lab = cv2.medianBlur((lab + 1).astype(np.uint8), 5).astype(np.int32) - 1
    lab[alpha == 0] = -1
    groups = []
    # the silhouette in ink: the black outlines and every line between two fills come from it
    sil = cv2.morphologyEx(alpha, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    groups.append(group(contours(sil, EPS_FILL), pal[0]))
    # then each fill colour, its holes cut (even-odd), so the ink shows through
    for i in range(1, len(pal)):
        m = (lab == i).astype(np.uint8)
        if m.sum() < MIN_AREA:
            continue
        if i in (4, 5):
            n, cc, st, _ = cv2.connectedComponentsWithStats(m)
            for j in range(1, n):
                if st[j, cv2.CC_STAT_AREA] < MIN_AREA_GREY:
                    m[cc == j] = 0
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
        if GROW:
            m = cv2.dilate(m, np.ones((2 * GROW + 1, 2 * GROW + 1), np.uint8)) & alpha
        ps = contours(m, EPS_FILL)
        if ps:
            groups.append(group(ps, pal[i]))
    # shift into reference space / UNIT
    for g in groups:
        for it in g["it"]:
            if it["ty"] == "sh":
                it["ks"]["k"]["v"] = [[x + off[0], y + off[1]] for x, y in it["ks"]["k"]["v"]]
    return groups


def main():
    out = sys.argv[1]
    P = H.parts()
    crops = {}
    for name in PARTS:
        im = getattr(P, name)
        bb = im.getchannel("A").getbbox()
        c = im.crop(bb)
        c = c.resize((max(1, round(c.width * SCALE)), max(1, round(c.height * SCALE))), Image.LANCZOS)
        crops[name] = (bb, c)
    pal = PALETTE
    res = {"unit": UNIT, "palette": pal.tolist()}
    for name, (bb, c) in crops.items():
        off = (round(bb[0] * SCALE), round(bb[1] * SCALE))
        res[name] = {"bbox": list(bb), "shapes": trace(c, pal, off, ALLOWED[name])}
    js = json.dumps(res, separators=(",", ":"))
    open(out, "w").write(js)
    for name in PARTS:
        print(name, len(json.dumps(res[name], separators=(",", ":"))) // 1024, "KB")
    print("total", len(js) // 1024, "KB; palette", pal.tolist())


if __name__ == "__main__":
    main()
