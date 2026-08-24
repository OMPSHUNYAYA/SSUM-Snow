#!/usr/bin/env python3
import argparse
import hashlib
import json
import math
import random
import re
import urllib.parse
import urllib.request
from bisect import bisect_left, bisect_right
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
CACHE = BASE / "source_cache"
NBM_CACHE = CACHE / "nbm"
GHCN_CACHE = CACHE / "ghcn"
NCEI_WINDOW_CACHE = CACHE / "ncei_prequential"
OUTPUT = BASE / "verification_output"
for p in (NBM_CACHE, GHCN_CACHE, NCEI_WINDOW_CACHE, OUTPUT):
    p.mkdir(parents=True, exist_ok=True)

VERSION = "1.0.1"
NBM_ROOT = "https://noaa-nbm-grib2-pds.s3.amazonaws.com"
GHCN_ROOT = "https://www.ncei.noaa.gov/pub/data/ghcn/daily/all"
NCEI_DATA = "https://www.ncei.noaa.gov/access/services/data/v1"
NOAA_MISSING = -99
BOOT_REPS = 20000
BOOT_SEED = 20260824

EXPECTED = {
    "r3_spf1_prediction_sha256": "786d452760ae75368cd47aba3f5f9023c59e837710b33a6d73d400ba04e410b4",
    "r3_nbm_prediction_sha256": "5d8429ef81a8e42512380050a09edf6941fdb2218d787ea26a793dbe452adc05",
    "r3_truth_sha256": "b760275910a4cb7706b2ad783daadfb1cbdfbf971cc9b05baf1b3ad51cb87610",
    "r3_standalone_score_sha256": "509b9af760f1b73c0c17ce2b2bc092a06337e617cbffbbc7b300b093cdf7b6cb",
    "r3_fusion_analysis_sha256": "76d0a511a14e9af6254a4da8ca6e1af17b95c8e5819362d6cb759c0175773ab8",
    "r3_weight_robustness_sha256": "d8bf5fb09a613a1d92f02eff581837b9db7b08998700a133084b041f81912681",
    "r4_nbm_prediction_sha256": "1b5d6100dd789fa3310aea5d94fc32335e06eb34f52e66d92dc936aaedb97a2f",
    "r4_spf1_prediction_sha256": "dd00a58b094d54da0287b7adaeb46a5d75da25cc532e345684a6a5b111b48b17",
    "r4_fusion_prediction_sha256": "a2227d4c45f631e9108782ecd15af7331853fee3396df2a2b0f077da27a03bb9",
    "r4_truth_sha256": "b82feb2a58abc3dd1d9fe5733a9511d31036274e58ee23763b919f4d0b1a29c0",
    "r4_final_score_sha256": "9cf14b6c373100dc054b94a257f725342e4426620c035653813eaa12f9fc74e2",
}

STATIONS = {
    "ALBANY": ("USW00014735", "KALB", "ET"),
    "BURLINGTON": ("USW00014742", "KBTV", "ET"),
    "SYRACUSE": ("USW00014771", "KSYR", "ET"),
    "CLEVELAND": ("USW00014820", "KCLE", "ET"),
    "DETROIT": ("USW00094847", "KDTW", "ET"),
    "MADISON": ("USW00014837", "KMSN", "CT"),
    "GREEN_BAY": ("USW00014898", "KGRB", "CT"),
    "DULUTH": ("USW00014913", "KDLH", "CT"),
    "BUFFALO": ("USW00014733", "KBUF", "ET"),
    "ROCHESTER_NY": ("USW00014768", "KROC", "ET"),
    "TOLEDO": ("USW00094830", "KTOL", "ET"),
    "GRAND_RAPIDS": ("USW00094860", "KGRR", "ET"),
    "LA_CROSSE": ("USW00014920", "KLSE", "CT"),
    "MINNEAPOLIS": ("USW00014922", "KMSP", "CT"),
    "FARGO": ("USW00014914", "KFAR", "CT"),
}
TARGETS = {
    "ALBANY": ["SYRACUSE", "BUFFALO"],
    "BURLINGTON": ["SYRACUSE", "BUFFALO"],
    "SYRACUSE": ["ROCHESTER_NY", "BUFFALO"],
    "CLEVELAND": ["DETROIT", "TOLEDO"],
    "DETROIT": ["GRAND_RAPIDS", "TOLEDO"],
    "MADISON": ["LA_CROSSE", "MINNEAPOLIS"],
    "GREEN_BAY": ["MINNEAPOLIS", "LA_CROSSE"],
    "DULUTH": ["FARGO", "MINNEAPOLIS"],
}
FEATURES = [
    "tmean", "trange", "prcp", "snow", "snow_lag1", "month_sin", "month_cos",
    "up_tmean", "up_prcp", "up_snow_sum", "up_snow_any", "temp_gradient",
    "cold_up_snow", "cold_up_prcp",
]
MEAN = [-1.3655904267328967,8.668337472717695,1.9373748777000077,1.0693384511176338,1.0701663279897644,0.37029225019976875,0.6471835790691776,-1.2459020094829532,1.862150974636863,2.112907353051855,0.35982539324151425,0.11968841724994358,2.4565025965229172,5.109482012493415]
SCALE = [7.35291882784391,4.101484949308128,4.8460674424979855,3.3221302118748395,3.3267289197299026,0.5561282423789786,0.36709459605620676,7.303488868934149,4.238175265332385,5.674770278675036,0.4799490385656625,2.4185436081077936,4.656087066755887,16.57895097112088]
COEF = [-0.25371601338679917,-0.1318924512720109,0.04187160605137054,0.14057361052281406,-0.02468235788670808,0.3843273548231735,0.3704161203528799,-0.22580438013076123,0.132542646131337,0.024425096716501282,0.5946087986045814,0.08947263724759182,-0.2097064989561956,0.022118870839349977]
INTERCEPT = -1.1555249871811413

