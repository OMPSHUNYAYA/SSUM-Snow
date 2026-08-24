import argparse
import pandas as pd
import numpy as np

EPS = 1e-12

def parse_isd_temp_c(x):
    if pd.isna(x):
        return np.nan
    s = str(x).strip()
    if not s:
        return np.nan
    p = s.split(",")[0].strip()
    if p in ("+9999", "-9999", "9999"):
        return np.nan
    try:
        v = int(p)
        return v / 10.0
    except Exception:
        try:
            return float(p)
        except Exception:
            return np.nan

def parse_aa_precip_mm(x, depth_scale_mm=0.1):
    if pd.isna(x):
        return 0.0
    s = str(x).strip()
    if not s:
        return 0.0
    parts = s.split(",")
    if len(parts) < 2:
        return 0.0
    depth = parts[1].strip()
    if not depth or depth in ("9999", "99999"):
        return 0.0
    try:
        d = int(depth)
        mm = float(d) * float(depth_scale_mm)
        if not np.isfinite(mm) or mm < 0:
            return 0.0
        return mm
    except Exception:
        return 0.0

def rh_from_t_td(Tc, Tdc):
    Tc = np.asarray(Tc, dtype=float)
    Tdc = np.asarray(Tdc, dtype=float)
    rh = np.full_like(Tc, np.nan)
    m = np.isfinite(Tc) & np.isfinite(Tdc)
    if not np.any(m):
        return rh
    a = 17.625
    b = 243.04
    es_td = np.exp((a * Tdc[m]) / (b + Tdc[m]))
    es_t = np.exp((a * Tc[m]) / (b + Tc[m]))
    r = 100.0 * (es_td / (es_t + EPS))
    r = np.clip(r, 0.0, 100.0)
    rh[m] = r
    return rh

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_path", required=True)
    ap.add_argument("--out", dest="out_path", required=True)

    ap.add_argument("--precip_col", default="AA1")
    ap.add_argument("--precip_depth_scale_mm", type=float, default=0.1)

    ap.add_argument("--snow_temp_c", type=float, default=0.0)
    ap.add_argument("--snow_ratio", type=float, default=10.0)

    args = ap.parse_args()

    df = pd.read_csv(args.in_path, low_memory=False)

    need = ["DATE", "TMP", "DEW"]
    miss = [c for c in need if c not in df.columns]
    if miss:
        raise SystemExit(f"Missing required columns: {miss}")

    df["time"] = pd.to_datetime(df["DATE"], errors="coerce", utc=True)
    df = df.dropna(subset=["time"]).sort_values("time").reset_index(drop=True)

    df["temperature_C"] = df["TMP"].apply(parse_isd_temp_c)
    df["dewpoint_C"] = df["DEW"].apply(parse_isd_temp_c)

    df["humidity_pct"] = rh_from_t_td(df["temperature_C"].values, df["dewpoint_C"].values)

    if args.precip_col in df.columns:
        df["precip_mm"] = df[args.precip_col].apply(lambda x: parse_aa_precip_mm(x, args.precip_depth_scale_mm))
    else:
        df["precip_mm"] = 0.0

    Tc = df["temperature_C"].astype(float).values
    Pmm = df["precip_mm"].astype(float).values

    snow_mask = np.isfinite(Tc) & (Tc <= float(args.snow_temp_c)) & (Pmm > 0.0)
    water_cm = Pmm / 10.0
    snowfall_cm = np.zeros(len(df), dtype=float)
    snowfall_cm[snow_mask] = water_cm[snow_mask] * float(args.snow_ratio)

    df["snowfall_cm"] = snowfall_cm

    out = df[["time", "temperature_C", "humidity_pct", "snowfall_cm", "precip_mm", "dewpoint_C"]].copy()

    out.to_csv(args.out_path, index=False)
    print("NOAA -> SSUM input written")
    print(f"Rows: {len(out)}")
    print(f"Saved: {args.out_path}")

if __name__ == "__main__":
    main()
