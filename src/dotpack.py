"""Pack dotrig.py's Lotties as a Kode Dot face pack (kode.json format 1, files zlib'd, sha256 listed).

    dotpack.py LOTTIE_DIR PACK_DIR VERSION
"""
import hashlib, json, os, sys, zlib

SCENE = {"name": "lab", "wake": "wake", "loop": "idle",
         "on": {"look": ["look"], "hour": ["hour"], "notice": ["notice"], "plug": ["charge"], "joke": ["joke", "sleep"]}}
ROLES = {"empty": "doubt", "writing": "work", "goodbye": "bye", "loading": "loading"}
JSON_MAX, FILE_MAX = 96 * 1024, 64 * 1024
DROP = ("nm", "mn", "ix", "markers")


IDENT = {"p": [0, 0], "a": [0, 0], "s": [100, 100], "r": 0, "o": 100}


def identity_tr(it):
    """a group transform that changes nothing: ThorVG treats a group without one the same."""
    if it.get("ty") != "tr":
        return False
    for k, v in it.items():
        if k == "ty":
            continue
        if not isinstance(v, dict) or v.get("a") != 0 or k not in IDENT or v.get("k") != IDENT[k]:
            return False
    return True


def lean(x):
    if isinstance(x, dict):
        if x.get("ty") == "gr" and "it" in x:
            x = dict(x, it=[i for i in x["it"] if not identity_tr(i)])
        return {k: lean(v) for k, v in x.items() if k not in DROP}
    if isinstance(x, list):
        return [lean(v) for v in x]
    if isinstance(x, float):
        r = round(x, 1) if abs(x) >= 2 else round(x, 3)
        return int(r) if r == int(r) else r
    return x


def main():
    src, out, ver = sys.argv[1:4]
    os.makedirs(out, exist_ok=True)
    for f in os.listdir(out):
        os.remove(os.path.join(out, f))
    names = [SCENE["wake"], SCENE["loop"]] + [a for v in SCENE["on"].values() for a in v] + list(ROLES.values())
    sha = {}
    for n in dict.fromkeys(names):
        js = json.dumps(lean(json.load(open(os.path.join(src, n + ".json")))), separators=(",", ":")).encode()
        z = zlib.compress(js, 9)
        if len(js) > JSON_MAX or len(z) > FILE_MAX:
            raise SystemExit("%s: %d bytes json / %d stored, over the Dot's %d / %d" % (n, len(js), len(z), JSON_MAX, FILE_MAX))
        fn = n + ".json.z"
        open(os.path.join(out, fn), "wb").write(z)
        sha[fn] = hashlib.sha256(z).hexdigest()
        print("  %-16s %3d KB json %3d KB stored" % (fn, len(js) // 1024, len(z) // 1024))
    z = lambda n: n + ".json.z"
    kode = {"format": 1, "name": "Hammie", "version": ver, "face": {"default": SCENE["name"], "hours": []},
            "scenes": [{"name": SCENE["name"], "wake": z(SCENE["wake"]), "loop": z(SCENE["loop"]), "anchor": 0,
                        "on": {k: [z(a) for a in v] for k, v in SCENE["on"].items()}}],
            **{r: z(n) for r, n in ROLES.items()}, "sha256": sha}
    json.dump(kode, open(os.path.join(out, "kode.json"), "w"), indent=2)
    print("pack:", len(sha), "files,", sum(os.path.getsize(os.path.join(out, f)) for f in sha) // 1024, "KB")


if __name__ == "__main__":
    main()
