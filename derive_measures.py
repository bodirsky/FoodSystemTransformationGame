"""
derive_measures.py

Derives measures.csv from:
  - fig4_heatmap.csv   : absolute indicator values per scenario in 2050
  - measures_gameplay.csv : gameplay parameters (id, name, cat, cost, popularity, desc)

Impact per indicator = (scenario_value - BASE_SSP2_2050_value) / 3
NA cells in the heatmap (grey / not quantified) are treated as 0 (no effect).
"""

import csv
import os

# ── Column mapping: fig4_heatmap column → measures.csv indicator id ──────────
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
IND_COLS = list(COL_MAP.values())

# Scenario names in fig4 that differ from id in measures_gameplay
SCENARIO_TO_ID = {
    'REDD+':             'REDD',
    'NitrogenEfficiency':'NitrogenEff',
}

# Scenarios to skip (reference baseline)
SKIP = {'BASE_SSP2_2050'}

# ── Read fig4_heatmap.csv ────────────────────────────────────────────────────
heatmap = {}
with open('fig4_heatmap.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        heatmap[row['scenario']] = row

base = heatmap['BASE_SSP2_2050']

# ── Read measures_gameplay.csv ───────────────────────────────────────────────
gameplay = {}
with open('measures_gameplay.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        gameplay[row['id']] = row

# ── Build output rows ────────────────────────────────────────────────────────
# 'synergy' column: non-empty for packages/pathways so the game's existing
# `.filter(r => !r.synergy || !r.synergy.trim())` excludes them from MEASURES
# while they remain in the CSV for reference.
out_cols = ['id', 'name', 'cat', 'cost', 'desc'] + IND_COLS + ['popularity', 'synergy']
rows_out = []

for scenario, row in heatmap.items():
    if scenario in SKIP:
        continue

    gp_id = SCENARIO_TO_ID.get(scenario, scenario)
    gp    = gameplay.get(gp_id, {})

    # Calculate indicator deltas; NA heatmap cells → 0 (no modelled effect)
    effects = {}
    for hcol, mcol in COL_MAP.items():
        val_str  = row.get(hcol,  'NA')
        base_str = base.get(hcol, 'NA')
        if val_str == 'NA' or base_str == 'NA':
            effects[mcol] = 0
        else:
            delta = (float(val_str) - float(base_str)) / 3
            effects[mcol] = round(delta, 3)

    # Derive cat for packages/pathways not in measures_gameplay
    row_type = row.get('type', '')
    if row_type == 'package':
        derived_cat = scenario          # e.g. "Diets", "Biosphere"
    elif row_type == 'pathway':
        derived_cat = 'Pathway'
    else:
        derived_cat = gp.get('cat', row_type.capitalize())

    # Mark packages and pathways so the game filters them out of MEASURES
    synergy_marker = row_type if row_type in ('package', 'pathway') else ''

    out_row = {
        'id':         gp_id if gp else scenario,
        'name':       gp.get('name', scenario),
        'cat':        gp.get('cat', derived_cat),
        'cost':       gp.get('cost', 0),
        'desc':       gp.get('desc', ''),
        'popularity': gp.get('popularity', 0),
        'synergy':    synergy_marker,
    }
    out_row.update(effects)
    rows_out.append(out_row)

# ── Write measures.csv ───────────────────────────────────────────────────────
out_path = 'measures.csv'
with open(out_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=out_cols)
    writer.writeheader()
    writer.writerows(rows_out)

print(f"Written {len(rows_out)} rows to {out_path}")
print()
print("Rows written:")
for r in rows_out:
    print(f"  {r['id']:25s}  cat={r['cat']}")
