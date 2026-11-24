"""Hammie in his original sticker drawing as Lottie, for a Kode Dot face pack.

The parts vectorize.py traced (body, head, pliers arm, scope arm) become layers with the pivots of
hamorig.py, each over a white sticker border of its own. Eyes, mouth, the scope's screen and the
props are small vector shapes on top. Poses come from hamorig.py's role functions (the watch's
animations), sampled and turned into keyframes; the roles the watch does not have are posed here.

    dotrig.py VECTORS.json OUTDIR
writes OUTDIR/<role>.json, one Lottie per animation, on its Dot canvas.
"""
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hamorig as H  # noqa: E402

FPS = 30
SAMPLE = 15                      # poses per second taken from the role functions
INK = [0.11, 0.11, 0.11, 1]
WHITE = [1, 1, 1, 1]
LENS = [0.965, 0.51, 0.114, 1]
MOUTH = [0.43, 0.118, 0.149, 1]
TONGUE = [0.94, 0.47, 0.43, 1]
YELLOW = [1, 0.76, 0.1, 1]
BLUE = [0.6, 0.82, 1, 1]
BATT = [0.133, 0.157, 0.192, 1]
GREEN = [0.37, 0.88, 0.54, 1]
SCREEN = [0.212, 0.525, 0.235, 1]
LIME = [0.714, 0.91, 0.282, 1]
REDS = [0.86, 0.2, 0.18, 1]

# The Dot's canvases (kui_pack.h) and the stage round the drawing hamorig.py uses for props.
CANVAS = {"scene": (410, 334), "empty": (410, 369), "card": (410, 160), "loading": (264, 264)}
REF_W, REF_H = 996, 956
M_T, M_X, M_B = H.MARGIN_T, H.MARGIN_X, H.MARGIN_B


# ---------------------------------------------------------------- lottie helpers
def st(v):
    return {"a": 0, "k": v}


def anim(keys, hold=False):
    """keys [(frame, value)] -> an animated property; one key is static."""
    keys = [(f, v if isinstance(v, list) else [v]) for f, v in keys]
    if len(keys) == 1 or all(v == keys[0][1] for _, v in keys):
        v = keys[0][1]
        return st(v[0] if len(v) == 1 else v)
    out = []
    for i, (f, v) in enumerate(keys):
        kf = {"t": f, "s": v}
        if i < len(keys) - 1:
            if hold:
                kf["h"] = 1
            else:
                kf["i"] = {"x": [0.5], "y": [1]}
                kf["o"] = {"x": [0.5], "y": [0]}
        out.append(kf)
    return {"a": 1, "k": out}


def thin(keys, tol):
    """Drop keys a straight line between their neighbours already gives (within tol)."""
    if len(keys) <= 2:
        return keys
    out = [keys[0]]
    for i in range(1, len(keys) - 1):
        f0, v0 = out[-1]
        f1, v1 = keys[i]
        f2, v2 = keys[i + 1]
        a, b, c = np.atleast_1d(v0), np.atleast_1d(v1), np.atleast_1d(v2)
        lin = a + (c - a) * (f1 - f0) / max(1e-9, (f2 - f0))
        if np.max(np.abs(lin - b)) > tol:
            out.append(keys[i])
    out.append(keys[-1])
    return out


def holds(keys):
    """Keep only the keys where a held value changes."""
    out = [keys[0]]
    for f, v in keys[1:]:
        if v != out[-1][1]:
            out.append((f, v))
    return out


def tr(p=(0, 0), a=(0, 0), s=(100, 100), r=0, o=100):
    return {"ty": "tr", "p": p if isinstance(p, dict) else st(list(p)), "a": a if isinstance(a, dict) else st(list(a)),
            "s": s if isinstance(s, dict) else st(list(s)), "r": r if isinstance(r, dict) else st(r),
            "o": o if isinstance(o, dict) else st(o)}


def fill(c):
    return {"ty": "fl", "c": st(c), "o": st(100), "r": 1}


def stroke(c, w):
    return {"ty": "st", "c": st(c), "o": st(100), "w": st(w), "lc": 2, "lj": 2}


