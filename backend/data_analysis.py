# backend/data_analysis.py
"""
Comprehensive data analysis and model evaluation visualization suite.
Generates publication-quality PNG charts for the Sri Lanka car price dataset.

Run:
    python data_analysis.py

Outputs (saved to ./analysis_plots/):
    01_price_distribution.png
    02_price_by_brand.png
    03_price_by_year.png
    04_mileage_vs_price.png
    05_fuel_type_analysis.png
    06_gear_type_analysis.png
    07_condition_price_analysis.png
    08_equipment_impact.png
    09_town_price_heatmap.png
    10_correlation_heatmap.png
    11_feature_importance.png
    12_bias_variance_tradeoff.png
    13_learning_curves.png
    14_cross_validation.png
    15_residual_analysis.png
    16_prediction_vs_actual.png
    17_price_segments.png
    18_depreciation_curves.png
"""

import os
import warnings
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
from matplotlib.ticker import FuncFormatter
import seaborn as sns
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.model_selection import train_test_split, cross_val_score, learning_curve, KFold
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.preprocessing import LabelEncoder
import joblib

warnings.filterwarnings('ignore')

# ── Style ────────────────────────────────────────────────────
matplotlib.rcParams.update({
    'figure.facecolor':  '#0F1117',
    'axes.facecolor':    '#1A1D27',
    'axes.edgecolor':    '#2E3250',
    'axes.labelcolor':   '#C8C8D4',
    'axes.titlecolor':   '#FFFFFF',
    'axes.titlesize':    14,
    'axes.titleweight':  'bold',
    'axes.labelsize':    11,
    'axes.grid':         True,
    'grid.color':        '#2E3250',
    'grid.linestyle':    '--',
    'grid.alpha':        0.5,
    'xtick.color':       '#8A8A9A',
    'ytick.color':       '#8A8A9A',
    'xtick.labelsize':   9,
    'ytick.labelsize':   9,
    'legend.facecolor':  '#1A1D27',
    'legend.edgecolor':  '#2E3250',
    'legend.fontsize':   9,
    'text.color':        '#C8C8D4',
    'font.family':       'DejaVu Sans',
    'figure.dpi':        150,
    'savefig.dpi':       300,
    'savefig.facecolor': '#0F1117',
    'savefig.bbox':      'tight',
    'savefig.pad_inches': 0.3,
})

# Palette
GOLD    = '#F4A227'
TEAL    = '#2DD4BF'
CORAL   = '#F87171'
PURPLE  = '#A78BFA'
GREEN   = '#34D399'
BLUE    = '#60A5FA'
ORANGE  = '#FB923C'
PINK    = '#F472B6'

BRAND_COLORS = {
    'TOYOTA':     GOLD,
    'HONDA':      TEAL,
    'SUZUKI':     CORAL,
    'NISSAN':     PURPLE,
    'MITSUBISHI': GREEN,
    'BMW':        BLUE,
    'MERCEDES':   ORANGE,
    'AUDI':       PINK,
}

OUTPUT_DIR = 'analysis_plots'


def setup():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"\n{'='*60}")
    print("  CarLensLK — Data Analysis Suite")
    print(f"{'='*60}\n")


def save(fig, name: str):
    path = os.path.join(OUTPUT_DIR, name)
    fig.savefig(path)
    plt.close(fig)
    print(f"  ✓ {name}")


def lakh_fmt(x, _):
    return f'Rs.{x:.0f}L'


def load_data(csv_path='car_price_dataset.csv') -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df = df.dropna(subset=['Price'])
    df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
    df = df.dropna(subset=['Price'])
    df = df[(df['Price'] > 5) & (df['Price'] < 500)]   # sanity bounds in Lakhs

    if 'YOM' in df.columns:
        df['YOM']     = pd.to_numeric(df['YOM'], errors='coerce')
        df['Car_Age'] = 2026 - df['YOM']

    if 'Millage(KM)' in df.columns:
        df['Millage(KM)'] = pd.to_numeric(df['Millage(KM)'], errors='coerce')

    if 'Engine (cc)' in df.columns:
        df['Engine (cc)'] = pd.to_numeric(df['Engine (cc)'], errors='coerce')

    if 'Brand' in df.columns:
        df['Brand'] = df['Brand'].astype(str).str.upper().str.strip()

    return df


# ═══════════════════════════════════════════════════════════
# 01  Price distribution
# ═══════════════════════════════════════════════════════════
def plot_price_distribution(df):
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle('Price Distribution — Sri Lanka Used Car Market', fontsize=16, fontweight='bold', color='white')

    prices = df['Price'].dropna()

    # Histogram
    ax = axes[0]
    n, bins, patches = ax.hist(prices, bins=60, color=GOLD, edgecolor='#0F1117', linewidth=0.4, alpha=0.85)
    ax.axvline(prices.mean(),   color=TEAL,  linestyle='--', lw=2, label=f'Mean  Rs.{prices.mean():.1f}L')
    ax.axvline(prices.median(), color=CORAL, linestyle='--', lw=2, label=f'Median Rs.{prices.median():.1f}L')
    ax.set_xlabel('Price (LKR Lakhs)')
    ax.set_ylabel('Number of listings')
    ax.set_title('Price Histogram')
    ax.legend()
    ax.xaxis.set_major_formatter(FuncFormatter(lakh_fmt))

    # Box + violin
    ax = axes[1]
    parts = ax.violinplot(prices, positions=[0], widths=0.6, showmedians=True, showextrema=True)
    for pc in parts['bodies']:
        pc.set_facecolor(GOLD)
        pc.set_alpha(0.6)
    parts['cmedians'].set_color(TEAL)
    parts['cmaxes'].set_color(CORAL)
    parts['cmins'].set_color(CORAL)
    parts['cbars'].set_color('#2E3250')
    ax.set_xticks([0])
    ax.set_xticklabels(['All cars'])
    ax.set_ylabel('Price (LKR Lakhs)')
    ax.set_title('Price Distribution (Violin)')
    ax.yaxis.set_major_formatter(FuncFormatter(lakh_fmt))

    # Stats text
    stats = (f"n={len(prices):,}  |  "
             f"Min=Rs.{prices.min():.1f}L  |  "
             f"Max=Rs.{prices.max():.1f}L  |  "
             f"Std=Rs.{prices.std():.1f}L")
    fig.text(0.5, 0.01, stats, ha='center', fontsize=10, color='#8A8A9A')

    save(fig, '01_price_distribution.png')


