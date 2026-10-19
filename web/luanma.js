/* luanma — CJK mojibake repair. Browser/Node port of the Python package.
 * Expects globalThis.LUANMA_DATA = {top, topTrad, words} (generated). MIT License. */
(function (root) {
  "use strict";
  const DATA = root.LUANMA_DATA;
  const ENCODINGS = ["utf-8", "gbk", "big5", "shift_jis", "euc_kr", "cp1252", "latin-1", "cp437"];
  const LABEL = { "utf-8": "UTF-8", gbk: "GBK", big5: "Big5", shift_jis: "Shift-JIS", euc_kr: "EUC-KR",
    cp1252: "Windows-1252", "latin-1": "Latin-1", cp437: "CP437(DOS)" };
  const WHATWG = { "utf-8": "utf-8", gbk: "gbk", big5: "big5", shift_jis: "shift_jis", euc_kr: "euc-kr", cp1252: "windows-1252" };
  const DBCS = new Set(["gbk", "big5", "shift_jis", "euc_kr"]);
  const PLACEHOLDER = 0x1a;
  const FFFD = "\ufffd";
  const CP437_HIGH = "ÇüéâäàåçêëèïîìÄÅÉæÆôöòûùÿÖÜ¢£¥₧ƒáíóúñÑªº¿⌐¬½¼¡«»░▒▓│┤╡╢╖╕╣║╗╝╜╛┐└┴┬├─┼╞╟╚╔╩╦╠═╬╧╨╤╥╙╘╒╓╫╪┘┌█▄▌▐▀αßΓπΣσµτΦΘΩδ∞φε∩≡±≥≤⌠⌡÷≈°∙·√ⁿ²■\u00a0";

  /* ---------------- codecs ---------------- */
  const decoders = {}, fatalDecoders = {};
  const dec = (enc, fatal) => {
    const cache = fatal ? fatalDecoders : decoders;
    return cache[enc] || (cache[enc] = new TextDecoder(WHATWG[enc], { fatal }));
  };
  class Lost extends Error {}

  function decode(bytes, enc, lossy) {
    if (enc === "latin-1") return String.fromCharCode.apply(null, Array.from(bytes));
    if (enc === "cp437") {
      let s = "";
      for (const b of bytes) s += b < 0x80 ? String.fromCharCode(b) : CP437_HIGH[b - 0x80];
      return s;
    }
    if (lossy) return dec(enc, false).decode(bytes);
    try { return dec(enc, true).decode(bytes); } catch (e) { throw new Lost(); }
  }

  /* characters that Windows code pages (cp950 / cp932, as used by the Python version) encode differently from (or
     that are missing in) some TextDecoder implementations (char + 4 hex digits of its bytes; 00xx = single byte) */
  const EXTRA = {
    big5: "Ёc7b3Дc7b1Еc7b2Жc7b4Зc7b5Иc7b6Йc7b7Кc7b8Лc7b9Мc7baУc7bbФc7bcХc7bdЦc7beЧc7bfШc7c0Щc7c1Ъc7c2Ыc7c3Ьc7c4Эc7c5Юc7c6Яc7c7аc7c8бc7c9вc7caгc7cbдc7ccеc7cdжc7cfзc7d0иc7d1йc7d2кc7d3лc7d4мc7d5нc7d6оc7d7пc7d8рc7d9сc7daтc7dbуc7dcфc7ddхc7deцc7dfчc7e0шc7e1щc7e2ъc7e3ыc7e4ьc7e5эc7e6юc7e7яc7e8ёc7ce①c7e9②c7ea③c7eb④c7ec⑤c7ed⑥c7ee⑦c7ef⑧c7f0⑨c7f1⑩c7f2⑴c7f3⑵c7f4⑶c7f5⑷c7f6⑸c7f7⑹c7f8⑺c7f9⑻c7fa⑼c7fb⑽c7fc▓f9fe々c6a4ぁc6a5あc6a6ぃc6a7いc6a8ぅc6a9うc6aaぇc6abえc6acぉc6adおc6aeかc6afがc6b0きc6b1ぎc6b2くc6b3ぐc6b4けc6b5げc6b6こc6b7ごc6b8さc6b9ざc6baしc6bbじc6bcすc6bdずc6beせc6bfぜc6c0そc6c1ぞc6c2たc6c3だc6c4ちc6c5ぢc6c6っc6c7つc6c8づc6c9てc6caでc6cbとc6ccどc6cdなc6ceにc6cfぬc6d0ねc6d1のc6d2はc6d3ばc6d4ぱc6d5ひc6d6びc6d7ぴc6d8ふc6d9ぶc6daぷc6dbへc6dcべc6ddぺc6deほc6dfぼc6e0ぽc6e1まc6e2みc6e3むc6e4めc6e5もc6e6ゃc6e7やc6e8ゅc6e9ゆc6eaょc6ebよc6ecらc6edりc6eeるc6efれc6f0ろc6f1ゎc6f2わc6f3ゐc6f4ゑc6f5をc6f6んc6f7ゝc6a2ゞc6a3ァc6f8アc6f9ィc6faイc6fbゥc6fcウc6fdェc6feエc740ォc741オc742カc743ガc744キc745ギc746クc747グc748ケc749ゲc74aコc74bゴc74cサc74dザc74eシc74fジc750スc751ズc752セc753ゼc754ソc755ゾc756タc757ダc758チc759ヂc75aッc75bツc75cヅc75dテc75eデc75fトc760ドc761ナc762ニc763ヌc764ネc765ノc766ハc767バc768パc769ヒc76aビc76bピc76cフc76dブc76eプc76fヘc770ベc771ペc772ホc773ボc774ポc775マc776ミc777ムc778メc779モc77aャc77bヤc77cュc77dユc77eョc7a1ヨc7a2ラc7a3リc7a4ルc7a5レc7a6ロc7a7ヮc7a8ワc7a9ヰc7aaヱc7abヲc7acンc7adヴc7aeヵc7afヶc7b0ヾc6a1仝c969十a451卅a4ca",
    shift_jis: "008000a000fd00fe00ff",
  };
  const encMaps = {};
  function encMap(enc) {
    if (encMaps[enc]) return encMaps[enc];
    const m = new Map();
    if (enc === "latin-1") for (let b = 0; b < 256; b++) m.set(String.fromCharCode(b), [b]);
    else if (enc === "cp437") {
      for (let b = 0; b < 128; b++) m.set(String.fromCharCode(b), [b]);
      for (let b = 128; b < 256; b++) m.set(CP437_HIGH[b - 128], [b]);
    } else {
      const d = dec(enc, true);
      for (let b = 0; b < 0x80; b++) m.set(String.fromCharCode(b), [b]);
      for (let b = 0x80; b < 0x100; b++) {
        try { const c = d.decode(new Uint8Array([b])); if (c.length && !m.has(c)) m.set(c, [b]); } catch (e) {}
      }
      if (DBCS.has(enc)) {
        const pair = new Uint8Array(2);
        // Big5: prefer standard rows over the HKSCS extension rows 0x81–0xA0 (as Windows cp950 does)
        const leads = range(0x81, 0xff);
        if (enc === "big5") leads.sort((x, y) => (x < 0xa1) - (y < 0xa1) || x - y);
        for (const a of leads) for (let b = 0x40; b < 0xff; b++) {
          pair[0] = a; pair[1] = b;
          try { const c = d.decode(pair); if (Array.from(c).length === 1 && !m.has(c)) m.set(c, [a, b]); } catch (e) {}
        }
      }
      if (EXTRA[enc]) for (const [, c, h] of EXTRA[enc].matchAll(/(.)([0-9a-f]{4})/gu))
        m.set(c, h.startsWith("00") ? [parseInt(h, 16)] : [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2), 16)]);
      if (enc === "gbk") m.set("\u20ac", [0x80]);
      if (enc === "gbk")   // GB18030-2005 private-use code points (Windows / Python) that WHATWG maps elsewhere
        for (const [c, a] of [[0xe5e5, 0xa3a0], [0xe78d, 0xa6d9], [0xe78e, 0xa6da], [0xe78f, 0xa6db], [0xe790, 0xa6dc],
          [0xe791, 0xa6dd], [0xe792, 0xa6de], [0xe793, 0xa6df], [0xe794, 0xa6ec], [0xe795, 0xa6ed], [0xe796, 0xa6f3],
          [0xe7c7, 0xa8bc], [0xe81e, 0xfe59], [0xe826, 0xfe61], [0xe82b, 0xfe66], [0xe82c, 0xfe67], [0xe832, 0xfe6d],
          [0xe843, 0xfe7e], [0xe854, 0xfe90], [0xe864, 0xfea0]])
          if (!m.has(String.fromCharCode(c))) m.set(String.fromCharCode(c), [a >> 8, a & 0xff]);
    }
    return (encMaps[enc] = m);
  }
  let gb4 = null;
  function gb18030Four(ch) {
    const cp = ch.codePointAt(0);
    if (cp >= 0x10000) {
      let i = cp - 0x10000;
      const b4 = 0x30 + i % 10; i = Math.floor(i / 10);
      const b3 = 0x81 + i % 126; i = Math.floor(i / 126);
      const b2 = 0x30 + i % 10, b1 = 0x90 + Math.floor(i / 10);
      return [b1, b2, b3, b4];
    }
    if (!gb4) {
      gb4 = new Map();
      const d = dec("gbk", true), q = new Uint8Array(4);
      for (let a = 0x81; a <= 0x84; a++) for (let b = 0x30; b <= 0x39; b++)
        for (let c = 0x81; c < 0xff; c++) for (let e = 0x30; e <= 0x39; e++) {
          q[0] = a; q[1] = b; q[2] = c; q[3] = e;
          try { const s = d.decode(q); if (s.length === 1 && !gb4.has(s)) gb4.set(s, [a, b, c, e]); } catch (x) {}
        }
    }
    return gb4.get(ch) || null;
  }
  const utf8 = new TextEncoder();

  /** text -> bytes in `enc`; U+FFFD becomes a placeholder byte unless keepFffd. Returns null if impossible. */
  function encode(text, enc, keepFffd) {
    if (!keepFffd) text = text.split(FFFD).join("\x1a");
    if (enc === "utf-8") return utf8.encode(text);
    const m = encMap(enc), out = [];
    for (const ch of text) {
      let b = m.get(ch);
      if (!b && enc === "gbk") b = gb18030Four(ch);
      if (!b && ch === FFFD) b = [PLACEHOLDER];
      if (!b && enc === "cp1252" && [0x81, 0x8d, 0x8f, 0x90, 0x9d].includes(ch.charCodeAt(0))) b = [ch.charCodeAt(0)];
      if (!b) return null;
      for (const x of b) out.push(x);
    }
    return Uint8Array.from(out);
  }

  /* first invalid position for strict UTF-8, or -1 */
  function utf8ErrorStart(d) {
    let i = 0;
    const n = d.length;
    while (i < n) {
      const b = d[i];
      if (b < 0x80) { i++; continue; }
      let need, lo = 0x80, hi = 0xbf;
      if (b >= 0xc2 && b <= 0xdf) need = 1;
      else if (b >= 0xe0 && b <= 0xef) { need = 2; if (b === 0xe0) lo = 0xa0; if (b === 0xed) hi = 0x9f; }
      else if (b >= 0xf0 && b <= 0xf4) { need = 3; if (b === 0xf0) lo = 0x90; if (b === 0xf4) hi = 0x8f; }
      else return i;
      for (let k = 1; k <= need; k++) {
        const c = d[i + k];
        if (c === undefined) return i;
        if (k === 1 ? (c < lo || c > hi) : (c < 0x80 || c > 0xbf)) return i;
      }
      i += need + 1;
    }
    return -1;
  }

  /* ---------------- scoring ---------------- */
  const RANK = new Map();
  (function () {   // simplified and traditional lists are aligned and share ranks
    const a = Array.from(DATA.top), b = Array.from(DATA.topTrad);
    for (let i = 0; i < a.length; i++) {
      if (!RANK.has(a[i])) RANK.set(a[i], i);
      if (!RANK.has(b[i])) RANK.set(b[i], i);
    }
  })();
  const WORDS = new Set(DATA.words.split(" "));

  function table(enc, leads, trails) {
    const out = new Set(), d = dec(enc, true), p = new Uint8Array(2);
    for (const a of leads) for (const b of trails) {
      p[0] = a; p[1] = b;
      try { out.add(d.decode(p)); } catch (e) {}
    }
    return out;
  }
  const range = (a, b) => Array.from({ length: b - a }, (_, i) => a + i);
  const TA1 = range(0xa1, 0xff);
  const GB_L1 = table("gbk", range(0xb0, 0xd8), TA1);
  const GB_L2 = table("gbk", range(0xd8, 0xf8), TA1);
  const BIG5_COMMON = table("big5", range(0xa4, 0xc7), range(0x40, 0x7f).concat(TA1));
  const JIS_L1 = table("shift_jis", range(0x88, 0x99), range(0x40, 0x7f).concat(range(0x80, 0xfd)));
  const KS_HANGUL = table("euc_kr", range(0xb0, 0xc9), TA1);
  const CJK_PUNCT = new Set("，。、；：？！“”‘’（）《》〈〉【】「」『』…—·～￥　");
  const KANA_ORDER = "いうんしのかたとてなにはるがでくすまこれもっりあらよおけさきつだそやめえせわみねひどろじばゆほぶげちずへべごぐぜびぞょゃゅぱぽぴぷぺ";
  const RARE_KANA = new Set("ぁぃぅぇぉゎゐゑゔゕゖヮヰヱヵヶヷヸヹヺ");
  const CP437_GREEK = new Set("αΓπΣστΦΘΩδφε");
  const LATIN_SYMBOLS = new Set("¡¢£¤¥¦§¨©ª«¬\xad®¯°±²³´µ¶·¸¹º»¼½¾¿×÷ƒˆ˜‰‹›•–—™šœžŸŠŒŽ€");
  const RE_L = /^\p{L}$/u, RE_MARK = /^[\p{Mn}\p{Mc}\p{Me}\p{Cf}]$/u, RE_ND = /^\p{Nd}$/u, RE_SO = /^\p{So}$/u;
  const RE_SPACE = /^\s$/u;

  const csCache = new Map();
  function charScore(ch) {
    let v = csCache.get(ch);
    if (v === undefined) { v = charScore0(ch); csCache.set(ch, v); }
    return v;
  }
  function charScore0(ch) {
    const o = ch.codePointAt(0);
    if (ch === FFFD) return -4;
    if (ch === "¿" || ch === "¡") return 0;
    if (ch === "锟") return -3;
    if (ch === "，" || ch === "。") return 3;
    if (o === 0x1a || (o < 0x20 && !"\t\n\r".includes(ch)) || (o >= 0x7f && o < 0xa0)) return -5;
    if (o < 0x80) return 0.5;
    const r = RANK.get(ch);
    if (r !== undefined) return r < 500 ? 4.5 : r < 1500 ? 3.8 : 3.2;
    if (GB_L1.has(ch)) return 3;
    if (CJK_PUNCT.has(ch)) return 2.5;
    if (RARE_KANA.has(ch)) return 1;
    if (KANA_ORDER.slice(0, 20).includes(ch)) return 3.8;
    if (o >= 0x3041 && o <= 0x30ff) return 3.5;
    if (KS_HANGUL.has(ch)) return 3.5;
    if (BIG5_COMMON.has(ch) || JIS_L1.has(ch)) return 2.2;
    if (GB_L2.has(ch)) return 1;
    if (o >= 0xff61 && o <= 0xff9f) return -2;
    if (o >= 0xac00 && o <= 0xd7a3) return -1.5;
    if (o >= 0x4e00 && o <= 0x9fff) return -1.5;
    if ((o >= 0x3400 && o <= 0x4dbf) || o >= 0x20000) return -3;
    if (o >= 0xe000 && o <= 0xf8ff) return -5;
    if (LATIN_SYMBOLS.has(ch)) return -2;
    if (o >= 0x391 && o <= 0x3c9 && CP437_GREEK.has(ch)) return -1;
    if (o >= 0x2500 && o <= 0x259f) return -2;
    if (o >= 0xc0 && o <= 0x24f) return -0.3;
    if (o >= 0xff01 && o <= 0xff5e) return 0.5;
    if (RE_L.test(ch)) return 0;
    if (RE_MARK.test(ch)) return 0;
    if (RE_ND.test(ch)) return 0;
    if (RE_SO.test(ch)) return 0;
    return -1;
  }
  const isHan = (c) => { const o = c.codePointAt(0); return o >= 0x4e00 && o <= 0x9fff; };
  function script(c) {
    const o = c.codePointAt(0);
    if (o >= 0xac00 && o <= 0xd7a3) return "hangul";
    if ((o >= 0x3041 && o <= 0x30ff) || (o >= 0xff61 && o <= 0xff9f)) return "kana";
    if ((o >= 0x4e00 && o <= 0x9fff) || (o >= 0x3400 && o <= 0x4dbf)) return "han";
    if (o >= 0xc0 && o <= 0x24f) return "latin_ext";
    return null;
  }
  function adjust(chars, i, v) {
    const c = chars[i], o = c.codePointAt(0);
    const nb = i ? chars.slice(i - 1, i).concat(chars.slice(i + 1, i + 2)) : chars.slice(i + 1, i + 2);
    if (o >= 0xc0 && o <= 0x24f && !LATIN_SYMBOLS.has(c)) {
      if (nb.some((x) => /^[A-Za-z]$/.test(x))) return 1.5;
    }
    if ((c === "─" || c === "━") && nb.length &&
        nb.every((x) => x === "─" || x === "━" || CJK_PUNCT.has(x) || isHan(x))) return 0;
    if (c === "\u20ac" && nb.some((x) => RE_ND.test(x))) return 0.5;
    if (o >= 0x370 && o <= 0x52f && RE_L.test(c)) {
      if (nb.some((x) => { const p = x.codePointAt(0); return p >= 0x370 && p <= 0x52f; })) return 1.5;
      if (nb.some((x) => { const p = x.codePointAt(0); return p >= 0xc0 && p <= 0x24f; })) return -1.5;
    }
    return v;
  }
  function details(text) {
    const chars = Array.from(text).filter((c) => !RE_SPACE.test(c));
    return [chars, chars.map((c, i) => adjust(chars, i, charScore(c)))];
  }
  function pairs(text) {
    const cs = Array.from(text);
    let p = 0, w = 0;
    for (let i = 1; i < cs.length; i++) {
      if (isHan(cs[i - 1]) && isHan(cs[i])) { p++; if (WORDS.has(cs[i - 1] + cs[i])) w++; }
    }
    return [p, w];
  }
  function score(text) {
    const [chars, vals] = details(text);
    if (!chars.length) return 0;
    let total = vals.reduce((a, b) => a + b, 0), prev = null, han = 0, kana = false;
    for (const c of chars) {
      const s = script(c);
      if (s && prev && s !== prev && !((s === "kana" && prev === "han") || (s === "han" && prev === "kana"))) total -= 1.5;
      prev = s;
      if (isHan(c)) han++;
      if (s === "kana") kana = true;
    }
    const [p, w] = pairs(text);
    total += 2 * w;
    if (p >= 3 && w === 0 && !kana) total -= 2 * han;
    return total / chars.length;
  }
  function suspicious(text, minPairs = 3) {
    const [chars, vals] = details(text);
    if (vals.some((v) => v <= -1)) return true;
    const [p, w] = pairs(text);
    return p >= minPairs && w === 0 && !chars.some((c) => script(c) === "kana");
  }

  /* ---------------- repair ---------------- */
  const MAX_DEPTH = 3, BEAM = 10, MIN_GAIN = 0.8, MIN_RESULT = 1.0;
  const cat = (...parts) => {
    let n = 0;
    for (const p of parts) n += p.length;
    const out = new Uint8Array(n);
    let o = 0;
    for (const p of parts) { out.set(p, o); o += p.length; }
    return out;
  };
  const dropPh = (b) => b.filter((x) => x !== PLACEHOLDER);
  const rankBonus = (t) => {   // tiny tie-breaker: prefer more frequent characters
    let s = 0;
    for (const c of t) {
      if (RANK.has(c)) s += 1 - RANK.get(c) / 4000;
      else if (KANA_ORDER.includes(c)) s += 1 - KANA_ORDER.indexOf(c) / 90;
    }
    return s * 0.01;
  };

  // look = [original, shownAs]: also judge a window one layer deeper (multi-layer mojibake)
  function best(cands, fn, enc, look) {
    let bestC = null, bestS = null;
    for (const c of cands) {
      const w = decode(fn(c), enc, true);
      let s = score(w) + rankBonus(w) - count(w, FFFD);   // never prefer an invalid sequence
      if (look && suspicious(w)) {
        const b = encode(w, look[1], false);
        if (b) { const inner = decode(b, look[0], true); s = Math.max(s, score(inner) + rankBonus(inner) - count(inner, FFFD) - 0.2); }
      }
      if (bestS === null || s > bestS) { bestC = c; bestS = s; }
    }
    return bestC;
  }
  const CONT = range(0x80, 0xc0).concat(range(0xe3, 0xea)).map((b) => Uint8Array.of(b));
  const EMPTY = new Uint8Array(0);

  function decodeUtf8Repair(raw, budget, w, look) {
    let data = Uint8Array.from(raw), guessed = 0;
    for (let round = 0; round <= budget; round++) {
      const i = data.indexOf(PLACEHOLDER);
      if (i >= 0) {
        const lo = Math.max(0, i - w), hi = Math.min(data.length, i + w + 1);
        // a placeholder always stands for one real byte, so no "delete" option
        const pick = best(CONT, (c) => cat(data.subarray(lo, i), c, dropPh(data.subarray(i + 1, hi))), "utf-8", look);
        data = cat(data.subarray(0, i), pick, data.subarray(i + 1));
        if (pick.length) guessed++;
        continue;
      }
      const st = utf8ErrorStart(data);
      if (st < 0) return [decode(data, "utf-8", true), guessed];
      if (guessed >= budget) break;
      const lo = Math.max(0, st - w), hi = Math.min(data.length, st + w + 1);
      const opts = [];
      for (const k of [1, 2, 3]) for (const c of CONT) opts.push(["ins", k, c]);
      opts.push(["del", 0, EMPTY]);
      const d = data;
      const pick = best(opts, ([kind, k, c]) => kind === "ins"
        ? cat(d.subarray(lo, st + k), c, d.subarray(st + k, hi))
        : cat(d.subarray(lo, st), d.subarray(st + 1, hi)), "utf-8");
      const [kind, k, c] = pick;
      data = kind === "ins" ? cat(d.subarray(0, st + k), c, d.subarray(st + k)) : cat(d.subarray(0, st), d.subarray(st + 1));
      guessed++;
    }
    return null;
  }

  const DBCS_BYTES = range(0x40, 0xff).filter((b) => b !== 0x7f).map((b) => Uint8Array.of(b));
  const isLead = (b, enc) => enc === "shift_jis" ? (b >= 0x81 && b <= 0x9f) || (b >= 0xe0 && b <= 0xfc) : b >= 0x81;
  function charStart(data, limit, enc) {
    let pos = 0, last = 0;
    while (pos <= limit && pos < data.length) {
      last = pos;
      pos += isLead(data[pos], enc) && pos + 1 < data.length && data[pos + 1] !== PLACEHOLDER ? 2 : 1;
    }
    return last;
  }
  function decodeDbcsRepair(raw, enc) {
    let data = Uint8Array.from(raw), guessed = 0, i;
    while ((i = data.indexOf(PLACEHOLDER)) >= 0) {
      const lo = charStart(data, Math.max(0, i - 8), enc), hi = Math.min(data.length, i + 9);
      const pick = best(DBCS_BYTES, (c) => cat(data.subarray(lo, i), c, dropPh(data.subarray(i + 1, hi))), enc);
      data = cat(data.subarray(0, i), pick, data.subarray(i + 1));
      if (pick.length) guessed++;
    }
    return [decode(data, enc, true), guessed];
  }
  const count = (s, ch) => s.split(ch).length - 1;

  const undoCache = new Map();
  function undo(text, original, shownAs, repair) {
    const key = original + "|" + shownAs + "|" + (repair ? 1 : 0) + "|" + text;
    if (undoCache.has(key)) return undoCache.get(key);
    if (undoCache.size > 4096) undoCache.clear();
    const r = undo0(text, original, shownAs, repair);
    undoCache.set(key, r);
    return r;
  }
  function undo0(text, original, shownAs, repair) {
    let raw;
    if (shownAs === "gbk" && text.includes("锟\ufffd")) {
      // "锟�" is exactly EF BF BD (a U+FFFD from an earlier layer) whose last byte was lost
      const parts = text.split("锟\ufffd").map((p) => encode(p, shownAs, false));
      if (parts.includes(null)) return null;
      const all = [];
      parts.forEach((p, i) => { if (i) all.push(0xef, 0xbf, 0xbd); all.push(...p); });
      raw = Uint8Array.from(all);
    } else raw = encode(text, shownAs, false);
    if (raw === null) return null;
    const budget = Math.max(1, Math.floor(Array.from(text).length / 12)) + count(text, FFFD);
    let out;
    if (original === "utf-8") {
      const r = decodeUtf8Repair(raw, budget, repair ? 9 : 4, repair ? [original, shownAs] : null);
      if (r) return r;
      const fixed = [];
      for (const b of raw) { if (b === PLACEHOLDER) fixed.push(0xef, 0xbf, 0xbd); else fixed.push(b); }
      out = decode(Uint8Array.from(fixed), "utf-8", true);
    } else if (repair && raw.includes(PLACEHOLDER) && DBCS.has(original)) {
      const [o, g] = decodeDbcsRepair(raw, original);
      return count(o, FFFD) > budget ? null : [o, g];
    } else {
      try { out = decode(raw, original, false); } catch (e) { out = decode(raw, original, true); }
      out = out.split("\x1a").join(FFFD);
    }
    if (count(out, FFFD) > budget) return null;
    return [out, 0];
  }

  function search(text) {
    const base = score(text);
    let beam = [[base, text, [], 0]], bestE = beam[0];
    for (let depth = 0; depth < MAX_DEPTH; depth++) {
      const nxt = [];
      for (const [, t, steps, g] of beam) {
        for (const shown of ENCODINGS) {
          if (shown === "utf-8") continue;   // legacy bytes read as UTF-8 become U+FFFD: nothing to undo
          for (const orig of ENCODINGS) {
            const last = steps[steps.length - 1];
            if (orig === shown || (last && last.original === shown && last.shownAs === orig)) continue;
            const r = undo(t, orig, shown, false);
            if (!r || r[0] === t) continue;
            nxt.push([score(r[0]), r[0], steps.concat([{ original: orig, shownAs: shown }]), g + r[1]]);
          }
        }
      }
      if (!nxt.length) break;
      nxt.sort((a, b) => b[0] - a[0]);
      const top = nxt.slice(0, BEAM);
      const short = nxt.filter((c) => c[3] === 0 && !c[1].includes(FFFD))
        .sort((a, b) => Array.from(a[1]).length - Array.from(b[1]).length).slice(0, 4);
      beam = top.concat(short.filter((c) => !top.includes(c)));
      if (beam[0][0] > bestE[0] + (bestE[2].length ? 0.3 : 0.05)) bestE = beam[0];
      if (bestE[2].length && bestE[0] >= 2.5 && !suspicious(bestE[1])) break;
    }
    if (bestE[2].length) bestE = replay(text, bestE);
    return [base, bestE];
  }
  function replay(text, cand) {   // redo the winning chain with lost-byte repair switched on
    let t = text, g = 0;
    for (const st of cand[2]) {
      const r = undo(t, st.original, st.shownAs, true);
      if (!r) return cand;
      t = r[0]; g += r[1];
    }
    const s = score(t);
    return s >= cand[0] ? [s, t, cand[2], g] : cand;
  }

  function result(text, fixed, extra) {
    return Object.assign({ text, fixed, steps: [], guessed: 0, lost: 0, before: 0, after: 0, note: "",
      changed: fixed !== text }, extra || {});
  }

  function fixUnit(text, minGain, minPairs = 3) {
    if (text.includes("锟斤拷") || count(text, "锟") >= 2) {
      const r = undo(text, "utf-8", "gbk", true);
      if (r) return result(text, r[0], { steps: [{ original: "utf-8", shownAs: "gbk" }], lost: count(r[0], FFFD),
        before: score(text), after: score(r[0]), note: "kunjinkao" });
    }
    if (/^(烫|屯)+$/.test(text.trim())) return result(text, text, { note: "tangtang" });
    if (!suspicious(text, minPairs)) { const s = score(text); return result(text, text, { before: s, after: s }); }
    const [base, [s, out, steps, g]] = search(text);
    if (steps.length && s - base >= minGain && s >= MIN_RESULT)
      return result(text, out, { steps, guessed: g, lost: count(out, FFFD), before: base, after: s });
    return result(text, text, { before: base, after: base });
  }

  const TOKEN = /([\s,，。:：;；/\\|()（）\[\]【】"'<>《》=]+)/u;
  const TOKEN_FULL = /^[\s,，。:：;；/\\|()（）\[\]【】"'<>《》=]+$/u;

  function fix(text) {
    const whole = fixUnit(text, MIN_GAIN);
    if (whole.changed || !text.trim()) return whole;
    const results = text.split(TOKEN).map((p) =>
      p && !TOKEN_FULL.test(p) && /[^\x00-\x7f]/.test(p) ? fixUnit(p, MIN_GAIN * 1.5, 6) : result(p, p));
    const changed = results.filter((r) => r.changed);
    if (!changed.length) return whole;
    const fixed = results.map((r) => r.fixed).join("");
    return result(text, fixed, { steps: changed[0].steps, guessed: changed.reduce((a, r) => a + r.guessed, 0),
      lost: changed.reduce((a, r) => a + r.lost, 0), before: score(text), after: score(fixed),
      note: "pieces", pieces: changed.length });
  }

  const api = { fix, fixText: (t) => fix(t).fixed, score, suspicious, encode, decode, ENCODINGS, LABEL };
  root.luanma = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
