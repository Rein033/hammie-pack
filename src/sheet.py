"""Contact sheet: 5 frames of each animation in DIR, on black, as the Dot shows them."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render
from PIL import Image
d = sys.argv[1]; names = sys.argv[3:] or sorted(f[:-5] for f in os.listdir(d) if f.endswith('.json'))
rows = []
for n in names:
    doc = json.load(open(os.path.join(d, n + '.json')))
    fr = render.gif(doc, os.path.join(d, n + '.gif'), 1.0, 1)
    pick = [fr[int(i * (len(fr) - 1) / 4)] for i in range(5)]
    rows.append(pick)
CW = 410; CH = 369
S = Image.new('RGB', (CW * 5, CH * len(rows)), (60, 60, 60))
for r, pick in enumerate(rows):
    for c, im in enumerate(pick):
        bg = Image.new('RGBA', im.size, (0, 0, 0, 255)); bg.alpha_composite(im.convert('RGBA'))
        S.paste(bg.convert('RGB'), (c * CW, r * CH))
S.save(sys.argv[2]); print(S.size)
