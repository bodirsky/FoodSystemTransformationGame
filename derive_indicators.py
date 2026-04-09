"""
derive_indicators.py

Derives indicators.csv from:
  - fig3_heatmap.csv       : baseline values per SSP scenario
  - fig2_historical.csv    : historical BASE_SSP2 values for 2000 and 2010
  - indicators_gameplay.csv: static gameplay parameters (id, name, emoji, unit,
                             lowerBetter, goodThreshold, badThreshold, voterWeight, desc)

Derivation:
  value2000 = BASE_SSP2_2000 value (from fig2_historical.csv)
  value2010 = BASE_SSP2_2010 value (from fig2_historical.csv)
  start     = BASE_SSP2_2020 value (from fig3_heatmap.csv)
  trendSSPx = (BASE_SSPx_2050 - BASE_SSP2_2020) / N_ROUNDS
  NA cells  → 0 (with warning)
"""

import csv
import sys

N_ROUNDS = 6  # 6 rounds × 5 years = 2020 → 2050

# ── Column mapping: fig3_heatmap column → indicators.csv indicator id ─────────
COL_MAP = {
    'underweight_Mio':    'underweight',
    'obesity_Mio':        'obesity',
    'premMort_MioYLL':    'premMort',
    'croplandBII_pct':    'croplandBII',
    'hotspotBII_pct':     'hotspotBII',
    'cropareaDiv_Shannon':'cropareaDiv',
    'nitrogen_MtN':       'nitrogen',
    'waterViol_km3':      'waterViol',
    'afoluGHG_GtCO2eq':   'afoluGHG',
    'globalWarm_degC':    'globalWarm',
    'foodExpend_USDpp':   'foodExpend',
    'poverty_Mio':        'poverty',
    'agLabor_Mio':        'agEmploy',
    'agWages_idx2010':    'agWages',
    'bioeconomy_BnUSD':   'bioeconomy',
    'prodFactor_BnUSD':   'prodCosts',
}

# Scenarios to read
BASE_2020  = 'BASE_SSP2_2020'
BASE_SSP1  = 'BASE_SSP1_2050'
BASE_SSP2  = 'BASE_SSP2_2050'
BASE_SSP3  = 'BASE_SSP3_2050'
HIST_2000  = 'BASE_SSP2_2000'
HIST_2010  = 'BASE_SSP2_2010'

# ── Read fig3_heatmap.csv ─────────────────────────────────────────────────────
heatmap = {}
with open('fig3_heatmap.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        heatmap[row['scenario']] = row

for key in (BASE_2020, BASE_SSP1, BASE_SSP2, BASE_SSP3):
    if key not in heatmap:
        sys.exit(f"ERROR: '{key}' not found in fig3_heatmap.csv")

base2020 = heatmap[BASE_2020]
ssp1     = heatmap[BASE_SSP1]
ssp2     = heatmap[BASE_SSP2]
ssp3     = heatmap[BASE_SSP3]

# ── Read fig2_historical.csv ──────────────────────────────────────────────────
historical = {}
with open('fig2_historical.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        historical[row['scenario']] = row

for key in (HIST_2000, HIST_2010):
    if key not in historical:
        sys.exit(f"ERROR: '{key}' not found in fig2_historical.csv")

def get_val(row, col, label):
    v = row.get(col, 'NA')
    if v == 'NA':
        print(f"  WARNING: {col} is NA for {label} — using 0")
        return None
    return float(v)

def trend(ssp_row, ssp_label, col):
    v2020 = get_val(base2020, col, BASE_2020)
    vssp  = get_val(ssp_row,  col, ssp_label)
    if v2020 is None or vssp is None:
        return 0
    return round((vssp - v2020) / N_ROUNDS, 3)

# ── Read indicators_gameplay.csv ──────────────────────────────────────────────
gameplay = []
with open('indicators_gameplay.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        gameplay.append(row)

# ── Build output rows ─────────────────────────────────────────────────────────
out_cols = ['id', 'name', 'emoji', 'unit',
            'value2000', 'value2010', 'start',
            'trendSSP1', 'trendSSP2', 'trendSSP3',
            'lowerBetter', 'goodThreshold', 'badThreshold',
            'voterWeight', 'desc']

rows_out = []
for gp in gameplay:
    ind_id = gp['id']

    # Find the shared column name for this indicator
    fig_col = next((c for c, i in COL_MAP.items() if i == ind_id), None)
    if fig_col is None:
        print(f"  WARNING: no column mapped for indicator '{ind_id}' — values/trends set to 0")
        v2000 = v2010 = start_val = 0
        t1 = t2 = t3 = 0
    else:
        raw_2000  = get_val(historical[HIST_2000], fig_col, HIST_2000)
        raw_2010  = get_val(historical[HIST_2010], fig_col, HIST_2010)
        raw_start = get_val(base2020,              fig_col, BASE_2020)
        v2000     = round(raw_2000,  3) if raw_2000  is not None else 0
        v2010     = round(raw_2010,  3) if raw_2010  is not None else 0
        start_val = round(raw_start, 3) if raw_start is not None else 0
        t1 = trend(ssp1, BASE_SSP1, fig_col)
        t2 = trend(ssp2, BASE_SSP2, fig_col)
        t3 = trend(ssp3, BASE_SSP3, fig_col)

    rows_out.append({
        'id':           ind_id,
        'name':         gp['name'],
        'emoji':        gp['emoji'],
        'unit':         gp['unit'],
        'value2000':    v2000,
        'value2010':    v2010,
        'start':        start_val,
        'trendSSP1':    t1,
        'trendSSP2':    t2,
        'trendSSP3':    t3,
        'lowerBetter':  gp['lowerBetter'],
        'goodThreshold':gp['goodThreshold'],
        'badThreshold': gp['badThreshold'],
        'voterWeight':  gp['voterWeight'],
        'desc':         gp['desc'],
    })

# ── Write indicators.csv ──────────────────────────────────────────────────────
out_path = 'indicators.csv'
with open(out_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=out_cols)
    writer.writeheader()
    writer.writerows(rows_out)

print(f"\nWritten {len(rows_out)} rows to {out_path}")
print()
print("Rows written:")
for r in rows_out:
    print(f"  {r['id']:20s}  2000={r['value2000']:8}  2010={r['value2010']:8}  2020={r['start']:8}  SSP1={r['trendSSP1']:8}  SSP2={r['trendSSP2']:8}  SSP3={r['trendSSP3']}")
