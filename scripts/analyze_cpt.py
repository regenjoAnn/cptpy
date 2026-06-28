"""Analyze CPT files with cptpy.

Usage
-----
Run a single file (writes <name>_results.csv next to it):

    python scripts/analyze_cpt.py "/path/to/210CPT01.cpt"

Run every .cpt in a folder (writes all_soundings_results.csv and
soundings_summary.csv into that folder):

    python scripts/analyze_cpt.py "/path/to/folder"

Add --kpa if the QC column is already in kPa (default assumes MPa).
"""
import glob
import os
import sys

import numpy as np
import cptpy

SOIL_ORDER = [
    "Sensitive Fine-Grained", "Organic Soils", "Clays", "Silt Mixtures",
    "Sand Mixtures", "Sands", "Gravelly to Dense Sand",
    "Stiff Sand to Clayed Sand", "Stiff Fine-Grained",
]


def analyze(path, qc_in_mpa):
    """Return (cpt, isbt, zone, soil) for one .cpt file."""
    cpt = cptpy.read_cpt(path, qc_in_mpa=qc_in_mpa)
    isbt, (zone, soil) = cpt.sbt()
    return cpt, isbt, zone, soil


def write_rows(f, hole, fname, cpt, isbt, zone, soil):
    for i in range(len(cpt)):
        u2 = f"{cpt.u2[i]:.2f}" if hasattr(cpt, "u2") else ""
        f.write(f"{hole},{fname},{cpt.depth[i]:.3f},{cpt.qc[i]:.2f},"
                f"{cpt.fs[i]:.2f},{u2},{cpt.rf[i]:.3f},{isbt[i]:.3f},"
                f"{zone[i]},{soil[i]}\n")


HEADER = "hole_id,file,depth_m,qc_kPa,fs_kPa,u2_kPa,Rf_pct,Isbt,zone,soil_type\n"


def run_file(path, qc_in_mpa):
    cpt, isbt, zone, soil = analyze(path, qc_in_mpa)
    out = os.path.splitext(path)[0] + "_results.csv"
    hole = cpt.metadata.get("HK", os.path.basename(path))
    with open(out, "w") as f:
        f.write(HEADER)
        write_rows(f, hole, os.path.basename(path), cpt, isbt, zone, soil)
    vals, counts = np.unique(soil, return_counts=True)
    dom = vals[np.argmax(counts)]
    print(f"{os.path.basename(path)}: {len(cpt)} readings, "
          f"0-{cpt.depth.max():.2f} m, dominant {dom}")
    print(f"Wrote {out}")


def run_folder(folder, qc_in_mpa):
    files = sorted(glob.glob(os.path.join(folder, "*.cpt")))
    if not files:
        print(f"No .cpt files found in {folder}")
        return
    print(f"Found {len(files)} .cpt files\n")
    combined = os.path.join(folder, "all_soundings_results.csv")
    summary = os.path.join(folder, "soundings_summary.csv")
    sums = []
    with open(combined, "w") as f:
        f.write(HEADER)
        for path in files:
            name = os.path.basename(path)
            try:
                cpt, isbt, zone, soil = analyze(path, qc_in_mpa)
            except Exception as e:
                print(f"  !! {name}: FAILED ({type(e).__name__}: {e})")
                continue
            hole = cpt.metadata.get("HK", name)
            write_rows(f, hole, name, cpt, isbt, zone, soil)
            n = len(cpt)
            vals, counts = np.unique(soil, return_counts=True)
            pct = {v: c / n * 100 for v, c in zip(vals, counts)}
            dom = max(pct, key=pct.get)
            print(f"  {name:18s} {n:4d} readings  0-{cpt.depth.max():5.2f} m"
                  f"  -> {dom} ({pct[dom]:.0f}%)")
            sums.append((hole, name, n, cpt.depth.max(), dom, pct))
    with open(summary, "w") as f:
        f.write("hole_id,file,n_readings,max_depth_m,dominant_soil,"
                + ",".join(f'pct_{s.replace(" ", "_")}' for s in SOIL_ORDER) + "\n")
        for hole, name, n, maxd, dom, pct in sums:
            f.write(f"{hole},{name},{n},{maxd:.2f},{dom},"
                    + ",".join(f"{pct.get(s, 0):.1f}" for s in SOIL_ORDER) + "\n")
    print(f"\nWrote {combined}")
    print(f"Wrote {summary}")


def main():
    args = [a for a in sys.argv[1:] if a != "--kpa"]
    qc_in_mpa = "--kpa" not in sys.argv
    if not args:
        print(__doc__)
        sys.exit(1)
    path = args[0]
    if os.path.isdir(path):
        run_folder(path, qc_in_mpa)
    elif os.path.isfile(path):
        run_file(path, qc_in_mpa)
    else:
        print(f"Not found: {path}")
        sys.exit(1)


if __name__ == "__main__":
    main()
