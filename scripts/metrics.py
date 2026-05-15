"""
tls_profiles.py
---------------
Parse TLS pgap/PAI/PAVD profile txt files and compute canopy structure metrics.

Usage
-----
    python tls_profiles.py --input ./data --height_mode both --pavd_threshold 1e-4 --output_dir
    
    kdayal@cave012:~/Documents/projects/qfl/profiles-with-pylidar/scripts$ python metrics.py --input /Stor1/karun/data/test-pylidar/r1_001_r1_002_1.txt --height_mode both --pavd_threshold 1e-4 --output_dir ~/Documents/projects/qfl/profiles-with-pylidar/
"""

import argparse
from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import entropy


# ---------------------------------------------------------------------------
# USER PARAMETERS (edit here if not using CLI)
# ---------------------------------------------------------------------------
INPUT_PATH      = Path("./data")   # folder or single file
HEIGHT_MODE     = "both"           # 'abs' | 'rel' | 'both'
PAVD_THRESHOLD  = 1e-4             # minimum PAVD to count as canopy
OUTPUT_CSV      = Path("./metrics_output.csv")


# ---------------------------------------------------------------------------
# HEADER PARSER
# ---------------------------------------------------------------------------
def parse_header(lines):
    """
    Parse #-prefixed header lines into a metadata dict.
    Stops at the first non-comment line.
    """
    meta = {}
    for line in lines:
        if not line.startswith("#"):
            break
        content = line.lstrip("#").strip()
        if ":" in content:
            key, val = content.split(":", 1)
            meta[key.strip()] = val.strip()
    return meta


# ---------------------------------------------------------------------------
# FILE PARSER
# ---------------------------------------------------------------------------
def parse_profile_file(filepath):
    """
    Parse a single TLS profile txt file.

    Returns
    -------
    meta : dict   — header metadata including parsed hres and hmax
    df   : DataFrame — height (metres, as-is from file) + profile columns
    """
    filepath = Path(filepath)
    lines = filepath.read_text().splitlines()

    # --- header ---
    meta = parse_header(lines)
    # store raw header lines verbatim for output reproduction
    meta["header_lines"] = [l for l in lines if l.startswith("#")]
    hres_str = meta.get("hres_zres_ares", "0.5 5 360")
    hres = float(hres_str.split()[0])
    meta["hres"] = hres
    meta["source_file"] = filepath.name

    # --- data lines (non-comment, non-empty) ---
    data_lines = [l for l in lines if l.strip() and not l.strip().startswith("#")]

    col_line = data_lines[0].strip()
    columns  = col_line.split()

    data_rows = []
    for line in data_lines[1:]:
        stripped = line.strip()
        if stripped == col_line or stripped.startswith("height"):
            continue  # skip duplicate header row
        data_rows.append(stripped)

    df = pd.read_csv(
        StringIO("\n".join(data_rows)),
        sep=r"\s+",
        header=None,
        names=columns,
    )

    # height column is already in metres — no conversion needed
    # rename camelCase to snake_case
    df.rename(columns={
        "hingePAI":     "hinge_pai",
        "weightedPAI":  "weighted_pai",
        "linearPAI":    "linear_pai",
        "hingePAVD":    "hinge_pavd",
        "weightedPAVD": "weighted_pavd",
        "linearPAVD":   "linear_pavd",
    }, inplace=True)

    # clip negative PAVD to zero
    for col in ["hinge_pavd", "weighted_pavd", "linear_pavd"]:
        if col in df.columns:
            df[col] = df[col].clip(lower=0)

    return meta, df


