# ssum_snow.py
import os
import json
import argparse
import numpy as np
import pandas as pd

EPS = 1e-12


def _safe_float(x):
    try:
        if pd.isna(x):
            return None
        return float(x)
    except Exception:
        return None


def _make_outdir(path):
    os.makedirs(path, exist_ok=True)


def _segment_ids(t: pd.Series, gap_hours: float) -> pd.Series:
    dt_h = t.diff().dt.total_seconds().fillna(0.0) / 3600.0
    cut = (dt_h > float(gap_hours)).astype(int)
    return cut.cumsum().astype(int)


def _rolling_range(x: pd.Series, win: int) -> pd.Series:
    mp = max(6, win // 3)
    rmax = x.rolling(win, min_periods=mp).max()
    rmin = x.rolling(win, min_periods=mp).min()
    return (rmax - rmin)


def _compute_feats_by_segment(df: pd.DataFrame, win: int, win_stress: int) -> pd.DataFrame:
    def apply_one(g):
        temp = g["temperature_C"].astype(float)
        rh = g["humidity_pct"].astype(float)

        dT = _rolling_range(temp, win)
        dH = _rolling_range(rh, win)

        # Core Potential (CP)
        cp = (dT * dH) / float(max(1, win))

        # Structural stress: rolling sum of CP "jerk"
        cp_jerk = cp.diff().abs()
        mp_stress = max(6, int(win_stress) // 3)
        s_struct = cp_jerk.rolling(int(win_stress), min_periods=mp_stress).sum()

        return pd.DataFrame({"CP": cp, "S_struct": s_struct}, index=g.index)

    gb = df.groupby("segment_id", group_keys=False)
    try:
        feats = gb.apply(apply_one, include_groups=False)
    except TypeError:
        feats = gb.apply(apply_one)
    return feats


def _pack_rows(dfx):
    rows = []
    for _, r in dfx.iterrows():
        rows.append(
            {
                "time": str(r["time"]),
                "CP": _safe_float(r["CP"]),
                "SCE": _safe_float(r["SCE"]),
                "S_struct": _safe_float(r["S_struct"]),
                "admissible": bool(r["admissible"]),
                "snowfall_cm": _safe_float(r["snowfall_cm"]),
                "depth_est_cm": _safe_float(r["depth_est_cm"]),
                "corridor_score": _safe_float(r["corridor_score"]),
                "segment_id": int(r["segment_id"]),
            }
        )
    return rows


def _print_row(label, r):
    print(label)
    print(
        f"  time={r['time']} "
        f"depth_est_cm={float(r['depth_est_cm']):.3f} "
        f"corridor_score={float(r['corridor_score']):.6f} "
        f"CP={float(r['CP']):.6f} "
        f"SCE={float(r['SCE']):.6f} "
        f"S_struct={float(r['S_struct']):.6f} "
        f"admissible={bool(r['admissible'])} "
        f"snowfall_cm={float(r['snowfall_cm']):.3f} "
        f"segment_id={int(r['segment_id'])}"
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_path", required=True)
    ap.add_argument("--out_dir", required=True)

    ap.add_argument("--tct_window_hours", type=int, default=24)
    # v1.2: ACTIVE. If omitted, defaults to tct_window_hours (matches v1.1 behavior).
    ap.add_argument("--stress_window_hours", type=int, default=None)

    ap.add_argument("--cp_threshold", type=float, default=0.08)
    ap.add_argument("--s_max", type=float, default=2.5)
    ap.add_argument("--k_depth", type=float, default=13.0)
    ap.add_argument("--gap_hours", type=float, default=6.0)

    args = ap.parse_args()

    df = pd.read_csv(args.in_path)

    need = ["time", "temperature_C", "humidity_pct", "snowfall_cm"]
    missing = [c for c in need if c not in df.columns]
    if missing:
        raise SystemExit(f"Missing required columns: {missing}")

    df["time"] = pd.to_datetime(df["time"], errors="coerce")
    df = df.dropna(subset=["time"]).sort_values("time").reset_index(drop=True)

    df["segment_id"] = _segment_ids(df["time"], args.gap_hours)

    win = int(args.tct_window_hours)
    win_stress = win if args.stress_window_hours is None else int(args.stress_window_hours)
    feats = _compute_feats_by_segment(df, win, win_stress)

    df["CP"] = feats["CP"]
    df["S_struct"] = feats["S_struct"]

    # Structural Confidence Envelope
    # `SCE = exp(-S_struct)`
    df["SCE"] = np.exp(-df["S_struct"].astype(float))
    df.loc[pd.isna(df["S_struct"]), "SCE"] = np.nan

    # Admissibility corridor rule
    df["admissible"] = (
        (df["CP"] >= float(args.cp_threshold))
        & (df["S_struct"] <= float(args.s_max))
        & (~pd.isna(df["CP"]))
        & (~pd.isna(df["S_struct"]))
    )

    # Depth estimate (monotone in CP)
    # `depth_est_cm = k_depth * log(CP + 1)`
    df["depth_est_cm"] = float(args.k_depth) * np.log(df["CP"].astype(float) + 1.0)
    df.loc[pd.isna(df["CP"]), "depth_est_cm"] = 0.0
    df.loc[df["depth_est_cm"] < 0.0, "depth_est_cm"] = 0.0

    # Optional min/max band using SCE (kept for continuity)
    sce = df["SCE"].astype(float)
    df["depth_min_cm"] = df["depth_est_cm"] * np.clip(sce, 0.0, 1.0)
    df["depth_max_cm"] = df["depth_est_cm"] * (2.0 - np.clip(sce, 0.0, 1.0))

    # NEW: Corridor Score (forecastable snow window score)
    # `corridor_score = depth_est_cm * SCE`
    df["corridor_score"] = df["depth_est_cm"].astype(float) * np.clip(sce, 0.0, 1.0)
    df.loc[pd.isna(df["SCE"]), "corridor_score"] = np.nan

    _make_outdir(args.out_dir)
    series_path = os.path.join(args.out_dir, "series.csv")
    summary_path = os.path.join(args.out_dir, "summary.json")

    df.to_csv(series_path, index=False)

    stable = df.dropna(subset=["CP", "S_struct", "SCE", "corridor_score"])

    # Existing top lists
    top_cp_df = stable.sort_values("CP", ascending=False).head(12)
    top_depth_df = stable.sort_values("depth_est_cm", ascending=False).head(12)

    adm = stable[stable["admissible"]]
    top_depth_adm_df = adm.sort_values("depth_est_cm", ascending=False).head(12)

    snow_adm = adm[adm["snowfall_cm"].astype(float) > 0.0]
    top_depth_snow_adm_df = snow_adm.sort_values("depth_est_cm", ascending=False).head(12)

    # NEW top corridor score lists
    top_corr_any_df = stable.sort_values("corridor_score", ascending=False).head(12)
    top_corr_adm_df = adm.sort_values("corridor_score", ascending=False).head(12)
    top_corr_snow_adm_df = snow_adm.sort_values("corridor_score", ascending=False).head(12)

    # Observed snow events sample (for quick inspection)
    obs_df = stable[stable["snowfall_cm"].astype(float) > 0.0].head(200)

    summary = {
        "rows": int(len(df)),
        "start": str(df["time"].iloc[0]) if len(df) else None,
        "end": str(df["time"].iloc[-1]) if len(df) else None,
        "segments": int(df["segment_id"].nunique()),
        "params": {
            "tct_window_hours": int(args.tct_window_hours),
            "stress_window_hours": int(win_stress),
            "cp_threshold": float(args.cp_threshold),
            "s_max": float(args.s_max),
            "k_depth": float(args.k_depth),
            "gap_hours": float(args.gap_hours),
        },
        "top_CP": _pack_rows(top_cp_df),
        "top_depth_any": _pack_rows(top_depth_df),
        "top_depth_admissible": _pack_rows(top_depth_adm_df),
        "top_depth_admissible_snow": _pack_rows(top_depth_snow_adm_df),
        "top_corridor_any": _pack_rows(top_corr_any_df),
        "top_corridor_admissible": _pack_rows(top_corr_adm_df),
        "top_corridor_admissible_snow": _pack_rows(top_corr_snow_adm_df),
        "observed_snow_events_first200": _pack_rows(obs_df),
    }

    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("SSUM-Snow run complete")
    print(f"Rows: {len(df)}")
    print(f"Segments: {df['segment_id'].nunique()}")
    print(f"Time: {df['time'].iloc[0]} -> {df['time'].iloc[-1]}")
    print(f"Saved: {series_path}")
    print(f"Saved: {summary_path}")

    if len(top_depth_df) > 0:
        _print_row("Top depth point (overall, may be inadmissible):", top_depth_df.iloc[0])
    else:
        print("Top depth point: none")

    if len(top_depth_adm_df) > 0:
        _print_row("Top depth point (admissible corridor):", top_depth_adm_df.iloc[0])
    else:
        print("Top depth point (admissible corridor): none")

    if len(top_depth_snow_adm_df) > 0:
        _print_row("Top depth point (admissible + snowfall > 0):", top_depth_snow_adm_df.iloc[0])
    else:
        print("Top depth point (admissible + snowfall > 0): none")

    if len(top_corr_any_df) > 0:
        _print_row("Top corridor_score (overall):", top_corr_any_df.iloc[0])
    else:
        print("Top corridor_score (overall): none")

    if len(top_corr_adm_df) > 0:
        _print_row("Top corridor_score (admissible corridor):", top_corr_adm_df.iloc[0])
    else:
        print("Top corridor_score (admissible corridor): none")

    if len(top_corr_snow_adm_df) > 0:
        _print_row("Top corridor_score (admissible + snowfall > 0):", top_corr_snow_adm_df.iloc[0])
    else:
        print("Top corridor_score (admissible + snowfall > 0): none")


if __name__ == "__main__":
    main()