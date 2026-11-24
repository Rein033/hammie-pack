"""Render Hammie Lottie files to PNG frames, GIF previews and a contact sheet (checks only;
the Dot plays the Lottie itself)."""
import io
import json
import sys

import resvg_py
from lottie.exporters.svg import export_svg
from lottie.objects import Animation
from PIL import Image

BG = (0, 0, 0, 255)


def frames(doc, step=1, scale=1.0):
    an = Animation.load(doc)
    out = []
    for f in range(int(doc["ip"]), int(doc["op"]), step):
        buf = io.StringIO()
        export_svg(an, buf, f)
        png = resvg_py.svg_to_bytes(svg_string=buf.getvalue(), width=int(doc["w"] * scale), height=int(doc["h"] * scale))
        im = Image.open(io.BytesIO(bytes(png))).convert("RGBA")
        bg = Image.new("RGBA", im.size, BG)
        bg.alpha_composite(im)
        out.append(bg.convert("RGB"))
    return out


def gif(doc, path, scale=0.5, step=2):
    fr = frames(doc, step, scale)
    pal = [f.convert("P", palette=Image.ADAPTIVE, colors=128) for f in fr]
    pal[0].save(path, save_all=True, append_images=pal[1:], duration=int(1000 / doc["fr"] * step), loop=0, disposal=2)
    return fr


def sheet(fr, path, cols=8):
    w, h = fr[0].size
    rows = (len(fr) + cols - 1) // cols
    s = Image.new("RGB", (w * cols, h * rows), (30, 30, 30))
    for k, f in enumerate(fr):
        s.paste(f, ((k % cols) * w, (k // cols) * h))
    s.save(path)


if __name__ == "__main__":
    doc = json.load(open(sys.argv[1]))
    fr = frames(doc, int(sys.argv[3]) if len(sys.argv) > 3 else 1, 0.5)
    sheet(fr, sys.argv[2])