# ---------------------------------------------------------------------------
# LOAD ALL PROFILES
# ---------------------------------------------------------------------------
def load_all_profiles(input_path, pavd_threshold=1e-4):
    """
    Load all .txt profile files from a folder or a single file.

    Returns
    -------
    list of (meta, df) tuples, one per file.
    """
    input_path = Path(input_path)

    if input_path.is_file():
        files = [input_path]
    elif input_path.is_dir():
        files = sorted(input_path.glob("*.txt"))
    else:
        raise FileNotFoundError(f"Path not found: {input_path}")

    print(f"Found {len(files)} file(s).")

    profiles = []
    for f in files:
        meta, df = parse_profile_file(f)
        meta["pavd_threshold"] = pavd_threshold 

        # hmax = last height where PAVD exceeds threshold (true canopy top)
        nonzero = df[df["hinge_pavd"] > pavd_threshold]
        hmax = nonzero["height"].max() if not nonzero.empty else df["height"].max()
        meta["hmax"] = hmax

        # trim flat zero tail (keep one step beyond hmax for context)
        df = df[df["height"] <= hmax + meta["hres"]].copy()

        profiles.append((meta, df))
        print(f"  {f.name}: hres={meta['hres']}m  hmax={hmax}m  rows={len(df)}")

    return profiles


# ---------------------------------------------------------------------------
# INTERPOLATION HELPER
# ---------------------------------------------------------------------------
def height_at_pai_prop(target, height, pai):
    """
    Return the height at which cumulative PAI reaches `target` fraction
    of total PAI. PAI is already cumulative and monotonically increasing.
    Uses linear interpolation between bounding rows.

    Parameters
    ----------
    target : float, 0–1  (e.g. 0.50 for RH50)
    height : array-like, metres
    pai    : array-like, cumulative PAI (hinge_pai)

    Returns
    -------
    float : interpolated height in metres, or np.nan if undefined
    """
    height = np.asarray(height, dtype=float)
    pai    = np.asarray(pai,    dtype=float)

    pai_max = pai.max()
    if pai_max == 0:
        return np.nan

    cprop = pai / pai_max  # normalise 0 → 1

    idx = np.searchsorted(cprop, target, side="left")

    if idx == 0:
        return float(height[0])
    if idx >= len(cprop):
        return float(height[-1])

    h_lo, h_hi = height[idx - 1], height[idx]
    p_lo, p_hi = cprop[idx - 1],  cprop[idx]

    if p_hi == p_lo:
        return float(h_lo)

    return float(h_lo + (target - p_lo) / (p_hi - p_lo) * (h_hi - h_lo))


# ---------------------------------------------------------------------------
# METRICS
# ---------------------------------------------------------------------------
def gini(x):
    """Gini coefficient of a non-negative array."""
    x = np.sort(x)
    n = len(x)
    if n == 0 or x.sum() == 0:
        return np.nan
    cumx = np.cumsum(x)
    return (2 * np.sum(np.arange(1, n + 1) * x) / (n * cumx[-1])) - (n + 1) / n


