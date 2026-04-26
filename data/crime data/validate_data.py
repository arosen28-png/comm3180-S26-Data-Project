"""Sanity checks on the CSV files in data/.

Runs a series of integrity checks. Exits non-zero if any check fails.
Used to catch mistakes (typos in source IDs, broken Part 1 totals, etc.)
before pushing to the repo.

Run from repo root: python validate_data.py
"""

import sys
from pathlib import Path

import pandas as pd

DATA = Path("data")
errors = []
warnings = []


def check(condition, msg, level="error"):
    """Record a check result."""
    if not condition:
        if level == "error":
            errors.append(msg)
            print(f"  ✗ {msg}")
        else:
            warnings.append(msg)
            print(f"  ⚠ {msg}")
    else:
        print(f"  ✓ {msg}")


# ---------------------------------------------------------------------------
# 1. All expected files exist
# ---------------------------------------------------------------------------
print("\n[1/6] Files exist")
expected = [
    "penn_clery_annual.csv",
    "penn_pa_ucr.csv",
    "ppd_homicides_citywide.csv",
    "upennalerts.csv",
    "data_sources.csv",
]
for fname in expected:
    check((DATA / fname).exists(), f"data/{fname}")


# ---------------------------------------------------------------------------
# 2. Schemas match data dictionary
# ---------------------------------------------------------------------------
print("\n[2/6] CSV schemas")

clery = pd.read_csv(DATA / "penn_clery_annual.csv")
ucr = pd.read_csv(DATA / "penn_pa_ucr.csv")
ppd = pd.read_csv(DATA / "ppd_homicides_citywide.csv")
alerts = pd.read_csv(DATA / "upennalerts.csv")
sources = pd.read_csv(DATA / "data_sources.csv")

check(
    list(clery.columns) == ["year", "crime_type", "count", "source_asr", "note"],
    f"penn_clery_annual.csv columns: {list(clery.columns)}",
)
check(
    "year" in ucr.columns and "fte_population" in ucr.columns and "total_part1" in ucr.columns,
    f"penn_pa_ucr.csv has year/fte_population/total_part1",
)
check(
    list(ppd.columns) == ["year", "homicides", "source"],
    f"ppd_homicides_citywide.csv columns: {list(ppd.columns)}",
)
check(
    list(alerts.columns) == ["year", "upennalert_count", "source"],
    f"upennalerts.csv columns: {list(alerts.columns)}",
)


# ---------------------------------------------------------------------------
# 3. Year ranges
# ---------------------------------------------------------------------------
print("\n[3/6] Year ranges")
check(
    clery.year.min() >= 2015 and clery.year.max() <= 2025,
    f"clery years: {clery.year.min()}–{clery.year.max()}",
)
check(
    ucr.year.min() >= 2015 and ucr.year.max() <= 2025,
    f"PA UCR years: {ucr.year.min()}–{ucr.year.max()}",
)
check(
    ppd.year.min() >= 2000,
    f"PPD years: {ppd.year.min()}–{ppd.year.max()}",
)


# ---------------------------------------------------------------------------
# 4. Referential integrity: every source_asr in clery/ucr exists in data_sources
# ---------------------------------------------------------------------------
print("\n[4/6] Referential integrity")
known_sources = set(sources.source_id)
clery_sources = set(clery.source_asr.dropna())
ucr_sources = set(ucr.source_asr.dropna())

missing_clery = clery_sources - known_sources
missing_ucr = ucr_sources - known_sources

check(
    not missing_clery,
    f"all clery source_asr values resolve in data_sources.csv (missing: {missing_clery or 'none'})",
)
check(
    not missing_ucr,
    f"all PA UCR source_asr values resolve in data_sources.csv (missing: {missing_ucr or 'none'})",
)


# ---------------------------------------------------------------------------
# 5. PA UCR: total_part1 must equal sum of all reported categories
# ---------------------------------------------------------------------------
# Note: Penn's PA UCR "total" includes simple_assault and attempted_mv_theft,
# even though those are not strictly FBI Part 1 offenses. We follow Penn's
# convention to verify the reported total. See docs/DATA_DICTIONARY.md.
print("\n[5/6] PA UCR totals")
sum_cols = [
    "criminal_homicide",
    "forcible_rape",
    "robbery",
    "aggravated_assault",
    "simple_assault",
    "burglary",
    "theft",
    "motor_vehicle_theft",
    "attempted_mv_theft",
    "arson",
]
ucr["computed_total"] = ucr[sum_cols].sum(axis=1)
mismatches = ucr[ucr.total_part1 != ucr.computed_total]

if len(mismatches) == 0:
    print(f"  ✓ all {len(ucr)} PA UCR rows: total_part1 == sum of reported categories")
else:
    for _, row in mismatches.iterrows():
        errors.append(
            f"PA UCR {int(row.year)}: reported total_part1={row.total_part1}, "
            f"computed sum={row.computed_total}"
        )
        print(
            f"  ✗ PA UCR {int(row.year)}: reported {row.total_part1}, computed {row.computed_total}"
        )


# ---------------------------------------------------------------------------
# 6. Sanity: no negative counts, no future years, no duplicate (year, crime_type)
# ---------------------------------------------------------------------------
print("\n[6/6] Sanity checks")

# no negative counts
check(
    (clery["count"] >= 0).all(),
    "clery: no negative counts",
)
check(
    (ppd["homicides"] >= 0).all(),
    "PPD: no negative homicide counts",
)

# no duplicates in clery for (year, crime_type)
dups = clery.duplicated(subset=["year", "crime_type"])
check(
    dups.sum() == 0,
    f"clery: no duplicate (year, crime_type) pairs (found {dups.sum()})",
)

# no duplicates in ucr/ppd by year
check(
    not ucr.year.duplicated().any(),
    f"PA UCR: no duplicate years (found {ucr.year.duplicated().sum()})",
)
check(
    not ppd.year.duplicated().any(),
    f"PPD: no duplicate years (found {ppd.year.duplicated().sum()})",
)

# no future years (current data should not exceed current year)
this_year = pd.Timestamp.now().year
check(
    clery.year.max() <= this_year,
    f"clery: no future years (max year {clery.year.max()})",
)
check(
    ppd.year.max() <= this_year,
    f"PPD: no future years (max year {ppd.year.max()})",
)


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
if errors:
    print(f"FAILED with {len(errors)} error(s):")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
elif warnings:
    print(f"PASSED with {len(warnings)} warning(s):")
    for w in warnings:
        print(f"  - {w}")
    sys.exit(0)
else:
    print("ALL CHECKS PASSED ✓")
    sys.exit(0)
