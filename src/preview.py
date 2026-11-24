"""Previews as the Dot shows them: full canvas size, on black, 15 fps GIFs.

    preview.py LOTTIE_DIR OUT_DIR
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render
from PIL import Image

src, out = sys.argv[1:3]
os.makedirs(out, exist_ok=True)
for f in sorted(os.listdir(src)):
    if not f.endswith('.json'):
        continue
    doc = json.load(open(os.path.join(src, f)))
    frames = []
    for im in render.frames(doc, step=2, scale=1.0):
        bg = Image.new('RGBA', im.size, (0, 0, 0, 255))
        bg.alpha_composite(im.convert('RGBA'))
        frames.append(bg.convert('RGB').quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE))
    p = os.path.join(out, f[:-5] + '.gif')
    frames[0].save(p, save_all=True, append_images=frames[1:], duration=int(1000 * 2 / doc['fr']), loop=0, optimize=True)
    print(f[:-5], frames[0].size, os.path.getsize(p) // 1024, 'KB')