EXPECTED_R3_NBM_MISSING = {
    ("KALB", "2025-02-04"), ("KBTV", "2025-02-04"),
    ("KCLE", "2025-02-04"), ("KDLH", "2025-02-04"),
    ("KDTW", "2025-02-04"), ("KGRB", "2025-02-04"),
    ("KMSN", "2025-02-04"), ("KSYR", "2025-02-04"),
}
EXPECTED_R3_SPF1_MISSING = {
    ("CLEVELAND", "2025-03-04"), ("CLEVELAND", "2025-03-05"),
    ("CLEVELAND", "2025-03-06"), ("DETROIT", "2025-03-04"),
    ("DETROIT", "2025-03-05"), ("DETROIT", "2025-03-06"),
    ("DULUTH", "2025-12-04"), ("DULUTH", "2025-12-07"),
}

HEADER_RE = re.compile(
    r"(?m)^[ \t]*([A-Z0-9]{4,5})[ \t]+NBM[^\r\n]*?[ \t]+NBS[ \t]+GUIDANCE[ \t]+"
    r"(\d{1,2})/(\d{1,2})/(\d{4})[ \t]+(\d{4})[ \t]+UTC[ \t]*\r?$"
)

NETWORK_FETCH_COUNT = 0


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def sha_obj(obj):
    return hashlib.sha256(canonical(obj)).hexdigest()


def dates_2025():
    out = []
    d = date(2025, 1, 1)
    while d.year == 2025:
        if d.month in (1, 2, 3, 11, 12):
            out.append(d)
        d += timedelta(days=1)
    return out


def dates_2026():
    out = []
    d = date(2026, 1, 1)
    end = date(2026, 3, 31)
    while d <= end:
        out.append(d)
        d += timedelta(days=1)
    return out


def logistic(z):
    if z >= 0:
        e = math.exp(-z)
        return 1.0 / (1.0 + e)
    e = math.exp(z)
    return e / (1.0 + e)


def predict_spf1(f):
    z = INTERCEPT
    for k, mu, sc, c in zip(FEATURES, MEAN, SCALE, COEF):
        z += ((float(f[k]) - mu) / sc) * c
    return logistic(z)


def fetch(url, path):
    global NETWORK_FETCH_COUNT
    if path.exists() and path.stat().st_size > 0:
        return path.read_bytes()
    req = urllib.request.Request(url, headers={"User-Agent": "SSUM-Snow-Fusion-F1/1.0.1 scientific verification"})
    with urllib.request.urlopen(req, timeout=180) as r:
        payload = r.read()
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(payload)
    tmp.replace(path)
    NETWORK_FETCH_COUNT += 1
    return payload


def load_raw_ghcn():
    raw = {}
    for i, (name, (sid, _, _)) in enumerate(STATIONS.items(), 1):
        payload = fetch(f"{GHCN_ROOT}/{sid}.dly", GHCN_CACHE / f"{sid}.dly")
        raw[name] = payload
        print(f"GHCN {i}/{len(STATIONS)} {name}")
    return raw


def parse_r3_feature_data(raw_payloads):
    data = {}
    for name, payload in raw_payloads.items():
        sid = STATIONS[name][0]
        rows = {}
        for line in payload.decode("ascii", errors="ignore").splitlines():
            if len(line) < 269 or line[:11] != sid:
                continue
            try:
                yr = int(line[11:15]); mo = int(line[15:17])
            except ValueError:
                continue
            el = line[17:21]
            if yr < 2024 or yr > 2025 or el not in ("TMAX", "TMIN", "PRCP", "SNOW"):
                continue
            for day in range(1, 32):
                j = 21 + (day - 1) * 8
                try:
                    value = int(line[j:j+5])
                except ValueError:
                    continue
                qflag = line[j+6:j+7]
                if value == -9999 or qflag.strip():
                    continue
                try:
                    d = date(yr, mo, day)
                except ValueError:
                    continue
                rows.setdefault(d, {})[el] = value / 10.0
        data[name] = rows
    return data


