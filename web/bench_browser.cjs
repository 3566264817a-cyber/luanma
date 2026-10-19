// Same as web/bench.mjs but runs inside real Chromium: npm i playwright; node web/bench_browser.cjs cases.json
// (set CHROME=/path/to/chromium to use a system browser)
const { chromium } = require('playwright'); const fs=require('fs');
(async()=>{
 const b=await chromium.launch({executablePath:process.env.CHROME||undefined,args:['--no-sandbox']}); const p=await b.newPage();
 await p.goto('file://'+require('path').resolve(__dirname,'../docs/index.html'));
 const cases=JSON.parse(fs.readFileSync(process.argv[2]));
 const r=await p.evaluate((cases)=>{
   const {fix}=window.luanma; const st={}; let same=0,ex=0,n=0,fp=0; const diffs=[]; const t0=Date.now();
   for (const [name,clean,bad,py] of cases.tasks){ const o=fix(bad).fixed; const s=(st[name] ||= {n:0,e:0}); s.n++; n++; if(o===clean){s.e++;ex++} if(o===py) same++; else if(diffs.length<40) diffs.push([name,bad,o,py]); }
   for (const [t] of cases.clean) if (fix(t).fixed!==t) fp++;
   return {st,same,ex,n,fp,nc:cases.clean.length,diffs,secs:(Date.now()-t0)/1000};
 }, cases);
 for (const [k,s] of Object.entries(r.st)) console.log(k.padEnd(34), String(s.n).padStart(5), (100*s.e/s.n).toFixed(0).padStart(5)+'%');
 console.log(`total ${r.n}, exact ${(100*r.ex/r.n).toFixed(1)}%, same as Python ${(100*r.same/r.n).toFixed(1)}%, false positives ${r.fp}/${r.nc}, ${r.secs}s`);
 
 await b.close(); process.exit(0);
})().catch(e=>{console.error(e);process.exit(1)});
