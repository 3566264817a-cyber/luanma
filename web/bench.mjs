// JS parity benchmark: node web/bench.mjs cases.json   (cases from: python bench/run.py --dump cases.json)
// Note: Node's bundled ICU decoders differ slightly from browsers (e.g. EUC-KR lacks the UHC extension), so
// Korean/Big5 numbers here can be lower than in a real browser. For browser numbers use web/bench_browser.cjs.
import fs from "node:fs";
import vm from "node:vm";
const html = fs.readFileSync(new URL("../docs/index.html", import.meta.url), "utf8");
const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((m) => m[1]);
vm.runInThisContext(scripts[0]); vm.runInThisContext(scripts[1]);
const { fix } = globalThis.luanma;
const cases = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const t0 = Date.now();
const stats = {};
let same = 0, exact = 0, n = 0;
for (const [name, clean, bad, py] of cases.tasks) {
  const out = fix(bad).fixed;
  const s = (stats[name] ||= { n: 0, exact: 0 });
  s.n++; n++;
  if (out === clean) { s.exact++; exact++; }
  if (out === py) same++;
  else if (process.argv.includes("-v")) console.log(`  ≠ [${name}] ${JSON.stringify(bad)}\n     js ${JSON.stringify(out)}\n     py ${JSON.stringify(py)}`);
}
for (const [k, s] of Object.entries(stats)) console.log(`${k.padEnd(34)} ${String(s.n).padStart(5)} ${(100 * s.exact / s.n).toFixed(0).padStart(5)}%`);
console.log(`total ${n}, exact ${(100 * exact / n).toFixed(1)}%, same as Python ${(100 * same / n).toFixed(1)}%`);
let fp = 0;
for (const [t] of cases.clean) if (fix(t).fixed !== t) { fp++; console.log("  false positive:", JSON.stringify(t)); }
console.log(`false positives ${fp}/${cases.clean.length}; ${((Date.now() - t0) / 1000).toFixed(1)}s`);
