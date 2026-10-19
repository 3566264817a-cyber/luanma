"""Reverse chains of wrong encode/decode steps for CJK mojibake."""
import re
from functools import lru_cache
from dataclasses import dataclass, field

from .codecs_ import ENCODINGS, LABEL, PLACEHOLDER, decode, encode
from .score import KANA_ORDER, score, suspicious
from .freq import RANK

MAX_DEPTH = 3
BEAM = 10
MIN_GAIN = 0.8        # required improvement in mean score
MIN_RESULT = 1.0      # result must look like real text


MSG = {
    "zh": {"step": "{a} 编码的内容被当成 {b} 解码", "nth": "第{i}次出错：", "clean": "文本看起来正常，未做修改。",
           "guessed": "有 {n} 个字节已丢失，已按常用字频率推测补回（请核对）", "lost": "有 {n} 个字符永久丢失，用 � 标出",
           "conf": "可信度约 {c}%（评分 {a:.2f} → {b:.2f}）", "pieces": "按片段修复了 {n} 处乱码",
           "kunjinkao": "「锟斤拷」：GBK 内容曾被当作 UTF-8 读取并保存，原始字节已被替换，丢失部分无法恢复。",
           "tangtang": "「烫烫烫/屯屯屯」不是乱码：这是 VC++ 调试模式下未初始化的内存（0xCC / 0xCD）。"},
    "en": {"step": "{a} bytes were decoded as {b}", "nth": "Error {i}: ", "clean": "Text looks fine - nothing changed.",
           "guessed": "{n} lost byte(s) were guessed from character frequency (please double-check)",
           "lost": "{n} character(s) are permanently lost (shown as �)",
           "conf": "Confidence ~{c}% (score {a:.2f} -> {b:.2f})", "pieces": "Fixed {n} garbled fragment(s)",
           "kunjinkao": "\"锟斤拷\": GBK text was once read as UTF-8 and saved; the original bytes were replaced and cannot be recovered.",
           "tangtang": "\"烫烫烫 / 屯屯屯\" is not mojibake: it is uninitialised memory (0xCC / 0xCD) in MSVC debug builds."},
    "ja": {"step": "{a} のデータが {b} として読み込まれた", "nth": "誤り{i}：", "clean": "正常なテキストのようです。変更なし。",
           "guessed": "失われた {n} バイトを文字頻度から推測して補完（要確認）", "lost": "{n} 文字は完全に失われています（� で表示）",
           "conf": "信頼度 約{c}%（スコア {a:.2f} → {b:.2f}）", "pieces": "{n} か所の文字化けを部分的に修復",
           "kunjinkao": "「锟斤拷」：GBK のデータが UTF-8 として読まれて保存されたもので、失われた部分は復元できません。",
           "tangtang": "「烫烫烫／屯屯屯」は文字化けではなく、MSVC デバッグビルドの未初期化メモリ（0xCC / 0xCD）です。"},
}


@dataclass
class Step:
    original: str     # encoding the bytes really were
    shown_as: str     # encoding they were wrongly decoded with

    def describe(self, lang="zh"):
        return MSG[lang]["step"].format(a=LABEL[self.original], b=LABEL[self.shown_as])


@dataclass
class Result:
    text: str
    fixed: str
    steps: list = field(default_factory=list)
    guessed: int = 0          # bytes guessed from frequency
    lost: int = 0             # characters permanently lost (U+FFFD left)
    before: float = 0.0
    after: float = 0.0
    note: str = ""            # "kunjinkao", "tangtang" or "pieces"
    pieces: int = 0

    @property
    def changed(self):
        return self.fixed != self.text

    def explain(self, lang: str = "zh") -> str:
        """Human-readable account of what went wrong. lang: "zh", "en" or "ja"."""
        m = MSG.get(lang, MSG["en"])
        if not self.changed:
            return m.get(self.note, m["clean"]) if self.note else m["clean"]
        lines = [m["nth"].format(i=i) + s.describe(lang) for i, s in enumerate(reversed(self.steps), 1)]
        if self.note == "pieces":
            lines.append(m["pieces"].format(n=self.pieces))
        if self.guessed:
            lines.append(m["guessed"].format(n=self.guessed))
        if self.lost:
            lines.append(m["lost"].format(n=self.lost))
        if self.note in ("kunjinkao", "tangtang"):
            lines.append(m[self.note])
        if self.note != "kunjinkao":
            conf = max(0, min(99, int(50 + (self.after - self.before) * 15)))
            lines.append(m["conf"].format(c=conf, a=self.before, b=self.after))
        return "\n".join("  " + x for x in lines)


def _rank_bonus(text):
    # tiny tie-breaker: prefer more frequent characters
    return sum(1 - RANK.get(c, 4000) / 4000 if c in RANK else 1 - KANA_ORDER.find(c) / 90 if c in KANA_ORDER else 0
               for c in text) * 0.01