# ═══════════════════════════════════════════════════════════
# 02  Price by brand
# ═══════════════════════════════════════════════════════════
def plot_price_by_brand(df):
    if 'Brand' not in df.columns:
        return

    top_brands = df['Brand'].value_counts().head(12).index
    brand_df   = df[df['Brand'].isin(top_brands)]
    brand_stats = (brand_df.groupby('Brand')['Price']
                   .agg(['median', 'mean', 'count', 'std'])
                   .sort_values('median', ascending=True))

    fig, axes = plt.subplots(1, 2, figsize=(18, 7))
    fig.suptitle('Price Analysis by Brand', fontsize=16, fontweight='bold', color='white')

    # Horizontal bar — median price
    ax = axes[0]
    colors = [BRAND_COLORS.get(b, GOLD) for b in brand_stats.index]
    bars = ax.barh(brand_stats.index, brand_stats['median'], color=colors, edgecolor='#0F1117', linewidth=0.4)
    for bar, val in zip(bars, brand_stats['median']):
        ax.text(val + 0.5, bar.get_y() + bar.get_height() / 2,
                f'Rs.{val:.1f}L', va='center', fontsize=8.5, color='white')
    ax.set_xlabel('Median Price (LKR Lakhs)')
    ax.set_title('Median Price by Brand')
    ax.xaxis.set_major_formatter(FuncFormatter(lakh_fmt))

    # Box plot
    ax = axes[1]
    brand_data = [brand_df[brand_df['Brand'] == b]['Price'].dropna().values
                  for b in brand_stats.index]
    bp = ax.boxplot(brand_data, vert=False, patch_artist=True,
                    medianprops=dict(color='white', linewidth=2),
                    whiskerprops=dict(color='#8A8A9A'),
                    capprops=dict(color='#8A8A9A'),
                    flierprops=dict(marker='o', markersize=2, alpha=0.4, color=CORAL))
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    ax.set_yticks(range(1, len(brand_stats) + 1))
    ax.set_yticklabels(brand_stats.index)
    ax.set_xlabel('Price (LKR Lakhs)')
    ax.set_title('Price Distribution by Brand')
    ax.xaxis.set_major_formatter(FuncFormatter(lakh_fmt))

    save(fig, '02_price_by_brand.png')


# ═══════════════════════════════════════════════════════════
# 03  Price by year of manufacture
# ═══════════════════════════════════════════════════════════
def plot_price_by_year(df):
    if 'YOM' not in df.columns:
        return

    yearly = (df.groupby('YOM')['Price']
               .agg(['median', 'count'])
               .reset_index()
               .query('count >= 5')
               .sort_values('YOM'))

    fig, axes = plt.subplots(2, 1, figsize=(16, 10))
    fig.suptitle('Price vs Year of Manufacture', fontsize=16, fontweight='bold', color='white')

    # Median price line
    ax = axes[0]
    ax.plot(yearly['YOM'], yearly['median'], color=GOLD, lw=2.5, marker='o', markersize=5)
    ax.fill_between(yearly['YOM'], yearly['median'], alpha=0.15, color=GOLD)
    ax.set_ylabel('Median Price (LKR Lakhs)')
    ax.set_title('Median Price by Year of Manufacture')
    ax.yaxis.set_major_formatter(FuncFormatter(lakh_fmt))

    # Scatter with colour by count
    ax = axes[1]
    sc = ax.scatter(df['YOM'], df['Price'],
                    c=df['YOM'], cmap='plasma',
                    alpha=0.25, s=8, linewidths=0)
    cb = plt.colorbar(sc, ax=ax)
    cb.set_label('Year', color='#C8C8D4')
    cb.ax.yaxis.set_tick_params(color='#8A8A9A')
    ax.set_xlabel('Year of Manufacture')
    ax.set_ylabel('Price (LKR Lakhs)')
    ax.set_title('All Listings — Price vs YOM')
    ax.yaxis.set_major_formatter(FuncFormatter(lakh_fmt))

    save(fig, '03_price_by_year.png')


# ═══════════════════════════════════════════════════════════
# 04  Mileage vs price
# ═══════════════════════════════════════════════════════════
def plot_mileage_vs_price(df):
    if 'Millage(KM)' not in df.columns:
        return

    d = df[['Millage(KM)', 'Price', 'Brand']].dropna()
    d = d[(d['Millage(KM)'] > 0) & (d['Millage(KM)'] < 500_000)]

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle('Mileage vs Price Analysis', fontsize=16, fontweight='bold', color='white')

    # Scatter
    ax = axes[0]
    top5 = d['Brand'].value_counts().head(5).index
    for brand in top5:
        sub = d[d['Brand'] == brand]
        ax.scatter(sub['Millage(KM)'] / 1000, sub['Price'],
                   alpha=0.4, s=10, label=brand,
                   color=BRAND_COLORS.get(brand, GOLD))
    # Trend line
    z = np.polyfit(d['Millage(KM)'], d['Price'], 1)
    p = np.poly1d(z)
    xs = np.linspace(d['Millage(KM)'].min(), d['Millage(KM)'].max(), 200)
    ax.plot(xs / 1000, p(xs), color=CORAL, lw=2, linestyle='--', label='Trend')
    ax.set_xlabel('Mileage (000 km)')
    ax.set_ylabel('Price (LKR Lakhs)')
    ax.set_title('Mileage vs Price by Brand')
    ax.legend(markerscale=2)
    ax.yaxis.set_major_formatter(FuncFormatter(lakh_fmt))

    # Mileage bins bar chart
    ax = axes[1]
    d['Mileage_Band'] = pd.cut(d['Millage(KM)'],
                                bins=[0, 50000, 100000, 150000, 200000, 300000, 500000],
                                labels=['0–50k', '50–100k', '100–150k', '150–200k', '200–300k', '300k+'])
    band_stats = d.groupby('Mileage_Band', observed=True)['Price'].median()
    colors = [GOLD, TEAL, GREEN, ORANGE, CORAL, PURPLE]
    bars = ax.bar(band_stats.index, band_stats.values, color=colors, edgecolor='#0F1117', linewidth=0.4)
    for bar, val in zip(bars, band_stats.values):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.5,
                f'Rs.{val:.1f}L', ha='center', fontsize=9, color='white')
    ax.set_xlabel('Mileage Band')
    ax.set_ylabel('Median Price (LKR Lakhs)')
    ax.set_title('Median Price by Mileage Band')
    ax.yaxis.set_major_formatter(FuncFormatter(lakh_fmt))

    save(fig, '04_mileage_vs_price.png')


