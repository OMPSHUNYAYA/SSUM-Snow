#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fail(msg):
    raise SystemExit("PACKAGE_VERIFICATION_FAIL: " + msg)


def read_json(rel):
    p = ROOT / rel
    if not p.exists():
        fail("missing file: " + rel)
    return json.loads(p.read_text(encoding="utf-8"))


def verify_checksums():
    manifest = ROOT / "SHA256SUMS.txt"
    if not manifest.exists():
        fail("SHA256SUMS.txt missing")
    checked = 0
    allowed = ("evidence/", "reference/", "verification/SSUM_Snow_Fusion_F1_Reproduction_")
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            h, rel = line.split("  ", 1)
        except ValueError:
            fail("malformed checksum line")
        if not rel.startswith(allowed):
            fail("checksum scope contains non-scientific path: " + rel)
        p = ROOT / rel
        if not p.exists():
            fail("missing checksummed file: " + rel)
        got = hashlib.sha256(p.read_bytes()).hexdigest()
        if got != h:
            fail("checksum mismatch: " + rel)
        checked += 1
    if checked < 9:
        fail("scientific checksum scope is unexpectedly small")
    return checked


def main():
    checks = 0
    standalone = read_json("evidence/SSUM_Snow_2025_Standalone_Result.json")
    fusion = read_json("evidence/SSUM_Snow_2025_Fusion_Analysis.json")
    weights = read_json("evidence/SSUM_Snow_2025_Weight_Robustness.json")
    result = read_json("evidence/SSUM_Snow_2026_Replication_Result.json")
    receipts = read_json("evidence/SSUM_Snow_Execution_Receipts.json")
    parity = read_json("evidence/SSUM_Snow_Source_Parity_Result.json")
    spec = read_json("reference/SSUM_Snow_Fusion_F1_Specification.json")

    if standalone["common_cases"] != 1192 or standalone["events"] != 392:
        fail("2025 standalone capacity")
    checks += 1
    if not standalone["spf1"]["roc_auc"] < standalone["nbm_joint"]["roc_auc"]:
        fail("2025 standalone ordering")
    checks += 1
    if fusion["out_of_fold"]["n"] != 944 or fusion["out_of_fold"]["positive_stations"] != 8:
        fail("2025 fusion chronology evidence")
    checks += 1
    if weights["selected_spf1_weight"] != 0.25 or weights["selected_nbm_joint_weight"] != 0.75:
        fail("fixed weights")
    checks += 1
    if weights["contiguous_passing_spf1_weights"] != [0.1, 0.15, 0.2, 0.25, 0.3]:
        fail("weight robustness region")
    checks += 1
    if spec["weights"] != {"nbm_joint": 0.75, "spf1": 0.25}:
        fail("specification weights")
    checks += 1
    if spec["rank_transform"]["reference_common_predictor_cases"] != 1192:
        fail("rank reference size")
    checks += 1
    sem = spec.get("source_semantics", {})
    if sem.get("r3_2025_spf1", {}).get("historical_feature_conversion") != "raw integer / 10 for TMAX, TMIN, PRCP and SNOW":
        fail("2025 SPF1 source convention")
    checks += 1
    if sem.get("r3_2025_nbm", {}).get("required_fields_for_case_admission") != ["S06", "P06", "PSN"]:
        fail("2025 NBM admission semantics")
    checks += 1
    if sem.get("r4_2026_nbm", {}).get("parser") != "fixed-width NBS joint-only P06/PSN":
        fail("2026 NBM parser semantics")
    checks += 1
    if sem.get("r4_2026_spf1", {}).get("request_window") != "D-2 through D-1":
        fail("2026 prequential request geometry")
    checks += 1

    prov = spec["spf1"].get("provenance", {})
    if prov.get("development_period") != "2010-2020" or prov.get("independent_confirmation_period") != "2021-2022" or prov.get("second_replication_year") != 2024:
        fail("SPF1 provenance")
    if prov.get("2025_used_to_fit_spf1_coefficients") or prov.get("2026_used_to_fit_spf1_coefficients"):
        fail("SPF1 chronology")
    checks += 1

    if result["n"] != 720 or result["events"] != 238 or result["non_events"] != 482:
        fail("2026 capacity")
    checks += 1
    if abs(result["delta"]["roc_auc"] - 0.015520938666) > 1e-12:
        fail("2026 ROC AUC delta")
    checks += 1
    if abs(result["delta"]["pr_auc"] - 0.037914636259) > 1e-12:
        fail("2026 PR-AUC delta")
    checks += 1
    if result["positive_stations"] != 6:
        fail("2026 station direction count")
    checks += 1
    if result["temporal_block_bootstrap_20000_95"][0] <= 0 or result["station_cluster_bootstrap_20000_95"][0] <= 0:
        fail("2026 bootstrap lower bound")
    checks += 1
    if not result["all_predeclared_gates_pass"]:
        fail("2026 predeclared gates")
    checks += 1

    if receipts["receipts"]["2025_spf1_prediction"] != "786d452760ae75368cd47aba3f5f9023c59e837710b33a6d73d400ba04e410b4":
        fail("2025 SPF1 historical identity")
    if receipts["receipts"]["2025_nbm_prediction"] != "5d8429ef81a8e42512380050a09edf6941fdb2218d787ea26a793dbe452adc05":
        fail("2025 NBM historical identity")
    if receipts["receipts"]["2026_final_score"] != "9cf14b6c373100dc054b94a257f725342e4426620c035653813eaa12f9fc74e2":
        fail("2026 final historical identity")
    checks += 1

    if parity.get("overall") != "PASS" or parity.get("frozen_receipt_identities") != "PASS":
        fail("source parity status")
    checks += 1
    if parity["r3_2025"]["spf1"]["mismatches"] != 0 or parity["r3_2025"]["nbm"]["mismatches"] != 0 or parity["r3_2025"]["truth"]["mismatches"] != 0:
        fail("2025 source parity")
    checks += 1
    if parity["r4_2026"]["nbm"]["mismatches"] != 0 or parity["r4_2026"]["truth"]["mismatches"] != 0 or parity["r4_2026"]["prequential_spf1"]["mismatches"] != 0:
        fail("2026 source parity")
    checks += 1
    if parity["r3_2025"]["common_predictor_count"] != 1192 or parity["r3_2025"]["nbm"]["source_missing_exclusions"] != 8:
        fail("2025 parity capacity")
    checks += 1

    n = verify_checksums()
    checks += 1
    print("SSUM-Snow Fusion-F1 package verification")
    print(f"evidence_checks:{checks}/{checks} PASS")
    print("checksum_files_verified:" + str(n))
    print("PACKAGE_VERIFICATION_PASS")


if __name__ == "__main__":
    main()
