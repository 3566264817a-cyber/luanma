"""Build the single-file web app docs/index.html (served by GitHub Pages).

    python tools/build_web.py [github-user/repo]
"""
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from luanma import __version__, freq  # noqa: E402
from luanma.codecs_ import decode, encode  # noqa: E402

REPO = sys.argv[1] if len(sys.argv) > 1 else "3566264817a-cyber/luanma"

# example buttons: (clean text, [(real encoding, wrongly shown as), ...])
EXAMPLES = [
    ("我是一只猫", [("utf-8", "gbk")]),
    ("文件名.txt", [("gbk", "cp437")]),
    ("中文乱码", [("utf-8", "cp1252")]),
    ("こんにちは", [("utf-8", "shift_jis")]),
    ("你好，世界", [("gbk", "latin-1")]),
    ("吾輩は猫である", [("shift_jis", "gbk")]),
    ("안녕하세요", [("utf-8", "cp1252")]),
    ("繁體中文", [("big5", "gbk")]),
]


def garble(text, chain):
    for orig, shown in chain:
        text = decode(encode(text, orig, keep_fffd=True), shown, lossy=True)
    return text


def main():
    words = " ".join(sorted(freq.WORDS))
    data = {"top": freq.TOP, "topTrad": freq.TOP_TRAD, "words": words}
    examples = [garble(t, c) for t, c in EXAMPLES] + ["锟斤拷锟斤拷"]
    html = (ROOT / "web" / "index.template.html").read_text("utf-8")
    js = (ROOT / "web" / "luanma.js").read_text("utf-8")
    html = (html.replace("__DATA__", json.dumps(data, ensure_ascii=False))
                .replace("__EXAMPLES__", json.dumps(examples, ensure_ascii=False))
                .replace("__REPO__", REPO).replace("__VERSION__", __version__)
                .replace("__LUANMA_JS__", js))
    out = ROOT / "docs" / "index.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(html, "utf-8")
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