# ═══════════════════════════════════════════════════════════
# 05  Fuel type analysis
# ═══════════════════════════════════════════════════════════
def plot_fuel_type(df):
    col = 'Fuel Type'
    if col not in df.columns:
        return

    fuel_counts = df[col].value_counts()
    fuel_price  = df.groupby(col)['Price'].median().reindex(fuel_counts.index)

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle('Fuel Type Analysis', fontsize=16, fontweight='bold', color='white')

    fuel_colors = [GOLD, TEAL, GREEN, CORAL, PURPLE, BLUE][:len(fuel_counts)]

    # Donut
    ax = axes[0]
    wedges, texts, autotexts = ax.pie(fuel_counts.values, labels=fuel_counts.index,
                                       autopct='%1.1f%%', colors=fuel_colors,
                                       wedgeprops=dict(width=0.55, edgecolor='#0F1117', linewidth=1.5),
                                       pctdistance=0.75)
    for t in autotexts:
        t.set_color('white')
        t.set_fontsize(9)
    ax.set_title('Listing Count by Fuel Type')

    # Bar — count
    ax = axes[1]
    bars = ax.bar(fuel_counts.index, fuel_counts.values, color=fuel_colors, edgecolor='#0F1117', linewidth=0.4)
    for bar, val in zip(bars, fuel_counts.values):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 10,
                f'{val:,}', ha='center', fontsize=9, color='white')
    ax.set_ylabel('Number of listings')
    ax.set_title('Count by Fuel Type')
    ax.tick_params(axis='x', rotation=20)

    # Bar — median price
    ax = axes[2]
    bars = ax.bar(fuel_price.index, fuel_price.values, color=fuel_colors, edgecolor='#0F1117', linewidth=0.4)
    for bar, val in zip(bars, fuel_price.values):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.5,
                f'Rs.{val:.1f}L', ha='center', fontsize=9, color='white')
    ax.set_ylabel('Median Price (LKR Lakhs)')
    ax.set_title('Median Price by Fuel Type')
    ax.yaxis.set_major_formatter(FuncFormatter(lakh_fmt))
    ax.tick_params(axis='x', rotation=20)

    save(fig, '05_fuel_type_analysis.png')


# ═══════════════════════════════════════════════════════════
# 06  Gear type analysis
# ═══════════════════════════════════════════════════════════
def plot_gear_type(df):
    col = 'Gear'
    if col not in df.columns:
        return

    gear_counts = df[col].value_counts()
    gear_price  = df.groupby(col)['Price'].agg(['median', 'mean', 'std'])

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('Transmission Type Analysis', fontsize=16, fontweight='bold', color='white')

    gear_colors = [GOLD, TEAL, CORAL, PURPLE][:len(gear_counts)]

    # Pie
    ax = axes[0]
    wedges, texts, autotexts = ax.pie(gear_counts.values, labels=gear_counts.index,
                                       autopct='%1.1f%%', colors=gear_colors,
                                       wedgeprops=dict(width=0.55, edgecolor='#0F1117', linewidth=1.5))
    for t in autotexts:
        t.set_color('white')
    ax.set_title('Listing Share by Gear Type')

    # Grouped bar — median vs mean
    ax = axes[1]
    x = np.arange(len(gear_price))
    w = 0.35
    b1 = ax.bar(x - w / 2, gear_price['median'], w, label='Median', color=GOLD, edgecolor='#0F1117')
    b2 = ax.bar(x + w / 2, gear_price['mean'],   w, label='Mean',   color=TEAL, edgecolor='#0F1117')
    ax.set_xticks(x)
    ax.set_xticklabels(gear_price.index)
    ax.set_ylabel('Price (LKR Lakhs)')
    ax.set_title('Price by Gear Type')
    ax.legend()
    ax.yaxis.set_major_formatter(FuncFormatter(lakh_fmt))

    save(fig, '06_gear_type_analysis.png')