def _best(cands, data_fn, enc="utf-8", look=None):
    """Candidate whose window decodes to the most plausible text. With
    look=(original, shown_as), also look one layer deeper, so that bytes of
    an intermediate layer of multi-layer mojibake are judged by the text they
    finally produce."""
    best, best_s = None, None
    for c in cands:
        window = decode(data_fn(c), enc, lossy=True) if enc != "utf-8" else data_fn(c).decode("utf-8", "replace")
        # never prefer an invalid sequence, even over private-use characters
        s = score(window) + _rank_bonus(window) - window.count("\ufffd")
        if look and suspicious(window):
            try:
                inner = decode(encode(window, look[1]), look[0], lossy=True)
                s = max(s, score(inner) + _rank_bonus(inner) - inner.count("\ufffd") - 0.2)
            except UnicodeEncodeError:
                pass
        if best_s is None or s > best_s:
            best, best_s = c, s
    return best


_CONT = [bytes([b]) for b in list(range(0x80, 0xC0)) + list(range(0xE3, 0xEA))]


def _decode_utf8_repair(raw: bytes, budget: int, w: int = 9, look=None):
    """Strict UTF-8 decode that repairs up to `budget` damaged spots:
    placeholder bytes (already lost, shown as U+FFFD) and silently dropped
    continuation bytes (e.g. Windows-1252 holes 0x81/0x8D/0x8F/0x90/0x9D that
    vanished on copy-paste). Candidates are ranked by character frequency."""
    data = bytearray(raw)
    guessed = 0
    for _ in range(budget + 1):
        if PLACEHOLDER in data:
            i = data.index(PLACEHOLDER)
            lo, hi = max(0, i - w), min(len(data), i + w + 1)
            # a placeholder always stands for one real byte, so no "delete" option
            pick = _best(_CONT, lambda c: bytes(data[lo:i]) + c + bytes(data[i + 1:hi]).replace(bytes([PLACEHOLDER]), b""), look=look)
            data[i:i + 1] = pick
            guessed += bool(pick)
            continue
        try:
            return bytes(data).decode("utf-8"), guessed
        except UnicodeDecodeError as e:
            if guessed >= budget:
                break
            st = e.start
            lo, hi = max(0, st - w), min(len(data), st + w + 1)
            opts = []
            for k in (1, 2, 3):
                for c in _CONT:
                    opts.append(("ins", k, c))
            opts.append(("del", 0, b""))

            def apply(o, d=data):
                kind, k, c = o
                if kind == "ins":
                    return bytes(d[lo:st + k]) + c + bytes(d[st + k:hi])
                return bytes(d[lo:st]) + bytes(d[st + 1:hi])
            pick = _best(opts, apply)
            kind, k, c = pick
            if kind == "ins":
                data[st + k:st + k] = c
            else:
                del data[st]
            guessed += 1
    return None


_DBCS_BYTES = [bytes([b]) for b in range(0x40, 0xFF) if b != 0x7F]


def _is_lead(b, enc):
    if enc == "shift_jis":
        return 0x81 <= b <= 0x9F or 0xE0 <= b <= 0xFC
    return b >= 0x81


def _char_start(data, limit, enc):
    """Last character boundary at or before `limit` (walk from the start,
    because double-byte text is not self-synchronising)."""
    pos = last = 0
    while pos <= limit and pos < len(data):
        last = pos
        pos += 2 if _is_lead(data[pos], enc) and pos + 1 < len(data) and data[pos + 1] != PLACEHOLDER else 1
    return last


def _decode_dbcs_repair(raw: bytes, enc: str):
    """Fill placeholder bytes (lost lead bytes) of a double-byte encoding with
    the byte that makes the surrounding text most plausible."""
    data, guessed = bytearray(raw), 0
    while PLACEHOLDER in data:
        i = data.index(PLACEHOLDER)
        lo, hi = _char_start(data, max(0, i - 8), enc), min(len(data), i + 9)
        pick = _best(_DBCS_BYTES, lambda c: bytes(data[lo:i]) + c + bytes(data[i + 1:hi]).replace(bytes([PLACEHOLDER]), b""), enc)
        data[i:i + 1] = pick
        guessed += bool(pick)
    return decode(bytes(data), enc, lossy=True), guessed


