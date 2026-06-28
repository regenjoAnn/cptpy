/*
 * cpt.js — client-side port of cptpy's vendor .cpt reader and the
 * Robertson (2010) non-normalized soil behaviour type classification.
 *
 * Faithfully mirrors cptpy/reader.py and cptpy/cpt.py so results match
 * the Python package. Runs in the browser (no upload) and in Node (for
 * the validation test in test_cpt.js).
 */
(function (root) {
  "use strict";

  var PA = 101.325; // kPa, atmospheric pressure (cptpy constants.py)

  // Parse a "key=value,key=value" line into an object of strings.
  function parseKv(line) {
    var out = {};
    line.split(",").forEach(function (tok) {
      var i = tok.indexOf("=");
      if (i !== -1) out[tok.slice(0, i).trim()] = tok.slice(i + 1).trim();
    });
    return out;
  }

  /*
   * Parse a column-style vendor .cpt file's text.
   * qcInMpa: when true (default) the QC column is converted MPa -> kPa.
   * Returns {metadata, hasU2, rows:[{depth, qc, fs, u2}], n}.
   */
  function readCpt(text, qcInMpa) {
    if (qcInMpa === undefined) qcInMpa = true;
    var metadata = {};
    var rows = [];
    var sawU2 = true;
    var lines = text.split(/\r\n|\r|\n/);
    for (var li = 0; li < lines.length; li++) {
      var line = lines[li].trim();
      if (!line) continue;
      if (line.slice(0, 2) === "D=") {
        var r = parseKv(line);
        var row = {
          depth: parseFloat(r.D),
          qc: parseFloat(r.QC) * (qcInMpa ? 1000 : 1),
          fs: parseFloat(r.FS),
        };
        if (r.U !== undefined) row.u2 = parseFloat(r.U);
        else sawU2 = false;
        rows.push(row);
      } else if (line[0] === "H") {
        Object.assign(metadata, parseKv(line));
      }
    }
    return { metadata: metadata, hasU2: sawU2 && rows.length > 0, rows: rows, n: rows.length };
  }

  function frictionRatio(qc, fs) {
    return (fs / qc) * 100;
  }

  // Robertson (2010) non-normalized soil behaviour type index.
  function isbt(qc, rf) {
    var a = 3.47 - Math.log10(qc / PA);
    var b = 1.22 + Math.log10(rf);
    return Math.sqrt(a * a + b * b);
  }

  // Robertson (2010) zone (1-9) and soil-type label for one reading.
  function classify(qc, fs) {
    var rf = frictionRatio(qc, fs);
    var i = isbt(qc, rf);
    var qcOnPa = qc / PA;
    var eqa = qcOnPa >= 1 / (0.006 * (rf - 0.9) - 0.004 * (rf - 0.9) * (rf - 0.9) - 0.005);
    var zone, soil;
    if (rf > 1.5 && rf < 4.5 && eqa) { zone = 8; soil = "Stiff Sand to Clayed Sand"; }
    else if (rf > 4.5 && eqa) { zone = 9; soil = "Stiff Fine-Grained"; }
    else if (qcOnPa < 12 * Math.exp(-1.4 * rf)) { zone = 1; soil = "Sensitive Fine-Grained"; }
    else if (i > 3.6) { zone = 2; soil = "Organic Soils"; }
    else if (i > 2.95) { zone = 3; soil = "Clays"; }
    else if (i > 2.6) { zone = 4; soil = "Silt Mixtures"; }
    else if (i > 2.05) { zone = 5; soil = "Sand Mixtures"; }
    else if (i > 1.31) { zone = 6; soil = "Sands"; }
    else if (i < 1.31) { zone = 7; soil = "Gravelly to Dense Sand"; }
    else { zone = 0; soil = "Unknown Soil Type"; }
    return { rf: rf, isbt: i, zone: zone, soil: soil };
  }

  // Full analysis of parsed file: attaches rf/isbt/zone/soil to each row.
  function analyze(parsed) {
    parsed.rows.forEach(function (row) {
      var c = classify(row.qc, row.fs);
      row.rf = c.rf;
      row.isbt = c.isbt;
      row.zone = c.zone;
      row.soil = c.soil;
    });
    return parsed;
  }

  var api = { PA: PA, readCpt: readCpt, classify: classify, isbt: isbt, frictionRatio: frictionRatio, analyze: analyze };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.CPT = api;
})(typeof self !== "undefined" ? self : this);