# ═══════════════════════════════════════════════════════════
# 07  Condition price analysis
# ═══════════════════════════════════════════════════════════
def plot_condition(df):
    col = 'Condition'
    if col not in df.columns:
        return

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('Vehicle Condition vs Price', fontsize=16, fontweight='bold', color='white')

    cond_colors = [GOLD, TEAL, GREEN, CORAL]
    cond_order  = df[col].value_counts().index

    # Box plot per condition
    ax = axes[0]
    data   = [df[df[col] == c]['Price'].dropna().values for c in cond_order]
    bp = ax.boxplot(data, patch_artist=True,
                    medianprops=dict(color='white', linewidth=2),
                    whiskerprops=dict(color='#8A8A9A'),
                    capprops=dict(color='#8A8A9A'),
                    flierprops=dict(marker='o', markersize=2, alpha=0.3, color=CORAL))
    for patch, color in zip(bp['boxes'], cond_colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    ax.set_xticklabels(cond_order, rotation=15)
    ax.set_ylabel('Price (LKR Lakhs)')
    ax.set_title('Price Distribution by Condition')
    ax.yaxis.set_major_formatter(FuncFormatter(lakh_fmt))

    # Count bar
    ax = axes[1]
    counts = df[col].value_counts()
    bars = ax.bar(counts.index, counts.values,
                  color=cond_colors[:len(counts)], edgecolor='#0F1117')
    for bar, val in zip(bars, counts.values):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 10,
                f'{val:,}', ha='center', fontsize=9, color='white')
    ax.set_ylabel('Number of listings')
    ax.set_title('Listing Count by Condition')
    ax.tick_params(axis='x', rotation=15)

    save(fig, '07_condition_price_analysis.png')


# ═══════════════════════════════════════════════════════════
# 08  Equipment impact on price
# ═══════════════════════════════════════════════════════════
def plot_equipment_impact(df):
    equipment = ['AIR CONDITION', 'POWER STEERING', 'POWER MIRROR', 'POWER WINDOW']
    equipment = [e for e in equipment if e in df.columns]
    if not equipment:
        return

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Equipment Features — Impact on Price', fontsize=16, fontweight='bold', color='white')
    axes = axes.flatten()

    for ax, feat in zip(axes, equipment):
        col = df[feat].astype(str).str.strip()
        has_it    = df[col.isin(['Available', 'Yes', '1', 1])]['Price'].dropna()
        hasnt_it  = df[~col.isin(['Available', 'Yes', '1', 1])]['Price'].dropna()

        bp = ax.boxplot([has_it, hasnt_it], patch_artist=True,
                        medianprops=dict(color='white', linewidth=2),
                        whiskerprops=dict(color='#8A8A9A'),
                        capprops=dict(color='#8A8A9A'),
                        flierprops=dict(marker='o', markersize=2, alpha=0.3, color=CORAL))
        bp['boxes'][0].set_facecolor(GREEN)
        bp['boxes'][0].set_alpha(0.7)
        bp['boxes'][1].set_facecolor(CORAL)
        bp['boxes'][1].set_alpha(0.7)

        ax.set_xticklabels(['Available', 'Not Available'])
        ax.set_title(feat.title())
        ax.set_ylabel('Price (LKR Lakhs)')
        ax.yaxis.set_major_formatter(FuncFormatter(lakh_fmt))

        diff = has_it.median() - hasnt_it.median()
        sign = '+' if diff >= 0 else ''
        ax.text(0.98, 0.97, f'Δ {sign}Rs.{diff:.1f}L',
                transform=ax.transAxes, ha='right', va='top',
                fontsize=11, color=GREEN if diff > 0 else CORAL,
                bbox=dict(boxstyle='round', facecolor='#1A1D27', edgecolor='#2E3250'))

    save(fig, '08_equipment_impact.png')


# ═══════════════════════════════════════════════════════════
# 09  Town price heatmap (top towns)
# ═══════════════════════════════════════════════════════════
def plot_town_heatmap(df):
    if 'Town' not in df.columns or 'Brand' not in df.columns:
        return

    top_towns  = df['Town'].value_counts().head(10).index
    top_brands = df['Brand'].value_counts().head(8).index
    pivot = (df[df['Town'].isin(top_towns) & df['Brand'].isin(top_brands)]
             .groupby(['Town', 'Brand'])['Price']
             .median()
             .unstack(fill_value=np.nan))

    fig, ax = plt.subplots(figsize=(16, 7))
    fig.suptitle('Median Price Heatmap — Town vs Brand (LKR Lakhs)',
                 fontsize=16, fontweight='bold', color='white')

    im = ax.imshow(pivot.values, cmap='YlOrRd', aspect='auto')
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, rotation=30, ha='right')
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)

    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            val = pivot.values[i, j]
            if not np.isnan(val):
                ax.text(j, i, f'{val:.0f}', ha='center', va='center',
                        fontsize=8, color='black' if val < pivot.values[~np.isnan(pivot.values)].max() * 0.7 else 'white')

    cb = plt.colorbar(im, ax=ax)
    cb.set_label('Median Price (LKR Lakhs)', color='#C8C8D4')

    save(fig, '09_town_price_heatmap.png')


# ═══════════════════════════════════════════════════════════
# 10  Correlation heatmap
# ═══════════════════════════════════════════════════════════
def plot_correlation(df):
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if 'Price' not in num_cols:
        return

    corr = df[num_cols].corr()

    fig, ax = plt.subplots(figsize=(14, 11))
    fig.suptitle('Feature Correlation Heatmap', fontsize=16, fontweight='bold', color='white')

    mask = np.triu(np.ones_like(corr, dtype=bool))
    cmap = sns.diverging_palette(10, 220, as_cmap=True)
    sns.heatmap(corr, mask=mask, cmap=cmap, center=0,
                annot=True, fmt='.2f', annot_kws={'size': 8},
                linewidths=0.5, linecolor='#0F1117',
                ax=ax, cbar_kws={'shrink': 0.8})
    ax.tick_params(axis='both', labelsize=9)

    save(fig, '10_correlation_heatmap.png')