@lru_cache(maxsize=4096)
def _undo(text: str, original: str, shown_as: str, repair: bool = True):
    """One reverse step: text was bytes(original) decoded as shown_as.
    repair=False skips the (slow) guessing of lost double-byte lead bytes;
    the search uses it and the winning chain is replayed with repair."""
    try:
        if shown_as == "gbk" and "锟\ufffd" in text:
            # "锟�" is exactly EF BF BD (a U+FFFD from an earlier layer) whose
            # last byte was lost: restore it instead of guessing
            raw = b"\xef\xbf\xbd".join(encode(p, shown_as) for p in text.split("锟\ufffd"))
        else:
            raw = encode(text, shown_as)
    except UnicodeEncodeError:
        return None
    budget = max(1, len(text) // 12) + text.count("\ufffd")
    if original == "utf-8":
        r = _decode_utf8_repair(raw, budget, 9 if repair else 4, (original, shown_as) if repair else None)
        if r is not None:
            return r
        out = decode(raw.replace(bytes([PLACEHOLDER]), "\ufffd".encode()), original, lossy=True)
    elif repair and PLACEHOLDER in raw and original in ("gbk", "big5", "shift_jis", "euc_kr"):
        out, g = _decode_dbcs_repair(raw, original)
        if out.count("\ufffd") > budget:
            return None
        return out, g
    else:
        try:
            out = decode(raw, original)
        except UnicodeDecodeError:
            out = decode(raw, original, lossy=True)
        out = out.replace("\x1a", "\ufffd")
    if out.count("\ufffd") > budget:
        return None
    return out, 0


def _search(text: str):
    base = score(text)
    beam = [(base, text, [], 0)]
    best = beam[0]
    for _ in range(MAX_DEPTH):
        nxt = []
        for s0, t, steps, g in beam:
            for shown in ENCODINGS:
                if shown == "utf-8":
                    continue            # legacy bytes read as UTF-8 become U+FFFD: nothing to undo
                for orig in ENCODINGS:
                    if orig == shown or (steps and (steps[-1].original, steps[-1].shown_as) == (shown, orig)):
                        continue            # skip no-ops and undoing the previous step
                    r = _undo(t, orig, shown, False)
                    if r is None or r[0] == t:
                        continue
                    out, gg = r
                    s = score(out)
                    if True:
                        nxt.append((s, out, steps + [Step(orig, shown)], g + gg))
        if not nxt:
            break
        nxt.sort(key=lambda x: -x[0])
        # keep diversity: a correct intermediate layer of multi-layer mojibake
        # still looks bad, but undoing it losslessly makes the text shorter
        short = sorted((c for c in nxt if c[3] == 0 and "\ufffd" not in c[1]), key=lambda x: len(x[1]))[:4]
        beam = nxt[:BEAM] + [c for c in short if c not in nxt[:BEAM]]
        if beam[0][0] > best[0] + (0.05 if not best[2] else 0.3):
            best = beam[0]
        if best[2] and best[0] >= 2.5 and not suspicious(best[1]):
            break                       # already looks like clean text
    if best[2]:
        best = _replay(text, best)
    return base, best


def _replay(text, cand):
    """Redo the winning chain with lost-byte repair switched on."""
    t, g = text, 0
    for st in cand[2]:
        r = _undo(t, st.original, st.shown_as, True)
        if r is None:
            return cand
        t, g = r[0], g + r[1]
    s = score(t)
    return (s, t, cand[2], g) if s >= cand[0] else cand


def _fix_unit(text: str, min_gain: float = MIN_GAIN, min_pairs: int = 3) -> Result:
    if "锟斤拷" in text or text.count("锟") >= 2:
        r = _undo(text, "utf-8", "gbk")
        if r:
            out = r[0]
            return Result(text, out, [Step("utf-8", "gbk")], lost=out.count("\ufffd"),
                          before=score(text), after=score(out),
                          note="kunjinkao")
    if re.fullmatch(r"(烫|屯)+", text.strip()):
        return Result(text, text, note="tangtang")
    if not suspicious(text, min_pairs):
        return Result(text, text, before=score(text), after=score(text))
    base, (s, out, steps, g) = _search(text)
    if steps and s - base >= min_gain and s >= MIN_RESULT:
        return Result(text, out, steps, guessed=g, lost=out.count("\ufffd"), before=base, after=s)
    return Result(text, text, before=base, after=base)


_TOKEN = re.compile(r"([\s,，。:：;；/\\|()（）\[\]【】\"'<>《》=]+)")


def fix(text: str) -> Result:
    """Fix the whole text; fall back to per-line, then per-token fixing for
    strings that mix correct text with garbled fragments."""
    whole = _fix_unit(text)
    if whole.changed or not text.strip():
        return whole
    parts, results = _TOKEN.split(text), []
    for p in parts:
        if p and not _TOKEN.fullmatch(p) and any(ord(c) > 0x7F for c in p):
            results.append(_fix_unit(p, MIN_GAIN * 1.5, 6))   # short fragments need stronger evidence
        else:
            results.append(Result(p, p))
    changed = [r for r in results if r.changed]
    if not changed:
        return whole
    fixed = "".join(r.fixed for r in results)
    steps = changed[0].steps
    return Result(text, fixed, steps, guessed=sum(r.guessed for r in changed),
                  lost=sum(r.lost for r in changed), before=score(text), after=score(fixed),
                  note="pieces", pieces=len(changed))


def fix_text(text: str) -> str:
    return fix(text).fixed
