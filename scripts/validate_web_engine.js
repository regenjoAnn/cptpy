const fs = require("fs");
const CPT = require("../web/cpt.js");

const src = process.argv[2];     // raw .cpt
const truth = process.argv[3];   // python results csv

const parsed = CPT.analyze(CPT.readCpt(fs.readFileSync(src, "latin1")));
const lines = fs.readFileSync(truth, "utf8").trim().split("\n").slice(1);

let max = { rf: 0, isbt: 0 }, mism = 0, checked = 0;
lines.forEach((l, i) => {
  const c = l.split(",");
  const t = { rf: +c[4], isbt: +c[5], zone: +c[6], soil: c.slice(7).join(",") };
  const r = parsed.rows[i];
  checked++;
  if (Number.isFinite(t.rf)) max.rf = Math.max(max.rf, Math.abs(r.rf - t.rf));
  if (Number.isFinite(t.isbt)) max.isbt = Math.max(max.isbt, Math.abs(r.isbt - t.isbt));
  if (r.soil !== t.soil || r.zone !== t.zone) {
    mism++;
    if (mism <= 5) console.log(`row ${i} d=${r.depth}: JS [${r.zone} ${r.soil}] vs PY [${t.zone} ${t.soil}]`);
  }
});
console.log(`Checked ${checked} rows | soil/zone mismatches: ${mism}`);
console.log(`Max |Rf diff| = ${max.rf.toExponential(2)} | Max |Isbt diff| = ${max.isbt.toExponential(2)}`);
