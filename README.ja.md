<div align="center">

<img src="docs/banner.png" alt="luanma — 文字化けを元の文字に" width="100%">

# luanma · 乱码克星

**`縺薙ｓ縺ｫ縺｡縺ｯ` → `こんにちは`。文字化けを貼り付けるだけで元の文字に戻し、何が原因で壊れたのかも教えてくれます。**

[![CI](https://github.com/3566264817a-cyber/luanma/actions/workflows/ci.yml/badge.svg)](https://github.com/3566264817a-cyber/luanma/actions/workflows/ci.yml)
![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-3776AB?logo=python&logoColor=white)
![依存ゼロ](https://img.shields.io/badge/依存-ゼロ-brightgreen)
![MIT](https://img.shields.io/badge/license-MIT-blue)
[![ブラウザで試す](https://img.shields.io/badge/ブラウザで-試す-ff5c8a)](https://3566264817a-cyber.github.io/luanma/)

### [👉 ブラウザで今すぐ試す（インストール不要・データ送信なし）](https://3566264817a-cyber.github.io/luanma/)

[English](README.md) · [简体中文](README.zh-CN.md) · 日本語

<img src="docs/demo.gif" alt="ブラウザ版デモ" width="760">

</div>

---

## 😫 こんな文字化け、見たことありませんか

| 見えている文字 | luanma の結果 | 何が起きたか |
|---|---|---|
| `縺薙ｓ縺ｫ縺｡縺ｯ` | **こんにちは** | UTF-8 を Shift-JIS として読んだ（古いソフト・メール） |
| `屷攜偼擫偱偁傞` | **吾輩は猫である** | 日本語のゲーム・ソフトを中国語版 Windows で起動 |
| `æ–‡å­—åŒ–ã‘` | **文字化け** | UTF-8 を Windows-1252 / Latin-1 として読んだ（Web・メール・DB） |
| `浣犲ソ涓栫晫` | **你好世界** | 中国語の UTF-8 を GBK として開いた（メモ帳 / Excel） |
| `ÄãºÃ£¬ÊÀ½ç` | **你好，世界** | GBK を MySQL の `latin1` 列に保存 |
| `╬─╝■├√.txt` | **文件名.txt** | 中国語版 Windows で作った zip を Mac / Linux で展開 |
| `羉砰いゅ` | **繁體中文** | Big5 を GBK として読んだ |
| `ì•ˆë…•í•˜ì„¸ìš”` | **안녕하세요** | 韓国語の UTF-8 を Windows-1252 として読んだ |
| `娑旇京鐖滈梻顕€顣�` | **乱码问题** | 文字化けがさらに文字化け（2 段重ね） |
| `锟斤拷` | 元データが失われていると教えてくれる | [FAQ](#-锟斤拷-と-烫烫烫-とは) を参照 |

どのエンコーディングを何回取り違えたのか、知っている必要はありません。luanma が自動で突き止めます。

## ⚡ 30 秒で使ってみる

```bash
pip install git+https://github.com/3566264817a-cyber/luanma   # Python 3.9 以上・依存ゼロ
```

```bash
$ luanma "縺薙ｓ縺ｫ縺｡縺ｯ"
こんにちは

$ luanma explain --lang ja "╬─╝■├√.txt"
文件名.txt
  誤り1：GBK のデータが CP437(DOS) として読み込まれた
  信頼度 約98%（スコア -0.70 → 2.50）

$ luanma -f broken.csv -o fixed.csv   # ファイル丸ごと（生の Shift-JIS / GBK / Big5 / EUC-KR も自動判定）
$ luanma zip archive.zip              # zip 内の文字化けしたファイル名を表示
$ cat broken.txt | luanma             # 標準入力
```

```python
import luanma

luanma.fix_text("æ–‡å­—åŒ–ã‘")        # '文字化け'

r = luanma.fix("縺薙ｓ縺ｫ縺｡縺ｯ")
r.fixed, r.changed                  # ('こんにちは', True)
print(r.explain("ja"))              # 取り違えたエンコーディング・推測したバイト数・信頼度（"zh" / "en" も可）
```

インストールしたくない場合は **[ブラウザ版](https://3566264817a-cyber.github.io/luanma/)** をどうぞ。HTML ファイル 1 つだけで、ファイルをドロップすれば UTF-8 に変換。オフラインでも動きます。

## ✨ ここが便利

- 🧭 **推測不要**：UTF-8・GBK・Big5・Shift-JIS・EUC-KR・Windows-1252・Latin-1・CP437 の組み合わせを探索し、最大 3 段の取り違えを元に戻します。
- 🩹 **欠けたバイトも補完**：文字化けによく出る `�` は、前後の文脈と出現頻度から元の文字を推測し、いくつ推測したかも報告します。
- 🛡️ **余計なことはしない**：正常なテキストはそのまま。混在している場合は文字化け部分だけを修復。テストでは正常なテキスト 618 件中 **0 件** しか変更しませんでした。
- 🗣️ **原因を説明**：「UTF-8 のデータが Shift-JIS として読み込まれた」のように教えてくれるので、再発防止にも。中文 / English / 日本語 対応。
- 📦 **依存ゼロ・メンテナンス不要**：純粋な Python。エンコーディングは確定した規格で、頻度表は一度生成すれば終わりです。
- 🔒 **プライバシー**：ブラウザ版はすべて手元で処理し、何もアップロードしません。

## 🆚 ftfy や chardet とどう違う？

文字化け修復の定番 [ftfy](https://github.com/rspeer/python-ftfy) は、GBK・Big5・Shift-JIS・EUC-KR を[扱わないと明記しています](https://ftfy.readthedocs.io/en/latest/avoid.html)。しかし CJK の文字化けの多くはまさにこれが原因です。chardet / charset-normalizer は生のバイト列のエンコーディングを推定するだけで、すでに誤ってデコードされたテキストは直せません。

| | luanma | ftfy | chardet / charset-normalizer |
|---|:-:|:-:|:-:|
| UTF-8 を Latin-1 / Windows-1252 で表示（`æ–‡å­—`） | ✅ | ✅ | ❌ |
| UTF-8 を Shift-JIS / GBK / Big5 / EUC-KR で表示（`縺薙ｓ`） | ✅ | ❌ | ❌ |
| Shift-JIS / GBK を GBK / Latin-1 / CP437 で表示（`屷攜偼`, `╬─╝■`） | ✅ | ❌ | ❌ |
| 多段の文字化け | ✅ 最大 3 段 | ✅（ラテン系のみ） | ❌ |
| 欠けたバイト（`�`）の推測 | ✅ | ❌ | ❌ |
| 生ファイルのエンコーディング判定 | ✅ | ❌ | ✅ |
| 原因の説明 | ✅ 中/英/日 | ✅ | – |
| ブラウザ版 | ✅ オフライン・1 ファイル | ❌ | ❌ |

## 📊 ベンチマーク

辞書作成に一切使っていない Wikipedia の文 **2,774** 件（簡体字・繁体字中国語、日本語、韓国語）を、実際によくある 15 通りの取り違えで文字化けさせてから修復しました。

- **バイト欠損のないケースはほぼ完全に解決**：Windows-1252、Latin-1、MySQL latin1、zip のファイル名、Big5→GBK、日本語ゲームはいずれも **100%**。
- 全体では **82%** が完全に元通り、文字正解率 **92.7%**、誤検出 **0 / 618**。
- ブラウザ版は **99.4%** のサンプルで Python 版と同じ結果。

<details>
<summary>詳細な結果表</summary>

| シナリオ | 件数 | バイト欠損あり | 完全復元 | 文字正解率 |
|---|--:|--:|--:|--:|
| UTF-8 を GBK として読む（メモ帳 / Excel） | 210 | 206 | 85% | 99.1% |
| UTF-8 を Windows-1252 として読む（Web・メール） | 468 | 0 | 100% | 100.0% |
| UTF-8 を Latin-1 として読む（DB・API） | 200 | 0 | 100% | 100.0% |
| GBK を Latin-1 として読む（MySQL latin1 列） | 200 | 0 | 100% | 100.0% |
| GBK を CP437 として読む（Windows の zip） | 210 | 0 | 100% | 100.0% |
| GBK を Big5 として読む | 200 | 89 | 60% | 93.1% |
| Big5 を GBK として読む | 85 | 0 | 100% | 100.0% |
| UTF-8 を Big5 として読む | 120 | 120 | 0% | 11.5% |
| Shift-JIS を GBK として読む（日本語ゲーム・ソフト） | 146 | 0 | 100% | 100.0% |
| UTF-8 を Shift-JIS として読む | 146 | 146 | 39% | 95.7% |
| Shift-JIS を CP437 として読む（日本語 zip） | 146 | 0 | 98% | 98.2% |
| EUC-KR を GBK として読む（韓国語ソフト） | 121 | 0 | 96% | 98.0% |
| UTF-8 を EUC-KR として読む | 122 | 122 | 0% | 53.5% |
| 2 段：UTF-8→GBK を 2 回 | 200 | 116 | 78% | 93.7% |
| 2 段：UTF-8→Windows-1252 を 2 回 | 200 | 0 | 100% | 100.0% |
| **合計** | **2774** | **799** | **82%** | **92.7%** |

文字化けの過程でバイトが壊れたケース（UTF-8 を Big5 / EUC-KR / Shift-JIS として読む、GBK を Big5 として読む）は、情報の一部がすでに失われています。luanma は復元できる部分を復元し、残りを `�` で示します。これらの行は正直な上限値であり、バグではありません。UTF-8 を Big5 として読んだ場合は失われる情報が多すぎるため、推測せずにそのまま残します。再現：`python bench/run.py`

</details>

## 🤔 锟斤拷 と 烫烫烫 とは

- **锟斤拷** は中国語圏で最も有名な文字化けです。GBK のテキストを UTF-8 として読んだため、不正なバイトがすべて `U+FFFD` になり、保存すると `EF BF BD` になります。これを 2 つずつ GBK で読むと「锟斤拷」。**元のデータは最初の段階で捨てられている**ので、どんなツールでも元には戻せません。luanma はでたらめを返さず、そのことを伝えます。
- **烫烫烫 / 屯屯屯** は文字化けではありません。MSVC のデバッグビルドは未初期化のスタックを `0xCC`、ヒープを `0xCD` で埋めるため、GBK で表示すると「烫」「屯」になります。プログラムが未初期化メモリを読んでいるサインです。
- **Excel で CSV が文字化けするのは？** 日本語版 Excel は BOM なしの UTF-8 CSV を Shift-JIS として開きます（中国語版は GBK）。`luanma -f` で修復するか、「UTF-8 (BOM 付き)」で書き出しましょう。
- **Mac で zip のファイル名が化けるのは？** Windows はファイル名を Shift-JIS / GBK で保存し、展開ツールがそれを CP437 などとして読むためです。`luanma zip file.zip` で本来の名前がわかります。

## 🔧 仕組み

1. **探索**：文字化けは「エンコーディング A のバイト列を B としてデコードした」誤りの連鎖です。8 種類のエンコーディングでビームサーチを行い、1 段ずつ元に戻します。
2. **評価**：文字の頻度（jieba の辞書）、3.1 万語の常用 2 字語、各国の常用漢字表から「自然なテキストらしさ」を採点。`�`・私用領域文字・半角カナ・罫線・語にならない漢字の並びなど、典型的な文字化けの特徴は減点します。
3. **補完**：欠けたバイトは文脈と頻度から推測し、推測した箇所を報告します。
4. **安全第一**：文字化けに見える部分だけを対象にし、明らかに良くなる場合にのみ修正を採用します。

## ⚠️ 制限

- ごく短い文字列（1〜2 文字）は曖昧なため、基本的に変更しません。
- 対応するのは上記のエンコーディングのみ。キリル文字やタイ語などの文字化けは対象外です。欧米言語の UTF-8 ↔ Windows-1252 なら ftfy を使ってください。
- 頻度データは中国語由来です。日本語・韓国語は主に JIS / KS の規格表に頼っており、十分機能しますが精度はやや粗めです。

<details>
<summary>🛠️ 開発</summary>

```bash
python tests/test_basic.py          # ユニットテスト
python bench/run.py [-v]            # ベンチマーク（-v で失敗例をすべて表示）
python tools/build_web.py user/luanma   # web/ や luanma/freq.py を変更したら docs/index.html を再生成
node web/test.mjs                   # 生成したブラウザ版のテスト
python bench/run.py --dump /tmp/c.json && node web/bench_browser.cjs /tmp/c.json   # ブラウザ版と Python 版の一致率（Chromium）
```

ブラウザ版は `docs/index.html` 1 ファイル（約 270 KB）。URL に `?q=...` を付けると入力欄に事前入力されます。

</details>

## 📄 データとライセンス

MIT。`luanma/freq.py` は [jieba](https://github.com/fxsjy/jieba) の `dict.txt`（MIT）と [OpenCC](https://github.com/BYVoid/OpenCC) の `STCharacters.txt` / `STPhrases.txt`（Apache-2.0）から生成しています。ベンチマークの文は Wikipedia（CC BY-SA 4.0）より。

---

<div align="center">

**luanma で文字化けが直ったら、⭐ をひとつ。次に「縺薙ｓ縺ｫ縺｡縺ｯ」に困る人が見つけやすくなります。**

</div>