def ell(cx, cy, w, h):
    return {"ty": "el", "p": st([cx, cy]), "s": st([w, h])}


def rect(cx, cy, w, h, rr=0):
    return {"ty": "rc", "p": st([cx, cy]), "s": st([w, h]), "r": st(rr)}


def poly(pts, closed=True):
    return {"ty": "sh", "ks": st({"c": closed, "v": [list(p) for p in pts], "i": [[0, 0]] * len(pts), "o": [[0, 0]] * len(pts)})}


def grp(items, t=None):
    return {"ty": "gr", "it": items + [t or tr()]}


def layer(ind, name, shapes=None, ks=None, parent=None, null=False, op=1):
    L = {"ind": ind, "ty": 3 if null else 4, "nm": name, "ks": ks or {
        "o": st(100), "r": st(0), "p": st([0, 0, 0]), "a": st([0, 0, 0]), "s": st([100, 100, 100])},
        "ip": 0, "op": op, "st": 0}
    if not null:
        L["shapes"] = shapes or []
    if parent:
        L["parent"] = parent
    return L


def layer_ks(p, a, s=(100, 100), r=0, o=100):
    def v3(x):
        if isinstance(x, dict):
            return x
        return st(list(x) + [0] if len(x) == 2 else list(x))
    return {"o": o if isinstance(o, dict) else st(o), "r": r if isinstance(r, dict) else st(r),
            "p": v3(p), "a": v3(a), "s": s if isinstance(s, dict) else st(list(s) + [100])}


# ---------------------------------------------------------------- the drawing
class Drawing:
    def __init__(self, vec_path):
        V = json.load(open(vec_path))
        self.V = V
        self.k = 1.0 / V["unit"]          # reference px -> vector units

    def R(self, x, y=None):
        """reference px -> vector units"""
        if y is None:
            return x * self.k
        return [round(x * self.k, 1), round(y * self.k, 1)]

    def shapes(self, part):
        """the part's groups, top first (Lottie draws the first item on top)"""
        return list(reversed(self.V[part]["shapes"]))

    def border(self, part):
        """the white sticker edge: the part's ink silhouette (its first group), drawn in white, fattened."""
        sil = self.V[part]["shapes"][0]
        paths = [it for it in sil["it"] if it["ty"] == "sh"]
        w = self.R(56)
        return [grp(paths + [stroke(WHITE, w), fill(WHITE)])]


# ---------------------------------------------------------------- overlays
def eye_groups(D, i, frames):
    """One eye: lens cover, pupil (look, wide), shut arc, happy arc - by keyframes over the poses."""
    (cx, cy), (rx, ry) = H.EYES[i]
    C = D.R(cx, cy)
    erx, ery = D.R(rx), D.R(ry)
    pk, sk, op_open, op_shut, op_happy = [], [], [], [], []
    for f, pose in frames:
        mode = pose.get("eyes", "open")
        look = pose.get("look", (0, 0))
        wide = pose.get("wide", 1.0)
        pk.append((f, [round(C[0] + D.R(look[0]), 1), round(C[1] + D.R(look[1]), 1)]))
        sk.append((f, [round(100 * wide, 1)] * 2))
        op_open.append((f, 100 if mode == "open" else 0))
        op_shut.append((f, 100 if mode == "shut" else 0))
        op_happy.append((f, 100 if mode == "happy" else 0))
    cover = grp([ell(C[0], C[1], 2 * erx + D.R(8), 2 * ery + D.R(8)), fill(LENS)])
    hl = D.R(7)
    pupil = grp([grp([ell(erx * 0.15, -ery * 0.35, 2 * hl, 2 * hl), fill(WHITE)]), grp([ell(0, 0, 2 * erx, 2 * ery), fill(INK)])],
                tr(p=anim(thin(pk, 0.3)), s=anim(thin(sk, 0.5)), o=anim(holds(op_open), True)))
    # an arc as a path: the lower half of an ellipse (shut) or the upper half (happy)
    def arc(up):
        pts, n = [], 9
        for j in range(n):
            a = math.pi * (0.12 + 0.76 * j / (n - 1))
            y = math.sin(a) * ery * 0.8
            pts.append([round(C[0] - math.cos(a) * (erx + D.R(4)), 1), round(C[1] + (-y + ery * 0.3 if up else y - ery * 0.1), 1)])
        return {"ty": "sh", "ks": st({"c": False, "v": pts, "i": [[0, 0]] * n, "o": [[0, 0]] * n})}
    shut = grp([arc(False), stroke(INK, D.R(9))], tr(o=anim(holds(op_shut), True)))
    happy = grp([arc(True), stroke(INK, D.R(9))], tr(o=anim(holds(op_happy), True)))
    # the cover only shows while the drawn eye must be hidden: whenever any overlay is in use
    return [pupil, shut, happy, cover]


