# SSUM-Snow Fusion-F1

## Fixed structural augmentation of archived operational NBM snow guidance

SSUM-Snow Fusion-F1 is a deterministic snow-event discrimination method that combines an archived NOAA National Blend of Models (NBM) joint snow score with the frozen SSUM-Snow SPF1 structural score.

The fixed formula is:

```text
F1 = 0.75 * R_NBM + 0.25 * R_SPF1
```

`R_NBM` and `R_SPF1` are midrank empirical-CDF transforms against the 1,192 common predictor pairs in the frozen 2025 reference period.

## Scientific result

The project produced two distinct findings.

1. SPF1 did not outperform the declared archived NBM comparator as a standalone predictor on the 2025 benchmark.
2. SPF1 nevertheless contained complementary ranking information. A fixed 75/25 fusion subsequently passed every predeclared gate on the January-March 2026 eight-station historical prequential benchmark.

Reserved-period result:

```text
Period: 2026-01-01 through 2026-03-31
Stations: 8
Cases: 720
Events: 238
Non-events: 482

NBM joint ROC AUC: 0.911647023955
Fusion-F1 ROC AUC: 0.927167962621
Delta ROC AUC: +0.015520938666

NBM joint PR-AUC: 0.837182439410
Fusion-F1 PR-AUC: 0.875097075669
Delta PR-AUC: +0.037914636259

Positive stations: 6/8
Temporal-block bootstrap 95%: [+0.002057587939, +0.025197946170]
Station-cluster bootstrap 95%: [+0.006764452593, +0.024041287735]
```

All seven predeclared gates passed.

## SPF1 provenance

SPF1 development used 2010-2020 data, followed by independent-period confirmation in 2021-2022 and a second replication period in 2024. The SPF1 coefficient vector and feature definition were frozen before the 2025 NBM comparison. Neither the 2025 fusion analysis nor the 2026 evaluation fitted SPF1 coefficients.

## Historical source semantics

The source reproducer preserves the actual semantics used by the frozen experiments.

- 2025 SPF1 predictor reconstruction uses the historical raw GHCN feature convention from the frozen R3 implementation: TMAX, TMIN, PRCP and SNOW raw integers are divided by 10 before feature construction. This is a model-input convention and is distinct from the source archive's element-specific native units.
- 2025 truth uses the raw GHCN-Daily SNOW integer only for the event test `SNOW > 0`, with `-9999` and nonblank QFLAG excluded.
- 2025 NBM common-case admission requires complete S06, P06 and PSN values on all required local-day six-hour endpoints. NOAA `-99` is missing, never zero. This produces 1,200 NBM rows and eight source-missing exclusions; intersecting with 1,200 SPF1 rows produces the frozen 1,192-case reference.
- 2026 NBM uses the frozen R4 joint-only parser based on P06 and PSN.
- 2026 SPF1 reconstruction uses the same date-bounded NCEI Daily Summaries request geometry as the frozen prequential R4 pipeline: for target day D, the observation request covers D-2 through D-1 only.

## Interpretation boundary

The supported result is a modest reserved-period improvement in snow-event discrimination over the declared archived NBM joint comparator. Fusion-F1 uses NBM input. It is not a standalone weather-forecasting system and its score is not asserted to be a calibrated probability.

The result does not establish universal improvement across winters, stations, NBM versions, thresholds, numerical weather prediction systems, or operational decision settings.

## Package layout

```text
README.md
LICENSE
THIRD_PARTY_DATA_NOTICE.md
SCIENTIFIC_STATUS.txt
CLAIM_BOUNDARIES.txt
LIMITATIONS.txt
REPRODUCIBILITY_SCOPE.txt
METHODOLOGY.txt
SOURCE_MANIFEST.txt
EVIDENCE_CHAIN.txt
SHA256SUMS.txt
VERSION.txt

evidence/
reference/
verification/
```

## Verification

No third-party Python packages are required.

```text
python -B verification/SSUM_Snow_Fusion_F1_Package_Verifier_v1_0_1.py
python -B reference/SSUM_Snow_Fusion_F1_Reference_Implementation_v1_0_0.py --self-test
python -B verification/SSUM_Snow_Fusion_F1_Reproduction_v1_0_1.py --self-test
```

Full source reconstruction:

```text
python -B verification/SSUM_Snow_Fusion_F1_Reproduction_v1_0_1.py --run
```

The full command acquires the declared NOAA/NCEI sources when the local `source_cache/` is empty. No earlier SSUM-Snow directory is required. Raw source payloads are not included in this package.