# ═══════════════════════════════════════════════════════════
# 11  Feature importance
# ═══════════════════════════════════════════════════════════
def plot_feature_importance(model, feature_names):
    if not hasattr(model, 'feature_importances_'):
        return

    imp = pd.Series(model.feature_importances_, index=feature_names).sort_values()
    top = imp.tail(20)

    fig, axes = plt.subplots(1, 2, figsize=(18, 8))
    fig.suptitle('Feature Importance Analysis', fontsize=16, fontweight='bold', color='white')

    # Horizontal bar
    ax = axes[0]
    colors = [GOLD if v > top.quantile(0.75) else TEAL if v > top.quantile(0.5) else '#4A4D6A'
              for v in top.values]
    bars = ax.barh(top.index, top.values, color=colors, edgecolor='#0F1117', linewidth=0.3)
    ax.set_xlabel('Importance Score')
    ax.set_title('Top 20 Features by Importance')
    for bar, val in zip(bars, top.values):
        ax.text(val + 0.001, bar.get_y() + bar.get_height() / 2,
                f'{val:.3f}', va='center', fontsize=8, color='white')

    # Cumulative importance
    ax = axes[1]
    all_sorted = imp.sort_values(ascending=False)
    cumulative  = all_sorted.cumsum() / all_sorted.sum()
    ax.plot(range(1, len(cumulative) + 1), cumulative.values * 100, color=GOLD, lw=2.5)
    ax.axhline(90, color=CORAL,  linestyle='--', lw=1.5, label='90%')
    ax.axhline(80, color=PURPLE, linestyle='--', lw=1.5, label='80%')
    ax.fill_between(range(1, len(cumulative) + 1), cumulative.values * 100, alpha=0.1, color=GOLD)
    n90 = (cumulative <= 0.90).sum() + 1
    ax.axvline(n90, color=CORAL, linestyle=':', lw=1.5, label=f'{n90} features → 90%')
    ax.set_xlabel('Number of features')
    ax.set_ylabel('Cumulative importance (%)')
    ax.set_title('Cumulative Feature Importance')
    ax.legend()

    save(fig, '11_feature_importance.png')


# ═══════════════════════════════════════════════════════════
# 12  Bias-variance tradeoff
# ═══════════════════════════════════════════════════════════
def plot_bias_variance(X_train, X_test, y_train, y_test):
    configs = [
        ('Linear Regression',    LinearRegression(), False),
        ('RF depth=3',           RandomForestRegressor(n_estimators=100, max_depth=3,  random_state=42, n_jobs=-1), False),
        ('RF depth=7',           RandomForestRegressor(n_estimators=100, max_depth=7,  random_state=42, n_jobs=-1), False),
        ('RF depth=12',          RandomForestRegressor(n_estimators=200, max_depth=12, random_state=42, n_jobs=-1), False),
        ('RF depth=20 ★',        RandomForestRegressor(n_estimators=300, max_depth=20, min_samples_split=5,
                                                       min_samples_leaf=2, max_features='sqrt',
                                                       random_state=42, n_jobs=-1), True),
        ('RF depth=30',          RandomForestRegressor(n_estimators=300, max_depth=30, random_state=42, n_jobs=-1), False),
        ('RF depth=None (full)', RandomForestRegressor(n_estimators=200, max_depth=None, random_state=42, n_jobs=-1), False),
    ]

    names, trains, tests, gaps, optimal_flags = [], [], [], [], []
    print("  Running bias-variance analysis...")
    for name, model, is_opt in configs:
        model.fit(X_train, y_train)
        tr = r2_score(y_train, model.predict(X_train))
        te = r2_score(y_test,  model.predict(X_test))
        names.append(name)
        trains.append(tr)
        tests.append(te)
        gaps.append(tr - te)
        optimal_flags.append(is_opt)
        print(f"    {name:<25}  Train={tr:.4f}  Test={te:.4f}  Gap={tr-te:.4f}")

    x  = np.arange(len(names))
    w  = 0.32

    fig, axes = plt.subplots(1, 2, figsize=(18, 7))
    fig.suptitle('Bias-Variance Tradeoff Analysis', fontsize=16, fontweight='bold', color='white')

    # Grouped bar
    ax = axes[0]
    bar_colors_tr = [GOLD   if f else '#4A4D6A' for f in optimal_flags]
    bar_colors_te = [GREEN  if f else TEAL      for f in optimal_flags]
    b1 = ax.bar(x - w / 2, trains, w, label='Train R²', color=bar_colors_tr, edgecolor='#0F1117')
    b2 = ax.bar(x + w / 2, tests,  w, label='Test R²',  color=bar_colors_te, edgecolor='#0F1117')
    for bar, val in zip(list(b1) + list(b2), trains + tests):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.003,
                f'{val:.3f}', ha='center', fontsize=7.5, color='white', rotation=90)
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=20, ha='right', fontsize=8.5)
    ax.set_ylabel('R² Score')
    ax.set_title('Train vs Test R² by Model Complexity')
    ax.legend()
    ax.set_ylim(0.3, 1.08)
    # Annotate optimal
    opt_i = optimal_flags.index(True)
    ax.annotate('Optimal', xy=(opt_i, tests[opt_i] + 0.03),
                xytext=(opt_i, tests[opt_i] + 0.09),
                arrowprops=dict(arrowstyle='->', color=GOLD, lw=2),
                ha='center', color=GOLD, fontsize=10, fontweight='bold')

    # Gap line chart
    ax = axes[1]
    ax.plot(names, gaps, color=CORAL, lw=2.5, marker='o', markersize=7)
    ax.fill_between(names, gaps, alpha=0.15, color=CORAL)
    ax.axhline(0.05,  color=GREEN,  linestyle='--', lw=1.5, label='5% gap (good)')
    ax.axhline(0.15,  color=GOLD,   linestyle='--', lw=1.5, label='15% gap (warning)')
    ax.axhline(0.25,  color=CORAL,  linestyle='--', lw=1.5, label='25% gap (overfit)')
    ax.scatter([opt_i], [gaps[opt_i]], color=GOLD, s=120, zorder=5, label='Optimal model')
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=20, ha='right', fontsize=8.5)
    ax.set_ylabel('Train − Test Gap')
    ax.set_title('Overfitting Gap by Model Complexity')
    ax.legend(fontsize=8)

    save(fig, '12_bias_variance_tradeoff.png')


