# backend/dashboard.py
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import pandas as pd
import numpy as np
from fetch_realtime_data import EconomicDataFetcher
from forecasting import CarPriceForecaster
import joblib
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Load models (guarded) - missing artifacts should not crash the app at import time
try:
    model = joblib.load('best_model.pkl')
    le_brand = joblib.load('label_encoder_brand.pkl')
    le_model = joblib.load('label_encoder_model.pkl')
    le_town = joblib.load('label_encoder_town.pkl')
    feature_names = joblib.load('feature_names.pkl')
except Exception as e:
    # If artifacts are missing (common on dev machines), continue with placeholders
    print(f"Warning: model artifacts not loaded: {e}")
    model = None
    le_brand = None
    le_model = None
    le_town = None
    feature_names = []

# Load dataset for forecasting
df = pd.read_csv('car_price_dataset.csv')

@app.route('/api/dashboard/economic-indicators', methods=['GET'])
def get_economic_indicators():
    """Get current economic indicators"""
    fetcher = EconomicDataFetcher()
    indicators = fetcher.get_all_indicators()
    
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'indicators': indicators,
        'impact_analysis': {
            'usd_lkr': {
                'value': indicators['usd_lkr_rate'],
                'impact': 'High' if indicators['usd_lkr_rate'] > 350 else 'Moderate',
                'description': 'Weak LKR increases import car prices (luxury brands affected most)'
            },
            'inflation': {
                'value': indicators['inflation_rate'],
                'impact': 'High' if indicators['inflation_rate'] > 10 else 'Low',
                'description': 'High inflation accelerates depreciation and reduces purchasing power'
            },
            'fuel_price': {
                'value': indicators['petrol_price'],
                'impact': 'Medium',
                'description': 'Higher fuel costs increase hybrid/electric premiums'
            },
            'stock_market': {
                'value': indicators['cse_aspi'],
                'impact': 'Low' if indicators['cse_aspi'] < 10000 else 'Positive',
                'description': 'Stock market strength correlates with consumer confidence'
            }
        }
    })

@app.route('/api/dashboard/brand-trends', methods=['GET'])
def get_brand_trends():
    """Get price trends for popular brands"""
    forecaster = CarPriceForecaster(df)
    forecaster.prepare_time_series()
    
    brands = ['TOYOTA', 'HONDA', 'SUZUKI', 'BMW']
    trends = {}
    
    for brand in brands:
        forecast = forecaster.forecast_brand_trends(brand, months_ahead=3)
        if 'error' not in forecast:
            trends[brand] = {
                'current_price': forecast['current_avg_price'],
                'trend': forecast['trend'],
                'confidence': forecast['confidence'],
                'next_month_price': forecast['forecasted_prices'][0] if forecast['forecasted_prices'] else None
            }
    
    return jsonify(trends)

@app.route('/api/dashboard/predict-with-economic-impact', methods=['POST'])
def predict_with_economic_impact():
    """
    Predict price showing how economic factors affect it
    
    Returns breakdown:
    - Base price (from model)
    - Economic adjustments
    - Final price
    """
    data = request.json
    
    # Get current economic data
    fetcher = EconomicDataFetcher()
    econ_data = fetcher.get_all_indicators(car_year=data.get('yom'))
    
    # Base prediction (without economic adjustments)
    # ... (use your existing prediction code)
    
    # Calculate economic adjustments
    adjustments = {}
    
    # 1. Currency impact (luxury brands)
    is_luxury = data.get('brand', '').upper() in ['BMW', 'MERCEDES-BENZ', 'AUDI']
    if is_luxury:
        currency_multiplier = econ_data['usd_lkr_rate'] / 200
        adjustments['currency_impact'] = (currency_multiplier - 1) * 10  # +X% for weak LKR
    
    # 2. Fuel price impact (hybrids/EVs)
    if data.get('fuel_type') in ['Hybrid', 'Electric']:
        fuel_premium = (econ_data['petrol_price'] - 300) / 300 * 5  # +X% premium
        adjustments['fuel_efficiency_premium'] = fuel_premium
    
    # 3. Inflation adjustment
    car_age = 2025 - data.get('yom', 2015)
    inflation_penalty = car_age * econ_data['inflation_rate'] / 100 * -0.5
    adjustments['inflation_penalty'] = inflation_penalty
    
    # 4. Import restriction premium
    if data.get('yom', 2015) >= 2020:
        adjustments['import_scarcity_premium'] = 5  # +5% for post-ban cars
    
    # Calculate final price
    base_price = 50  # Placeholder - use your actual model prediction
    total_adjustment = sum(adjustments.values())
    final_price = base_price * (1 + total_adjustment / 100)
    
    return jsonify({
        'base_price': base_price,
        'adjustments': adjustments,
        'total_adjustment_pct': total_adjustment,
        'final_price': final_price,
        'economic_context': econ_data,
        'breakdown': {
            'base': base_price,
            'currency_adj': adjustments.get('currency_impact', 0),
            'fuel_adj': adjustments.get('fuel_efficiency_premium', 0),
            'inflation_adj': adjustments.get('inflation_penalty', 0),
            'scarcity_adj': adjustments.get('import_scarcity_premium', 0),
            'final': final_price
        }
    })

@app.route('/api/dashboard/market-health', methods=['GET'])
def get_market_health():
    """Overall market health score"""
    fetcher = EconomicDataFetcher()
    econ = fetcher.get_all_indicators()
    
    # Calculate health score (0-100)
    score = 50  # Base
    
    # Better exchange rate → higher score
    if econ['usd_lkr_rate'] < 300:
        score += 20
    elif econ['usd_lkr_rate'] > 400:
        score -= 20
    
    # Lower inflation → higher score
    if econ['inflation_rate'] < 5:
        score += 15
    elif econ['inflation_rate'] > 15:
        score -= 15
    
    # Higher stock market → higher score
    if econ['cse_aspi'] > 11000:
        score += 15
    
    score = max(0, min(100, score))  # Clamp 0-100
    
    if score >= 70:
        health = 'Good'
        color = 'green'
    elif score >= 40:
        health = 'Fair'
        color = 'yellow'
    else:
        health = 'Poor'
        color = 'red'
    
    return jsonify({
        'health_score': score,
        'health_status': health,
        'color': color,
        'indicators': econ,
        'recommendation': 'Good time to buy' if score >= 60 else 'Wait for better conditions'
    })

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Starting Dashboard API Server")
    print("="*60)
    print("Endpoints:")
    print("  GET  /api/dashboard/economic-indicators")
    print("  GET  /api/dashboard/brand-trends")
    print("  POST /api/dashboard/predict-with-economic-impact")
    print("  GET  /api/dashboard/market-health")
    print("="*60 + "\n")
    app.run(debug=True, port=5001)
