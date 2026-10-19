import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import luanma

CASES = {
    "ÎÒÊÇÒ»Ö»Ã¨": "我是一只猫",
    "æˆ‘æ˜¯ä¸€åªçŒ«": "我是一只猫",
    "╬─╝■├√.txt": "文件名.txt",
    "屷攜偼擫偱偁傞": "吾輩は猫である",
}
CLEAN = ["我是一只猫", "吾輩は猫である", "안녕하세요", "繁體中文測試", "café crème", "I ❤️ Unicode", "25€"]


def test_fix():
    for bad, good in CASES.items():
        assert luanma.fix_text(bad) == good


def test_no_false_positive():
    for t in CLEAN:
        assert luanma.fix_text(t) == t


if __name__ == "__main__":
    test_fix()
    test_no_false_positive()
    print("ok")