# ═══════════════════════════════════════════════════════════
# 13  Learning curves
# ═══════════════════════════════════════════════════════════
def plot_learning_curves(model, X, y):
    print("  Running learning curves (this takes a few minutes)...")
    sizes, tr_scores, val_scores = learning_curve(
        model, X, y,
        cv=5,
        train_sizes=np.linspace(0.1, 1.0, 10),
        scoring='r2',
        n_jobs=-1,
    )

    tr_mean  = tr_scores.mean(axis=1)
    tr_std   = tr_scores.std(axis=1)
    val_mean = val_scores.mean(axis=1)
    val_std  = val_scores.std(axis=1)

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle('Learning Curves — Model Generalisation', fontsize=16, fontweight='bold', color='white')

    # R² curves
    ax = axes[0]
    ax.plot(sizes, tr_mean,  color=GOLD,  lw=2.5, label='Train R²', marker='o', markersize=5)
    ax.plot(sizes, val_mean, color=TEAL,  lw=2.5, label='Val R²',   marker='s', markersize=5)
    ax.fill_between(sizes, tr_mean  - tr_std,  tr_mean  + tr_std,  alpha=0.15, color=GOLD)
    ax.fill_between(sizes, val_mean - val_std, val_mean + val_std, alpha=0.15, color=TEAL)
    ax.set_xlabel('Training set size')
    ax.set_ylabel('R² Score')
    ax.set_title('R² vs Training Size')
    ax.legend()

    # Gap curve
    ax = axes[1]
    gap = tr_mean - val_mean
    ax.plot(sizes, gap, color=CORAL, lw=2.5, marker='D', markersize=5)
    ax.fill_between(sizes, 0, gap, alpha=0.15, color=CORAL)
    ax.axhline(0.05, color=GREEN, linestyle='--', lw=1.5, label='5% threshold')
    ax.set_xlabel('Training set size')
    ax.set_ylabel('Train − Val gap')
    ax.set_title('Overfitting Gap vs Training Size')
    ax.legend()

    save(fig, '13_learning_curves.png')


# ═══════════════════════════════════════════════════════════
# 14  Cross-validation
# ═══════════════════════════════════════════════════════════
def plot_cross_validation(model, X, y):
    print("  Running 10-fold cross-validation...")
    kf = KFold(n_splits=10, shuffle=True, random_state=42)
    scores = cross_val_score(model, X, y, cv=kf, scoring='r2', n_jobs=-1)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('10-Fold Cross-Validation Results', fontsize=16, fontweight='bold', color='white')

    # Bar per fold
    ax = axes[0]
    fold_colors = [GREEN if s > scores.mean() else CORAL for s in scores]
    bars = ax.bar(range(1, 11), scores, color=fold_colors, edgecolor='#0F1117', linewidth=0.4)
    ax.axhline(scores.mean(), color=GOLD, linestyle='--', lw=2, label=f'Mean={scores.mean():.4f}')
    ax.fill_between(range(1, 11),
                    scores.mean() - scores.std(),
                    scores.mean() + scores.std(),
                    alpha=0.15, color=GOLD, label=f'±1σ={scores.std():.4f}')
    for bar, val in zip(bars, scores):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.001,
                f'{val:.3f}', ha='center', fontsize=8.5, color='white')
    ax.set_xlabel('Fold')
    ax.set_ylabel('R² Score')
    ax.set_title('R² per Fold')
    ax.legend()
    ax.set_ylim(max(0, scores.min() - 0.05), min(1.02, scores.max() + 0.05))

    # Distribution
    ax = axes[1]
    ax.hist(scores, bins=8, color=GOLD, edgecolor='#0F1117', linewidth=0.4, alpha=0.8)
    ax.axvline(scores.mean(), color=TEAL,  linestyle='--', lw=2, label=f'Mean={scores.mean():.4f}')
    ax.axvline(scores.mean() - 1.96 * scores.std(), color=CORAL, linestyle=':', lw=1.5, label='95% CI')
    ax.axvline(scores.mean() + 1.96 * scores.std(), color=CORAL, linestyle=':', lw=1.5)
    ax.set_xlabel('R² Score')
    ax.set_ylabel('Frequency')
    ax.set_title('Score Distribution across Folds')
    ax.legend()

    ci_lo = scores.mean() - 1.96 * scores.std()
    ci_hi = scores.mean() + 1.96 * scores.std()
    fig.text(0.5, 0.01,
             f'Mean={scores.mean():.4f}  Std={scores.std():.4f}  '
             f'95% CI=[{ci_lo:.4f}, {ci_hi:.4f}]',
             ha='center', fontsize=10, color='#8A8A9A')

    save(fig, '14_cross_validation.png')


