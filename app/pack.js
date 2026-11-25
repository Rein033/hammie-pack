/* Kode Avatar: checks Lottie animations against kodeOS's face-pack rules and builds the pack.
 * The rules are the ones in kui_pack.c (kode-sdk); the packing is the same as src/dotpack.py.
 * Plain script, no build step: the page loads it, and tests load it in Node 18+. */
(function (g) {
  "use strict";

  const SCENE = { w: 410, h: 334 }, EMPTY = { w: 410, h: 369 }, CARD = { w: 410, h: 160 }, LOAD = { w: 264, h: 264 };

  /* Every animation an avatar has. `file` is the name in the pack, `slot` where kode.json lists it. */
  const ROLES = [
    { file: "wake", slot: "wake", ...SCENE, need: true, title: "Wake up", when: "the face appears after the screen turns on",
      idea: "starts asleep or out of frame, opens its eyes and ends in the exact neutral pose of the idle loop" },
    { file: "idle", slot: "loop", ...SCENE, need: true, title: "Idle (loop)", when: "the face, looping all day",
      idea: "calm breathing, a blink, a small sway; the first and last frame must be identical so it loops without a jump" },
    { file: "look", slot: "on.look", ...SCENE, title: "Look at you", when: "someone picks up or taps the Dot",
      idea: "turns its head or eyes toward the viewer, smiles, then returns to the neutral idle pose" },
    { file: "hour", slot: "on.hour", ...SCENE, title: "On the hour", when: "every full hour",
      idea: "shows a small clock, rings a bell or checks a watch, then returns to the neutral idle pose" },
    { file: "notice", slot: "on.notice", ...SCENE, title: "Notification", when: "a notification arrives",
      idea: "surprised jump, an exclamation mark or an envelope pops up, then returns to the neutral idle pose" },
    { file: "charge", slot: "on.plug", ...SCENE, title: "Charging", when: "the USB cable is plugged in",
      idea: "a lightning bolt or battery fills up, the character looks energised, then returns to the neutral idle pose" },
    { file: "joke", slot: "on.joke", ...SCENE, title: "Joke 1", when: "now and then, at random",
      idea: "laughs, does a little dance or a trick, then returns to the neutral idle pose" },
    { file: "sleep", slot: "on.joke", ...SCENE, title: "Joke 2", when: "now and then, at random",
      idea: "dozes off with floating Z's, wakes with a start, then returns to the neutral idle pose" },
    { file: "doubt", slot: "empty", ...EMPTY, title: "No apps", when: "the launcher when no apps are installed",
      idea: "shrugs or looks around puzzled with a question mark, looping" },
    { file: "work", slot: "writing", ...CARD, title: "Installing", when: "a wide, short card while an app is written",
      idea: "the character small on the left, busy working (typing, hammering), looping" },
    { file: "bye", slot: "goodbye", ...CARD, title: "Goodbye", when: "a wide, short card just before an app starts",
      idea: "the character small on the left, waving goodbye" },
    { file: "loading", slot: "loading", ...LOAD, title: "Loading", when: "the square loading screen",
      idea: "a looping spinner made from the character or its prop, centred" },
  ];

  /* Spanish texts for the roles; English is in ROLES itself. */
  const ROLES_ES = {
    wake: { title: "Despertar", when: "la cara aparece al encenderse la pantalla",
      idea: "empieza dormido o fuera de la imagen, abre los ojos y termina en la misma pose neutra exacta del bucle de reposo" },
    idle: { title: "Reposo (bucle)", when: "la cara, en bucle todo el día",
      idea: "respiración tranquila, un parpadeo, un pequeño balanceo; el primer y el último fotograma deben ser idénticos para que el bucle no salte" },
    look: { title: "Te mira", when: "alguien levanta o toca el Dot",
      idea: "gira la cabeza o los ojos hacia quien mira, sonríe y vuelve a la pose neutra de reposo" },
    hour: { title: "En punto", when: "cada hora en punto",
      idea: "muestra un pequeño reloj, toca una campana o mira un reloj de pulsera, y vuelve a la pose neutra de reposo" },
    notice: { title: "Notificación", when: "llega una notificación",
      idea: "salta sorprendido, aparece un signo de exclamación o un sobre, y vuelve a la pose neutra de reposo" },
    charge: { title: "Cargando", when: "se conecta el cable USB",
      idea: "un rayo o una batería se llena, el personaje se ve con energía, y vuelve a la pose neutra de reposo" },
    joke: { title: "Broma 1", when: "de vez en cuando, al azar",
      idea: "se ríe, baila un poco o hace un truco, y vuelve a la pose neutra de reposo" },
    sleep: { title: "Broma 2", when: "de vez en cuando, al azar",
      idea: "se queda dormido con zetas flotando, se despierta de golpe, y vuelve a la pose neutra de reposo" },
    doubt: { title: "Sin apps", when: "el lanzador cuando no hay apps instaladas",
      idea: "se encoge de hombros o mira alrededor confundido con un signo de interrogación, en bucle" },
    work: { title: "Instalando", when: "una tarjeta ancha y baja mientras se escribe una app",
      idea: "el personaje pequeño a la izquierda, trabajando (tecleando, martillando), en bucle" },
    bye: { title: "Adiós", when: "una tarjeta ancha y baja justo antes de que arranque una app",
      idea: "el personaje pequeño a la izquierda, diciendo adiós con la mano" },
    loading: { title: "Cargando app", when: "la pantalla cuadrada de carga",
      idea: "un indicador de carga en bucle hecho con el personaje o su objeto, centrado" },
  };

  let LANG = "en";
  /* Messages the checks and the packer show, in each language. */
  const MSG = {
    en: {
      notLottie: "not a Lottie object",
      noLayers: "no \"layers\" list: this is not a Lottie animation",
      canvas: (aw, ah, w, h) => `canvas is ${aw} x ${ah}, must be exactly ${w} x ${h} (use "Fit to canvas")`,
      fps: (fr) => `frame rate "fr" is ${fr}, must be a whole number 1-60 (30 is best)`,
      frames: (ip, op) => `frames: ip ${ip} to op ${op} must be whole numbers, 1-1800 frames apart`,
      precomp: (pc, max) => `precomps nest ${pc === Infinity ? "in a loop" : pc + " deep"}, at most ${max}`,
      big: (kb) => `${kb} KB of JSON, at most 96 KB: ask for fewer shapes or keyframes`,
      deep: (d, max) => `JSON nests ${d} deep, at most ${max}: ask for flatter groups`,
      empty: "no layers: the screen stays black",
      rExpr: "expressions (JavaScript in the animation) are not run on the Dot",
      rImg: "image layers: the pack carries no image files, draw with shapes instead",
      rText: "text layers: fonts are not in the pack, draw letters as shapes instead",
      rFx: "effects (blur, glow, shadow) are not drawn on the Dot",
      r3d: "3D layers are drawn flat",
      rAsset: (p) => `image assets (${p}): draw with shapes instead`,
      info: (w, h, fr, f, s, kb) => `${w}x${h}, ${fr} fps, ${f} frames (${s} s), ${kb} KB`,
      noJson: "no JSON found",
      needed: (t) => `${t} is needed`,
      stored: (t, kb) => `${t}: ${kb} KB stored, at most 64 KB`,
    },
    es: {
      notLottie: "no es un objeto Lottie",
      noLayers: "no hay lista \"layers\": esto no es una animación Lottie",
      canvas: (aw, ah, w, h) => `el lienzo es ${aw} x ${ah}, debe ser exactamente ${w} x ${h} (usa "Ajustar al lienzo")`,
      fps: (fr) => `la velocidad "fr" es ${fr}, debe ser un número entero de 1 a 60 (30 es lo mejor)`,
      frames: (ip, op) => `fotogramas: ip ${ip} a op ${op} deben ser números enteros, con 1-1800 fotogramas de diferencia`,
      precomp: (pc, max) => `las precomposiciones se anidan ${pc === Infinity ? "en un bucle" : pc + " niveles"}, como máximo ${max}`,
      big: (kb) => `${kb} KB de JSON, como máximo 96 KB: pide menos formas o fotogramas clave`,
      deep: (d, max) => `el JSON se anida ${d} niveles, como máximo ${max}: pide grupos más planos`,
      empty: "no hay capas: la pantalla queda negra",
      rExpr: "las expresiones (JavaScript en la animación) no se ejecutan en el Dot",
      rImg: "capas de imagen: el pack no lleva imágenes, dibuja con formas",
      rText: "capas de texto: el pack no lleva fuentes, dibuja las letras como formas",
      rFx: "los efectos (desenfoque, brillo, sombra) no se dibujan en el Dot",
      r3d: "las capas 3D se dibujan planas",
      rAsset: (p) => `imágenes (${p}): dibuja con formas`,
      info: (w, h, fr, f, s, kb) => `${w}x${h}, ${fr} fps, ${f} fotogramas (${s} s), ${kb} KB`,
      noJson: "no se encontró JSON",
      needed: (t) => `${t} es obligatorio`,
      stored: (t, kb) => `${t}: ${kb} KB guardados, como máximo 64 KB`,
    },
  };
  const T = (k, ...a) => { const m = (MSG[LANG] || MSG.en)[k] ?? MSG.en[k]; return typeof m === "function" ? m(...a) : m; };
  const setLang = (l) => { LANG = MSG[l] ? l : "en"; };
  /* A role with its texts in the current language. */
  const text = (role) => (LANG === "es" ? { ...role, ...ROLES_ES[role.file] } : role);

  const LIMIT = { json: 96 * 1024, stored: 64 * 1024, depth: 32, precomp: 2, fps: 60, frames: 1800, text: 31 };
  const DROP = new Set(["nm", "mn", "ix", "markers", "meta", "props"]);
  const IDENT = { p: [0, 0], a: [0, 0], s: [100, 100], r: 0, o: 100 };
  const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);

  function identityTr(it) {
    if (!it || it.ty !== "tr") return false;
    for (const [k, v] of Object.entries(it)) {
      if (k === "ty") continue;
      if (!(k in IDENT) || !v || typeof v !== "object" || v.a !== 0 || !same(v.k, IDENT[k])) return false;
    }
    return true;
  }

  /* Smaller JSON, same picture: drop names and markers, round numbers (as dotpack.py does). */
  function lean(x) {
    if (Array.isArray(x)) return x.map(lean);
    if (x && typeof x === "object") {
      if (x.ty === "gr" && Array.isArray(x.it)) x = { ...x, it: x.it.filter((i) => !identityTr(i)) };
      const o = {};
      for (const [k, v] of Object.entries(x)) if (!DROP.has(k)) o[k] = lean(v);
      return o;
    }
    if (typeof x === "number" && !Number.isInteger(x)) {
      const r = Math.abs(x) >= 2 ? Math.round(x * 10) / 10 : Math.round(x * 1000) / 1000;
      return r === 0 ? 0 : r;
    }
    return x;
  }

  /* Deepest nesting of {} and [], counted like kui_pack_json_depth(). */
  function depth(text) {
    let d = 0, max = 0, str = false;
    for (let i = 0; i < text.length; i++) {
      const c = text[i];
      if (str) { if (c === "\\") i++; else if (c === '"') str = false; continue; }
      if (c === '"') str = true;
      else if (c === "{" || c === "[") { d++; if (d > max) max = d; }
      else if (c === "}" || c === "]") { if (d > 0) d--; }
    }
    return max;
  }

  /* Longest chain of precomps the root reaches (0 = none). */
  function precompDepth(root) {
    const assets = new Map((root.assets || []).filter((a) => Array.isArray(a.layers)).map((a) => [a.id, a]));
    let level = 0, layers = [root.layers];
    const seen = new Set();
    while (layers.length) {
      const next = [];
      for (const ls of layers) for (const l of ls || []) {
        if (l && l.ty === 0 && assets.has(l.refId)) {
          if (seen.has(l.refId) && level > assets.size) return Infinity;
          seen.add(l.refId);
          next.push(assets.get(l.refId).layers);
        }
      }
      if (!next.length) break;
      level++;
      if (level > assets.size) return Infinity; // a loop
      layers = next;
    }
    return level;
  }

  /* Things kodeOS's renderer (ThorVG) may not draw, or that need files the pack cannot carry. */
  function risks(root) {
    const out = new Set();
    const walk = (x, inLayer) => {
      if (Array.isArray(x)) return x.forEach((v) => walk(v, inLayer));
      if (!x || typeof x !== "object") return;
      if (typeof x.x === "string") out.add(T("rExpr"));
      if (x.ty === 2) out.add(T("rImg"));
      if (x.ty === 5) out.add(T("rText"));
      if (Array.isArray(x.ef) && x.ef.length) out.add(T("rFx"));
      if (x.ddd === 1) out.add(T("r3d"));
      for (const v of Object.values(x)) walk(v, inLayer);
    };
    walk(root.layers);
    for (const a of root.assets || []) {
      if (a.p && !a.layers) out.add(T("rAsset", a.p.length > 40 ? a.p.slice(0, 40) + "…" : a.p));
      if (a.layers) walk(a.layers);
    }
    return [...out];
  }

  /* Pull a Lottie object out of what an AI answered: raw JSON, a ```json block, or text around it. */
  function extract(text) {
    text = String(text || "").trim();
    const fence = text.match(/```(?:json|lottie)?\s*([\s\S]*?)```/i);
    if (fence) text = fence[1].trim();
    try { return JSON.parse(text); } catch (e) { /* fall through */ }
    const a = text.indexOf("{"), b = text.lastIndexOf("}");
    if (a >= 0 && b > a) return JSON.parse(text.slice(a, b + 1));
    throw new Error(T("noJson"));
  }

  const isWhole = (n, lo, hi) => typeof n === "number" && Number.isInteger(n) && n >= lo && n <= hi;

  /* Check one animation for a role. Returns {ok, errors[], warnings[], info, bytes}. */
  function check(anim, role) {
    const errors = [], warnings = [];
    if (!anim || typeof anim !== "object" || Array.isArray(anim)) return { ok: false, errors: [T("notLottie")], warnings };
    if (!Array.isArray(anim.layers)) errors.push(T("noLayers"));
    if (anim.w !== role.w || anim.h !== role.h)
      errors.push(T("canvas", anim.w, anim.h, role.w, role.h));
    if (!isWhole(anim.fr, 1, LIMIT.fps)) errors.push(T("fps", anim.fr));
    const f = anim.op - anim.ip;
    if (!isWhole(anim.ip, 0, 1e6) || !isWhole(anim.op, 0, 1e6) || !(f >= 1 && f <= LIMIT.frames))
      errors.push(T("frames", anim.ip, anim.op));
    const pc = Array.isArray(anim.layers) ? precompDepth(anim) : 0;
    if (pc > LIMIT.precomp) errors.push(T("precomp", pc, LIMIT.precomp));
    const text = JSON.stringify(lean(anim));
    const bytes = new TextEncoder().encode(text).length;
    const d = depth(text);
    if (bytes > LIMIT.json) errors.push(T("big", (bytes / 1024).toFixed(1)));
    if (d > LIMIT.depth) errors.push(T("deep", d, LIMIT.depth));
    warnings.push(...risks(anim));
    if (anim.layers && !anim.layers.length) warnings.push(T("empty"));
    return { ok: !errors.length, errors, warnings, bytes, text,
      info: T("info", anim.w, anim.h, anim.fr, f, (f / anim.fr).toFixed(1), (bytes / 1024).toFixed(1)) };
  }

  /* Scale an animation into another canvas, centred, by wrapping it in one precomp. */
  function fit(anim, w, h, mode) {
    const ow = anim.w, oh = anim.h;
    const s = (mode === "fill" ? Math.max : Math.min)(w / ow, h / oh) * 100;
    const id = "_fit" + Math.random().toString(36).slice(2, 7);
    const v = (k) => ({ a: 0, k });
    return {
      v: anim.v || "5.7.0", fr: anim.fr, ip: anim.ip, op: anim.op, w, h,
      assets: [...(anim.assets || []), { id, layers: anim.layers }],
      layers: [{ ty: 0, ind: 1, refId: id, w: ow, h: oh, ip: anim.ip, op: anim.op, st: 0, sr: 1,
        ks: { o: v(100), r: v(0), p: v([w / 2, h / 2, 0]), a: v([ow / 2, oh / 2, 0]), s: v([s, s, 100]) } }],
    };
  }

  /* Lengthen or shorten nothing; just round fr/ip/op that are almost whole (AIs write 29.97, 120.0001). */
  function tidy(anim) {
    const r = (n) => (typeof n === "number" && Math.abs(n - Math.round(n)) < 0.05 ? Math.round(n) : n);
    return { ...anim, fr: r(anim.fr), ip: r(anim.ip), op: r(anim.op), w: r(anim.w), h: r(anim.h) };
  }

  async function streamBytes(bytes, stream) {
    const s = new Blob([bytes]).stream().pipeThrough(stream);
    return new Uint8Array(await new Response(s).arrayBuffer());
  }
  const zlib = (bytes) => streamBytes(bytes, new CompressionStream("deflate"));
  const unzlib = (bytes) => streamBytes(bytes, new DecompressionStream("deflate"));
  async function sha256(bytes) {
    const h = new Uint8Array(await crypto.subtle.digest("SHA-256", bytes));
    return [...h].map((b) => b.toString(16).padStart(2, "0")).join("");
  }

  /* Build the pack: {files: {name: Uint8Array}, manifest}. anims maps role.file to a Lottie object. */
  async function build(anims, name, version) {
    name = String(name || "Avatar").trim().slice(0, LIMIT.text) || "Avatar";
    version = String(version).slice(0, LIMIT.text);
    const files = {}, sha = {};
    const z = (f) => f + ".json.z";
    for (const role of ROLES) {
      const a = anims[role.file];
      if (!a) { if (role.need) throw new Error(T("needed", text(role).title)); continue; }
      const c = check(a, role);
      if (!c.ok) throw new Error(text(role).title + ": " + c.errors[0]);
      const data = await zlib(new TextEncoder().encode(c.text));
      if (data.length > LIMIT.stored) throw new Error(T("stored", text(role).title, (data.length / 1024).toFixed(1)));
      files[z(role.file)] = data;
      sha[z(role.file)] = await sha256(data);
    }
    const on = {};
    for (const role of ROLES) if (role.slot.startsWith("on.") && files[z(role.file)]) (on[role.slot.slice(3)] ||= []).push(z(role.file));
    const manifest = { format: 1, name, version, face: { default: "face", hours: [] },
      scenes: [{ name: "face", wake: z("wake"), loop: z("idle"), anchor: 0, on }] };
    for (const role of ROLES) if (!role.slot.includes(".") && !["wake", "loop"].includes(role.slot) && files[z(role.file)])
      manifest[role.slot] = z(role.file);
    manifest.sha256 = sha;
    files["kode.json"] = new TextEncoder().encode(JSON.stringify(manifest, null, 2));
    return { files, manifest };
  }

  /* A plain ZIP (stored, no compression: the .json.z files are compressed already). */
  const CRC = (() => { const t = new Uint32Array(256); for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; t[n] = c >>> 0; } return t; })();
  const crc32 = (b) => { let c = 0xffffffff; for (let i = 0; i < b.length; i++) c = CRC[(c ^ b[i]) & 0xff] ^ (c >>> 8); return (c ^ 0xffffffff) >>> 0; };
  function zip(entries) {
    const enc = new TextEncoder(), parts = [], central = [];
    let off = 0;
    const le = (n, len) => { const b = new Uint8Array(len); for (let i = 0; i < len; i++) b[i] = (n >>> (8 * i)) & 0xff; return b; };
    const cat = (...a) => { const o = new Uint8Array(a.reduce((s, x) => s + x.length, 0)); let p = 0; for (const x of a) { o.set(x, p); p += x.length; } return o; };
    for (const [path, data] of Object.entries(entries)) {
      const nm = enc.encode(path), crc = crc32(data);
      const head = cat(le(0x04034b50, 4), le(20, 2), le(0, 2), le(0, 2), le(0, 2), le(0x21, 2), le(crc, 4), le(data.length, 4), le(data.length, 4), le(nm.length, 2), le(0, 2), nm);
      central.push(cat(le(0x02014b50, 4), le(20, 2), le(20, 2), le(0, 2), le(0, 2), le(0, 2), le(0x21, 2), le(crc, 4), le(data.length, 4), le(data.length, 4), le(nm.length, 2), le(0, 2), le(0, 2), le(0, 2), le(0, 2), le(0, 4), le(off, 4), nm));
      parts.push(head, data);
      off += head.length + data.length;
    }
    const cd = cat(...central);
    return cat(...parts, cd, cat(le(0x06054b50, 4), le(0, 2), le(0, 2), le(central.length, 2), le(central.length, 2), le(cd.length, 4), le(off, 4), le(0, 2)));
  }

  /* The prompt a person pastes into Claude or ChatGPT for one animation, in the current language. */
  function prompt(role, character, style) {
    const r = text(role), es = LANG === "es";
    const loops = role.slot === "loop" || ["doubt", "work", "loading"].includes(role.file);
    const ch = String(character || "").trim() || (es ? "(describe aquí a tu personaje)" : "(describe your character here)");
    const st = style && style.trim() ? style.trim() : null;
    if (es) return [
      `Haz una animación Lottie (JSON de Bodymovin) para la pantalla de un pequeño aparato, el Kode Dot.`,
      ``,
      `Personaje: ${ch}`,
      `Estilo: ${st || "dibujo vectorial plano, contornos oscuros gruesos, pocos colores sólidos, sobre fondo transparente (la pantalla es negra)."}`,
      ``,
      `Esta animación: "${r.title}", se reproduce cuando: ${r.when}.`,
      `Qué pasa: ${r.idea}.`,
      ``,
      `Reglas estrictas (si no, el aparato rechaza el archivo):`,
      `- "w": ${role.w}, "h": ${role.h} exactamente. Mantén el personaje dentro de este lienzo${role.h === 160 ? " (ancho y bajo: dibújalo pequeño)" : ""}.`,
      `- "fr": 30, "ip": 0, "op": entre 60 y 150. Solo números enteros.`,
      `- Todo el JSON por debajo de 90 KB: pocas formas, pocos fotogramas clave, números con 2 decimales como máximo.`,
      `- Solo capas de forma ("ty": 4) y capas nulas. Sin imágenes, sin capas de texto, sin expresiones, sin efectos, sin 3D.`,
      `- Como máximo un nivel de precomposiciones; mejor ninguno. Grupos anidados 6 niveles como máximo.`,
      `- Cada grupo de formas necesita su propio relleno ("fl") y/o trazo ("st") y una transformación ("tr").`,
      loops ? `- Es un bucle: el último fotograma debe verse exactamente igual que el primero.`
            : `- Empieza y termina en la misma pose neutra que el bucle de reposo, para que enlace bien.`,
      `- Mantén el personaje del mismo tamaño y en el mismo sitio que en las demás animaciones del conjunto.`,
      role.file !== "idle"
        ? `- Si este chat ya contiene la animación de reposo, reutiliza exactamente sus formas y colores; cambia solo el movimiento.`
        : `- Construye el personaje con grupos con nombre (cabeza, ojos, boca, cuerpo, brazos) para reutilizarlos en las demás animaciones.`,
      ``,
      `Responde solo con el JSON completo, en un único bloque de código \`\`\`json, sin explicación. No lo acortes con "..." en ninguna parte.`,
    ].join("\n");
    return [
      `Make a Lottie animation (Bodymovin JSON) for the screen of a small gadget, the Kode Dot.`,
      ``,
      `Character: ${ch}`,
      `Style: ${st || "flat vector cartoon, thick dark outlines, a few solid colours, on a transparent background (the screen is black)."}`,
      ``,
      `This animation: "${r.title}", played when: ${r.when}.`,
      `What happens: ${r.idea}.`,
      ``,
      `Hard rules (the device refuses the file otherwise):`,
      `- "w": ${role.w}, "h": ${role.h} exactly. Keep the character inside this canvas${role.h === 160 ? " (wide and short: draw it small)" : ""}.`,
      `- "fr": 30, "ip": 0, "op": between 60 and 150. Whole numbers only.`,
      `- The whole JSON under 90 KB: few shapes, few keyframes, numbers with at most 2 decimals.`,
      `- Only shape layers ("ty": 4) and null layers. No images, no text layers, no expressions, no effects, no 3D.`,
      `- At most one level of precomps; better none. Group nesting at most 6 deep.`,
      `- Every shape group needs its own fill ("fl") and/or stroke ("st") and a transform ("tr").`,
      loops ? `- It loops: the last frame must look exactly like the first.`
            : `- Start and end in the same neutral pose as the idle loop, so it blends back.`,
      `- Keep the character the same size and in the same place as in the other animations of this set.`,
      role.file !== "idle"
        ? `- If this chat already holds the idle animation, reuse its character shapes and colours exactly; change only the motion.`
        : `- Build the character from named groups (head, eyes, mouth, body, arms) so later animations can reuse them.`,
      ``,
      `Answer with the complete JSON only, in one \`\`\`json code block, no explanation. Do not shorten it with "..." anywhere.`,
    ].join("\n");
  }

  g.KodeAvatar = { ROLES, ROLES_ES, setLang, text, T, LIMIT, lean, depth, precompDepth, check, fit, tidy, extract, build, zip, prompt, zlib, unzlib, sha256 };
})(typeof window !== "undefined" ? window : globalThis);
