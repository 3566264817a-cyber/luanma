<div align="center">

<img src="docs/banner.png" alt="luanma — turn CJK mojibake back into real text" width="100%">

# luanma · 乱码克星

**`浣犲ソ涓栫晫` → `你好世界`. Paste garbled Chinese, Japanese or Korean text, get the original back, and see what broke it.**

[![CI](https://github.com/3566264817a-cyber/luanma/actions/workflows/ci.yml/badge.svg)](https://github.com/3566264817a-cyber/luanma/actions/workflows/ci.yml)
![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-3776AB?logo=python&logoColor=white)
![zero dependencies](https://img.shields.io/badge/dependencies-0-brightgreen)
![MIT](https://img.shields.io/badge/license-MIT-blue)
[![Try it online](https://img.shields.io/badge/try%20it-online-ff5c8a)](https://3566264817a-cyber.github.io/luanma/)

### [👉 Try it in your browser (no install, nothing uploaded)](https://3566264817a-cyber.github.io/luanma/)

English · [简体中文](README.zh-CN.md) · [日本語](README.ja.md)

<img src="docs/demo.gif" alt="web demo" width="760">

</div>

---

## 😫 You've seen these

| You see | luanma gives back | What happened |
|---|---|---|
| `浣犲ソ涓栫晫` | **你好世界** | UTF-8 opened as GBK (Notepad / Excel on Chinese Windows) |
| `╬─╝■├√.txt` | **文件名.txt** | zip made on Chinese Windows, unpacked on macOS / Linux |
| `ÄãºÃ£¬ÊÀ½ç` | **你好，世界** | GBK stored in a MySQL `latin1` column |
| `æˆ‘æ˜¯ä¸€åªçŒ«` | **我是一只猫** | UTF-8 read as Latin-1 / Windows-1252 (web, e-mail, APIs) |
| `羉砰いゅ` | **繁體中文** | Big5 opened on a Simplified-Chinese system |
| `縺薙ｓ縺ｫ縺｡縺ｯ` | **こんにちは** | Japanese UTF-8 read as Shift-JIS |
| `屷攜偼擫偱偁傞` | **吾輩は猫である** | Japanese game / software on a Chinese system |
| `ì•ˆë…•í•˜ì„¸ìš”` | **안녕하세요** | Korean UTF-8 read as Windows-1252 |
| `娑旇京鐖滈梻顕€顣�` | **乱码问题** | mojibake of mojibake (two layers) |
| `锟斤拷` | tells you the text is gone | see the [FAQ](#-what-are-锟斤拷-and-烫烫烫) |

You don't need to know which encoding went wrong or how many times. luanma works it out.

## ⚡ 30-second start

```bash
pip install git+https://github.com/3566264817a-cyber/luanma   # Python ≥ 3.9, zero dependencies
```

```bash
$ luanma "浣犲ソ涓栫晫"
你好世界

$ luanma explain --lang en "╬─╝■├√.txt"
文件名.txt
  Error 1: GBK bytes were decoded as CP437(DOS)
  Confidence ~98% (score -0.70 -> 2.50)

$ luanma -f broken.csv -o fixed.csv   # whole files (raw GBK / Big5 / Shift-JIS / EUC-KR bytes are detected too)
$ luanma zip archive.zip              # real names of garbled files inside a zip
$ cat broken.txt | luanma             # stdin
```

```python
import luanma

luanma.fix_text("æˆ‘æ˜¯ä¸€åªçŒ«")    # '我是一只猫'

r = luanma.fix("鏂囦欢鍚嶏細")
r.fixed, r.changed                  # ('文件名：', True)
print(r.explain("en"))              # which encodings were mixed up, bytes guessed, confidence ("zh" / "ja" too)
```

Don't want to install anything? Use the **[web version](https://3566264817a-cyber.github.io/luanma/)**. It's a single HTML file: drop a whole file in, get UTF-8 back. It works offline too.

## ✨ Why it's nice

- 🧭 **No guessing**: searches across UTF-8, GBK, Big5, Shift-JIS, EUC-KR, Windows-1252, Latin-1 and CP437, and undoes up to 3 layers of mistakes.
- 🩹 **Repairs lost bytes**: for the `�` you often see in mojibake, luanma guesses the original character from context and frequency, and says how many it guessed.
- 🛡️ **Does no harm**: clean text is left alone; in mixed strings only the garbled parts are fixed. **0** of 618 clean texts were changed in testing.
- 🗣️ **Explains itself**: "UTF-8 was decoded as GBK", so you know how to avoid it next time. In 中文 / English / 日本語.
- 📦 **Zero dependencies, zero maintenance**: pure Python. Encodings are frozen standards, and the frequency tables are generated once.
- 🔒 **Private**: the web version runs entirely in your browser and uploads nothing.

## 🆚 How is this different from ftfy or chardet?

[ftfy](https://github.com/rspeer/python-ftfy) is the go-to mojibake fixer, but its docs [explicitly say](https://ftfy.readthedocs.io/en/latest/avoid.html) it doesn't handle GBK, Big5, Shift-JIS or EUC-KR, and that's where most CJK mojibake comes from. chardet / charset-normalizer only guess the encoding of raw bytes. They can't repair text that's already been decoded wrongly.

| | luanma | ftfy | chardet / charset-normalizer |
|---|:-:|:-:|:-:|
| UTF-8 shown as Latin-1 / Windows-1252 (`æˆ‘æ˜¯`) | ✅ | ✅ | ❌ |
| UTF-8 shown as GBK / Big5 / Shift-JIS / EUC-KR (`浣犲ソ`) | ✅ | ❌ | ❌ |
| GBK / Big5 / Shift-JIS shown as Latin-1 / CP437 (`ÄãºÃ`, `╬─╝■`) | ✅ | ❌ | ❌ |
| Multiple layers | ✅ up to 3 | ✅ (Latin only) | ❌ |
| Guesses lost bytes (`�`) | ✅ | ❌ | ❌ |
| Detects the encoding of a raw file | ✅ | ❌ | ✅ |
| Explains what went wrong | ✅ zh/en/ja | ✅ | – |
| Browser version | ✅ offline, one file | ❌ | ❌ |

## 📊 Benchmark

**2,774** held-out Wikipedia sentences (Simplified & Traditional Chinese, Japanese, Korean; none were used to build any table), garbled through 15 real-world mix-ups, then fixed:

- **Scenarios without lost bytes are essentially solved**: Windows-1252, Latin-1, MySQL latin1, zip file names, Big5→GBK and Japanese games are all at **100%**.
- **82%** of samples come back exactly, with **92.7%** character accuracy overall and **0 / 618** false positives.
- The web version matches the Python output on **99.4%** of samples.

<details>
<summary>Full results table</summary>

| Scenario | Samples | With lost bytes | Fully restored | Char accuracy |
|---|--:|--:|--:|--:|
| UTF-8 read as GBK (Notepad / Excel) | 210 | 206 | 85% | 99.1% |
| UTF-8 read as Windows-1252 (web, e-mail) | 468 | 0 | 100% | 100.0% |
| UTF-8 read as Latin-1 (databases, APIs) | 200 | 0 | 100% | 100.0% |
| GBK read as Latin-1 (MySQL latin1 column) | 200 | 0 | 100% | 100.0% |
| GBK read as CP437 (zip from Windows) | 210 | 0 | 100% | 100.0% |
| GBK read as Big5 | 200 | 89 | 60% | 93.1% |
| Big5 read as GBK | 85 | 0 | 100% | 100.0% |
| UTF-8 read as Big5 | 120 | 120 | 0% | 11.5% |
| Shift-JIS read as GBK (Japanese games/software) | 146 | 0 | 100% | 100.0% |
| UTF-8 read as Shift-JIS | 146 | 146 | 39% | 95.7% |
| Shift-JIS read as CP437 (Japanese zip) | 146 | 0 | 98% | 98.2% |
| EUC-KR read as GBK (Korean software) | 121 | 0 | 96% | 98.0% |
| UTF-8 read as EUC-KR | 122 | 122 | 0% | 53.5% |
| 2 layers: UTF-8 → GBK twice | 200 | 116 | 78% | 93.7% |
| 2 layers: UTF-8 → Windows-1252 twice | 200 | 0 | 100% | 100.0% |
| **Total** | **2774** | **799** | **82%** | **92.7%** |

When the wrong decoding destroyed bytes (UTF-8 read as Big5 / EUC-KR / Shift-JIS, GBK read as Big5), part of the information is gone. luanma recovers what it can and marks the rest with `�`. These rows are an honest upper bound, not a bug. UTF-8 read as Big5 loses so much that luanma deliberately leaves the text unchanged instead of guessing. Reproduce with `python bench/run.py`.

</details>

## 🤔 What are 锟斤拷 and 烫烫烫?

- **锟斤拷** is the most famous Chinese mojibake. GBK text was read as UTF-8, so every invalid byte became `U+FFFD`. Once saved, those are the bytes `EF BF BD`, and every two of them read back as GBK spell 锟斤拷. **The original was thrown away at the first step**, so no tool can bring it back. luanma tells you so instead of making something up.
- **烫烫烫 / 屯屯屯** isn't mojibake at all. MSVC debug builds fill uninitialized stack memory with `0xCC` and heap memory with `0xCD`, which display as 烫 and 屯 in GBK. It means your program read uninitialized memory.
- **Why does Excel garble my CSV?** Excel on Chinese Windows opens UTF-8 CSVs without a BOM as GBK. Fix the file with `luanma -f`, or export as "UTF-8 with BOM".
- **Why are zip file names `╬─╝■` on my Mac?** Windows stores the names in GBK, and the unzipper reads them as CP437. `luanma zip file.zip` shows the real names.

## 🔧 How it works

1. **Search.** Mojibake is a chain of "bytes in encoding A were decoded as encoding B" mistakes. luanma runs a beam search over 8 encodings, undoing one layer at a time.
2. **Score.** Candidates are scored for "looks like real text" using character frequency (from jieba's dictionary), 31k common two-character words and the national common-character tables. Typical mojibake symptoms are penalized (`�`, private-use characters, half-width katakana, box-drawing characters, hanzi that form no words…).
3. **Repair.** Lost bytes are guessed from context and frequency, and the guesses are reported.
4. **Do no harm.** Only text that looks garbled is touched, and a fix is accepted only if it is clearly better.

## ⚠️ Limitations

- Very short strings (1–2 characters) are ambiguous, so luanma prefers to leave them alone.
- Only the encodings listed above are covered. Cyrillic, Thai and other mojibake are out of scope; for European UTF-8 ↔ Windows-1252 issues, use ftfy.
- The frequency data is Chinese. Japanese and Korean rely mostly on the JIS / KS standard tables, which work well but are coarser.

<details>
<summary>🛠️ Development</summary>

```bash
python tests/test_basic.py          # unit tests
python bench/run.py [-v]            # benchmark (-v prints every failure)
python tools/build_web.py user/luanma   # rebuild docs/index.html after changing web/ or luanma/freq.py
node web/test.mjs                   # test the built web app
python bench/run.py --dump /tmp/c.json && node web/bench_browser.cjs /tmp/c.json   # web vs Python parity (Chromium)
```

The web version is the single file `docs/index.html` (≈270 KB). Adding `?q=...` to the URL pre-fills the input.

</details>

## 📄 Data & license

MIT. `luanma/freq.py` is derived from [jieba](https://github.com/fxsjy/jieba)'s `dict.txt` (MIT) and [OpenCC](https://github.com/BYVoid/OpenCC)'s `STCharacters.txt` / `STPhrases.txt` (Apache-2.0). Benchmark sentences are from Wikipedia (CC BY-SA 4.0).

---

<div align="center">

**If luanma rescued a file for you, a ⭐ helps the next person drowning in 锟斤拷 find it.**

</div>
