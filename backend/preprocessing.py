import os
import sys
import argparse
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Tuple
from fetch_economic_data import EconomicDataFetcher
# -----------------------------
# Core preprocessing functions
# -----------------------------

def load_and_clean_data(filepath: str) -> pd.DataFrame:
    """Load CSV, remove duplicates, and drop rows with missing target (Price)."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"CSV not found at: {filepath}\n"
            "Tips:\n"
            "  - If the CSV is next to this file, call preprocess_data('car_price_dataset.csv')\n"
            "  - If it’s in a subfolder, use a relative path like 'data/car_price_dataset.csv'\n"
            "  - Or use an absolute path (Windows: r'C:\\path\\to\\file.csv' or 'C:/path/to/file.csv')"
        )
    df = pd.read_csv(filepath)

    # Remove duplicates
    before = df.shape[0]
    df = df.drop_duplicates()
    removed = before - df.shape[0]

    # Drop rows with missing prices
    df = df.dropna(subset=['Price'])

    print(f"[load_and_clean_data] Removed duplicates: {removed}")
    print(f"[load_and_clean_data] Dataset shape after cleaning: {df.shape}")
    return df


def feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    """Create new features specific to the Sri Lankan used-car market."""
    # 1. Car Age (critical feature)
    current_year = 2025
    # df['Car_Age'] = current_year - df['YOM']
    df['Car_Age'] = datetime.now().year - df['YOM']

    # 2. Mileage per Year
    df['Mileage_Per_Year'] = df['Millage(KM)'] / (df['Car_Age'] + 1)  # +1 to avoid division by zero

    # 3. Convert equipment features to binary (create if missing)
    equipment_cols = ['AIR CONDITION', 'POWER STEERING', 'POWER MIRROR', 'POWER WINDOW']
    for col in equipment_cols:
        if col not in df.columns:
            df[col] = 0
        else:
            df[col] = df[col].map({'Available': 1, 'Not_Available': 0}).fillna(0)

    # 4. Total Equipment Score
    df['Equipment_Score'] = df[equipment_cols].sum(axis=1)

    # 5. Brand Popularity (frequency encoding)
    brand_counts = df['Brand'].value_counts()
    df['Brand_Popularity'] = df['Brand'].map(brand_counts).fillna(0)

    # 6. Luxury Brand Flag
    luxury_brands = ['BMW', 'MERCEDES-BENZ', 'AUDI', 'LEXUS', 'LAND ROVER', 'PORSCHE']
    df['Is_Luxury'] = df['Brand'].isin(luxury_brands).astype(int)

    # 7. Popular Brand Flag
    popular_brands = ['TOYOTA', 'HONDA', 'SUZUKI']
    df['Is_Popular_Brand'] = df['Brand'].isin(popular_brands).astype(int)

    # 8. Import Era flag
    df['Post_Import_Restriction'] = (df['YOM'] >= 2020).astype(int)

    # 9. Engine Size Category
    df['Engine_Category'] = pd.cut(
        df['Engine (cc)'],
        bins=[0, 1000, 1500, 2000, 5000],
        labels=['Small', 'Medium', 'Large', 'Very_Large']
    )

    return df


def encode_categorical(df: pd.DataFrame):
    """Encode categorical variables and return (df, le_brand, le_model, le_town)."""
    from sklearn.preprocessing import LabelEncoder

    # Ensure required columns exist
    for col in ['Brand', 'Model', 'Town']:
        if col not in df.columns:
            df[col] = 'UNKNOWN'
        df[col] = df[col].astype(str)

    le_brand = LabelEncoder()
    le_model = LabelEncoder()
    le_town = LabelEncoder()

    df['Brand_Encoded'] = le_brand.fit_transform(df['Brand'])
    df['Model_Encoded'] = le_model.fit_transform(df['Model'])
    df['Town_Encoded'] = le_town.fit_transform(df['Town'])

    # One-hot encode smaller categoricals if present
    small_cats = ['Gear', 'Fuel Type', 'Leasing', 'Condition', 'Engine_Category']
    present = [c for c in small_cats if c in df.columns]
    if present:
        df = pd.get_dummies(df, columns=present, drop_first=True)

    return df, le_brand, le_model, le_town


def handle_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """Cap mileage at 99th percentile, remove cars older than 50 years, IQR‑filter prices."""
    # Cap mileage
    if 'Millage(KM)' in df.columns:
        p99 = df['Millage(KM)'].quantile(0.99)
        df['Millage(KM)'] = df['Millage(KM)'].clip(upper=p99)
        print(f"[handle_outliers] Capped mileage at 99th percentile: {p99:.0f}")

    # Remove very old cars
    if 'Car_Age' in df.columns:
        before = df.shape[0]
        df = df[df['Car_Age'] <= 50]
        print(f"[handle_outliers] Removed very old cars: {before - df.shape[0]}")

    # IQR filter for Price
    Q1, Q3 = df['Price'].quantile(0.25), df['Price'].quantile(0.75)
    IQR = Q3 - Q1
    lower, upper = Q1 - 3 * IQR, Q3 + 3 * IQR
    before = df.shape[0]
    df = df[(df['Price'] >= lower) & (df['Price'] <= upper)]
    print(f"[handle_outliers] Removed price outliers: {before - df.shape[0]}")
    return df


def prepare_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """Build X and y; include dynamic one-hot columns if present."""
    feature_cols = [
        'YOM', 'Engine (cc)', 'Millage(KM)', 'Car_Age', 'Mileage_Per_Year',
        'AIR CONDITION', 'POWER STEERING', 'POWER MIRROR', 'POWER WINDOW',
        'Equipment_Score', 'Brand_Popularity', 'Is_Luxury', 'Is_Popular_Brand',
        'Post_Import_Restriction', 'Brand_Encoded', 'Model_Encoded', 'Town_Encoded'
    ]

    # Add one‑hot columns created by get_dummies
    encoded_prefixes = ('Gear_', 'Fuel Type_', 'Leasing_', 'Condition_', 'Engine_Category_')
    feature_cols.extend([c for c in df.columns if c.startswith(encoded_prefixes)])

    # Create any missing features as zero columns to stabilize schema
    for col in feature_cols:
        if col not in df.columns:
            df[col] = 0

    X = df[feature_cols]
    y = df['Price']
    return X, y


def preprocess_data(filepath: str):
    """
    Full pipeline:
      CSV -> clean -> engineer -> outliers -> encode -> build X,y
    Returns: X, y, le_brand, le_model, le_town
    """
    # Resolve relative paths to absolute for reliability
    if not os.path.isabs(filepath):
        here = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(here, filepath)

    df = load_and_clean_data(filepath)
    df = feature_engineering(df)
    df = handle_outliers(df)
    df, le_brand, le_model, le_town = encode_categorical(df)
    X, y = prepare_features(df)
    return X, y, le_brand, le_model, le_town



# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(description="Run preprocessing on a car price CSV.")
#     parser.add_argument(
#         "--csv",
#         type=str,
#         default="car_price_dataset.csv",
#         help="Path to the CSV (relative or absolute). Default: car_price_dataset.csv"
#     )
#     args = parser.parse_args()

#     try:
#         X, y, le_brand, le_model, le_town = preprocess_data(args.csv)
#         print(f"[main] X shape: {X.shape} | y length: {len(y)} | Features: {X.shape[1]}")
#     except FileNotFoundError as e:
#         print(f"[ERROR] {e}")
#         sys.exit(1)
#     except Exception as e:
#         print(f"[ERROR] Unexpected error: {e}")
#         sys.exit(2)


# VISUALIZATION FUNCTIONS

import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10

def create_visualizations(df_original, X, y, output_dir="visualizations"):
    """
    Generate comprehensive EDA and preprocessing visualizations
    
    Creates:
    1. Target distribution (price histogram)
    2. Feature correlations heatmap
    3. Top features vs price scatter plots
    4. Category distributions (brand, fuel type, etc.)
    5. Outlier detection plots
    6. Feature importance (for tree models)
    """
    # Create output directory
    Path(output_dir).mkdir(exist_ok=True)
    
    print(f"\n{'='*60}")
    print("Generating Visualizations...")
    print(f"{'='*60}")
    
    # ===== 1. PRICE DISTRIBUTION =====
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Histogram
    axes[0].hist(y, bins=50, color='steelblue', edgecolor='black', alpha=0.7)
    axes[0].axvline(y.mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {y.mean():.2f} Lakhs')
    axes[0].axvline(y.median(), color='green', linestyle='--', linewidth=2, label=f'Median: {y.median():.2f} Lakhs')
    axes[0].set_xlabel('Price (Lakhs)', fontsize=12, fontweight='bold')
    axes[0].set_ylabel('Frequency', fontsize=12, fontweight='bold')
    axes[0].set_title('Price Distribution', fontsize=14, fontweight='bold')
    axes[0].legend()
    axes[0].grid(alpha=0.3)
    
    # Box plot
    axes[1].boxplot(y, vert=True, patch_artist=True,
                    boxprops=dict(facecolor='lightblue', alpha=0.7),
                    medianprops=dict(color='red', linewidth=2))
    axes[1].set_ylabel('Price (Lakhs)', fontsize=12, fontweight='bold')
    axes[1].set_title('Price Box Plot (Outlier Detection)', fontsize=14, fontweight='bold')
    axes[1].grid(alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/01_price_distribution.png', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: 01_price_distribution.png")
    plt.close()
    
    # ===== 2. CORRELATION HEATMAP (Top 15 features) =====
    # Select numeric features
    numeric_features = X.select_dtypes(include=[np.number]).columns[:15]
    corr_data = pd.concat([X[numeric_features], y.rename('Price')], axis=1)
    corr_matrix = corr_data.corr()
    
    plt.figure(figsize=(12, 10))
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
    sns.heatmap(corr_matrix, mask=mask, annot=True, fmt='.2f', cmap='coolwarm',
                center=0, square=True, linewidths=1, cbar_kws={"shrink": 0.8})
    plt.title('Feature Correlation Heatmap (Top 15 Features)', fontsize=16, fontweight='bold', pad=20)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/02_correlation_heatmap.png', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: 02_correlation_heatmap.png")
    plt.close()
    
    # ===== 3. KEY FEATURES vs PRICE =====
    key_features = ['Car_Age', 'Millage(KM)', 'Engine (cc)', 'Mileage_Per_Year']
    existing_features = [f for f in key_features if f in X.columns]
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()
    
    for idx, feature in enumerate(existing_features):
        if idx < 4:
            axes[idx].scatter(X[feature], y, alpha=0.3, s=10, color='steelblue')
            axes[idx].set_xlabel(feature, fontsize=11, fontweight='bold')
            axes[idx].set_ylabel('Price (Lakhs)', fontsize=11, fontweight='bold')
            axes[idx].set_title(f'{feature} vs Price', fontsize=12, fontweight='bold')
            axes[idx].grid(alpha=0.3)
            
            # Add trend line
            z = np.polyfit(X[feature], y, 1)
            p = np.poly1d(z)
            axes[idx].plot(X[feature], p(X[feature]), "r--", alpha=0.8, linewidth=2, label='Trend')
            axes[idx].legend()
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/03_key_features_vs_price.png', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: 03_key_features_vs_price.png")
    plt.close()
    
    # ===== 4. CATEGORICAL DISTRIBUTIONS =====
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    
    # Top 10 brands by count
    if 'Brand' in df_original.columns:
        brand_counts = df_original['Brand'].value_counts().head(10)
        axes[0, 0].barh(brand_counts.index, brand_counts.values, color='steelblue')
        axes[0, 0].set_xlabel('Count', fontsize=11, fontweight='bold')
        axes[0, 0].set_title('Top 10 Brands', fontsize=12, fontweight='bold')
        axes[0, 0].grid(axis='x', alpha=0.3)
    
    # Fuel type distribution
    if 'Fuel Type' in df_original.columns:
        fuel_counts = df_original['Fuel Type'].value_counts()
        axes[0, 1].pie(fuel_counts.values, labels=fuel_counts.index, autopct='%1.1f%%',
                      startangle=90, colors=sns.color_palette("Set2"))
        axes[0, 1].set_title('Fuel Type Distribution', fontsize=12, fontweight='bold')
    
    # Gear distribution
    if 'Gear' in df_original.columns:
        gear_counts = df_original['Gear'].value_counts()
        axes[1, 0].bar(gear_counts.index, gear_counts.values, color='lightcoral', edgecolor='black')
        axes[1, 0].set_xlabel('Gear Type', fontsize=11, fontweight='bold')
        axes[1, 0].set_ylabel('Count', fontsize=11, fontweight='bold')
        axes[1, 0].set_title('Transmission Distribution', fontsize=12, fontweight='bold')
        axes[1, 0].grid(axis='y', alpha=0.3)
    
    # Year of manufacture distribution
    if 'YOM' in X.columns:
        axes[1, 1].hist(X['YOM'], bins=20, color='seagreen', edgecolor='black', alpha=0.7)
        axes[1, 1].set_xlabel('Year of Manufacture', fontsize=11, fontweight='bold')
        axes[1, 1].set_ylabel('Frequency', fontsize=11, fontweight='bold')
        axes[1, 1].set_title('YOM Distribution', fontsize=12, fontweight='bold')
        axes[1, 1].grid(alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/04_categorical_distributions.png', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: 04_categorical_distributions.png")
    plt.close()
    
    # ===== 5. FEATURE ENGINEERING IMPACT =====
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    
    # Luxury vs Popular brands pricing
    if 'Is_Luxury' in X.columns and 'Is_Popular_Brand' in X.columns:
        brand_type_price = pd.DataFrame({
            'Luxury': y[X['Is_Luxury'] == 1],
            'Popular': y[X['Is_Popular_Brand'] == 1],
            'Other': y[(X['Is_Luxury'] == 0) & (X['Is_Popular_Brand'] == 0)]
        })
        
        bp = axes[0].boxplot([brand_type_price['Luxury'].dropna(),
                              brand_type_price['Popular'].dropna(),
                              brand_type_price['Other'].dropna()],
                             labels=['Luxury', 'Popular', 'Other'],
                             patch_artist=True,
                             boxprops=dict(facecolor='lightblue'))
        axes[0].set_ylabel('Price (Lakhs)', fontsize=11, fontweight='bold')
        axes[0].set_title('Brand Category Impact on Price', fontsize=12, fontweight='bold')
        axes[0].grid(alpha=0.3)
    
    # Car age vs price
    if 'Car_Age' in X.columns:
        age_bins = pd.cut(X['Car_Age'], bins=[0, 5, 10, 15, 50], labels=['0-5', '6-10', '11-15', '16+'])
        age_price = pd.DataFrame({'Age_Group': age_bins, 'Price': y})
        age_price.boxplot(column='Price', by='Age_Group', ax=axes[1], patch_artist=True)
        axes[1].set_xlabel('Car Age (years)', fontsize=11, fontweight='bold')
        axes[1].set_ylabel('Price (Lakhs)', fontsize=11, fontweight='bold')
        axes[1].set_title('Car Age Impact on Price', fontsize=12, fontweight='bold')
        axes[1].get_figure().suptitle('')  # Remove default title
        axes[1].grid(alpha=0.3)
    
    # Equipment score vs price
    if 'Equipment_Score' in X.columns:
        equipment_price = pd.DataFrame({'Equipment_Score': X['Equipment_Score'], 'Price': y})
        equipment_avg = equipment_price.groupby('Equipment_Score')['Price'].mean()
        axes[2].bar(equipment_avg.index, equipment_avg.values, color='coral', edgecolor='black')
        axes[2].set_xlabel('Equipment Score (0-4)', fontsize=11, fontweight='bold')
        axes[2].set_ylabel('Average Price (Lakhs)', fontsize=11, fontweight='bold')
        axes[2].set_title('Equipment Features Impact', fontsize=12, fontweight='bold')
        axes[2].grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/05_feature_engineering_impact.png', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: 05_feature_engineering_impact.png")
    plt.close()
    
    print(f"\n✓ All visualizations saved in '{output_dir}/' directory")
    print(f"{'='*60}\n")


def plot_feature_importance(model, feature_names, output_dir="visualizations", top_n=20):
    """
    Plot feature importance for tree-based models (Random Forest, XGBoost)
    """
    if not hasattr(model, 'feature_importances_'):
        print("  Model doesn't have feature_importances_ attribute")
        return
    
    # Get feature importances
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1][:top_n]
    
    plt.figure(figsize=(12, 8))
    plt.barh(range(top_n), importances[indices], color='steelblue', edgecolor='black')
    plt.yticks(range(top_n), [feature_names[i] for i in indices])
    plt.xlabel('Feature Importance', fontsize=12, fontweight='bold')
    plt.title(f'Top {top_n} Most Important Features', fontsize=14, fontweight='bold')
    plt.gca().invert_yaxis()
    plt.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/06_feature_importance.png', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: 06_feature_importance.png")
    plt.close()

def add_economic_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add real-time and historical economic indicators
    
    NEW FEATURES:
    - Currency_Devaluation: USD/LKR impact on imports
    - Fuel_Price_Impact: Oil prices affect hybrid premiums
    - Interest_Rate_Factor: CBSL rates affect leasing
    - Inflation_Adjusted_Price: Real vs nominal pricing
    - Crisis_Discount: Economic crisis panic selling
    - Seasonal_Premium: Month/quarter effects
    """
    
    # Fetch current economic data
    fetcher = EconomicDataFetcher()
    economic_data = fetcher.get_data()
    
    print("\n[add_economic_features] Using economic data:")
    print(f"  USD/LKR: {economic_data.get('usd_lkr', 360)}")
    print(f"  Inflation: {economic_data.get('inflation_rate', 5.0)}%")
    print(f"  Interest Rate: {economic_data.get('cbsl_rate', 15.0)}%")
    
    # ========================================
    # 1. EXCHANGE RATE FEATURES
    # ========================================
    baseline_usd_lkr = 135  # 2015 average (pre-crisis)
    current_usd_lkr = economic_data.get('usd_lkr', 360)
    
    df['Currency_Devaluation'] = current_usd_lkr / baseline_usd_lkr  # 2.67x in 2024
    df['Import_Cost_Multiplier'] = df.get('Is_Luxury', 0) * (df['Currency_Devaluation'] - 1)
    
    # ========================================
    # 2. FUEL PRICE FEATURES
    # ========================================
    baseline_fuel_price = 120  # LKR per liter (2015)
    current_fuel_price = economic_data.get('fuel_prices', {}).get('petrol_92', 420)
    fuel_ratio = current_fuel_price / baseline_fuel_price
    
    # Hybrids/Electric get premium when fuel expensive
    df['Fuel_Efficiency_Premium'] = 0.0
    if 'Fuel Type' in df.columns:
        df.loc[df['Fuel Type'] == 'Hybrid', 'Fuel_Efficiency_Premium'] = (fuel_ratio - 1) * 0.1
        df.loc[df['Fuel Type'] == 'Electric', 'Fuel_Efficiency_Premium'] = (fuel_ratio - 1) * 0.15
    
    # ========================================
    # 3. INTEREST RATE FEATURES
    # ========================================
    baseline_interest_rate = 6.5  # % (2015 CBSL rate)
    current_interest_rate = economic_data.get('cbsl_rate', 15.0)
    
    # High rates make leasing expensive → lower demand for expensive cars
    df['Interest_Rate_Impact'] = (current_interest_rate - baseline_interest_rate) / 100
    df['Leasing_Affordability'] = df.get('Is_Luxury', 0) * (-df['Interest_Rate_Impact'])
    
    # ========================================
    # 4. INFLATION ADJUSTMENT
    # ========================================
    current_inflation = economic_data.get('inflation_rate', 5.0)
    
    # Inflation erodes purchasing power
    df['Inflation_Factor'] = 1 + (current_inflation / 100)
    
    # ========================================
    # 5. ECONOMIC CRISIS FEATURES
    # ========================================
    if 'YOM' in df.columns:
        df['During_Economic_Crisis'] = ((df['YOM'] >= 2022) & (df['YOM'] <= 2023)).astype(int)
        df['Crisis_Discount'] = df['During_Economic_Crisis'] * 0.10  # 10% panic selling
    
    # ========================================
    # 6. SEASONAL FEATURES
    # ========================================
    if 'Listing_Date' in df.columns:
        df['Listing_Date'] = pd.to_datetime(df['Listing_Date'], errors='coerce')
        df['Month'] = df['Listing_Date'].dt.month
        df['Quarter'] = df['Listing_Date'].dt.quarter
    else:
        # Use current date if no listing date
        current_month = datetime.now().month
        current_quarter = (current_month - 1) // 3 + 1
        df['Month'] = current_month
        df['Quarter'] = current_quarter
    
    # Get seasonal factors from fetcher
    seasonal = fetcher.get_seasonal_factors()
    df['December_Premium'] = (df['Month'] == 12).astype(int) * seasonal['december_premium']
    df['Q1_Premium'] = (df['Quarter'] == 1).astype(int) * seasonal['q1_premium']
    
    # ========================================
    # 7. IMPORT RESTRICTION FEATURES
    # ========================================
    if 'YOM' in df.columns:
        df['Import_Restriction_Severity'] = df['YOM'].apply(
            lambda year: fetcher.get_import_restriction_status(year)
        )
    
    print(f"[add_economic_features] Added 12 economic features")
    return df


# ========================================
# UPDATE YOUR MAIN PREPROCESSING FUNCTION
# ========================================
def preprocess_data(filepath: str, generate_plots=True):
    """
    Full pipeline with optional visualization generation
    """
    # ... (your existing preprocessing code) ...
    
    df = load_and_clean_data(filepath)
    df_original = df.copy()  # Keep for visualizations
    
    df = feature_engineering(df)
    df = handle_outliers(df)
    df, le_brand, le_model, le_town = encode_categorical(df)
    X, y = prepare_features(df)
    
    # Generate visualizations
    if generate_plots:
        create_visualizations(df_original, X, y)
    
    return X, y, le_brand, le_model, le_town

