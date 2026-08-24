# ❄️ SSUM-Snow

## Structural Snow Modeling — Reserved Historical Replication with Fusion-F1

![SSUM-Snow](https://img.shields.io/badge/Structural%20Snow%20Modeling-SSUM--Snow-black)
![Package](https://img.shields.io/badge/Fusion--F1-v1.0.1-blue)
![Reserved Test](https://img.shields.io/badge/2026%20Reserved%20Test-PASS-green)
![Source Parity](https://img.shields.io/badge/Source%20Parity-PASS-green)
![Verification](https://img.shields.io/badge/Package%20Verification-24%2F24%20PASS-green)
![Dependencies](https://img.shields.io/badge/Python-Standard%20Library%20Only-purple)
![2025 Standalone](https://img.shields.io/badge/2025%20Standalone-SPF1%20Did%20Not%20Beat%20NBM-orange)
![Replication](https://img.shields.io/badge/Outside%20Replication-OPEN-orange)
![Shunyaya](https://img.shields.io/badge/Part%20of-Shunyaya%20Framework-gold)

[![SSUM-Snow Verification](https://github.com/OMPSHUNYAYA/SSUM-Snow/actions/workflows/verification.yml/badge.svg)](https://github.com/OMPSHUNYAYA/SSUM-Snow/actions/workflows/verification.yml)

---

## Scientific status at a glance

**SSUM-Snow Fusion-F1 showed a modest but consistently positive reserved-period improvement in snow-event discrimination over the declared archived NBM comparator.**

The frozen Fusion-F1 rule is:

```text
F1 = 0.75 * R_NBM + 0.25 * R_SPF1
```

where:

- `R_NBM` is the midrank empirical-CDF rank of the declared NBM joint snow-event score;
- `R_SPF1` is the corresponding rank of the frozen SSUM-Snow SPF1 structural predictor;
- the ranking reference is the frozen 2025 common-case population;
- no station-specific or month-specific adaptive weight is used.

The principal reserved evaluation used **January-March 2026**, covering:

```text
720 station-date cases
238 snow events
482 non-events
8 U.S. stations
```

### Reserved 2026 result

| Metric | Archived NBM comparator | Fusion-F1 | Difference |
|---|---:|---:|---:|
| ROC AUC | `0.911647023955` | `0.927167962621` | `+0.015520938666` |
| PR AUC | `0.837182439410` | `0.875097075669` | `+0.037914636259` |

Additional frozen checks:

```text
stations with positive ROC-AUC delta = 6 / 8

temporal bootstrap 95% interval
[+0.002057587939, +0.025197946170]

station bootstrap 95% interval
[+0.006764452593, +0.024041287735]
```

The station bootstrap contains only eight stations and should therefore be interpreted cautiously.

---

## Important scientific boundary

**Fusion-F1 is not a standalone replacement for numerical weather prediction.**

It explicitly uses an archived NBM predictor as one of its inputs.

The demonstrated result is therefore:

```text
frozen NBM information
        +
frozen SSUM-Snow SPF1 structural information
        |
        v
Fusion-F1
        |
        v
modest reserved-period discrimination improvement
over the declared archived NBM comparator
```

The current evidence does **not** establish:

- universal superiority over NBM;
- superiority over modern weather forecasting generally;
- snow-depth superiority;
- calibrated probability superiority;
- operational utility superiority;
- performance outside the tested stations, periods and event definition;
- independent outside-party replication.

See:

- [Scientific status](./SSUM_Snow_Fusion_F1_v1_0_1/SCIENTIFIC_STATUS.txt)
- [Claim boundaries](./SSUM_Snow_Fusion_F1_v1_0_1/CLAIM_BOUNDARIES.txt)
- [Limitations](./SSUM_Snow_Fusion_F1_v1_0_1/LIMITATIONS.txt)

---

## The 2025 standalone result is retained

Before Fusion-F1 was evaluated, the frozen SSUM-Snow SPF1 predictor was tested **standalone** against the declared archived NBM comparator over the 2025 test period.

That standalone test did **not** beat NBM.

Frozen 2025 common-case result:

| Predictor | ROC AUC | PR AUC |
|---|---:|---:|
| SPF1 | `0.760264668367347` | `0.5713264383974201` |
| NBM S06 | `0.8118096301020408` | `0.7352367642928685` |
| NBM joint | `0.910983737244898` | `0.8549787219684549` |

SPF1 ROC-AUC difference versus the NBM joint comparator:

```text
-0.15071906887755104
```

Positive station count:

```text
0 / 8
```

This negative result remains part of the evidence chain.

Fusion-F1 was subsequently formed as a simple frozen rank blend and evaluated under a separate reserved historical test.

See:

- [2025 standalone result](./SSUM_Snow_Fusion_F1_v1_0_1/evidence/SSUM_Snow_2025_Standalone_Result.json)
- [2025 Fusion analysis](./SSUM_Snow_Fusion_F1_v1_0_1/evidence/SSUM_Snow_2025_Fusion_Analysis.json)
- [Weight robustness evidence](./SSUM_Snow_Fusion_F1_v1_0_1/evidence/SSUM_Snow_2025_Weight_Robustness.json)

---

## Scientific chain

```text
SSUM-Snow structural development
2010-2020
        |
        v
independent confirmation
2021-2022
        |
        v
second replication
2024
        |
        v
SPF1 frozen before 2025
        |
        v
2025 standalone test
SPF1 < archived NBM comparator
        |
        v
simple frozen rank-fusion investigation
        |
        v
Fusion-F1
75% NBM rank + 25% SPF1 rank
        |
        v
2026 JFM reserved historical replication
        |
        v
positive discrimination delta
```

The 2025 and 2026 target periods were not used to fit the frozen SPF1 coefficients.

---

## Future-of-the-past validation

The principal evaluation is retrospective but chronologically constrained.

For each historical target date, the predictor is reconstructed only from information that would have been available before the target truth was revealed.

For the 2026 reserved period:

```text
target date D

observation information available through D-1
        +
archived NBM 01 UTC forecast information
        |
        v
frozen SPF1 and NBM predictor construction
        |
        v
Fusion-F1 prediction
        |
        v
only afterward:
target-date GHCN snow truth
```

The 2026 SPF1 reconstruction uses only the declared `D-2` through `D-1` pre-target observation window.

The target-date truth is excluded from predictor construction.

---

## Source-parity result

The package includes a completed source-parity audit against the frozen historical prediction and truth receipts.

```text
2025 SPF1
actual count:     1200
frozen count:     1200
mismatches:       0
parity:           PASS

2025 NBM
actual count:     1200
frozen count:     1200
mismatches:       0
intended exclusions: 8
common predictors:   1192
parity:           PASS

2025 truth
actual count:     1208
frozen count:     1208
mismatches:       0
parity:           PASS

2026 NBM
actual count:     720
frozen count:     720
mismatches:       0
parity:           PASS

2026 truth
actual count:     720
frozen count:     720
mismatches:       0
parity:           PASS

2026 prequential SPF1
actual count:     720
frozen count:     720
mismatches:       0
parity:           PASS

overall source parity: PASS
```

See:

[SSUM_Snow_Source_Parity_Result.json](./SSUM_Snow_Fusion_F1_v1_0_1/evidence/SSUM_Snow_Source_Parity_Result.json)

---

## Why the 2025 and 2026 NBM routes differ

The frozen historical experiments used two deliberately different NBM admission rules.

### 2025 R3

The 2025 common-case population requires complete:

```text
S06 + P06 + PSN
```

NOAA `-99` values are treated as missing and are never converted to zero.

Eight NBM station-date cases are excluded, all on `2025-02-04`.

This produces:

```text
1200 SPF1 predictions
1200 admitted NBM predictions
1192 common predictor pairs
1208 admissible truth cases
```

### 2026 R4

The reserved 2026 experiment uses the frozen R4 **joint-only** comparator route:

```text
P06 + PSN
```

and admits all:

```text
720 / 720
```

reserved station-date cases.

These historical rules are preserved rather than retrospectively standardized.

---

## Historical SPF1 source convention

Exact reproduction preserves the model-input convention used by the frozen historical SPF1 implementation.

For the 2025 predictor reconstruction, the original GHCN `.dly` reader applies:

```text
raw integer / 10
```

to:

```text
TMAX
TMIN
PRCP
SNOW
```

before those values enter the SPF1 feature calculations.

This is a **historical model-input convention**. It is not a statement that the native GHCN `SNOW` field is physically expressed in the same units as the other variables.

Binary snow-event truth remains:

```text
admissible GHCN SNOW raw value > 0
```

The package preserves the frozen predictor semantics rather than silently changing them after evaluation.

---

## Quick links

### Main Fusion-F1 package

- [SSUM_Snow_Fusion_F1_v1_0_1](./SSUM_Snow_Fusion_F1_v1_0_1/)
- [Package README](./SSUM_Snow_Fusion_F1_v1_0_1/README.md)
- [Methodology](./SSUM_Snow_Fusion_F1_v1_0_1/METHODOLOGY.txt)
- [Scientific status](./SSUM_Snow_Fusion_F1_v1_0_1/SCIENTIFIC_STATUS.txt)
- [Evidence chain](./SSUM_Snow_Fusion_F1_v1_0_1/EVIDENCE_CHAIN.txt)
- [Claim boundaries](./SSUM_Snow_Fusion_F1_v1_0_1/CLAIM_BOUNDARIES.txt)
- [Limitations](./SSUM_Snow_Fusion_F1_v1_0_1/LIMITATIONS.txt)
- [Reproducibility scope](./SSUM_Snow_Fusion_F1_v1_0_1/REPRODUCIBILITY_SCOPE.txt)
- [Source manifest](./SSUM_Snow_Fusion_F1_v1_0_1/SOURCE_MANIFEST.txt)
- [Third-party data notice](./SSUM_Snow_Fusion_F1_v1_0_1/THIRD_PARTY_DATA_NOTICE.md)

### Frozen specification and implementation

- [Fusion-F1 specification](./SSUM_Snow_Fusion_F1_v1_0_1/reference/SSUM_Snow_Fusion_F1_Specification.json)
- [Reference implementation](./SSUM_Snow_Fusion_F1_v1_0_1/reference/SSUM_Snow_Fusion_F1_Reference_Implementation_v1_0_0.py)

### Verification

- [Package verifier](./SSUM_Snow_Fusion_F1_v1_0_1/verification/SSUM_Snow_Fusion_F1_Package_Verifier_v1_0_1.py)
- [Source reproducer](./SSUM_Snow_Fusion_F1_v1_0_1/verification/SSUM_Snow_Fusion_F1_Reproduction_v1_0_1.py)
- [Verification instructions](./SSUM_Snow_Fusion_F1_v1_0_1/verification/VERIFY.txt)
- [Scientific SHA-256 manifest](./SSUM_Snow_Fusion_F1_v1_0_1/SHA256SUMS.txt)

### Evidence

- [2025 standalone result](./SSUM_Snow_Fusion_F1_v1_0_1/evidence/SSUM_Snow_2025_Standalone_Result.json)
- [2025 Fusion analysis](./SSUM_Snow_Fusion_F1_v1_0_1/evidence/SSUM_Snow_2025_Fusion_Analysis.json)
- [2025 weight robustness](./SSUM_Snow_Fusion_F1_v1_0_1/evidence/SSUM_Snow_2025_Weight_Robustness.json)
- [2026 reserved replication result](./SSUM_Snow_Fusion_F1_v1_0_1/evidence/SSUM_Snow_2026_Replication_Result.json)
- [Execution receipts](./SSUM_Snow_Fusion_F1_v1_0_1/evidence/SSUM_Snow_Execution_Receipts.json)
- [Source-parity result](./SSUM_Snow_Fusion_F1_v1_0_1/evidence/SSUM_Snow_Source_Parity_Result.json)

---

## Package verification

Requirements:

```text
Python 3.9 or later
Python standard library only
```

From the repository root:

```text
python -B SSUM_Snow_Fusion_F1_v1_0_1/verification/SSUM_Snow_Fusion_F1_Package_Verifier_v1_0_1.py
```

Expected result:

```text
SSUM-Snow Fusion-F1 package verification
evidence_checks:24/24 PASS
checksum_files_verified:9
PACKAGE_VERIFICATION_PASS
```

---

## Reference implementation self-test

```text
python -B SSUM_Snow_Fusion_F1_v1_0_1/reference/SSUM_Snow_Fusion_F1_Reference_Implementation_v1_0_0.py --self-test
```

Expected:

```text
SSUM-Snow Fusion-F1 reference implementation self-test
checks:3/3 PASS
formula:F1=0.75*R_NBM+0.25*R_SPF1
dependencies:PYTHON_STANDARD_LIBRARY_ONLY
```

---

## Source reproducer self-test

```text
python -B SSUM_Snow_Fusion_F1_v1_0_1/verification/SSUM_Snow_Fusion_F1_Reproduction_v1_0_1.py --self-test
```

Expected:

```text
SSUM-Snow Fusion-F1 source reproduction self-test
checks:10/10 PASS
dependencies:PYTHON_STANDARD_LIBRARY_ONLY
network_used:false
```

---

## Full source reconstruction

The complete source reconstruction can be started with:

```text
python -B SSUM_Snow_Fusion_F1_v1_0_1/verification/SSUM_Snow_Fusion_F1_Reproduction_v1_0_1.py --run
```

The reconstruction retrieves the declared upstream meteorological source material required by the frozen protocol.

Downloaded source payloads are working data and are not part of the repository's scientific artifact set.

The package distributes project-generated evidence, specifications, software and receipt identities rather than bulk NOAA/NCEI source payloads.

---

## Deterministic reference implementation

The core Fusion-F1 operation is intentionally small:

```text
F1 = 0.75 * R_NBM + 0.25 * R_SPF1
```

The complexity lies primarily in preserving:

- frozen predictor definitions;
- chronological source admission;
- rank-reference identity;
- historical missing-data rules;
- target-truth separation;
- deterministic scoring;
- evidence identity.

The reference implementation therefore separates the compact Fusion rule from the larger source-reconstruction pipeline.

---

## Evidence identity

`SHA256SUMS.txt` covers only scientifically material stable artifacts.

It intentionally does not freeze ordinary explanatory prose such as the package README or other editorial documentation.

The current manifest covers:

```text
6 scientific evidence/result JSON files
1 frozen specification
1 reference implementation
1 source reproduction implementation
```

Total:

```text
9 scientifically material artifacts
```

This permits explanatory documentation to evolve without silently changing the identity of the frozen scientific objects.

---

## Repository structure

```text
SSUM-Snow/
│
├── README.md
├── LICENSE
├── .gitattributes
│
├── SSUM_Snow_Fusion_F1_v1_0_1/
│   ├── README.md
│   ├── LICENSE
│   ├── CLAIM_BOUNDARIES.txt
│   ├── EVIDENCE_CHAIN.txt
│   ├── LIMITATIONS.txt
│   ├── METHODOLOGY.txt
│   ├── REPRODUCIBILITY_SCOPE.txt
│   ├── SCIENTIFIC_STATUS.txt
│   ├── SHA256SUMS.txt
│   ├── SOURCE_MANIFEST.txt
│   ├── THIRD_PARTY_DATA_NOTICE.md
│   ├── VERSION.txt
│   │
│   ├── evidence/
│   │   ├── SSUM_Snow_2025_Fusion_Analysis.json
│   │   ├── SSUM_Snow_2025_Standalone_Result.json
│   │   ├── SSUM_Snow_2025_Weight_Robustness.json
│   │   ├── SSUM_Snow_2026_Replication_Result.json
│   │   ├── SSUM_Snow_Execution_Receipts.json
│   │   └── SSUM_Snow_Source_Parity_Result.json
│   │
│   ├── reference/
│   │   ├── SSUM_Snow_Fusion_F1_Reference_Implementation_v1_0_0.py
│   │   └── SSUM_Snow_Fusion_F1_Specification.json
│   │
│   └── verification/
│       ├── SSUM_Snow_Fusion_F1_Package_Verifier_v1_0_1.py
│       ├── SSUM_Snow_Fusion_F1_Reproduction_v1_0_1.py
│       └── VERIFY.txt
│
└── archive/
    └── pre_fusion/
        ├── docs/
        ├── evidence/
        ├── inputs/
        ├── results_hourly/
        ├── results_hourly_reference_traces/
        └── scripts/
```

Runtime cache/output directories may be created locally by the source reproducer and are intentionally not tracked as scientific repository artifacts.

---

## Earlier SSUM-Snow materials

The earlier SSUM-Snow trust/corridor implementation and its associated documentation, scripts, inputs and evidence remain preserved under:

[archive/pre_fusion](./archive/pre_fusion/)

The material is retained for historical traceability rather than silently removed.

Key historical locations:

- [Earlier documentation](./archive/pre_fusion/docs/)
- [Earlier evidence](./archive/pre_fusion/evidence/)
- [Earlier inputs](./archive/pre_fusion/inputs/)
- [Earlier hourly summaries](./archive/pre_fusion/results_hourly/)
- [Earlier reference traces](./archive/pre_fusion/results_hourly_reference_traces/)
- [Earlier scripts](./archive/pre_fusion/scripts/)

The current Fusion-F1 evidence should not be interpreted as retrospectively rewriting the claims or results recorded in those earlier materials.

---

## Reproducibility boundary

The package distinguishes three different levels of reproducibility:

```text
1. artifact verification
   |
   +--> verify frozen scientific identities and evidence consistency

2. deterministic implementation replay
   |
   +--> verify the frozen Fusion-F1 rule and implementation behavior

3. source reconstruction
   |
   +--> re-retrieve declared upstream meteorological inputs
        and reconstruct the historical predictor/truth pipeline
```

Upstream public datasets may be revised after the historical experiment. A future source reconstruction should therefore distinguish source drift from changes in the frozen project evidence.

See:

[REPRODUCIBILITY_SCOPE.txt](./SSUM_Snow_Fusion_F1_v1_0_1/REPRODUCIBILITY_SCOPE.txt)

---

## Third-party data boundary

SSUM-Snow uses declared public meteorological sources, including NOAA/NWS/NCEI resources, as factual scientific inputs.

Raw third-party source payloads and bulk caches are not distributed as part of the Fusion-F1 scientific package.

The repository does not claim ownership of third-party meteorological observations, forecast products, services or other externally governed materials and does not relicense them.

See:

[THIRD_PARTY_DATA_NOTICE.md](./SSUM_Snow_Fusion_F1_v1_0_1/THIRD_PARTY_DATA_NOTICE.md)

---

## 📜 License

See: [LICENSE](./LICENSE)

Package-specific copy:

[SSUM_Snow_Fusion_F1_v1_0_1/LICENSE](./SSUM_Snow_Fusion_F1_v1_0_1/LICENSE)

Use, copying, modification, study, testing, redistribution and other permissions are governed by the terms stated in the LICENSE.

Third-party software, meteorological observations, forecast products, services, datasets and other externally governed materials remain subject to their own applicable rights and terms and are not relicensed by this repository.

The declared source and rights boundary for Fusion-F1 is documented in:

[THIRD_PARTY_DATA_NOTICE.md](./SSUM_Snow_Fusion_F1_v1_0_1/THIRD_PARTY_DATA_NOTICE.md)

This repository does not claim formal meteorological certification, operational forecasting qualification, universal predictive superiority, or independent outside-party scientific verification.

---

## Independent replication

The current package contains deterministic verification, frozen evidence identities and source-reconstruction software.

Independent outside-party end-to-end replication remains:

```text
OPEN_NOT_YET_CONFIRMED
```

Outside replication can independently examine:

- artifact identities;
- frozen specification;
- source admission;
- chronology;
- predictor reconstruction;
- truth reconstruction;
- metric reproduction;
- claim boundaries.

---

## Final statement

```text
negative standalone result
        +
frozen structural signal
        +
declared archived NBM information
        +
chronologically reserved replication
        |
        v
a modest, source-parity-verified Fusion-F1 discrimination improvement
within the tested boundary
```

**SSUM-Snow Fusion-F1 is presented as a bounded scientific result, not as a universal forecasting claim.**

*Part of the Shunyaya Framework.*
