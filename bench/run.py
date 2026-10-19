"""Benchmark: garble clean text through real-world encoding mix-ups, then fix.

Usage:
  python bench/run.py            # held-out Wikipedia sentences (default, honest numbers)
  python bench/run.py --hand     # small handwritten sets (used during development)
  python bench/run.py --all      # both
  add -v to print every failure
"""
import sys, time, difflib, pathlib, collections, multiprocessing
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from luanma import fix
from luanma.codecs_ import decode, encode

HERE = pathlib.Path(__file__).parent
load = lambda n: [l for l in (HERE / n).read_text("utf-8").splitlines() if l.strip()]
FN = load("corpus_files.txt")
OTHER = load("corpus_clean_other.txt")
_hand = list(map(load, ["corpus_zh.txt", "corpus_zh_trad.txt", "corpus_ja.txt", "corpus_ko.txt"]))
_wiki = list(map(load, ["wiki_zh.txt", "wiki_zh_trad.txt", "wiki_ja.txt", "wiki_ko.txt"]))
if "--all" in sys.argv:
    ZH, TW, JA, KO = (a + b for a, b in zip(_wiki, _hand))
elif "--hand" in sys.argv:
    ZH, TW, JA, KO = _hand
else:
    ZH, TW, JA, KO = _wiki

# (scenario, corpus, chain of (true encoding, wrongly decoded as))
SCENARIOS = [
    ("UTF-8 被当 GBK 读（Windows 记事本/Excel）", ZH + FN, [("utf-8", "gbk")]),
    ("UTF-8 被当 Windows-1252 读（网页/邮件）", ZH + JA + KO, [("utf-8", "cp1252")]),
    ("UTF-8 被当 Latin-1 读（数据库/接口）", ZH, [("utf-8", "latin-1")]),
    ("GBK 被当 Latin-1 读（MySQL latin1 字段）", ZH, [("gbk", "latin-1")]),
    ("GBK 被当 CP437 读（Windows zip 文件名）", FN + ZH, [("gbk", "cp437")]),
    ("GBK 被当 Big5 读（简体在繁体系统）", ZH, [("gbk", "big5")]),
    ("Big5 被当 GBK 读（繁体在简体系统）", TW, [("big5", "gbk")]),
    ("UTF-8 被当 Big5 读", TW, [("utf-8", "big5")]),
    ("Shift-JIS 被当 GBK 读（日文游戏/软件）", JA, [("shift_jis", "gbk")]),
    ("UTF-8 被当 Shift-JIS 读", JA, [("utf-8", "shift_jis")]),
    ("Shift-JIS 被当 CP437 读（日文 zip）", JA, [("shift_jis", "cp437")]),
    ("EUC-KR 被当 GBK 读（韩文软件）", KO, [("euc_kr", "gbk")]),
    ("UTF-8 被当 EUC-KR 读", KO, [("utf-8", "euc_kr")]),
    ("两层：UTF-8→GBK 乱码两次", ZH, [("utf-8", "gbk"), ("utf-8", "gbk")]),
    ("两层：UTF-8→Windows-1252 乱码两次", ZH, [("utf-8", "cp1252"), ("utf-8", "cp1252")]),
]


def garble(text, chain):
    for orig, shown in chain:
        text = decode(encode(text, orig, keep_fffd=True), shown, lossy=True)
    return text


def _fix(t):
    return fix(t).fixed


def main():
    t0 = time.time()
    tasks = []
    for name, corpus, chain in SCENARIOS:
        for clean in corpus:
            try:
                bad = garble(clean, chain)
            except UnicodeEncodeError:
                continue
            if bad != clean:
                tasks.append((name, clean, bad))
    clean_all = ZH + TW + JA + KO + FN + OTHER
    with multiprocessing.Pool() as pool:
        outs = pool.map(_fix, [b for _, _, b in tasks] + clean_all, chunksize=8)
    fixed, fp_out = outs[:len(tasks)], outs[len(tasks):]

    stats = {name: collections.Counter() for name, _, _ in SCENARIOS}
    tot = collections.Counter()
    for (name, clean, bad), out in zip(tasks, fixed):
        c = collections.Counter(n=1, lossy="\ufffd" in bad, exact=out == clean,
                                chars=difflib.SequenceMatcher(None, out, clean).ratio())
        stats[name].update(c)
        tot.update(c)
        if out != clean and "-v" in sys.argv:
            print(f"  ✗ [{name}] {bad!r} -> {out!r} (want {clean!r})")
    print(f"{'场景':<34}{'样本':>5}{'含丢失字节':>8}{'完全还原':>9}{'字符准确率':>9}")
    for name, c in stats.items():
        print(f"{name:<34}{c['n']:>5}{c['lossy']:>8}{c['exact']/c['n']:>10.0%}{c['chars']/c['n']:>10.1%}")
    print(f"{'合计':<34}{tot['n']:>5}{tot['lossy']:>8}{tot['exact']/tot['n']:>10.0%}{tot['chars']/tot['n']:>10.1%}")

    if "--dump" in sys.argv:   # cases + Python outputs, for the JS parity check (web/bench.mjs)
        import json
        path = sys.argv[sys.argv.index("--dump") + 1]
        json.dump({"tasks": [[n, c, b, o] for (n, c, b), o in zip(tasks, fixed)],
                   "clean": [[t, o] for t, o in zip(clean_all, fp_out)]},
                  open(path, "w", encoding="utf-8"), ensure_ascii=False)
    fp = [(t, o) for t, o in zip(clean_all, fp_out) if o != t]
    print(f"\n误伤测试：{len(clean_all)} 条正常文本，被错误修改 {len(fp)} 条（误伤率 {len(fp)/len(clean_all):.1%}）")
    for a, b in fp[:30]:
        print(f"  ✗ {a!r} -> {b!r}")
    print(f"耗时 {time.time()-t0:.1f}s")

if __name__ == "__main__":
    main()