def parse_truth(raw_payloads, year, months):
    out = {}
    for name in TARGETS:
        sid = STATIONS[name][0]
        payload = raw_payloads[name]
        for line in payload.decode("ascii", errors="ignore").splitlines():
            if len(line) < 269 or line[:11] != sid:
                continue
            try:
                yr = int(line[11:15]); mo = int(line[15:17])
            except ValueError:
                continue
            if yr != year or mo not in months or line[17:21] != "SNOW":
                continue
            for day in range(1, 32):
                j = 21 + (day - 1) * 8
                try:
                    value = int(line[j:j+5])
                except ValueError:
                    continue
                qflag = line[j+6:j+7]
                try:
                    d = date(yr, mo, day)
                except ValueError:
                    continue
                if value == -9999 or qflag.strip():
                    continue
                out[(name, d.isoformat())] = 1 if value > 0 else 0
    return out


def features(data, target, predictor_day):
    r = data[target].get(predictor_day, {})
    lag = data[target].get(predictor_day - timedelta(days=1), {})
    if not all(k in r for k in ("TMAX", "TMIN", "PRCP", "SNOW")) or "SNOW" not in lag:
        return None
    ups = []
    for u in TARGETS[target]:
        ru = data[u].get(predictor_day, {})
        if not all(k in ru for k in ("TMAX", "TMIN", "PRCP", "SNOW")):
            return None
        ups.append(ru)
    tm = (r["TMAX"] + r["TMIN"]) / 2.0
    ut = sum((x["TMAX"] + x["TMIN"]) / 2.0 for x in ups) / len(ups)
    upr = sum(x["PRCP"] for x in ups) / len(ups)
    usn = sum(x["SNOW"] for x in ups)
    ua = float(usn > 0)
    m = predictor_day.month
    return {
        "tmean": tm,
        "trange": r["TMAX"] - r["TMIN"],
        "prcp": r["PRCP"],
        "snow": r["SNOW"],
        "snow_lag1": lag["SNOW"],
        "month_sin": math.sin(2 * math.pi * m / 12),
        "month_cos": math.cos(2 * math.pi * m / 12),
        "up_tmean": ut,
        "up_prcp": upr,
        "up_snow_sum": usn,
        "up_snow_any": ua,
        "temp_gradient": ut - tm,
        "cold_up_snow": ua * max(0.0, 2.0 - tm),
        "cold_up_prcp": upr * max(0.0, 2.0 - tm),
    }


def r3_spf1_predictions(data):
    out = {}
    for d in dates_2025():
        pd = d - timedelta(days=1)
        for t in TARGETS:
            f = features(data, t, pd)
            if f is not None:
                out[(t, d.isoformat())] = round(predict_spf1(f), 12)
    return out


def _first_sunday(year, month):
    d = date(year, month, 1)
    return d + timedelta(days=(6 - d.weekday()) % 7)


def _second_sunday(year, month):
    return _first_sunday(year, month) + timedelta(days=7)


def utc_to_local(dt, zone):
    mar = _second_sunday(dt.year, 3)
    nov = _first_sunday(dt.year, 11)
    if zone == "ET":
        start = datetime(dt.year, 3, mar.day, 7, tzinfo=timezone.utc)
        end = datetime(dt.year, 11, nov.day, 6, tzinfo=timezone.utc)
        off = -4 if start <= dt < end else -5
    elif zone == "CT":
        start = datetime(dt.year, 3, mar.day, 8, tzinfo=timezone.utc)
        end = datetime(dt.year, 11, nov.day, 7, tzinfo=timezone.utc)
        off = -5 if start <= dt < end else -6
    else:
        raise ValueError("unsupported zone")
    return (dt + timedelta(hours=off)).replace(tzinfo=None)


def runtime_from_header(m):
    return datetime(
        int(m.group(4)), int(m.group(2)), int(m.group(3)),
        int(m.group(5)[:2]), int(m.group(5)[2:]), tzinfo=timezone.utc,
    )


def row_candidates(lines, label):
    pat = re.compile(r"^[ \t]*" + re.escape(label) + r"(?=\s)")
    out = []
    for raw in lines:
        line = raw.rstrip("\r\n")
        m = pat.match(line)
        if m:
            out.append(label + line[m.end():])
    return out


def slot_int(line, index):
    start = 4 + 3 * int(index)
    cell = line[start:start+3].strip()
    if not re.fullmatch(r"-?\d+", cell):
        return None
    return int(cell)


