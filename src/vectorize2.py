"""Hammie's sticker as smooth vector shapes: vectorize.py's clean colour regions, traced by vtracer
into real Bezier curves (not polygons), at full resolution, so fine lines (whiskers, fur strokes,
the ear's inside) stay.

    vectorize2.py OUT.json [--scale S] [--speckle N] [--corner DEG] [--length L] [--splice DEG]
Same output as vectorize.py: {"unit": U, part: {"bbox", "shapes": [lottie groups, back to front]}}.
"""
import json
import os
import re
import sys
import tempfile

import cv2
import numpy as np
import vtracer
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vectorize as V  # noqa: E402  (PALETTE, ALLOWED, parts and the cut-edge growth)

H = V.H


def opt(name, default):
    if name in sys.argv:
        return float(sys.argv[sys.argv.index(name) + 1])
    return default


SCALE = opt("--scale", 1.0)
SPECKLE = int(opt("--speckle", 6))
CORNER = int(opt("--corner", 70))
LENGTH = opt("--length", 6.0)
SPLICE = int(opt("--splice", 45))
PREC = int(opt("--prec", 0))
SHADE_MIN = opt("--shade-min", 300)
# each part traced at its own resolution (the face needs the most); output is in 1/SCALE units for all
PART_SCALE = {"head": opt("--s-head", SCALE), "body": opt("--s-body", SCALE),
              "pliers": opt("--s-pliers", SCALE), "scope": opt("--s-scope", SCALE)}  # fur-shade islands smaller than this (reference px^2) become fur         # decimals kept in the output coordinates


def labels(part_img, grown_img, allowed, sc):
    """palette index per pixel; -1 transparent. Ink only inside the part itself, fills over its cuts."""
    a = np.asarray(grown_img if grown_img is not None else part_img)
    pa = np.asarray(part_img)[:, :, 3] > 128
    ga = a[:, :, 3] > 128
    rgb = a[:, :, :3].astype(np.int32)
    sub = V.PALETTE[allowed].astype(np.int32)
    lab = np.array(allowed)[((rgb[:, :, None, :] - sub[None, None]) ** 2).sum(-1).argmin(-1)]
    lab[~ga] = -1
    lab = cv2.medianBlur((lab + 1).astype(np.uint8), 3).astype(np.int32) - 1
    lab[~ga] = -1
    lab[(lab == 0) & ~pa] = -1
    # the antialiased ring just inside the outline reads as grey: it is ink
    edge = cv2.erode(pa.astype(np.uint8), np.ones((5, 5), np.uint8)) == 0
    lab[edge & pa & ((lab == 4) | (lab == 5))] = 0
    # grey islands too small to be the drawing's own (antialiasing round black lines) become ink
    for i, mn in ((4, V.MIN_AREA_GREY * sc * sc / 0.36), (5, V.MIN_AREA_DARK * sc * sc / 0.36)):
        m = (lab == i).astype(np.uint8)
        n, cc, st, _ = cv2.connectedComponentsWithStats(m)
        for j in range(1, n):
            if st[j, cv2.CC_STAT_AREA] < mn:
                lab[cc == j] = 0
    # fur shade: only its bigger strokes are kept, the rest is plain fur
    m = (lab == 2).astype(np.uint8)
    n, cc, st, _ = cv2.connectedComponentsWithStats(m)
    for j in range(1, n):
        if st[j, cv2.CC_STAT_AREA] < SHADE_MIN * sc * sc:
            lab[cc == j] = 1
    return lab


