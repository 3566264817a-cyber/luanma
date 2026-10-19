"""luanma command line.

  luanma "鎴戞槸涓€鍙\ue046尗"        fix a string
  luanma -f broken.txt -o fixed.txt  fix a file (auto-detects raw bytes too)
  luanma explain "ÎÒÊÇÒ»Ö»Ã¨"      show what went wrong
  luanma zip archive.zip             list fixed file names inside a zip
  --lang zh|en|ja                    language of explanations (default: from $LANG)
"""
import argparse, os, sys, zipfile
from . import fix
from .score import score


def _read_file(path):
    """Decode raw bytes with whichever encoding gives the most plausible text."""
    data = open(path, "rb").read()
    try:
        return data.decode("utf-8-sig"), "utf-8"
    except UnicodeDecodeError:
        pass
    best = None
    for enc, py in (("gbk", "gb18030"), ("big5", "cp950"), ("shift_jis", "cp932"), ("euc_kr", "cp949")):
        try:
            text = data.decode(py)
        except UnicodeDecodeError:
            continue
        s = score(text[:20000])
        if best is None or s > best[0]:
            best = (s, text, enc)
    if best:
        return best[1], best[2]
    return data.decode("utf-8", "replace"), "utf-8(lossy)"


def _lang(argv):
    if "--lang" in argv:
        i = argv.index("--lang")
        lang = argv[i + 1] if i + 1 < len(argv) else "en"
        del argv[i:i + 2]
    else:
        env = (os.environ.get("LC_ALL") or os.environ.get("LC_MESSAGES") or os.environ.get("LANG") or "").lower()
        lang = "zh" if env.startswith("zh") else "ja" if env.startswith("ja") else "en"
    return lang if lang in ("zh", "en", "ja") else "en"


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    lang = _lang(argv)
    if argv[:1] == ["explain"]:
        r = fix(" ".join(argv[1:]) if argv[1:] else sys.stdin.read())
        print(r.fixed)
        print(r.explain(lang))
        return
    if argv[:1] == ["zip"]:
        with zipfile.ZipFile(argv[1]) as z:
            for info in z.infolist():
                name = info.filename
                if not info.flag_bits & 0x800:     # not flagged UTF-8 → stored as cp437 by Python
                    r = fix(name)
                    print(f"{name}  →  {r.fixed}" if r.changed else name)
                else:
                    print(name)
        return
    ap = argparse.ArgumentParser(prog="luanma", description="Fix CJK mojibake / 中日韩文乱码修复. Also: luanma explain TEXT, luanma zip FILE.zip")
    ap.add_argument("text", nargs="*")
    ap.add_argument("-f", "--file")
    ap.add_argument("-o", "--output")
    a = ap.parse_args(argv)
    if a.file:
        text, enc = _read_file(a.file)
        out = "\n".join(fix(line).fixed for line in text.split("\n"))
        if a.output:
            open(a.output, "w", encoding="utf-8").write(out)
            print(f"wrote {a.output} (source read as {enc})", file=sys.stderr)
        else:
            sys.stdout.write(out)
        return
    text = " ".join(a.text) if a.text else sys.stdin.read()
    print(fix(text).fixed)


if __name__ == "__main__":
    main()