def parse_fhrs(line):
    vals = [slot_int(line, i) for i in range(23)]
    if any(v is None for v in vals):
        return None
    if any(b - a != 3 for a, b in zip(vals, vals[1:])):
        return None
    return vals


def parse_field(lines, label, indices):
    indices = list(indices)
    for line in row_candidates(lines, label):
        vals = [slot_int(line, i) for i in indices]
        if all(v is not None for v in vals):
            return vals
    return None


def six_hour_indices(runtime, fhrs):
    return [
        i for i, fhr in enumerate(fhrs)
        if int(fhr) >= 6 and (runtime + timedelta(hours=int(fhr))).hour % 6 == 0
    ]


def parse_r3_block(block, icao, run):
    matches = list(HEADER_RE.finditer(block))
    if not matches:
        return None
    m = matches[0]
    if m.group(1) != icao or runtime_from_header(m) != run:
        return None
    lines = block[m.start():].splitlines()
    frows = row_candidates(lines, "FHR")
    if not frows:
        return None
    fhrs = parse_fhrs(frows[0])
    if not fhrs:
        return None
    six = six_hour_indices(run, fhrs)
    if len(six) != 11:
        return None
    s06 = parse_field(lines, "S06", six)
    p06 = parse_field(lines, "P06", six)
    psn = parse_field(lines, "PSN", range(23))
    if s06 is None or p06 is None or psn is None:
        return None
    eps = []
    for j, idx in enumerate(six):
        sv, pv, cv = s06[j], p06[j], psn[idx]
        sv = None if sv == NOAA_MISSING else sv
        pv = None if pv == NOAA_MISSING else pv
        cv = None if cv == NOAA_MISSING else cv
        if sv is not None and sv < 0:
            return None
        if pv is not None and not 0 <= pv <= 100:
            return None
        if cv is not None and not 0 <= cv <= 100:
            return None
        eps.append({
            "valid_utc": run + timedelta(hours=fhrs[idx]),
            "s06": sv,
            "p06": pv,
            "psn": cv,
            "joint": None if pv is None or cv is None else (pv / 100.0) * (cv / 100.0),
        })
    return eps


def parse_r4_block(block, icao, run):
    matches = list(HEADER_RE.finditer(block))
    if not matches:
        return None
    m = matches[0]
    if m.group(1) != icao or runtime_from_header(m) != run:
        return None
    lines = block[m.start():].splitlines()
    frows = row_candidates(lines, "FHR")
    if not frows:
        return None
    fhrs = parse_fhrs(frows[0])
    if not fhrs:
        return None
    six = six_hour_indices(run, fhrs)
    if len(six) != 11:
        return None
    p06 = parse_field(lines, "P06", six)
    psn = parse_field(lines, "PSN", range(23))
    if p06 is None or psn is None:
        return None
    eps = []
    for j, idx in enumerate(six):
        pv, cv = p06[j], psn[idx]
        pv = None if pv == NOAA_MISSING else pv
        cv = None if cv == NOAA_MISSING else cv
        if pv is not None and not 0 <= pv <= 100:
            return None
        if cv is not None and not 0 <= cv <= 100:
            return None
        eps.append({
            "valid_utc": run + timedelta(hours=fhrs[idx]),
            "joint": None if pv is None or cv is None else (pv / 100.0) * (cv / 100.0),
        })
    return eps


def nbm_predictions(days, mode):
    out = {}
    exclusions = []
    for day_i, d in enumerate(days, 1):
        path = NBM_CACHE / f"blend_nbstx_{d.strftime('%Y%m%d')}_t01z.txt"
        url = f"{NBM_ROOT}/blend.{d.strftime('%Y%m%d')}/01/text/blend_nbstx.t01z"
        text = fetch(url, path).decode("ascii", errors="ignore")
        run = datetime(d.year, d.month, d.day, 1, tzinfo=timezone.utc)
        matches = list(HEADER_RE.finditer(text))
        block_map = {}
        for i, m in enumerate(matches):
            if runtime_from_header(m) != run:
                continue
            end = matches[i+1].start() if i+1 < len(matches) else len(text)
            block_map[m.group(1)] = text[m.start():end]
        for t in TARGETS:
            icao = STATIONS[t][1]
            block = block_map.get(icao)
            eps = None if block is None else (parse_r3_block(block, icao, run) if mode == "R3" else parse_r4_block(block, icao, run))
            if eps is None:
                exclusions.append((icao, d.isoformat(), "PARSE"))
                continue
            local = [x for x in eps if utc_to_local(x["valid_utc"], STATIONS[t][2]).date() == d]
            if not local:
                exclusions.append((icao, d.isoformat(), "LOCAL_DAY"))
                continue
            if mode == "R3":
                if any(x["s06"] is None or x["p06"] is None or x["psn"] is None for x in local):
                    exclusions.append((icao, d.isoformat(), "MISSING_REQUIRED_FIELD"))
                    continue
            else:
                if any(x["joint"] is None for x in local):
                    exclusions.append((icao, d.isoformat(), "MISSING_P06_OR_PSN"))
                    continue
            out[(t, d.isoformat())] = round(max(x["joint"] for x in local), 12)
        if day_i == 1 or day_i % 10 == 0 or day_i == len(days):
            print(f"NBM_{mode} {day_i}/{len(days)} score_rows={len(out)}")
    return out, exclusions


