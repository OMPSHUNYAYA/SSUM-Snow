import os
import json
import argparse
import numpy as np
import pandas as pd

EPS = 1e-12


def _make_outdir(p):
    os.makedirs(p, exist_ok=True)


def _fit_alpha(score_train, obs_train):
    s = np.asarray(score_train, dtype=float)
    y = np.asarray(obs_train, dtype=float)
    m = np.isfinite(s) & np.isfinite(y)
    s = s[m]
    y = y[m]
    if len(s) < 10:
        return None
    denom = float(np.dot(s, s))
    if denom < EPS:
        return None
    alpha = float(np.dot(s, y) / denom)
    return alpha


def _metrics(y_true, y_pred):
    yt = np.asarray(y_true, dtype=float)
    yp = np.asarray(y_pred, dtype=float)
    m = np.isfinite(yt) & np.isfinite(yp)
    yt = yt[m]
    yp = yp[m]
    if len(yt) < 10:
        return {"n": int(len(yt)), "mae": None, "rmse": None, "corr": None}
    err = yp - yt
    mae = float(np.mean(np.abs(err)))
    rmse = float(np.sqrt(np.mean(err * err)))
    if float(np.std(yt)) < EPS or float(np.std(yp)) < EPS:
        corr = None
    else:
        corr = float(np.corrcoef(yt, yp)[0, 1])
    return {"n": int(len(yt)), "mae": mae, "rmse": rmse, "corr": corr}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_path", required=True)
    ap.add_argument("--out_dir", required=True)

    ap.add_argument("--time_col", default="time")
    ap.add_argument("--segment_col", default="segment_id")

    ap.add_argument("--score_col", default="corridor_score")
    ap.add_argument("--snow_col", default="snowfall_cm")

    ap.add_argument("--horizon_hours", type=int, default=24)
    ap.add_argument("--train_frac", type=float, default=0.7)

    ap.add_argument("--rho_scale", type=float, default=1.0)

    ap.add_argument("--min_valid_points", type=int, default=48)

    args = ap.parse_args()

    df = pd.read_csv(args.in_path)

    need = [args.time_col, args.score_col, args.snow_col]
    missing = [c for c in need if c not in df.columns]
    if missing:
        raise SystemExit(f"Missing required columns: {missing}")

    if args.segment_col not in df.columns:
        df[args.segment_col] = 0

    df[args.time_col] = pd.to_datetime(df[args.time_col], errors="coerce")
    df = df.dropna(subset=[args.time_col]).sort_values(args.time_col).reset_index(drop=True)

    H = int(args.horizon_hours)

    df[args.score_col] = pd.to_numeric(df[args.score_col], errors="coerce")
    df[args.snow_col] = pd.to_numeric(df[args.snow_col], errors="coerce").fillna(0.0)

    out_rows = []
    per_seg = {}

    # segment-level rolling sums + alpha fits
    for seg_id, g in df.groupby(args.segment_col, sort=False):
        gg = g.copy()

        s = gg[args.score_col].astype(float)
        y = gg[args.snow_col].astype(float)

        score_H = s.rolling(H, min_periods=H).sum().shift(-(H - 1))
        obs_H = y.rolling(H, min_periods=H).sum().shift(-(H - 1))

        gg["score_H"] = score_H
        gg["obs_snow_H"] = obs_H

        good = gg.dropna(subset=["score_H", "obs_snow_H"])
        if len(good) < int(args.min_valid_points):
            gg["pred_snow_H_seg"] = np.nan
            gg["pred_depth_H_seg"] = np.nan
            per_seg[int(seg_id)] = {
                "segment_id": int(seg_id),
                "alpha_seg": None,
                "train_metrics_seg": {"n": 0, "mae": None, "rmse": None, "corr": None},
                "test_metrics_seg": {"n": 0, "mae": None, "rmse": None, "corr": None},
                "note": "insufficient_valid_points",
            }
            out_rows.append(gg)
            continue

        n = len(good)
        n_train = max(10, int(round(float(args.train_frac) * n)))
        train = good.iloc[:n_train]
        test = good.iloc[n_train:]

        alpha_seg = _fit_alpha(train["score_H"].values, train["obs_snow_H"].values)

        if alpha_seg is None:
            gg["pred_snow_H_seg"] = np.nan
            gg["pred_depth_H_seg"] = np.nan
            per_seg[int(seg_id)] = {
                "segment_id": int(seg_id),
                "alpha_seg": None,
                "train_metrics_seg": {"n": int(len(train)), "mae": None, "rmse": None, "corr": None},
                "test_metrics_seg": {"n": int(len(test)), "mae": None, "rmse": None, "corr": None},
                "note": "alpha_fit_failed",
            }
            out_rows.append(gg)
            continue

        gg["pred_snow_H_seg"] = alpha_seg * gg["score_H"].astype(float)
        gg.loc[pd.isna(gg["score_H"]), "pred_snow_H_seg"] = np.nan

        rho = float(args.rho_scale)
        gg["pred_depth_H_seg"] = rho * gg["pred_snow_H_seg"].astype(float)

        tr_pred = alpha_seg * train["score_H"].astype(float)
        te_pred = alpha_seg * test["score_H"].astype(float)

        tr_m = _metrics(train["obs_snow_H"].values, tr_pred.values)
        te_m = _metrics(test["obs_snow_H"].values, te_pred.values)

        per_seg[int(seg_id)] = {
            "segment_id": int(seg_id),
            "alpha_seg": float(alpha_seg),
            "rho_scale": float(rho),
            "train_metrics_seg": tr_m,
            "test_metrics_seg": te_m,
            "note": "ok",
        }

        out_rows.append(gg)

    out = pd.concat(out_rows, axis=0).sort_values(args.time_col).reset_index(drop=True)

    # compute global alpha as median of segment alphas that fit successfully
    ok_alphas = [v["alpha_seg"] for v in per_seg.values() if v.get("alpha_seg") is not None]
    alpha_global = None
    if len(ok_alphas) > 0:
        alpha_global = float(np.median(np.asarray(ok_alphas, dtype=float)))

    # add global predictions for all rows
    out["pred_snow_H_global"] = np.nan
    out["pred_depth_H_global"] = np.nan
    if alpha_global is not None:
        out["pred_snow_H_global"] = alpha_global * out["score_H"].astype(float)
        out.loc[pd.isna(out["score_H"]), "pred_snow_H_global"] = np.nan
        out["pred_depth_H_global"] = float(args.rho_scale) * out["pred_snow_H_global"].astype(float)

    # global metrics across all segments for rows where we have valid obs + score
    valid_global = out.dropna(subset=["score_H", "obs_snow_H"])
    global_metrics = {"n": 0, "mae": None, "rmse": None, "corr": None}
    if alpha_global is not None and len(valid_global) >= 10:
        y_true = valid_global["obs_snow_H"].values
        y_pred = alpha_global * valid_global["score_H"].astype(float).values
        global_metrics = _metrics(y_true, y_pred)

    _make_outdir(args.out_dir)
    pred_path = os.path.join(args.out_dir, "predictions.csv")
    report_path = os.path.join(args.out_dir, "calibration_report.json")

    out.to_csv(pred_path, index=False)

    report = {
        "input_rows": int(len(df)),
        "start": str(out[args.time_col].iloc[0]) if len(out) else None,
        "end": str(out[args.time_col].iloc[-1]) if len(out) else None,
        "horizon_hours": int(H),
        "train_frac": float(args.train_frac),
        "rho_scale": float(args.rho_scale),
        "global_alpha_median": alpha_global,
        "global_metrics": global_metrics,
        "per_segment": list(per_seg.values()),
        "formulas": {
            "score_H(t)": "sum_{h=t..t+H-1} corridor_score(h)",
            "obs_snow_H(t)": "sum_{h=t..t+H-1} snowfall_cm(h)",
            "alpha_seg": "a = (score^T obs) / (score^T score) fitted inside each segment on train split",
            "alpha_global": "median(alpha_seg over segments where alpha_seg exists)",
            "pred_snow_H_seg(t)": "alpha_seg * score_H(t)",
            "pred_snow_H_global(t)": "alpha_global * score_H(t)",
            "pred_depth_H_*": "rho_scale * pred_snow_H_*",
        },
    }

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("SSUM-Snow calibration complete")
    print(f"Saved: {pred_path}")
    print(f"Saved: {report_path}")

    if alpha_global is not None:
        print(f"Global alpha (median across segments): {alpha_global:.6f}")
        print(f"Global metrics (all segments): n={global_metrics['n']} corr={global_metrics['corr']} rmse={global_metrics['rmse']}")

    ok_segs = [v for v in per_seg.values() if v.get("note") == "ok"]
    if len(ok_segs) > 0:
        best = sorted(
            ok_segs,
            key=lambda d: (-1 if d["test_metrics_seg"]["corr"] is None else d["test_metrics_seg"]["corr"]),
            reverse=True,
        )[0]
        print("Example segment result:")
        print(
            f"  segment_id={best['segment_id']} alpha_seg={best['alpha_seg']:.6f} "
            f"test_corr={best['test_metrics_seg']['corr']} test_rmse={best['test_metrics_seg']['rmse']}"
        )


if __name__ == "__main__":
    main()