def mouth_groups(D, frames):
    o_k, open_k = [], []
    for f, pose in frames:
        m = pose.get("mouth", "smile")
        o_k.append((f, 100 if m == "o" else 0))
        open_k.append((f, 100 if m == "open" else 0))
    o = grp([ell(*D.R(382, 403), D.R(44), D.R(50)), stroke(INK, D.R(7)), fill(MOUTH)], tr(o=anim(holds(o_k), True)))
    # open laugh: half a disc under the nose, the tongue in it
    x0, y0, x1, y1 = 318, 360, 445, 452
    cx, cy, w, h = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2
    pts = [D.R(cx - w, cy)] + [D.R(cx - w * math.cos(math.pi * j / 8), cy + h * math.sin(math.pi * j / 8)) for j in range(1, 8)] + [D.R(cx + w, cy)]
    lau = grp([grp([ell(*D.R(381, 429), D.R(58), D.R(34)), fill(TONGUE)]), grp([poly(pts), stroke(INK, D.R(8)), fill(MOUTH)])],
              tr(o=anim(holds(open_k), True)))
    return [lau, o]


def screen_groups(D, frames, scope_box):
    """clock face for 'hour', red X for 'err'; otherwise the drawing's own wave shows."""
    x0, y0, x1, y1 = scope_box
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    C = D.R(cx, cy)
    clk, err, mk, hk = [], [], [], []
    for f, pose in frames:
        s = pose.get("screen", "wave")
        clk.append((f, 100 if s == "clock" else 0))
        err.append((f, 100 if s == "err" else 0))
        t = pose.get("t", 0.0)
        mk.append((f, round(360 * t, 1)))
        hk.append((f, round(30 * t, 1)))
    bg = rect(C[0], C[1], D.R(x1 - x0), D.R(y1 - y0), D.R(8))
    hand = lambda L, w, k: grp([poly([[0, 0], [0, -D.R(L)]], False), stroke(INK, D.R(w))], tr(p=C, r=anim(thin(k, 1.0))))
    clock = grp([hand(40, 7, mk), hand(26, 9, hk), grp([ell(C[0], C[1], D.R(104), D.R(104)), stroke(INK, D.R(7)), fill([0.98, 0.98, 0.96, 1])]),
                 grp([bg, fill(SCREEN)])], tr(o=anim(holds(clk), True)))
    a = D.R(40)
    x = grp([poly([[C[0] - a, C[1] - a], [C[0] + a, C[1] + a]], False), poly([[C[0] + a, C[1] - a], [C[0] - a, C[1] + a]], False),
             stroke(WHITE, D.R(16)), grp([bg, fill(REDS)])], tr(o=anim(holds(err), True)))
    return [clock, x]


# ---------------------------------------------------------------- props (stage coords = reference px, margins included)
def prop_bang(D, x, y, keys):
    w = D.R(22)
    g = grp([rect(0, D.R(-42), 2 * w, D.R(105), w), ell(0, D.R(25) + w, 2 * w, 2 * w), stroke(INK, D.R(9)), fill(YELLOW)],
            tr(p=D.R(x, y), s=anim(thin([(f, [100 * v] * 2) for f, v in keys], 2))))
    return g


def prop_bolt(D, x, y, keys):
    pts = [[D.R(px), D.R(py)] for px, py in [(14, -70), (-30, 6), (2, 6), (-12, 64), (36, -14), (4, -14)]]
    return grp([poly(pts), stroke(INK, D.R(9)), fill(YELLOW)], tr(p=D.R(x, y), s=anim(thin([(f, [100 * v] * 2) for f, v in keys], 2))))