def ncei_window_url(d):
    station_ids = ",".join(STATIONS[n][0] for n in sorted(STATIONS))
    q = {
        "dataset": "daily-summaries",
        "dataTypes": "TMAX,TMIN,PRCP,SNOW",
        "stations": station_ids,
        "startDate": (d - timedelta(days=2)).isoformat(),
        "endDate": (d - timedelta(days=1)).isoformat(),
        "units": "metric",
        "includeAttributes": "false",
        "format": "json",
    }
    return NCEI_DATA + "?" + urllib.parse.urlencode(q)


def parse_ncei_json(payload):
    obj = json.loads(payload.decode("utf-8"))
    if isinstance(obj, dict) and "results" in obj:
        obj = obj["results"]
    if not isinstance(obj, list):
        raise RuntimeError("unexpected NCEI response shape")
    id_to_name = {sid: name for name, (sid, _, _) in STATIONS.items()}
    data = {name: {} for name in STATIONS}
    for r in obj:
        if not isinstance(r, dict):
            continue
        sid = str(r.get("STATION") or r.get("station") or "")
        name = id_to_name.get(sid)
        if not name:
            continue
        ds = str(r.get("DATE") or r.get("date") or "")[:10]
        try:
            d = date.fromisoformat(ds)
        except ValueError:
            continue
        vals = {}
        for k in ("TMAX", "TMIN", "PRCP", "SNOW"):
            v = r.get(k)
            if v is None or v == "":
                continue
            try:
                vals[k] = float(v)
            except (TypeError, ValueError):
                continue
        data[name][d] = vals
    return data


def r4_spf1_predictions():
    out = {}
    for i, d in enumerate(dates_2026(), 1):
        path = NCEI_WINDOW_CACHE / f"predictor_window_for_{d.isoformat()}.json"
        payload = fetch(ncei_window_url(d), path)
        data = parse_ncei_json(payload)
        pd = d - timedelta(days=1)
        for t in TARGETS:
            f = features(data, t, pd)
            if f is not None:
                out[(t, d.isoformat())] = round(predict_spf1(f), 12)
        if i == 1 or i % 10 == 0 or i == 90:
            print(f"NCEI_R4 {i}/90 score_rows={len(out)}")
    return out


def auc(y, s):
    p = sum(y); n = len(y) - p
    if p == 0 or n == 0:
        return None
    order = sorted(range(len(y)), key=lambda i: (s[i], i))
    rank = [0.0] * len(y)
    k = 0
    while k < len(order):
        j = k + 1
        while j < len(order) and s[order[j]] == s[order[k]]:
            j += 1
        r = (k + 1 + j) / 2.0
        for z in range(k, j):
            rank[order[z]] = r
        k = j
    sr = sum(rank[i] for i, v in enumerate(y) if v == 1)
    return (sr - p * (p + 1) / 2.0) / (p * n)


def average_precision(y, s):
    p = sum(y)
    if p == 0:
        return None
    order = sorted(range(len(y)), key=lambda i: s[i], reverse=True)
    tp = fp = 0
    prev_recall = 0.0
    total = 0.0
    k = 0
    while k < len(order):
        j = k + 1
        score = s[order[k]]
        while j < len(order) and s[order[j]] == score:
            j += 1
        group_pos = sum(y[order[z]] for z in range(k, j))
        group_n = j - k
        tp += group_pos
        fp += group_n - group_pos
        recall = tp / p
        precision = tp / (tp + fp)
        total += (recall - prev_recall) * precision
        prev_recall = recall
        k = j
    return total


def empirical_cdf(reference, x):
    ref = sorted(float(v) for v in reference)
    left = bisect_left(ref, float(x))
    right = bisect_right(ref, float(x))
    return (left + 0.5 * (right - left)) / len(ref)


def fixed_weight_oof(rows, w):
    folds = [({1}, {2}), ({1, 2}, {3}), ({1, 2, 3}, {11, 12})]
    pooled = []
    for train_months, test_months in folds:
        train = [r for r in rows if r["month"] in train_months]
        test = [r for r in rows if r["month"] in test_months]
        ref_nbm = sorted(r["nbm"] for r in train)
        ref_spf = sorted(r["spf"] for r in train)
        for r in test:
            z = dict(r)
            z["f1"] = (1.0 - w) * empirical_cdf(ref_nbm, r["nbm"]) + w * empirical_cdf(ref_spf, r["spf"])
            pooled.append(z)
    return pooled


