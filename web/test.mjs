// Quick test of the shipped single-file web app: node web/test.mjs
import fs from "node:fs";
import vm from "node:vm";
const html = fs.readFileSync(new URL("../docs/index.html", import.meta.url), "utf8");
const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((m) => m[1]);
vm.runInThisContext(scripts[0]);
vm.runInThisContext(scripts[1]);
const { fixText } = globalThis.luanma;
const cases = {
  "ÎÒÊÇÒ»Ö»Ã¨": "我是一只猫",
  "æˆ‘æ˜¯ä¸€åªçŒ«": "我是一只猫",
  "╬─╝■├√.txt": "文件名.txt",
  "屷攜偼擫偱偁傞": "吾輩は猫である",
  "ì•ˆë…•í•˜ì„¸ìš”": "안녕하세요",
};
const clean = ["我是一只猫", "吾輩は猫である", "안녕하세요", "繁體中文測試", "café crème", "I ❤️ Unicode", "25€"];
let bad = 0;
for (const [k, v] of Object.entries(cases)) if (fixText(k) !== v) { bad++; console.log("FAIL", k, "->", fixText(k)); }
for (const t of clean) if (fixText(t) !== t) { bad++; console.log("FALSE POSITIVE", t, "->", fixText(t)); }
console.log(bad ? `${bad} failures` : "ok");
process.exit(bad ? 1 : 0);