def prop_battery(D, x, y, keys):
    full = D.R(96)
    bar = grp([rect(full / 2, 0, full, D.R(36), D.R(6)), fill(GREEN)],
              tr(p=D.R(x + 12, y + 30), a=[0, 0], s=anim(thin([(f, [round(100 * v, 1), 100]) for f, v in keys], 2))))
    return grp([bar, grp([rect(*D.R(x + 127, y + 30), D.R(14), D.R(28), D.R(4)), stroke(INK, D.R(6)), fill(BATT)]),
                grp([rect(*D.R(x + 60, y + 30), D.R(120), D.R(60), D.R(12)), stroke(INK, D.R(9)), fill(BATT)])])


def prop_z(D, x, y, s, keys):
    pts = [D.R(0, 0), D.R(40 * s, 0), D.R(0, 44 * s), D.R(40 * s, 44 * s)]
    return grp([grp([poly(pts, False), stroke(BLUE, D.R(9 * s))]), grp([poly(pts, False), stroke(INK, D.R(18 * s))])],
               tr(p=anim(thin([(f, D.R(x, y - 60 * v)) for f, v in keys], 0.5)),
                  o=anim(thin([(f, round(100 * min(1, 2 * min(v, 1 - v) * 2.5), 1)) for f, v in keys], 3))))


def prop_q(D, x, y, keys):
    """a question mark, blue, in the sticker's line"""
    pts = [D.R(-22, -40), D.R(-14, -62), D.R(10, -66), D.R(26, -50), D.R(22, -28), D.R(4, -16), D.R(2, 4)]
    return grp([grp([ell(*D.R(2, 32), D.R(20), D.R(20)), fill(BLUE)]), grp([poly(pts, False), stroke(BLUE, D.R(12))]),
                grp([poly(pts, False), stroke(INK, D.R(24))]), grp([ell(*D.R(2, 32), D.R(34), D.R(34)), fill(INK)])],
               tr(p=D.R(x, y), s=anim(thin([(f, [100 * v] * 2) for f, v in keys], 2))))


# ---------------------------------------------------------------- poses for the roles the watch does not have
k_ = H.k


def role_joke(n):
    """he laughs: happy eyes, mouth open, bouncing, the scope shaking along"""
    for i in range(n):
        t = i / n
        on = 0.1 < t < 0.85
        b = abs(math.sin(2 * math.pi * 3 * t)) if on else 0
        yield {"eyes": "happy" if on else "open", "mouth": "open" if on else "smile", "hop": 14 * b,
               "squash": 0.02 * (1 - b) if on else 0, "head_r": 4 * math.sin(2 * math.pi * 3 * t) if on else 0,
               "scope_r": -3 * b, "pliers_r": 6 * b, "t": t * 2}


def role_doubt(n):
    """the empty launcher: head tilted, looking up at a question mark, pliers scratching his head"""
    for i in range(n):
        t = i / n
        yield {"head_r": 7 + 1.5 * math.sin(2 * math.pi * t), "look": (6, -8), "pliers_r": 6 * math.sin(4 * math.pi * t) - 6,
               "eyes": H.blink_eyes(t, 0.55, 0.07), "breathe": (1 - math.cos(2 * math.pi * t)) / 2, "t": t * 2,
               "q": 1 + 0.08 * math.sin(2 * math.pi * t)}


def role_work(n):
    """writing an app: eyes on the scope, pliers working at it"""
    for i in range(n):
        t = i / n
        yield {"head_r": -3, "look": (10, 8), "pliers_r": 9 * abs(math.sin(2 * math.pi * 3 * t)), "scope_r": -4,
               "breathe": (1 - math.cos(2 * math.pi * t)) / 2, "eyes": H.blink_eyes(t, 0.7, 0.06), "t": t * 3}


