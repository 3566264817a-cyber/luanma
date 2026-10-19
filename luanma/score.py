"""Plausibility score for a string: higher = more like real human text.

All tables are derived from frozen national standards that ship with Python's
codecs, so no data files and nothing to update:
  GB2312 level-1/2 hanzi, Big5 common characters, JIS X 0208 level-1 kanji,
  KS X 1001 hangul.
"""
import unicodedata

from .freq import RANK, WORDS
from functools import lru_cache


def _table(enc, lead, trail):
    out = set()
    for a in lead:
        for b in trail:
            try:
                out.add(bytes([a, b]).decode(enc))
            except UnicodeDecodeError:
                pass
    return out


_TRAIL_A1 = range(0xA1, 0xFF)
GB_L1 = _table("gb2312", range(0xB0, 0xD8), _TRAIL_A1)       # 3755 most common hanzi
GB_L2 = _table("gb2312", range(0xD8, 0xF8), _TRAIL_A1)       # 3008 less common
BIG5_COMMON = _table("big5", range(0xA4, 0xC7), list(range(0x40, 0x7F)) + list(_TRAIL_A1))
JIS_L1 = _table("shift_jis", range(0x88, 0x99), list(range(0x40, 0x7F)) + list(range(0x80, 0xFD)))
KS_HANGUL = _table("euc_kr", range(0xB0, 0xC9), _TRAIL_A1)   # 2350 common syllables
CJK_PUNCT = set("，。、；：？！“”‘’（）《》〈〉【】「」『』…—·～￥　")

# hiragana roughly by frequency in running Japanese text
KANA_ORDER = "いうんしのかたとてなにはるがでくすまこれもっりあらよおけさきつだそやめえせわみねひどろじばゆほぶげちずへべごぐぜびぞょゃゅぱぽぴぷぺ"
RARE_KANA = set("ぁぃぅぇぉゎゐゑゔゕゖヮヰヱヵヶヷヸヹヺ")   # small / obsolete kana
CP437_GREEK = set("αΓπΣστΦΘΩδφε")
LATIN_SYMBOLS = set("¡¢£¤¥¦§¨©ª«¬\xad®¯°±²³´µ¶·¸¹º»¼½¾¿×÷ƒˆ˜‰‹›•–—™šœžŸŠŒŽ€")


@lru_cache(maxsize=65536)
def char_score(ch: str) -> float:
    o = ord(ch)
    if ch == "\ufffd":
        return -4.0
    if ch in "¿¡":
        return 0.0
    if ch in "锟斤拷"[:1] or ch in "烫屯"[:0]:
        return -3.0                     # 锟 almost only appears in 锟斤拷 mojibake
    if ch in "，。":
        return 3.0
    if o == 0x1A or (o < 0x20 and ch not in "\t\n\r") or 0x7F <= o < 0xA0:
        return -5.0
    if o < 0x80:
        return 0.5
    r = RANK.get(ch)
    if r is not None:
        return 4.5 if r < 500 else 3.8 if r < 1500 else 3.2
    if ch in GB_L1:
        return 3.0
    if ch in CJK_PUNCT:
        return 2.5
    if ch in RARE_KANA:
        return 1.0
    if ch in KANA_ORDER[:20]:
        return 3.8
    if 0x3041 <= o <= 0x30FF:          # full-width hiragana / katakana
        return 3.5
    if ch in KS_HANGUL:
        return 3.5
    if ch in BIG5_COMMON or ch in JIS_L1:
        return 2.2
    if ch in GB_L2:
        return 1.0
    if 0xFF61 <= o <= 0xFF9F:          # half-width katakana: classic mojibake
        return -2.0
    if 0xAC00 <= o <= 0xD7A3:          # rare hangul syllables
        return -1.5
    if 0x4E00 <= o <= 0x9FFF:          # rare CJK
        return -1.5
    if 0x3400 <= o <= 0x4DBF or o >= 0x20000:
        return -3.0
    if 0xE000 <= o <= 0xF8FF:          # private use
        return -5.0
    if ch in LATIN_SYMBOLS:
        return -2.0
    if 0x391 <= o <= 0x3C9 and ch in CP437_GREEK:
        return -1.0                     # lone Greek letter from cp437 mojibake
    if 0x2500 <= o <= 0x259F:          # box drawing (cp437 mojibake)
        return -2.0
    if 0xC0 <= o <= 0x24F:             # accented latin
        return -0.3
    if 0xFF01 <= o <= 0xFF5E:          # full-width ascii
        return 0.5
    if ch in "¿¡":
        return 0.0
    cat = unicodedata.category(ch)
    if cat.startswith("L"):
        return 0.0
    if cat in ("Mn", "Mc", "Me", "Cf"):  # combining marks, variation selectors, ZWJ
        return 0.0
    if cat == "Nd":                     # digits of other scripts
        return 0.0
    if cat == "So":                     # emoji etc.
        return 0.0
    return -1.0


