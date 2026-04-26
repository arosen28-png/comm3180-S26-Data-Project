"""Generate chart PNGs for embedding in README/FINDINGS.

Run from repo root: python build_charts.py
Output: docs/img/*.png
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# --- config ---
DATA = Path("data")
OUT = Path("docs/img")
OUT.mkdir(parents=True, exist_ok=True)

ACCENT = "#c44536"
DARK = "#1a1a2e"
MUTED = "#5c6b73"
CONTEXT = "#82a0aa"
GREEN = "#3a7d44"
GOLD = "#b58a2e"

plt.rcParams.update({
    "font.family": "sans-serif",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.edgecolor": "#cccccc",
    "axes.labelcolor": MUTED,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "axes.titleweight": "bold",
    "axes.titlecolor": DARK,
    "axes.titlesize": 13,
    "axes.titlepad": 14,
    "figure.dpi": 110,
})


def save(fig, name):
    path = OUT / name
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"wrote {path}")


# --- load ---
clery = pd.read_csv(DATA / "penn_clery_annual.csv")
ucr = pd.read_csv(DATA / "penn_pa_ucr.csv")
ppd = pd.read_csv(DATA / "ppd_homicides_citywide.csv")


# --- 1. Citywide homicides ---
fig, ax = plt.subplots(figsize=(9, 4.5))
ax.plot(ppd.year, ppd.homicides, marker="o", color=ACCENT, linewidth=2.5, markersize=6)
ax.set_title("Philadelphia citywide homicides, 2007–2025")
ax.set_ylabel("Homicides")
ax.set_xlabel("Year")
ax.grid(axis="y", alpha=0.3)

# annotate peak
peak = ppd.loc[ppd.homicides.idxmax()]
ax.annotate(
    f"Peak: {int(peak.homicides)} ({int(peak.year)})",
    xy=(peak.year, peak.homicides),
    xytext=(peak.year - 7, peak.homicides - 60),
    arrowprops=dict(arrowstyle="->", color=DARK, lw=1),
    fontsize=10, color=DARK, fontweight="bold",
)
# annotate latest
latest = ppd.iloc[-1]
ax.annotate(
    f"{int(latest.homicides)} (YTD)",
    xy=(latest.year, latest.homicides),
    xytext=(latest.year - 3, latest.homicides - 80),
    arrowprops=dict(arrowstyle="->", color=GREEN, lw=1),
    fontsize=10, color=GREEN, fontweight="bold",
)
save(fig, "01_citywide_homicides.png")


# --- 2. Patrol Zone violent crime ---
violent_cats = ["robbery", "aggravated_assault", "rape", "domestic_violence"]
labels_map = {
    "robbery": "Robbery",
    "aggravated_assault": "Aggravated Assault",
    "rape": "Rape",
    "domestic_violence": "Domestic Violence",
}
violent = (
    clery[clery.crime_type.isin(violent_cats)]
    .pivot_table(index="year", columns="crime_type", values="count", aggfunc="sum")
    [violent_cats]
    .fillna(0)
)
colors = [ACCENT, DARK, CONTEXT, GOLD]

fig, ax = plt.subplots(figsize=(9, 4.5))
for cat, color in zip(violent_cats, colors):
    ax.plot(violent.index, violent[cat], marker="o", linewidth=2,
            color=color, label=labels_map[cat], markersize=5)
ax.set_title("Penn Patrol Zone — Violent crime, 2017–2024")
ax.set_ylabel("Reported incidents")
ax.set_xlabel("Year")
ax.legend(loc="upper left", frameon=False, fontsize=9)
ax.grid(axis="y", alpha=0.3)
save(fig, "02_patrol_zone_violent.png")


# --- 3. Motor vehicle theft spike ---
mvt = clery[clery.crime_type == "motor_vehicle_theft"].sort_values("year")
fig, ax = plt.subplots(figsize=(9, 4.5))
bars = ax.bar(mvt.year.astype(str), mvt["count"], color=ACCENT)
ax.set_title("Penn Patrol Zone — Motor vehicle theft (the Hyundai/Kia trend)")
ax.set_ylabel("MVT incidents")
ax.set_xlabel("Year")
ax.grid(axis="y", alpha=0.3)
for bar, val in zip(bars, mvt["count"]):
    ax.text(bar.get_x() + bar.get_width() / 2, val + 4, str(int(val)),
            ha="center", fontsize=10, color=DARK)
save(fig, "03_mvt_spike.png")


# --- 4. PA UCR Part 1 + FTE ---
fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
axes[0].plot(ucr.year, ucr.total_part1, marker="o", color=ACCENT, linewidth=2.5, markersize=6)
axes[0].set_title("PA UCR — Total Part 1 offenses")
axes[0].set_ylabel("Offenses")
axes[0].set_xlabel("Year")
axes[0].grid(axis="y", alpha=0.3)
for x, y in zip(ucr.year, ucr.total_part1):
    axes[0].text(x, y + 30, str(int(y)), ha="center", fontsize=9, color=DARK)

axes[1].plot(ucr.year, ucr.fte_population, marker="s", color=MUTED, linewidth=2.5, markersize=6)
axes[1].set_title("PA UCR — FTE population (rate denominator)")
axes[1].set_ylabel("FTE")
axes[1].set_xlabel("Year")
axes[1].grid(axis="y", alpha=0.3)
plt.tight_layout()
save(fig, "04_pa_ucr_trend.png")


# --- 5. Sex offenses & hate crimes (small-N) ---
rape = clery[clery.crime_type == "rape"].sort_values("year")
hate = clery[clery.crime_type == "hate_crimes_total"].sort_values("year")

fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
axes[0].bar(rape.year.astype(str), rape["count"], color=ACCENT)
axes[0].set_title("Rape (Patrol Zone) — small-N, year-to-year volatile")
axes[0].set_ylabel("Reported incidents")
axes[0].grid(axis="y", alpha=0.3)
for x, y in zip(rape.year.astype(str), rape["count"]):
    axes[0].text(x, y + 0.2, str(int(y)), ha="center", fontsize=10, color=DARK)

axes[1].bar(hate.year.astype(str), hate["count"], color=DARK)
axes[1].set_title("Hate Crimes (Patrol Zone) — totals only")
axes[1].set_ylabel("Reported incidents")
axes[1].grid(axis="y", alpha=0.3)
for x, y in zip(hate.year.astype(str), hate["count"]):
    axes[1].text(x, y + 0.1, str(int(y)), ha="center", fontsize=10, color=DARK)
plt.tight_layout()
save(fig, "05_small_n_categories.png")


# --- 6. Liquor disciplinary (presence proxy) ---
liquor = clery[clery.crime_type == "liquor_disciplinary"].sort_values("year")
fig, ax = plt.subplots(figsize=(9, 4.5))
bars = ax.bar(liquor.year.astype(str), liquor["count"], color=DARK)
ax.set_title("Liquor disciplinary referrals — proxy for campus presence")
ax.set_ylabel("Referrals")
ax.set_xlabel("Year")
ax.grid(axis="y", alpha=0.3)
for bar, val in zip(bars, liquor["count"]):
    ax.text(bar.get_x() + bar.get_width() / 2, val + 8, str(int(val)),
            ha="center", fontsize=10, color=DARK)
save(fig, "06_liquor_disciplinary.png")

print("\nAll charts written to docs/img/")