NUM = re.compile(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?")


def svg_paths(svg):
    """vtracer's stacked SVG -> [(rgb, [subpath: [(cmd, pts)]])], bottom first."""
    out = []
    for m in re.finditer(r'<path d="([^"]+)" fill="#([0-9A-Fa-f]{6})"(?: transform="translate\(([^,]+),([^)]+)\)")?', svg):
        d, col = m.group(1), m.group(2)
        tx, ty = float(m.group(3) or 0), float(m.group(4) or 0)
        rgb = [int(col[i:i + 2], 16) for i in (0, 2, 4)]
        subs, cur = [], None
        for tok in re.finditer(r"([MLCZz])([^MLCZz]*)", d):
            c, args = tok.group(1), [float(x) for x in NUM.findall(tok.group(2))]
            pts = [(args[i] + tx, args[i + 1] + ty) for i in range(0, len(args), 2)]
            if c == "M":
                cur = [("M", pts[:1])]
                subs.append(cur)
                for p in pts[1:]:
                    cur.append(("L", [p]))
            elif c == "L":
                for p in pts:
                    cur.append(("L", [p]))
            elif c == "C":
                for i in range(0, len(pts), 3):
                    cur.append(("C", pts[i:i + 3]))
        out.append((rgb, subs))
    return out


MERGE = opt("--merge", 3.0)       # vertices closer than this (output units) are one
STRAIGHT = opt("--straight", 0.8)  # a corner vertex this close to the line through its neighbours goes


def simplify(v, i, o):
    """vtracer leaves pairs of near-equal vertices at corners and straight runs cut in many pieces."""
    v, i, o = [list(p) for p in v], [list(p) for p in i], [list(p) for p in o]
    changed = True
    while changed and len(v) > 4:
        changed = False
        k = 0
        while k < len(v) and len(v) > 4:
            n = (k + 1) % len(v)
            if abs(v[k][0] - v[n][0]) + abs(v[k][1] - v[n][1]) <= MERGE:
                # one vertex for both: k's in, n's out
                o[k] = [v[n][0] + o[n][0] - v[k][0], v[n][1] + o[n][1] - v[k][1]]
                del v[n], i[n], o[n]
                changed = True
                continue
            p = (k - 1) % len(v)
            if i[k] == [0, 0] and o[k] == [0, 0] and o[p] == [0, 0] and i[n] == [0, 0]:
                ax, ay = v[p]; bx, by = v[n]; cx, cy = v[k]
                L = max(1e-9, ((bx - ax) ** 2 + (by - ay) ** 2) ** 0.5)
                if abs((bx - ax) * (ay - cy) - (ax - cx) * (by - ay)) / L <= STRAIGHT:
                    del v[k], i[k], o[k]
                    changed = True
                    continue
            k += 1
    return v, i, o


def lottie_path(sub, unit, off):
    """one closed subpath -> a Lottie 'sh' (vertices with in/out tangents relative to them)."""
    f = lambda p: [round(p[0] * unit + off[0], PREC), round(p[1] * unit + off[1], PREC)]
    verts, ins, outs = [], [], []
    start = sub[0][1][0]
    pos = start
    verts.append(f(pos)); ins.append([0, 0]); outs.append([0, 0])
    for c, pts in sub[1:]:
        if c == "L":
            nxt = pts[0]
            verts.append(f(nxt)); ins.append([0, 0]); outs.append([0, 0])
        else:
            c1, c2, nxt = pts
            v0 = verts[-1]
            o = f(c1)
            outs[-1] = [round(o[0] - v0[0], PREC), round(o[1] - v0[1], PREC)]
            vn = f(nxt)
            i2 = f(c2)
            verts.append(vn); ins.append([round(i2[0] - vn[0], PREC), round(i2[1] - vn[1], PREC)]); outs.append([0, 0])
        pos = pts[-1]
    # the last vertex usually repeats the first: fold it in
    if len(verts) > 1 and verts[-1] == verts[0]:
        ins[0] = ins[-1]
        verts.pop(); ins.pop(); outs.pop()
    verts, ins, outs = simplify(verts, ins, outs)
    if len(verts) < 2:
        return None
    clean = lambda v: [int(x) if float(x).is_integer() else x for x in v]
    return {"ty": "sh", "ks": {"a": 0, "k": {"c": True, "v": [clean(v) for v in verts], "i": [clean(v) for v in ins],
                                              "o": [clean(v) for v in outs]}}}


def trace(lab, off, k=1.0):
    """labels -> Lottie groups, bottom first, one group per vtracer layer, merged by colour runs."""
    h, w = lab.shape
    img = np.zeros((h, w, 4), np.uint8)
    for i, c in enumerate(V.PALETTE):
        img[lab == i, :3] = c
        img[lab == i, 3] = 255
    with tempfile.TemporaryDirectory() as td:
        p, o = os.path.join(td, "in.png"), os.path.join(td, "out.svg")
        Image.fromarray(img, "RGBA").save(p)
        vtracer.convert_image_to_svg_py(p, o, colormode="color", hierarchical="stacked", mode="spline",
                                        filter_speckle=SPECKLE, color_precision=8, layer_difference=1,
                                        corner_threshold=CORNER, length_threshold=LENGTH, max_iterations=10,
                                        splice_threshold=SPLICE, path_precision=2)
        svg = open(o).read()
    groups, last = [], None
    for rgb, subs in svg_paths(svg):
        # snap vtracer's colour back to the palette
        ci = int(((V.PALETTE.astype(int) - np.array(rgb)) ** 2).sum(1).argmin())
        shapes = [s for s in (lottie_path(sb, k, off) for sb in subs) if s]
        if not shapes:
            continue
        if last is not None and last[0] == ci:
            last[1].extend(shapes)       # neighbours in the stack with one colour: one group
            continue
        last = (ci, shapes)
        groups.append(last)
    out = []
    for ci, shapes in groups:
        c = [round(x / 255, 3) for x in V.PALETTE[ci]] + [1]
        out.append({"ty": "gr", "it": shapes + [
            {"ty": "fl", "c": {"a": 0, "k": c}, "o": {"a": 0, "k": 100}, "r": 1},
            {"ty": "tr", "p": {"a": 0, "k": [0, 0]}, "a": {"a": 0, "k": [0, 0]}, "s": {"a": 0, "k": [100, 100]},
             "r": {"a": 0, "k": 0}, "o": {"a": 0, "k": 100}}]})
    return out


def silhouette(part_img, off, k=1.0):
    """the part's own outline, in ink, under everything: what vectorize.py's first group was (the sticker edge uses it)."""
    a = (np.asarray(part_img)[:, :, 3] > 128).astype(np.uint8)
    a = cv2.morphologyEx(a, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    cnts, _ = cv2.findContours(a, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    paths = []
    for c in cnts:
        if cv2.contourArea(c) < 50:
            continue
        pts = cv2.approxPolyDP(c, 1.2, True).reshape(-1, 2)
        paths.append({"ty": "sh", "ks": {"a": 0, "k": {"c": True, "v": [[round(x * k + off[0]), round(y * k + off[1])] for x, y in pts],
                                                        "i": [[0, 0]] * len(pts), "o": [[0, 0]] * len(pts)}}})
    return {"ty": "gr", "it": paths + [
        {"ty": "fl", "c": {"a": 0, "k": [round(x / 255, 3) for x in V.PALETTE[0]] + [1]}, "o": {"a": 0, "k": 100}, "r": 1},
        {"ty": "tr", "p": {"a": 0, "k": [0, 0]}, "a": {"a": 0, "k": [0, 0]}, "s": {"a": 0, "k": [100, 100]},
         "r": {"a": 0, "k": 0}, "o": {"a": 0, "k": 100}}]}


def main():
    out = sys.argv[1]
    P = H.parts()
    full = H.cutout()
    fa = np.asarray(full.getchannel("A")) > 128
    res = {"unit": 1.0 / SCALE, "palette": V.PALETTE.tolist()}
    for name in V.PARTS:
        im = getattr(P, name)
        g = None
        if name != "body":
            pa = (np.asarray(im.getchannel("A")) > 128).astype(np.uint8)
            gm = cv2.dilate(pa, np.ones((2 * V.GROWCUT + 1,) * 2, np.uint8)).astype(bool) & fa
            g = full.copy()
            g.putalpha(Image.fromarray((gm * 255).astype(np.uint8)))
            bb = g.getchannel("A").getbbox()
        else:
            bb = im.getchannel("A").getbbox()
        ps = PART_SCALE[name]
        size = (max(1, round((bb[2] - bb[0]) * ps)), max(1, round((bb[3] - bb[1]) * ps)))
        pc = im.crop(bb).resize(size, Image.LANCZOS)
        gc = g.crop(bb).resize(size, Image.LANCZOS) if g else None
        off = (round(bb[0] * SCALE), round(bb[1] * SCALE))
        k = SCALE / ps                      # part trace px -> output units
        lab = labels(pc, gc, V.ALLOWED[name], ps)
        res[name] = {"bbox": list(bb), "shapes": [silhouette(pc, off, k)] + trace(lab, off, k)}
    js = json.dumps(res, separators=(",", ":"))
    open(out, "w").write(js)
    for name in V.PARTS:
        nv = sum(len(it["ks"]["k"]["v"]) for g in res[name]["shapes"] for it in g["it"] if it["ty"] == "sh")
        print(name, len(json.dumps(res[name], separators=(",", ":"))) // 1024, "KB", nv, "vertices")
    print("total", len(js) // 1024, "KB")


if __name__ == "__main__":
    main()
