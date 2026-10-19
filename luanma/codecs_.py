"""Encoding helpers that mimic how real software (mostly Windows) garbles bytes.

- "gbk": Windows cp936 maps byte 0x80 to "€"; Python's gbk does not.
- "cp1252": Windows passes the 5 undefined bytes through as U+0081 etc.
- U+FFFD in input marks bytes that were already lost; we encode it as a
  placeholder byte so later stages can try to guess the missing byte.
"""
import codecs

ENCODINGS = ["utf-8", "gbk", "big5", "shift_jis", "euc_kr", "cp1252", "latin-1", "cp437"]
LABEL = {
    "utf-8": "UTF-8", "gbk": "GBK", "big5": "Big5", "shift_jis": "Shift-JIS",
    "euc_kr": "EUC-KR", "cp1252": "Windows-1252", "latin-1": "Latin-1", "cp437": "CP437(DOS)",
}
PLACEHOLDER = 0x1A  # ASCII SUB, never appears in normal text
_CP1252_HOLES = {0x81, 0x8D, 0x8F, 0x90, 0x9D}
_PY = {"gbk": "gb18030", "big5": "cp950", "shift_jis": "cp932", "euc_kr": "cp949"}


class Lost(Exception):
    pass


def _py(enc):
    return _PY.get(enc, enc)


def _sloppy_decode(enc, lossy):
    def handler(err):
        bad = err.object[err.start:err.end]
        if enc == "gbk" and bad[:1] == b"\x80":
            return "\u20ac", err.start + 1
        if enc == "cp1252" and bad[0] in _CP1252_HOLES:
            return chr(bad[0]), err.start + 1
        if lossy:
            return "\ufffd", err.start + 1
        raise err
    return handler


def _sloppy_encode(enc):
    def handler(err):
        out = b""
        for ch in err.object[err.start:err.end]:
            if ch == "\ufffd":
                out += bytes([PLACEHOLDER])
            elif enc == "gbk" and ch == "\u20ac":
                out += b"\x80"
            elif enc == "cp1252" and ord(ch) in _CP1252_HOLES:
                out += bytes([ord(ch)])
            else:
                raise err
        return out, err.end
    return handler


def decode(data: bytes, enc: str, lossy: bool = False) -> str:
    name = f"luanma-dec-{enc}-{int(lossy)}"
    try:
        codecs.lookup_error(name)
    except LookupError:
        codecs.register_error(name, _sloppy_decode(enc, lossy))
    return data.decode(_py(enc), errors=name)


def encode(text: str, enc: str, keep_fffd: bool = False) -> bytes:
    name = f"luanma-enc-{enc}"
    try:
        codecs.lookup_error(name)
    except LookupError:
        codecs.register_error(name, _sloppy_encode(enc))
    # U+FFFD marks bytes lost earlier: keep it as a placeholder byte instead of
    # letting UTF-8 turn it into EF BF BD (which would then become 锟斤拷)
    if not keep_fffd:
        text = text.replace("\ufffd", "\x1a")
    if enc == "gbk" and "\u20ac" in text:
        # GB18030 encodes € as A2E3, but Windows GBK (cp936) uses 0x80
        return b"\x80".join(part.encode(_py(enc), errors=name) for part in text.split("\u20ac"))
    return text.encode(_py(enc), errors=name)