def _script(ch):
    o = ord(ch)
    if 0xAC00 <= o <= 0xD7A3:
        return "hangul"
    if 0x3041 <= o <= 0x30FF or 0xFF61 <= o <= 0xFF9F:
        return "kana"
    if 0x4E00 <= o <= 0x9FFF or 0x3400 <= o <= 0x4DBF:
        return "han"
    if 0xC0 <= o <= 0x24F:
        return "latin_ext"
    return None


def _adjust(chars, i, v):
    """Context rules: things that look odd alone but are normal in context."""
    c = chars[i]
    o = ord(c)
    nb = chars[i - 1:i] + chars[i + 1:i + 2] if i else chars[i + 1:i + 2]
    if 0xC0 <= o <= 0x24F and c not in LATIN_SYMBOLS:
        # accented letter inside a normal latin word (café, Müller)
        if any(x.isascii() and x.isalpha() for x in nb):
            return 1.5
    if c in "─━" and nb and all(x in "─━" or x in CJK_PUNCT or 0x4E00 <= ord(x) <= 0x9FFF for x in nb):
        return 0.0                      # "──" used as a dash in CJK text
    if c == "\u20ac" and any(x.isdigit() for x in nb):
        return 0.5                      # 25€
    if 0x370 <= o <= 0x52F and c.isalpha():
        # Greek / Cyrillic letter next to a letter of the same script
        if any(0x370 <= ord(x) <= 0x52F for x in nb):
            return 1.5
        if any(0xC0 <= ord(x) <= 0x24F for x in nb):
            return -1.5                 # Greek glued to accented Latin: cp437 mojibake
    return v


def _details(text):
    chars = [c for c in text if not c.isspace()]
    vals = [_adjust(chars, i, char_score(c)) for i, c in enumerate(chars)]
    return chars, vals


def score(text: str) -> float:
    """Mean plausibility per non-space character, with a script-mixing
    penalty and a bonus for common two-character words."""
    chars, vals = _details(text)
    if not chars:
        return 0.0
    total = sum(vals)
    prev, han = None, 0
    for c in chars:
        s = _script(c)
        if s and prev and s != prev and {s, prev} != {"kana", "han"}:
            total -= 1.5
        prev = s
        han += 0x4E00 <= ord(c) <= 0x9FFF
    pairs, words = _pairs(text)
    total += 2.0 * words
    kana = any(_script(c) == "kana" for c in chars)
    if pairs >= 3 and words == 0 and not kana:
        total -= 2.0 * han              # hanzi text forming no common words: mojibake
    return total / len(chars)


def _pairs(text):
    """(adjacent hanzi pairs, how many of them are common words)."""
    pairs = words = 0
    for a, b in zip(text, text[1:]):
        if 0x4E00 <= ord(a) <= 0x9FFF and 0x4E00 <= ord(b) <= 0x9FFF:
            pairs += 1
            words += a + b in WORDS
    return pairs, words


def suspicious(text: str, min_pairs: int = 3) -> bool:
    """Only try to fix text that shows signs of mojibake (ftfy's rule:
    never touch text that already looks fine)."""
    chars, vals = _details(text)
    if any(v <= -1.0 for v in vals):
        return True
    pairs, words = _pairs(text)
    if pairs >= min_pairs and words == 0 and not any(_script(c) == "kana" for c in chars):
        return True                     # hanzi that form no words at all
    return False