# ═══════════════════════════════════════════════════════════
# 15  Residual analysis
# ═══════════════════════════════════════════════════════════
def plot_residuals(model, X_test, y_test):
    y_pred = model.predict(X_test)
    resid  = y_test - y_pred

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Residual Analysis — Model Error Diagnostics', fontsize=16, fontweight='bold', color='white')

    # Residuals vs predicted
    ax = axes[0, 0]
    ax.scatter(y_pred, resid, alpha=0.3, s=8, color=TEAL)
    ax.axhline(0, color=CORAL, linestyle='--', lw=2)
    ax.set_xlabel('Predicted Price (LKR Lakhs)')
    ax.set_ylabel('Residual (Actual − Predicted)')
    ax.set_title('Residuals vs Predicted Values')
    ax.xaxis.set_major_formatter(FuncFormatter(lakh_fmt))
    ax.yaxis.set_major_formatter(FuncFormatter(lakh_fmt))

    # Residual histogram
    ax = axes[0, 1]
    ax.hist(resid, bins=60, color=GOLD, edgecolor='#0F1117', linewidth=0.3, alpha=0.85)
    ax.axvline(0,           color=CORAL, linestyle='--', lw=2, label='Zero error')
    ax.axvline(resid.mean(), color=TEAL,  linestyle='--', lw=2, label=f'Mean={resid.mean():.2f}L')
    ax.set_xlabel('Residual (LKR Lakhs)')
    ax.set_ylabel('Count')
    ax.set_title('Residual Distribution')
    ax.legend()
    ax.xaxis.set_major_formatter(FuncFormatter(lakh_fmt))

    # Absolute error vs actual
    ax = axes[1, 0]
    abs_err = np.abs(resid)
    sc = ax.scatter(y_test, abs_err, alpha=0.25, s=8, c=abs_err, cmap='plasma')
    plt.colorbar(sc, ax=ax).set_label('Abs Error', color='#C8C8D4')
    ax.set_xlabel('Actual Price (LKR Lakhs)')
    ax.set_ylabel('Absolute Error (LKR Lakhs)')
    ax.set_title('Absolute Error vs Actual Price')
    ax.xaxis.set_major_formatter(FuncFormatter(lakh_fmt))
    ax.yaxis.set_major_formatter(FuncFormatter(lakh_fmt))

    # Cumulative error distribution
    ax = axes[1, 1]
    sorted_abs = np.sort(abs_err)
    cumulative  = np.arange(1, len(sorted_abs) + 1) / len(sorted_abs)
    ax.plot(sorted_abs, cumulative * 100, color=GOLD, lw=2.5)
    for pct_err in [5, 10, 20]:
        n = (abs_err <= pct_err).mean() * 100
        ax.axvline(pct_err, color=CORAL, linestyle='--', lw=1, label=f'±Rs.{pct_err}L → {n:.0f}%')
    ax.set_xlabel('Absolute Error (LKR Lakhs)')
    ax.set_ylabel('Cumulative % of predictions')
    ax.set_title('Cumulative Error Distribution')
    ax.legend(fontsize=8)
    ax.xaxis.set_major_formatter(FuncFormatter(lakh_fmt))

    save(fig, '15_residual_analysis.png')


# ═══════════════════════════════════════════════════════════
# 16  Prediction vs actual
# ═══════════════════════════════════════════════════════════
def plot_prediction_vs_actual(model, X_test, y_test):
    y_pred = model.predict(X_test)
    r2  = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    fig.suptitle('Predicted vs Actual Price', fontsize=16, fontweight='bold', color='white')

    # Scatter
    ax = axes[0]
    ax.scatter(y_test, y_pred, alpha=0.3, s=8, color=TEAL)
    mn, mx = min(y_test.min(), y_pred.min()), max(y_test.max(), y_pred.max())
    ax.plot([mn, mx], [mn, mx], color=GOLD, lw=2, linestyle='--', label='Perfect prediction')
    ax.set_xlabel('Actual Price (LKR Lakhs)')
    ax.set_ylabel('Predicted Price (LKR Lakhs)')
    ax.set_title(f'Predicted vs Actual  (R²={r2:.4f})')
    ax.legend()
    ax.xaxis.set_major_formatter(FuncFormatter(lakh_fmt))
    ax.yaxis.set_major_formatter(FuncFormatter(lakh_fmt))
    ax.text(0.05, 0.92,
            f'R² = {r2:.4f}\nMAE = Rs.{mae:.2f}L\nRMSE = Rs.{rmse:.2f}L',
            transform=ax.transAxes, fontsize=10, color='white',
            bbox=dict(boxstyle='round', facecolor='#1A1D27', edgecolor=GOLD, alpha=0.8))

    # Error heatmap by price range
    ax = axes[1]
    bins = pd.cut(y_test, bins=10)
    bin_mae = pd.Series(np.abs(y_test - y_pred)).groupby(bins).mean()
    colors = plt.cm.YlOrRd(np.linspace(0.2, 0.9, len(bin_mae)))
    bars = ax.bar(range(len(bin_mae)), bin_mae.values, color=colors, edgecolor='#0F1117')
    ax.set_xticks(range(len(bin_mae)))
    ax.set_xticklabels([f'Rs.{b.left:.0f}–\n{b.right:.0f}L' for b in bin_mae.index],
                       rotation=30, fontsize=7.5)
    ax.set_ylabel('Mean Absolute Error (LKR Lakhs)')
    ax.set_title('Prediction Error by Price Range')

    save(fig, '16_prediction_vs_actual.png')


# ═══════════════════════════════════════════════════════════
# 17  Price segments
# ═══════════════════════════════════════════════════════════
def plot_price_segments(df):
    bins   = [0, 25, 50, 100, 200, 500]
    labels = ['Budget\n(<Rs.25L)', 'Economy\n(25–50L)', 'Mid-range\n(50–100L)',
              'Premium\n(100–200L)', 'Luxury\n(200L+)']
    df['Segment'] = pd.cut(df['Price'], bins=bins, labels=labels)

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Market Segment Analysis', fontsize=16, fontweight='bold', color='white')
    seg_colors = [GREEN, TEAL, GOLD, ORANGE, PURPLE]

    seg_counts = df['Segment'].value_counts().reindex(labels)

    # Donut
    ax = axes[0, 0]
    wedges, texts, autotexts = ax.pie(seg_counts.values, labels=labels,
                                       autopct='%1.1f%%', colors=seg_colors,
                                       wedgeprops=dict(width=0.55, edgecolor='#0F1117', linewidth=1.5))
    for t in autotexts:
        t.set_color('white')
        t.set_fontsize(9)
    ax.set_title('Market Share by Segment')

    # Count bar
    ax = axes[0, 1]
    bars = ax.bar(labels, seg_counts.values, color=seg_colors, edgecolor='#0F1117')
    for bar, val in zip(bars, seg_counts.values):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 10,
                f'{val:,}', ha='center', fontsize=9, color='white')
    ax.set_ylabel('Number of listings')
    ax.set_title('Listing Count by Segment')

    # Top brands per segment
    ax = axes[1, 0]
    if 'Brand' in df.columns:
        seg_brand = (df.groupby(['Segment', 'Brand'])
                     .size()
                     .reset_index(name='count'))
        top_per_seg = (seg_brand.groupby('Segment', observed=True)
                       .apply(lambda x: x.nlargest(3, 'count'))
                       .reset_index(drop=True))
        for i, (seg, color) in enumerate(zip(labels, seg_colors)):
            sub = top_per_seg[top_per_seg['Segment'] == seg]
            for j, (_, row) in enumerate(sub.iterrows()):
                ax.barh(i * 4 + j, row['count'], color=color, alpha=0.7 - j * 0.15,
                        edgecolor='#0F1117', linewidth=0.3)
                ax.text(row['count'] + 1, i * 4 + j, row['Brand'],
                        va='center', fontsize=7.5, color='white')
        ax.set_yticks([i * 4 + 1 for i in range(len(labels))])
        ax.set_yticklabels(labels, fontsize=8)
        ax.set_xlabel('Number of listings')
        ax.set_title('Top Brands per Segment')

    # Year distribution per segment
    ax = axes[1, 1]
    if 'YOM' in df.columns:
        for seg, color in zip(labels, seg_colors):
            sub = df[df['Segment'] == seg]['YOM'].dropna()
            if len(sub) > 10:
                sub.hist(bins=15, ax=ax, color=color, alpha=0.5,
                         label=seg.replace('\n', ' '), density=True)
        ax.set_xlabel('Year of Manufacture')
        ax.set_ylabel('Density')
        ax.set_title('YOM Distribution by Segment')
        ax.legend(fontsize=7.5)

    save(fig, '17_price_segments.png')


