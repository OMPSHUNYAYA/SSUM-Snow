#!/usr/bin/env python3
import argparse
import json
import math
from bisect import bisect_left, bisect_right
from pathlib import Path

FEATURES = [
    "tmean","trange","prcp","snow","snow_lag1","month_sin","month_cos",
    "up_tmean","up_prcp","up_snow_sum","up_snow_any","temp_gradient",
    "cold_up_snow","cold_up_prcp"
]
MEAN = [-1.3655904267328967,8.668337472717695,1.9373748777000077,1.0693384511176338,1.0701663279897644,0.37029225019976875,0.6471835790691776,-1.2459020094829532,1.862150974636863,2.112907353051855,0.35982539324151425,0.11968841724994358,2.4565025965229172,5.109482012493415]
SCALE = [7.35291882784391,4.101484949308128,4.8460674424979855,3.3221302118748395,3.3267289197299026,0.5561282423789786,0.36709459605620676,7.303488868934149,4.238175265332385,5.6747702786750365,0.4799490385656625,2.4185436081077936,4.656087066755887,16.57895097112088]
COEF = [-0.25371601338679917,-0.1318924512720109,0.04187160605137054,0.14057361052281406,-0.02468235788670808,0.3843273548231735,0.3704161203528799,-0.22580438013076123,0.132542646131337,0.024425096716501282,0.5946087986045814,0.08947263724759182,-0.2097064989561956,0.022118870839349977]
INTERCEPT = -1.1555249871811413
W_NBM = 0.75
W_SPF1 = 0.25

def logistic(z):
    if z >= 0:
        e = math.exp(-z)
        return 1.0 / (1.0 + e)
    e = math.exp(z)
    return e / (1.0 + e)

def spf1_score(features):
    z = INTERCEPT
    for k, mu, sc, c in zip(FEATURES, MEAN, SCALE, COEF):
        z += ((float(features[k]) - mu) / sc) * c
    return logistic(z)

def empirical_cdf(reference, x):
    ref = sorted(float(v) for v in reference)
    n = len(ref)
    if n == 0:
        raise ValueError("empty reference")
    left = bisect_left(ref, float(x))
    right = bisect_right(ref, float(x))
    return (left + 0.5 * (right - left)) / n

def fusion_f1(nbm_joint, spf1, nbm_reference, spf1_reference):
    r_nbm = empirical_cdf(nbm_reference, nbm_joint)
    r_spf1 = empirical_cdf(spf1_reference, spf1)
    return W_NBM * r_nbm + W_SPF1 * r_spf1

def self_test():
    f = {k: MEAN[i] for i,k in enumerate(FEATURES)}
    assert abs(spf1_score(f) - logistic(INTERCEPT)) < 1e-15
    ref = [0.0,1.0,1.0,3.0]
    assert abs(empirical_cdf(ref,1.0) - 0.5) < 1e-15
    assert abs(fusion_f1(1.0,1.0,ref,ref) - 0.5) < 1e-15
    print("SSUM-Snow Fusion-F1 reference implementation self-test")
    print("checks:3/3 PASS")
    print("formula:F1=0.75*R_NBM+0.25*R_SPF1")
    print("dependencies:PYTHON_STANDARD_LIBRARY_ONLY")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        self_test()
    else:
        ap.error("use --self-test; full source reproduction is provided in verification/")

if __name__ == "__main__":
    main()
