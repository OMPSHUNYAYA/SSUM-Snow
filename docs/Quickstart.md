# ⚡ SSUM-Snow

## Quickstart

*(using concepts of Shunyaya Structural Universal Mathematics — SSUM)*

**Deterministic • Trust-Gated • Observational • Reproducible • Low False Signals**

---

## WHAT YOU NEED

SSUM-Snow is intentionally minimal.

### Requirements
- Python 3.9+
- Standard library only (as released)

Everything is:
- **deterministic**
- **offline**
- **reproducible**
- **identical across machines**

No randomness.  
No training.  
No probabilistic heuristics.  
No station-specific tuning.

---

## MINIMAL PROJECT LAYOUT

A minimal SSUM-Snow setup contains:

- **Inputs**: one or more `_SSUM_INPUT.csv` files (converted from NOAA ISD)
- **Core scripts**: the SSUM-Snow engine + calibration helper
- **Results**: per-station outputs (hourly summaries)

SSUM-Snow does **not** replace meteorology.  
It adds a **structural trust layer**:

- it may permit a forecast corridor
- it may deny / suppress prediction under instability
- it treats silence as informative

---

## ONE-MINUTE MENTAL MODEL

Classical weather forecasting asks:

> **“What will happen?”**

SSUM-Snow asks:

> **“Is it structurally safe to speak?”**

SSUM-Snow’s primary output is **trust-gated snow signaling**:
- when snow is structurally admissible
- when it is unsafe to issue a forecast
- when depth should remain conservative

---

## CORE STRUCTURAL IDEA (IN ONE LINE)

A snow signal can be physically plausible —  
yet structurally unsafe to trust.

SSUM-Snow is designed to reduce false alarms by enforcing **permissibility before prediction**.

---

## PRIMARY OUTPUTS (WHAT SSUM-SNOW PRODUCES)

For each station run, SSUM-Snow produces deterministic artifacts such as:

- `summary.json`  
  (the station’s headline results)

- optional auxiliary CSVs  
  (used for local auditing or review; implementation-dependent)

In addition, SSUM-Snow can generate a **reference trace** (used in a single public reference case):

- `series.csv`  
  (hourly structural series; useful for proof-style evidence)

Large raw datasets are intentionally excluded to avoid file explosion.  
Full series are internally validated and selectively published for auditability.

---

## QUICK RUN (HOURLY) — ONE STATION

Run SSUM-Snow on a single station input:

```
python scripts/ssum_snow.py --in "inputs/Milwaukee_2024_SSUM_INPUT.csv" --out_dir "results_hourly/Milwaukee_2024"
```

### Expected behavior
- stable regimes → admissible corridor + conservative snow state
- violent / unstable regimes → corridor collapses, prediction suppressed
- false alarms → structurally minimized (by design)

(Use the exact CLI flags defined in your repository version if additional parameters are required.)

---

## RUN ALL 10 STATIONS (HOURLY)

If your public release has:
- `inputs/` containing 10 files `*_SSUM_INPUT.csv`
- `scripts/ssum_snow.py`

Then you can run them one-by-one (recommended for clarity), e.g.:

```
python scripts/ssum_snow.py --in "inputs/Buffalo_2014_SSUM_INPUT.csv" --out_dir "results_hourly/Buffalo_2014"
python scripts/ssum_snow.py --in "inputs/ChicagoOHare_2022_SSUM_INPUT.csv" --out_dir "results_hourly/ChicagoOHare_2022"
python scripts/ssum_snow.py --in "inputs/DesMoines_2019_SSUM_INPUT.csv" --out_dir "results_hourly/DesMoines_2019"
python scripts/ssum_snow.py --in "inputs/Lubbock_2021_SSUM_INPUT.csv" --out_dir "results_hourly/Lubbock_2021"
python scripts/ssum_snow.py --in "inputs/Milwaukee_2024_SSUM_INPUT.csv" --out_dir "results_hourly/Milwaukee_2024"
python scripts/ssum_snow.py --in "inputs/Minneapolis_2019_SSUM_INPUT.csv" --out_dir "results_hourly/Minneapolis_2019"
python scripts/ssum_snow.py --in "inputs/Omaha_2019_SSUM_INPUT.csv" --out_dir "results_hourly/Omaha_2019"
python scripts/ssum_snow.py --in "inputs/Rochester_2019_SSUM_INPUT.csv" --out_dir "results_hourly/Rochester_2019"
python scripts/ssum_snow.py --in "inputs/SiouxFalls_2014_SSUM_INPUT.csv" --out_dir "results_hourly/SiouxFalls_2014"
python scripts/ssum_snow.py --in "inputs/WichitaDwight_2022_SSUM_INPUT.csv" --out_dir "results_hourly/WichitaDwight_2022"
```

---

## OPTIONAL — INPUT CONVERSION (NOAA → SSUM INPUT)

If you need to regenerate an input file from a NOAA ISD CSV:

```
python scripts/noaa_isd_to_ssum_input.py --in "NOAA/<raw_station_file>.csv" --out "inputs/<Station_Year>_SSUM_INPUT.csv"
```

This step is **deterministic** and produces a stable, reusable `_SSUM_INPUT.csv`.

---

## ABOUT “CALIBRATION” (ALPHA / MAPPING)

`ssum_snow_calibrate.py` exists to support conservative mapping and consistency checks.

SSUM-Snow’s philosophy:
- no station-specific tuning
- calibration is used only to set **global, conservative mapping rules**
- **structural permissibility always dominates magnitude**

---

## WHAT SSUM-SNOW IS — AND IS NOT

### SSUM-Snow is:
- a **structural trust-gating layer**
- deterministic and reproducible
- conservative by design
- explainable via corridor permission and collapse behavior
- compatible with classical meteorology (non-invasive)

---

### SSUM-Snow is not:
- a numerical weather prediction (NWP) model
- a deep learning forecaster
- a probability / ensemble substitute
- a system that forces a forecast every hour
- a promise of daily depth accuracy

---

## DETERMINISM GUARANTEE

Given identical inputs:
- identical outputs
- identical summaries
- identical corridor behavior

No randomness.  
No hidden state.

---

## QUICKSTART SUMMARY

SSUM-Snow provides a **trust-first hourly snow framework** that makes it safe to say:

- “snow” when structure supports it
- “no snow / do not trust” when structure collapses

Its biggest practical advantage is **false-signal suppression through structural permissibility**.