def pair_credit(event_score, nonevent_score):
    if event_score > nonevent_score:
        return 1.0
    if event_score < nonevent_score:
        return 0.0
    return 0.5


def build_cluster_auc_matrix(rows, cluster_key, score_key):
    keys = sorted({cluster_key(r) for r in rows})
    idx = {k: i for i, k in enumerate(keys)}
    pos = [[] for _ in keys]
    neg = [[] for _ in keys]
    for r in rows:
        bucket = pos if r["y"] == 1 else neg
        bucket[idx[cluster_key(r)]].append(float(r[score_key]))
    pcount = [len(x) for x in pos]
    ncount = [len(x) for x in neg]
    mat = [[0.0 for _ in keys] for _ in keys]
    for a in range(len(keys)):
        for b in range(len(keys)):
            total = 0.0
            for ps in pos[a]:
                for ns in neg[b]:
                    total += pair_credit(ps, ns)
            mat[a][b] = total
    return keys, pcount, ncount, mat


def weighted_auc_from_cluster_counts(counts, pcount, ncount, mat):
    tp = sum(counts[i] * pcount[i] for i in range(len(counts)))
    tn = sum(counts[i] * ncount[i] for i in range(len(counts)))
    if tp == 0 or tn == 0:
        return None
    num = 0.0
    for i, ci in enumerate(counts):
        if ci == 0:
            continue
        for j, cj in enumerate(counts):
            if cj:
                num += ci * cj * mat[i][j]
    return num / (tp * tn)


def percentile(vals, p):
    a = sorted(vals)
    x = (len(a) - 1) * p
    lo = int(x); hi = min(lo + 1, len(a) - 1); f = x - lo
    return a[lo] * (1.0 - f) + a[hi] * f


def exact_cluster_bootstrap_delta(rows, cluster_key):
    k1, p1, n1, m1 = build_cluster_auc_matrix(rows, cluster_key, "fusion_f1")
    k2, p2, n2, m2 = build_cluster_auc_matrix(rows, cluster_key, "nbm_joint_day")
    if k1 != k2 or p1 != p2 or n1 != n2:
        raise RuntimeError("cluster matrices disagree")
    K = len(k1)
    rng = random.Random(BOOT_SEED)
    vals = []
    for _ in range(BOOT_REPS):
        counts = [0] * K
        for _draw in range(K):
            counts[rng.randrange(K)] += 1
        a1 = weighted_auc_from_cluster_counts(counts, p1, n1, m1)
        a2 = weighted_auc_from_cluster_counts(counts, p2, n2, m2)
        if a1 is not None and a2 is not None:
            vals.append(a1 - a2)
    return [percentile(vals, 0.025), percentile(vals, 0.975)]


def close(got, expected, tol=2e-9):
    return abs(float(got) - float(expected)) <= tol