def compute_metrics(meta, df, height_mode="both"):
    """
    Compute canopy structure metrics for a single scan profile.

    Parameters
    ----------
    meta        : dict from parse_profile_file / load_all_profiles
    df          : DataFrame from parse_profile_file
    height_mode : 'abs' | 'rel' | 'both'
                  abs  -> RH metrics in metres
                  rel  -> RH metrics as fraction of hmax
                  both -> both sets of columns

    Returns
    -------
    dict of metrics (one row per scan)
    """
    hmax   = meta["hmax"]
    hres   = meta["hres"]
    height = df["height"].values
    pai    = df["hinge_pai"].values
    pavd   = df["hinge_pavd"].values

    # scalar PAI
    pai_total  = float(pai.max())

    # PAVD stats
    pavd_max   = float(pavd.max())
    h_pavd_max = float(height[np.argmax(pavd)])

    # RH metrics — absolute (metres)
    rh25_abs = height_at_pai_prop(0.25, height, pai)
    rh50_abs = height_at_pai_prop(0.50, height, pai)
    rh75_abs = height_at_pai_prop(0.75, height, pai)
    rh99_abs = height_at_pai_prop(0.99, height, pai)

    # RH metrics — relative (fraction of hmax)
    rh25_rel = rh25_abs / hmax if hmax > 0 else np.nan
    rh50_rel = rh50_abs / hmax if hmax > 0 else np.nan
    rh75_rel = rh75_abs / hmax if hmax > 0 else np.nan
    rh99_rel = rh99_abs / hmax if hmax > 0 else np.nan
    
    pavd_threshold = meta.get("pavd_threshold", 0.0)

    # PAVD distribution metrics (positive values only)
    pavd_pos = pavd[pavd > pavd_threshold]

    gini_val = gini(pavd_pos) if len(pavd_pos) > 1 else np.nan
    cv_val = (pavd_pos.std(ddof=1) / pavd_pos.mean()) if len(pavd_pos) > 1 else np.nan
    pavd_norm = pavd_pos / pavd_pos.sum()
    shannon  = float(entropy(pavd_norm)) if len(pavd_norm) > 1 else np.nan

    # base row — always included
    row = {
        "source_file"  : meta.get("source_file", ""),
        "scanpositions": meta.get("scanpositions", ""),
        "timestamp"    : meta.get("timestamp", ""),
        "query"        : meta.get("query_str", ""),
        "hres"         : hres,
        "hmax"         : hmax,
        "pai"          : pai_total,
        "pavd_max"     : pavd_max,
        "h_pavd_max"   : h_pavd_max,
        "gini"         : gini_val,
        "cv"           : cv_val,
        "shannon"      : shannon,
    }

    if height_mode in ("abs", "both"):
        row.update({
            "rh25_abs": rh25_abs,
            "rh50_abs": rh50_abs,
            "rh75_abs": rh75_abs,
            "rh99_abs": rh99_abs,
        })

    if height_mode in ("rel", "both"):
        row.update({
            "rh25_rel": rh25_rel,
            "rh50_rel": rh50_rel,
            "rh75_rel": rh75_rel,
            "rh99_rel": rh99_rel,
        })

    return row


# ---------------------------------------------------------------------------
# OUTPUT WRITER
# ---------------------------------------------------------------------------
def write_metrics_file(meta, metrics_row, output_path):
    """
    Write a per-scan output file containing:
      - all original header lines (# key : value)
      - a separator
      - computed metrics as additional # key : value lines

    No data table — header only.

    Parameters
    ----------
    meta         : dict from parse_profile_file (includes 'header_lines' raw)
    metrics_row  : dict from compute_metrics
    output_path  : Path to write to
    """
    lines = []

    # original header lines verbatim
    for line in meta.get("header_lines", []):
        lines.append(line)

    # separator + metrics block
    lines.append("# ---")
    lines.append("# metrics")
    lines.append("# ---")

    # keys to skip — already in original header or internal
    skip_keys = {"source_file", "header_lines", "hres"}

    for key, val in metrics_row.items():
        if key in skip_keys:
            continue
        if isinstance(val, float):
            formatted = f"{val:.6f}"
        else:
            formatted = str(val)
        lines.append(f"# {key:<20}: {formatted}")

    Path(output_path).write_text("\n".join(lines) + "\n")
    print(f"  Written: {output_path}")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="TLS profile parser and metrics")
    parser.add_argument("--input",          default=str(INPUT_PATH),  help="Folder or single .txt file")
    parser.add_argument("--height_mode",    default=HEIGHT_MODE,      choices=["abs", "rel", "both"])
    parser.add_argument("--pavd_threshold", default=PAVD_THRESHOLD,   type=float)
    parser.add_argument("--output_dir",     default="./metrics",      help="Output folder for per-file metric txt files")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    profiles = load_all_profiles(args.input, pavd_threshold=args.pavd_threshold)

    print("\nComputing and writing metrics...")
    for meta, df in profiles:
        row = compute_metrics(meta, df, height_mode=args.height_mode)
        stem = Path(meta["source_file"]).stem
        out_path = out_dir / f"{stem}_metrics.txt"
        write_metrics_file(meta, row, out_path)

    print(f"\nDone. {len(profiles)} file(s) written to {out_dir}/")


if __name__ == "__main__":
    main()