def role_bye(n):
    """goodbye: waves the pliers arm, happy"""
    for i in range(n):
        t = i / n
        on = t < 0.9
        yield {"pliers_r": (18 * math.sin(2 * math.pi * 2.5 * t) + 10) if on else 0, "eyes": "happy" if 0.1 < t < 0.85 else "open",
               "head_r": -3 * math.sin(2 * math.pi * 2.5 * t) if on else 0, "mouth": "open" if 0.15 < t < 0.7 else "smile", "t": t * 2}


def role_loading(n):
    """loading: little hops, in a loop"""
    for i in range(n):
        t = i / n
        b = abs(math.sin(2 * math.pi * 2 * t))
        yield {"hop": 30 * b, "squash": 0.03 * (1 - b) ** 4, "pliers_r": -6 * b, "scope_r": 5 * b, "eyes": "happy" if b > 0.6 else "open", "t": t * 2}


def role_sleep(n):
    """dozing: eyes shut, head down, slow breath, z's rising"""
    for i in range(n):
        t = i / n
        yield {"eyes": "shut", "head_r": 6, "head_dy": 12 + 3 * math.sin(2 * math.pi * t), "breathe": 1.4 * (1 - math.cos(2 * math.pi * t)) / 2,
               "pliers_r": -8, "scope_r": 6, "z": t, "t": t}


# name: (pose fn, seconds, loop, canvas, props)
ROLES = {
    "idle":    (H.role_idle, 3.0, True, "scene"),
    "wake":    (H.role_wake, 2.0, False, "scene"),
    "look":    (H.role_look, 2.0, False, "scene"),
    "hour":    (H.role_hour, 2.0, False, "scene"),
    "notice":  (H.role_notice, 2.0, False, "scene"),
    "charge":  (H.role_charge, 2.0, False, "scene"),
    "joke":    (role_joke, 2.0, False, "scene"),
    "sleep":   (role_sleep, 3.0, True, "scene"),
    "doubt":   (role_doubt, 3.0, True, "empty"),
    "work":    (role_work, 2.0, True, "card"),
    "bye":     (role_bye, 1.6, False, "card"),
    "loading": (role_loading, 1.6, True, "loading"),
}