def run():
    raw = load_raw_ghcn()
    r3_data = parse_r3_feature_data(raw)
    spf25 = r3_spf1_predictions(r3_data)
    missing_spf25 = {(t, d.isoformat()) for d in dates_2025() for t in TARGETS if (t, d.isoformat()) not in spf25}
    if missing_spf25 != EXPECTED_R3_SPF1_MISSING:
        raise RuntimeError("2025 SPF1 missing-pair set differs from frozen definition")

    nbm25, exclusions25 = nbm_predictions(dates_2025(), "R3")
    nbm_missing25 = {(icao, ds) for icao, ds, reason in exclusions25 if reason == "MISSING_REQUIRED_FIELD"}
    if nbm_missing25 != EXPECTED_R3_NBM_MISSING or len(nbm25) != 1200:
        raise RuntimeError("2025 NBM source-missing set differs from frozen definition")

    truth25 = parse_truth(raw, 2025, {1, 2, 3, 11, 12})
    common25 = sorted(set(spf25) & set(nbm25) & set(truth25), key=lambda k: (k[1], k[0]))
    rows25 = [{
        "target": k[0], "date": k[1], "month": int(k[1][5:7]),
        "y": truth25[k], "nbm": nbm25[k], "spf": spf25[k],
    } for k in common25]

    y25 = [r["y"] for r in rows25]
    spf_auc25 = auc(y25, [r["spf"] for r in rows25])
    nbm_auc25 = auc(y25, [r["nbm"] for r in rows25])
    oof25 = fixed_weight_oof(rows25, 0.25)
    oof_auc25 = auc([r["y"] for r in oof25], [r["f1"] for r in oof25])

    print("2025_spf1_prediction_count:" + str(len(spf25)))
    print("2025_nbm_prediction_count:" + str(len(nbm25)))
    print("2025_nbm_source_missing_exclusions:" + str(len(nbm_missing25)))
    print("2025_common_cases:" + str(len(rows25)))
    print("2025_events:" + str(sum(y25)))
    print(f"2025_spf1_auc:{spf_auc25:.12f}")
    print(f"2025_nbm_joint_auc:{nbm_auc25:.12f}")
    print(f"2025_fixed_25_oof_auc:{oof_auc25:.12f}")

    ref_nbm = [r["nbm"] for r in rows25]
    ref_spf = [r["spf"] for r in rows25]

    nbm26, exclusions26 = nbm_predictions(dates_2026(), "R4")
    if exclusions26 or len(nbm26) != 720:
        raise RuntimeError("2026 NBM predictor capacity differs from frozen definition")
    spf26 = r4_spf1_predictions()
    if len(spf26) != 720:
        raise RuntimeError("2026 SPF1 predictor capacity differs from frozen definition")
    truth26 = parse_truth(raw, 2026, {1, 2, 3})
    keys26 = sorted(set(nbm26) & set(spf26) & set(truth26), key=lambda k: (k[1], k[0]))
    rows26 = []
    for k in keys26:
        ds = k[1]
        f1 = round(0.75 * empirical_cdf(ref_nbm, nbm26[k]) + 0.25 * empirical_cdf(ref_spf, spf26[k]), 12)
        rows26.append({
            "target": k[0], "target_date": ds, "month": int(ds[5:7]), "day": int(ds[8:10]),
            "y": truth26[k], "nbm_joint_day": nbm26[k], "fusion_f1": f1,
        })

    y26 = [r["y"] for r in rows26]
    a_nbm = auc(y26, [r["nbm_joint_day"] for r in rows26])
    a_f1 = auc(y26, [r["fusion_f1"] for r in rows26])
    p_nbm = average_precision(y26, [r["nbm_joint_day"] for r in rows26])
    p_f1 = average_precision(y26, [r["fusion_f1"] for r in rows26])
    temporal = exact_cluster_bootstrap_delta(rows26, lambda r: (r["month"], (r["day"] - 1) // 7))
    station = exact_cluster_bootstrap_delta(rows26, lambda r: r["target"])

    station_rows = []
    positive = 0
    for st in TARGETS:
        z = [r for r in rows26 if r["target"] == st]
        yy = [r["y"] for r in z]
        an = auc(yy, [r["nbm_joint_day"] for r in z])
        af = auc(yy, [r["fusion_f1"] for r in z])
        delta = af - an
        if delta > 0:
            positive += 1
        station_rows.append({"target": st, "n": len(z), "events": sum(yy), "nbm_auc": an, "fusion_f1_auc": af, "delta_auc": delta})

    ok = all([
        len(rows25) == 1192,
        sum(y25) == 392,
        close(spf_auc25, 0.760264668367347),
        close(nbm_auc25, 0.910983737244898),
        len(oof25) == 944,
        close(oof_auc25, 0.934291061895),
        len(rows26) == 720,
        sum(y26) == 238,
        close(a_nbm, 0.911647023955),
        close(a_f1, 0.927167962621),
        close(a_f1 - a_nbm, 0.015520938666),
        close(p_nbm, 0.837182439410),
        close(p_f1, 0.875097075669),
        close(p_f1 - p_nbm, 0.037914636259),
        positive == 6,
        close(temporal[0], 0.002057587939),
        close(temporal[1], 0.025197946170),
        close(station[0], 0.006764452593),
        close(station[1], 0.024041287735),
    ])

    print("2026_cases:" + str(len(rows26)))
    print("2026_events:" + str(sum(y26)))
    print(f"2026_nbm_joint_auc:{a_nbm:.12f}")
    print(f"2026_fusion_f1_auc:{a_f1:.12f}")
    print(f"2026_delta_auc:{a_f1-a_nbm:+.12f}")
    print(f"2026_nbm_joint_pr_auc:{p_nbm:.12f}")
    print(f"2026_fusion_f1_pr_auc:{p_f1:.12f}")
    print(f"2026_delta_pr_auc:{p_f1-p_nbm:+.12f}")
    print(f"2026_temporal_bootstrap_95:[{temporal[0]:+.12f},{temporal[1]:+.12f}]")
    print(f"2026_station_bootstrap_95:[{station[0]:+.12f},{station[1]:+.12f}]")
    for r in station_rows:
        print(f"station_{r['target']}_delta_auc:{r['delta_auc']:+.12f}")
    print("2026_positive_stations:" + str(positive) + "/8")

    result = {
        "schema": "SSUM_SNOW_FUSION_F1_SOURCE_REPRODUCTION_RESULT_1.0.1",
        "formula": "F1=0.75*R_NBM+0.25*R_SPF1",
        "source_cache_files": {
            "ghcn_raw": len(list(GHCN_CACHE.glob("*.dly"))),
            "nbm_nbs": len(list(NBM_CACHE.glob("blend_nbstx_*_t01z.txt"))),
            "ncei_prequential_windows": len(list(NCEI_WINDOW_CACHE.glob("predictor_window_for_*.json"))),
        },
        "network_fetch_count": NETWORK_FETCH_COUNT,
        "r3_2025": {
            "spf1_prediction_count": len(spf25),
            "nbm_prediction_count": len(nbm25),
            "nbm_source_missing_exclusions": len(nbm_missing25),
            "common_cases": len(rows25),
            "events": sum(y25),
            "spf1_auc": spf_auc25,
            "nbm_joint_auc": nbm_auc25,
            "fixed_25_oof_n": len(oof25),
            "fixed_25_oof_auc": oof_auc25,
        },
        "r4_2026": {
            "cases": len(rows26),
            "events": sum(y26),
            "nbm_joint_auc": a_nbm,
            "fusion_f1_auc": a_f1,
            "delta_auc": a_f1 - a_nbm,
            "nbm_joint_pr_auc": p_nbm,
            "fusion_f1_pr_auc": p_f1,
            "delta_pr_auc": p_f1 - p_nbm,
            "positive_stations": positive,
            "temporal_bootstrap_95": temporal,
            "station_bootstrap_95": station,
            "stations": station_rows,
        },
        "historical_evidence_identities": EXPECTED,
        "scientific_reproduction": "PASS" if ok else "FAIL",
    }
    result["sha256"] = sha_obj(result)
    out_path = OUTPUT / "SSUM_Snow_Fusion_F1_Source_Reproduction_Result_v1_0_1.json"
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("source_reproduction_result:" + str(out_path.relative_to(BASE)))
    print("source_reproduction_result_sha256:" + result["sha256"])
    print("scientific_reproduction:" + result["scientific_reproduction"])
    if not ok:
        raise SystemExit(1)


def self_test():
    checks = 0
    assert len(dates_2025()) == 151 and len(dates_2026()) == 90; checks += 1
    f = {k: MEAN[i] for i, k in enumerate(FEATURES)}
    assert abs(predict_spf1(f) - logistic(INTERCEPT)) < 1e-15; checks += 1
    assert abs(empirical_cdf([0.0, 1.0, 1.0, 3.0], 1.0) - 0.5) < 1e-15; checks += 1
    assert abs(auc([0,0,1,1], [0.1,0.2,0.8,0.9]) - 1.0) < 1e-15; checks += 1
    assert abs(average_precision([0,0,1,1], [0.1,0.2,0.8,0.9]) - 1.0) < 1e-15; checks += 1

    run25 = datetime(2025, 2, 4, 1, tzinfo=timezone.utc)
    fhrs = list(range(5, 74, 3))
    six = six_hour_indices(run25, fhrs)
    def fixed_row(label, vals):
        return label + " " + "".join(f"{int(v):3d}" for v in vals)
    s06 = [0] * 23
    p06 = [0] * 23
    psn = [50] * 23
    for j, idx in enumerate(six):
        s06[idx] = 1
        p06[idx] = 10 + j
    s06[six[3]] = -99
    block = (
        " KALB    NBM V4.3 NBS GUIDANCE    2/04/2025  0100 UTC\n" +
        fixed_row("FHR", fhrs) + "\n" + fixed_row("S06", s06) + "\n" +
        fixed_row("P06", p06) + "\n" + fixed_row("PSN", psn) + "\n"
    )
    r3 = parse_r3_block(block, "KALB", run25)
    assert r3 is not None and any(x["s06"] is None for x in r3); checks += 1
    assert any(x["s06"] is None for x in r3); checks += 1
    r4 = parse_r4_block(block, "KALB", run25)
    assert r4 is not None and all(x["joint"] is not None for x in r4); checks += 1

    prefix = "USW00014735" + "2025" + "01" + "SNOW"
    fields = []
    for d in range(1, 32):
        v = 25 if d == 1 else 0
        fields.append(f"{v:5d}" + " " + " " + " ")
    raw = {name: b"" for name in STATIONS}
    raw["ALBANY"] = (prefix + "".join(fields) + "\n").encode("ascii")
    parsed = parse_r3_feature_data(raw)
    assert parsed["ALBANY"][date(2025,1,1)]["SNOW"] == 2.5; checks += 1
    truth = parse_truth(raw, 2025, {1})
    assert truth[("ALBANY", "2025-01-01")] == 1; checks += 1

    print("SSUM-Snow Fusion-F1 source reproduction self-test")
    print(f"checks:{checks}/{checks} PASS")
    print("dependencies:PYTHON_STANDARD_LIBRARY_ONLY")
    print("network_used:false")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    args = ap.parse_args()
    if args.self_test == args.run:
        ap.error("choose exactly one of --self-test or --run")
    if args.self_test:
        self_test()
    else:
        run()


if __name__ == "__main__":
    main()