# ═══════════════════════════════════════════════════════════
# 18  Depreciation curves
# ═══════════════════════════════════════════════════════════
def plot_depreciation(df):
    if 'YOM' not in df.columns or 'Brand' not in df.columns:
        return

    df2 = df.copy()
    df2['Car_Age'] = 2026 - df2['YOM']
    df2 = df2[(df2['Car_Age'] >= 0) & (df2['Car_Age'] <= 25)]

    top_brands = df2['Brand'].value_counts().head(6).index
    colors = [GOLD, TEAL, CORAL, PURPLE, GREEN, BLUE]

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    fig.suptitle('Depreciation Curves by Brand', fontsize=16, fontweight='bold', color='white')

    # Median price by age per brand
    ax = axes[0]
    for brand, color in zip(top_brands, colors):
        sub = (df2[df2['Brand'] == brand]
               .groupby('Car_Age')['Price']
               .median()
               .reset_index())
        if len(sub) >= 5:
            ax.plot(sub['Car_Age'], sub['Price'], color=color, lw=2,
                    marker='o', markersize=4, label=brand)
    ax.set_xlabel('Car Age (years)')
    ax.set_ylabel('Median Price (LKR Lakhs)')
    ax.set_title('Depreciation by Brand (Median)')
    ax.legend()
    ax.yaxis.set_major_formatter(FuncFormatter(lakh_fmt))

    # Normalised (% of new price)
    ax = axes[1]
    for brand, color in zip(top_brands, colors):
        sub = (df2[df2['Brand'] == brand]
               .groupby('Car_Age')['Price']
               .median()
               .reset_index())
        if len(sub) >= 5 and sub.iloc[0]['Price'] > 0:
            sub['pct'] = sub['Price'] / sub.iloc[0]['Price'] * 100
            ax.plot(sub['Car_Age'], sub['pct'], color=color, lw=2,
                    marker='o', markersize=4, label=brand)
    ax.axhline(50, color='#4A4D6A', linestyle='--', lw=1.5, label='50% value retained')
    ax.set_xlabel('Car Age (years)')
    ax.set_ylabel('Value retained (%)')
    ax.set_title('Depreciation — % of Original Value')
    ax.legend(fontsize=8)

    save(fig, '18_depreciation_curves.png')


# ═══════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════
def main():
    setup()

    # ── Load data ──────────────────────────────────────────
    csv_path = 'car_price_dataset.csv'
    if not os.path.exists(csv_path):
        print(f"ERROR: {csv_path} not found. Run from your backend folder.")
        return

    print("Loading data...")
    df = load_data(csv_path)
    print(f"  {len(df):,} records loaded\n")

    # ── EDA plots ──────────────────────────────────────────
    print("Generating EDA charts...")
    plot_price_distribution(df)
    plot_price_by_brand(df)
    plot_price_by_year(df)
    plot_mileage_vs_price(df)
    plot_fuel_type(df)
    plot_gear_type(df)
    plot_condition(df)
    plot_equipment_impact(df)
    plot_town_heatmap(df)
    plot_correlation(df)
    plot_price_segments(df)
    plot_depreciation(df)

    # ── ML analysis ────────────────────────────────────────
    print("\nBuilding ML features for model analysis...")
    try:
        from preprocessing import preprocess_data
        X, y, _, _, _ = preprocess_data(csv_path)
    except Exception:
        # Minimal fallback preprocessing
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        num_cols = [c for c in num_cols if c != 'Price']
        X = df[num_cols].fillna(df[num_cols].median())
        y = df['Price'].values

    print(f"  Features: {X.shape[1]}  |  Samples: {len(y)}\n")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42)

    # Best model for analysis
    print("Training optimal model for analysis plots...")
    best_model = RandomForestRegressor(
        n_estimators=300, max_depth=20, min_samples_split=5,
        min_samples_leaf=2, max_features='sqrt',
        random_state=42, n_jobs=-1)
    best_model.fit(X_train, y_train)

    print("\nGenerating model analysis charts...")
    plot_feature_importance(best_model, list(X.columns))
    plot_bias_variance(X_train, X_test, y_train, y_test)
    plot_learning_curves(best_model, X, y)
    plot_cross_validation(best_model, X, y)
    plot_residuals(best_model, X_test, pd.Series(y_test))
    plot_prediction_vs_actual(best_model, X_test, pd.Series(y_test))

    print(f"\n{'='*60}")
    print(f"  Done! 18 charts saved to ./{OUTPUT_DIR}/")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