# ---------------------------------------------------------------- one animation
def build(D, name):
    fn, secs, loop, canvas = ROLES[name]
    n = int(secs * SAMPLE)
    poses = list(fn(n))
    poses.append(poses[0] if loop else poses[-1])
    step = FPS // SAMPLE
    frames = [(i * step, p) for i, p in enumerate(poses)]
    op = n * step
    W, Hc = CANVAS[canvas]

    # fit the stage (drawing + margins for props) onto the canvas, as hamorig.py does onto the watch's box
    SW, SH = REF_W + 2 * M_X, REF_H + M_T + M_B
    sc = min(Hc / SH, W / SW)
    ox = (W - SW * sc) / 2 + M_X * sc
    oy = (Hc - SH * sc) + M_T * sc
    u = sc / D.k                        # vector units -> canvas px

    def track(key, default=0.0, f=lambda v: v, tol=0.2):
        return thin([(fr, f(p.get(key, default))) for fr, p in frames], tol)

    feet = D.R(REF_W / 2, REF_H)
    lift = lambda p: 6 * p.get("breathe", 0.0)

    L = []
    ind = iter(range(1, 100))
    root = next(ind)
    L.append(layer(root, "root", null=True, op=op, ks=layer_ks((round(ox, 1), round(oy, 1)), (0, 0), (round(100 * u, 2), round(100 * u, 2)))))
    fig = next(ind)
    L.append(layer(fig, "figure", null=True, op=op, parent=root, ks=layer_ks(
        anim(thin([(fr, [feet[0], round(feet[1] - D.R(p.get("hop", 0.0)), 1), 0]) for fr, p in frames], 0.3)),
        feet + [0],
        anim(thin([(fr, [round(100 * (1 + p.get("squash", 0.0)), 1), round(100 * (1 - p.get("squash", 0.0)), 1), 100]) for fr, p in frames], 0.3)))))

    def part_ks(pivot, rkey, dxkey, dykey, lift_k):
        P = D.R(*pivot)
        return layer_ks(
            anim(thin([(fr, [round(P[0] + D.R(p.get(dxkey, 0.0)), 1) if dxkey else P[0],
                             round(P[1] + D.R(p.get(dykey, 0.0) - lift_k * lift(p)), 1), 0]) for fr, p in frames], 0.3)),
            P + [0], (100, 100),
            anim(thin([(fr, round(p.get(rkey, 0.0), 2)) for fr, p in frames], 0.15)))

    head_ks = part_ks(H.HEAD_PIVOT, "head_r", "head_dx", "head_dy", 1.0)
    scope_ks = part_ks(H.SCOPE_PIVOT, "scope_r", None, "scope_dy", 0.6)
    pliers_ks = part_ks(H.PLIERS_PIVOT, "pliers_r", None, "pliers_dy", 0.6)
    body_ks = layer_ks(feet, feet, anim(thin([(fr, [100, round(100 * (1 + 0.012 * p.get("breathe", 0.0)), 2), 100]) for fr, p in frames], 0.05)))

    # screen box: hamorig's screen mask, in reference px
    sb = H.parts().screen_mask.getbbox()

    props = []
    if name == "notice":
        pop = [(fr, k_(fr / op, [(0, 0), (0.08, 1.25), (0.16, 1.0), (0.85, 1.0), (1.0, 0)])) for fr, _ in frames]
        props.append(prop_bang(D, 470, 110 - M_T, pop))
    if name == "charge":
        props.append(prop_bolt(D, -10, 150 - M_T, [(fr, 1 + 0.12 * math.sin(4 * math.pi * fr / op)) for fr, _ in frames]))
        props.append(prop_battery(D, 830, 20 - M_T, [(fr, min(1.0, 1.15 * fr / op)) for fr, _ in frames]))
    if name == "doubt":
        props.append(prop_q(D, 640, 40 - M_T + 75, [(fr, p.get("q", 1.0)) for fr, p in frames]))
    if name == "sleep":
        for j, (dx, s) in enumerate([(0, 0.7), (50, 0.9), (110, 1.1)]):
            props.append(prop_z(D, 600 + dx, 120 - M_T - 30 * j, s, [(fr, ((fr / op) + j / 3) % 1.0) for fr, _ in frames]))

    if props:
        L.append(layer(next(ind), "props", props, parent=fig, op=op))
    # top first: pliers arm, scope arm, head, body; then their sticker borders under all of them
    pl, sc_, hd, bd = next(ind), next(ind), next(ind), next(ind)
    L.append(layer(pl, "pliers", D.shapes("pliers"), pliers_ks, parent=fig, op=op))
    L.append(layer(sc_, "scope", screen_groups(D, frames, sb) + D.shapes("scope"), scope_ks, parent=fig, op=op))
    L.append(layer(hd, "head", eye_groups(D, 0, frames) + eye_groups(D, 1, frames) + mouth_groups(D, frames) + D.shapes("head"),
                   head_ks, parent=fig, op=op))
    L.append(layer(bd, "body", D.shapes("body"), body_ks, parent=fig, op=op))
    L.append(layer(next(ind), "pliers_edge", D.border("pliers"), pliers_ks, parent=fig, op=op))
    L.append(layer(next(ind), "scope_edge", D.border("scope"), scope_ks, parent=fig, op=op))
    L.append(layer(next(ind), "head_edge", D.border("head"), head_ks, parent=fig, op=op))
    L.append(layer(next(ind), "body_edge", D.border("body"), body_ks, parent=fig, op=op))
    return {"v": "5.7.0", "fr": FPS, "ip": 0, "op": op, "w": W, "h": Hc, "nm": "hammie_" + name, "ddd": 0, "assets": [], "layers": L}


def main():
    D = Drawing(sys.argv[1])
    out = sys.argv[2]
    os.makedirs(out, exist_ok=True)
    only = sys.argv[3:]
    for name in ROLES:
        if only and name not in only:
            continue
        doc = build(D, name)
        js = json.dumps(doc, separators=(",", ":"))
        open(os.path.join(out, name + ".json"), "w").write(js)
        print("%-8s %-7s %3d frames %3d KB" % (name, ROLES[name][3], doc["op"], len(js) // 1024))


if __name__ == "__main__":
    main()
