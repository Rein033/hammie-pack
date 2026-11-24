/* SPDX-License-Identifier: MIT */
/* packcheck: run kodeOS's own pack checks (kui_pack.c) on a pack folder, as a Dot does on load. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <zlib.h>
#include "kui_pack.h"

static unsigned char *slurp(const char *path, size_t *len)
{
    FILE *f = fopen(path, "rb");
    if (!f) return NULL;
    fseek(f, 0, SEEK_END); long n = ftell(f); fseek(f, 0, SEEK_SET);
    unsigned char *b = malloc((size_t)n + 1);
    *len = fread(b, 1, (size_t)n, f); b[*len] = 0; fclose(f);
    return b;
}

int main(int argc, char **argv)
{
    if (argc != 2) { fprintf(stderr, "usage: packcheck DIR\n"); return 2; }
    char path[1024];
    size_t len;
    snprintf(path, sizeof path, "%s/kode.json", argv[1]);
    unsigned char *m = slurp(path, &len);
    if (!m) { printf("FAIL kode.json missing\n"); return 1; }
    kui_pack_t p;
    kui_pack_err_t e = kui_pack_parse((const char *)m, len, &p);
    if (e != KUI_PACK_OK) { printf("FAIL kode.json: %s\n", kui_pack_err_word(e)); return 1; }
    printf("manifest ok: name=%s version=%s files=%u scenes=%u reactions=%u hashed=%d\n",
           p.name, p.version, p.n_files, p.n_scenes, p.n_react, kui_pack_hashed(&p));
    int bad = 0;
    for (uint16_t i = 0; i < p.n_files; i++) {
        uint16_t w, h, anchor;
        if (!kui_pack_file_canvas(&p, i, &w, &h, &anchor)) { printf("FAIL %s: canvas role\n", p.files[i].name); bad++; continue; }
        snprintf(path, sizeof path, "%s/%s", argv[1], p.files[i].name);
        size_t zl; unsigned char *z = slurp(path, &zl);
        if (!z) { printf("FAIL %s: missing\n", p.files[i].name); bad++; continue; }
        if (zl > KUI_PACK_FILE_MAX) { printf("FAIL %s: %zu bytes stored > %u\n", p.files[i].name, zl, KUI_PACK_FILE_MAX); bad++; }
        uLongf jl = KUI_PACK_JSON_MAX + 1; unsigned char *j = malloc(jl);
        int zr = uncompress(j, &jl, z, zl);
        if (zr != Z_OK) { printf("FAIL %s: inflate %d (or > %u bytes)\n", p.files[i].name, zr, KUI_PACK_JSON_MAX); bad++; free(z); free(j); continue; }
        kui_pack_anim_t a;
        e = kui_pack_check_anim((const char *)j, jl, w, h, anchor, &a);
        if (e != KUI_PACK_OK) { printf("FAIL %s: %s (%ux%u wanted %ux%u)\n", p.files[i].name, kui_pack_err_word(e), a.w, a.h, w, h); bad++; }
        else printf("ok   %-16s %ux%u %u fps %u frames depth %u precomp %u, %lu bytes json\n", p.files[i].name, a.w, a.h, a.fps, a.frames, a.depth, a.precomp, (unsigned long)jl);
        free(z); free(j);
    }
    kui_pack_free(&p);
    printf(bad ? "PACK REFUSED: %d problem(s)\n" : "PACK OK\n", bad);
    return bad ? 1 : 0;
}
