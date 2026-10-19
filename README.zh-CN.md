# luanma · 乱码克星

**自动修复中文 / 日文 / 韩文乱码。** 粘贴乱码，还原原文，并告诉你是哪一步编码出了错。

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md)

```
$ luanma "浣犲ソ涓栫晫"
你好世界
$ luanma explain "╬─╝■├√.txt"
文件名.txt
  第1次出错：GBK 编码的内容被当成 CP437(DOS) 解码
  可信度约 98%（评分 -0.70 → 2.50）
```

**在线使用 → https://3566264817a-cyber.github.io/luanma/**（单个 HTML 文件，可离线使用，内容不会上传）

![网页版截图](docs/screenshot.png)

## 为什么要做这个

处理乱码最有名的工具是 [ftfy](https://github.com/rspeer/python-ftfy)，但它的文档[明确写着](https://ftfy.readthedocs.io/en/latest/avoid.html)不处理 GBK / GB18030、Big5、Shift-JIS、EUC-KR 这些中日韩传统编码——而中文用户遇到的乱码大多正是这些：Excel 打开 UTF-8 的 CSV、Mac 上解压 Windows 打包的 zip、MySQL 的 `latin1` 字段、在简体系统上运行日文游戏……

luanma 专门补上这一块：纯 Python、零依赖，另有一个可以直接在浏览器里用的网页版。

## 能修什么

| 你看到的 | 原文 | 发生了什么 |
|---|---|---|
| `浣犲ソ涓栫晫` | 你好世界 | UTF-8 被当成 GBK 打开（记事本 / Excel） |
| `æˆ‘æ˜¯ä¸€åªçŒ«` | 我是一只猫 | UTF-8 被当成 Windows-1252 / Latin-1（网页、邮件、数据库） |
| `ÄãºÃ£¬ÊÀ½ç` | 你好，世界 | GBK 存进了 MySQL 的 `latin1` 字段 |
| `╬─╝■├√.txt` | 文件名.txt | Windows 上打包的 zip，在 Mac / Linux 解压 |
| `縺薙ｓ縺ｫ縺｡縺ｯ` | こんにちは | UTF-8 日文被当成 Shift-JIS |
| `屷攜偼擫偱偁傞` | 吾輩は猫である | 日文游戏 / 软件（Shift-JIS）在简体系统上运行 |
| `羉砰いゅ` | 繁體中文 | Big5 繁体被当成 GBK |
| `ì•ˆë…•í•˜ì„¸ìš”` | 안녕하세요 | UTF-8 韩文被当成 Windows-1252 |
| `救崇窍技夸` | 안녕하세요 | EUC-KR 韩文被当成 GBK |
| `娑旇京鐖滈梻顕€顣�` | 乱码问题 | UTF-8→GBK **乱了两次**，还丢了一个字节 |
| `锟斤拷` | – | 会说明原因：GBK 被当作 UTF-8 读取并保存过，原始字节已被替换 |

本来就正常的文本不会被改动；正常文字里夹着乱码片段的，会逐段修复。

## 安装与使用

```bash
pip install luanma          # Python ≥ 3.9，无任何依赖
```

```python
import luanma

luanma.fix_text("æˆ‘æ˜¯ä¸€åªçŒ«")        # '我是一只猫'

r = luanma.fix("鏂囦欢鍚嶏細")
r.fixed, r.changed                      # ('文件名：', True)
print(r.explain())                       # 哪两种编码搞混了、补了几个字节、可信度（explain("en") / explain("ja") 切换语言）
```

命令行：

```bash
luanma "ÎÒÊÇÒ»Ö»Ã¨"                  # 修复一段文字
luanma explain "ÎÒÊÇÒ»Ö»Ã¨"          # 并解释出了什么错
luanma -f 乱码.csv -o 修好.csv         # 修复文件（GBK/Big5/Shift-JIS/EUC-KR 原始字节也能自动识别）
luanma zip 压缩包.zip                  # 列出 zip 里乱码文件名对应的真实名字
cat broken.txt | luanma                # 从标准输入读
```

## 原理

1. **搜索**：乱码就是一串「A 编码的字节被当成 B 解码」的错误。luanma 在 UTF-8、GBK、Big5、Shift-JIS、EUC-KR、Windows-1252、Latin-1、CP437 之间做束搜索（最多 3 层），逐层反推。
2. **打分**：每个候选结果按「像不像正常文字」打分——字频（来自 jieba 词典）、3.1 万个常用双字词、国家标准常用字表（GB2312 一级字、Big5 常用字、JIS X 0208 第一水准、KS X 1001 韩文），并惩罚典型乱码特征（`�`、私用区字符、半角片假名、制表符号、一个词里混了几种文字、汉字连在一起却组不成任何词）。
3. **补回丢失字节**：如果有字节已经被破坏（例如 `鍚�` 的最后一个字节），会根据上下文和字频推测补回，并告诉你补了几个。
4. **不误伤**：只有看起来像乱码的文本才会尝试修复，而且修复结果必须明显更好才会采用。

## 测试结果

测试句子取自中文（简/繁）、日文、韩文维基百科，**没有参与任何字表的构建**；先按 15 种真实场景制造乱码，再修复。运行 `python bench/run.py` 可复现。

| 场景 | 样本 | 含丢失字节 | 完全还原 | 字符准确率 |
|---|--:|--:|--:|--:|
| UTF-8 被当 GBK 读（Windows 记事本/Excel） | 210 | 206 | 85% | 99.1% |
| UTF-8 被当 Windows-1252 读（网页/邮件） | 468 | 0 | 100% | 100.0% |
| UTF-8 被当 Latin-1 读（数据库/接口） | 200 | 0 | 100% | 100.0% |
| GBK 被当 Latin-1 读（MySQL latin1 字段） | 200 | 0 | 100% | 100.0% |
| GBK 被当 CP437 读（Windows zip 文件名） | 210 | 0 | 100% | 100.0% |
| GBK 被当 Big5 读（简体在繁体系统） | 200 | 89 | 60% | 93.1% |
| Big5 被当 GBK 读（繁体在简体系统） | 85 | 0 | 100% | 100.0% |
| UTF-8 被当 Big5 读 | 120 | 120 | 0% | 11.5% |
| Shift-JIS 被当 GBK 读（日文游戏/软件） | 146 | 0 | 100% | 100.0% |
| UTF-8 被当 Shift-JIS 读 | 146 | 146 | 39% | 95.7% |
| Shift-JIS 被当 CP437 读（日文 zip） | 146 | 0 | 98% | 98.2% |
| EUC-KR 被当 GBK 读（韩文软件） | 121 | 0 | 96% | 98.0% |
| UTF-8 被当 EUC-KR 读 | 122 | 122 | 0% | 53.5% |
| 两层：UTF-8→GBK 乱码两次 | 200 | 116 | 78% | 93.7% |
| 两层：UTF-8→Windows-1252 乱码两次 | 200 | 0 | 100% | 100.0% |
| **合计** | **2774** | **799** | **82%** | **92.7%** |

误伤测试：618 条正常文本，被错误修改 **0** 条。（完整跑一遍约 6 分钟，2 核）网页版（JavaScript，在 Chromium 中测试）对这些样本的输出与 Python 版 99.4% 一致。

- 没有丢失字节的场景基本都能完全还原。
- 如果错误的解码已经把字节毁掉了（UTF-8 被当成 Big5 / EUC-KR / Shift-JIS，GBK 被当成 Big5），信息本身就丢了一部分，luanma 会尽量推测，推不出来的用 `�` 标出。这几行是如实的上限，不是 bug。其中「UTF-8 被当 Big5 读」丢失太多，luanma 会选择原样保留，而不是瞎猜。

## 局限

- 只有 1–2 个字的极短文本有歧义，luanma 倾向于不改。
- 只支持上面列出的编码。俄文、泰文等其他乱码不在范围内；欧洲语言的 UTF-8 ↔ Windows-1252 问题请用 ftfy。
- 字频数据来自中文；日文、韩文主要依靠 JIS / KS 标准字表，效果不错但更粗一些。

## 不需要维护

编码是冻结的国家标准；字频表只需用 `tools/build_tables.py` 生成一次并提交。不联网、不下载模型、没有运行时依赖——没有需要跟进更新的东西。

## 网页版

`docs/index.html` 是一个独立的单文件（约 270 KB），由 `python tools/build_web.py 你的用户名/luanma` 生成。发布方法：GitHub 仓库 → Settings → Pages → Deploy from a branch → 选 `main` 分支的 `/docs` 目录。也可以直接下载这个文件在本地打开。网址加 `?q=乱码` 可以预填输入框。

## 开发

```bash
python tests/test_basic.py        # 单元测试
python bench/run.py [-v]          # 基准测试（-v 打印每个失败样例）
python tools/build_web.py         # 修改 web/ 或 luanma/freq.py 后重新生成 docs/index.html
node web/test.mjs                 # 测试生成的网页版
python bench/run.py --dump /tmp/c.json && node web/bench.mjs /tmp/c.json   # JS 与 Python 结果一致性
```

## 数据与许可

MIT。`luanma/freq.py` 由 [jieba](https://github.com/fxsjy/jieba) 的 `dict.txt`（MIT）和 [OpenCC](https://github.com/BYVoid/OpenCC) 的 `STCharacters.txt` / `STPhrases.txt`（Apache-2.0）生成。测试句子来自维基百科（CC BY-SA 4.0）。
