# # ============================================================
# # ADD THIS TO app.py
# # Replace the existing /predict route AND add the new
# # /predict-with-economics route below it.
# # Also add this import at the top of app.py:
# #   from fetch_realtime_data import EconomicDataFetcher, EconomicAdjustmentEngine
# # ============================================================

# from flask import Flask, request, jsonify
# from flask_cors import CORS
# import joblib
# import pandas as pd
# import numpy as np
# import os
# from datetime import datetime
# from fetch_realtime_data import EconomicDataFetcher, EconomicAdjustmentEngine
# from forecasting import CarPriceForecaster

# app = Flask(__name__)
# CORS(app, resources={
#     r"/*": {
#         "origins": ["http://localhost:3000", "http://localhost:3001",
#                     "https://sathmipeiris.github.io"],
#         "methods": ["GET", "POST", "OPTIONS"],
#         "allow_headers": ["Content-Type"],
#     }
# })

# # ── Load ML artifacts ────────────────────────────────────────
# model = le_brand = le_model = le_town = feature_names = None

# def load_models():
#     global model, le_brand, le_model, le_town, feature_names

#     # Load brand popularity mapping saved at training time
#     global brand_popularity_map
#     brand_popularity_map = {}

#     for path in ['final_best_model.pkl', 'best_model.pkl']:
#         if os.path.exists(path):
#             model = joblib.load(path)
#             print(f"✓ Loaded model: {path}")
#             break

#     try:
#         le_brand           = joblib.load('label_encoder_brand.pkl')
#         le_model           = joblib.load('label_encoder_model.pkl')
#         le_town            = joblib.load('label_encoder_town.pkl')
#         feature_names      = joblib.load('feature_names.pkl')

#         # Load brand popularity map if saved during training
#         if os.path.exists('brand_popularity.pkl'):
#             brand_popularity_map = joblib.load('brand_popularity.pkl')
#             print("✓ Loaded brand popularity map")
#         else:
#             # Build from label encoder classes as fallback
#             # (not ideal — see note below about retraining)
#             print("⚠ brand_popularity.pkl not found — Brand_Popularity set to 0. "
#                   "Re-run training with save_brand_popularity() to fix this.")

#         print("✓ All artifacts loaded")
#         return True
#     except Exception as e:
#         print(f"✗ Artifact load error: {e}")
#         return False


# # ── Feature engineering (must match training exactly) ────────
# def engineer_features(data: dict) -> dict:
#     luxury_brands  = {'BMW', 'MERCEDES-BENZ', 'AUDI', 'LEXUS',
#                       'LAND ROVER', 'PORSCHE', 'VOLVO', 'JAGUAR'}
#     popular_brands = {'TOYOTA', 'HONDA', 'SUZUKI', 'NISSAN', 'MITSUBISHI', 'MAZDA'}

#     brand     = str(data.get('brand', '')).upper()
#     yom       = int(data.get('yom', 2015))
#     mileage   = float(data.get('mileage', 60000))
#     car_age   = datetime.now().year - yom
#     mil_per_y = mileage / max(car_age, 1)

#     eq = (int(data.get('air_condition', 1)) +
#           int(data.get('power_steering', 1)) +
#           int(data.get('power_mirror', 1)) +
#           int(data.get('power_window', 1)))

#     # Use saved frequency map; fall back to 0 if brand unseen
#     brand_pop = brand_popularity_map.get(brand, 0)

#     brand_enc = le_brand.transform([brand])[0] if brand in le_brand.classes_ else 0
#     model_enc = le_model.transform([data.get('model', 'UNKNOWN')])[0] \
#                 if data.get('model', 'UNKNOWN') in le_model.classes_ else 0
#     town_enc  = le_town.transform([data.get('town', 'Colombo')])[0] \
#                 if data.get('town', 'Colombo') in le_town.classes_ else 0

#     features = {
#         'YOM':                    yom,
#         'Engine (cc)':            float(data.get('engine_cc', 1500)),
#         'Millage(KM)':            mileage,
#         'Car_Age':                car_age,
#         'Mileage_Per_Year':       mil_per_y,
#         'AIR CONDITION':          int(data.get('air_condition', 1)),
#         'POWER STEERING':         int(data.get('power_steering', 1)),
#         'POWER MIRROR':           int(data.get('power_mirror', 1)),
#         'POWER WINDOW':           int(data.get('power_window', 1)),
#         'Equipment_Score':        eq,
#         'Brand_Popularity':       brand_pop,
#         'Is_Luxury':              1 if brand in luxury_brands else 0,
#         'Is_Popular_Brand':       1 if brand in popular_brands else 0,
#         'Post_Import_Restriction': 1 if yom >= 2020 else 0,
#         'Brand_Encoded':          brand_enc,
#         'Model_Encoded':          model_enc,
#         'Town_Encoded':           town_enc,
#     }

#     # One-hot features
#     features[f'Gear_{data.get("gear", "Automatic")}']        = 1
#     features[f'Fuel Type_{data.get("fuel_type", "Petrol")}'] = 1
#     features[f'Leasing_{data.get("leasing", "No Leasing")}'] = 1
#     features[f'Condition_{data.get("condition", "USED")}']   = 1

#     return features


# def _validate_input(data: dict) -> list:
#     """Return list of validation error strings."""
#     errors = []
#     if not data:
#         return ['No data provided']
#     if not data.get('brand'):
#         errors.append('brand is required')
#     yom = data.get('yom')
#     if yom:
#         try:
#             y = int(yom)
#             if y < 1980 or y > datetime.now().year:
#                 errors.append(f'yom must be between 1980 and {datetime.now().year}')
#         except ValueError:
#             errors.append('yom must be a number')
#     mileage = data.get('mileage')
#     if mileage:
#         try:
#             m = float(mileage)
#             if m < 0 or m > 1_000_000:
#                 errors.append('mileage must be between 0 and 1,000,000')
#         except ValueError:
#             errors.append('mileage must be a number')
#     return errors


# # ── Routes ───────────────────────────────────────────────────

# @app.route('/health', methods=['GET'])
# def health():
#     models_loaded = all([model, le_brand, le_model, le_town, feature_names])
#     return jsonify({
#         'status':        'healthy' if models_loaded else 'models_not_loaded',
#         'models_loaded': models_loaded,
#         'timestamp':     datetime.now().isoformat(),
#     })


# @app.route('/predict', methods=['POST', 'OPTIONS'])
# def predict():
#     """Base prediction — model output only, no economic adjustment."""
#     if request.method == 'OPTIONS':
#         return '', 204

#     data   = request.json
#     errors = _validate_input(data)
#     if errors:
#         return jsonify({'error': '; '.join(errors)}), 400

#     try:
#         features = engineer_features(data)
#         df = pd.DataFrame(
#             [{fn: features.get(fn, 0) for fn in feature_names}],
#             columns=feature_names,
#         )
#         prediction = float(model.predict(df)[0])

#         return jsonify({
#             'predicted_price': round(prediction, 2),
#             'unit':            'LKR Lakhs',
#             'model':           'Random Forest',
#             'note':            'Base prediction — use /predict-with-economics for adjusted price',
#         })
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500


# @app.route('/predict-with-economics', methods=['POST', 'OPTIONS'])
# def predict_with_economics():
#     """
#     Full prediction with real-time economic adjustments.

#     Returns:
#     {
#         base_price          : float  (raw model output)
#         final_price         : float  (after economic adjustments)
#         total_adjustment_pct: float
#         total_adjustment_lkr: float
#         adjustments: {
#             usd_lkr:          { pct, lkr_lakhs, explanation, ... }
#             inflation:         { pct, lkr_lakhs, explanation, ... }
#             fuel:              { pct, lkr_lakhs, explanation, ... }
#             import_scarcity:   { pct, lkr_lakhs, explanation, ... }
#         }
#         economic_context: { live indicator values + sources }
#         car_summary:      { brand, yom, fuel_type, segment }
#     }
#     """
#     if request.method == 'OPTIONS':
#         return '', 204

#     data   = request.json
#     errors = _validate_input(data)
#     if errors:
#         return jsonify({'error': '; '.join(errors)}), 400

#     try:
#         # Step 1 — base prediction
#         features = engineer_features(data)
#         df = pd.DataFrame(
#             [{fn: features.get(fn, 0) for fn in feature_names}],
#             columns=feature_names,
#         )
#         base_price = float(model.predict(df)[0])

#         # Step 2 — economic adjustment
#         engine = EconomicAdjustmentEngine()
#         result = engine.adjust(base_price=base_price, car_data=data)

#         return jsonify(result)

#     except Exception as e:
#         import traceback
#         print(traceback.format_exc())
#         return jsonify({'error': str(e)}), 500


# @app.route('/api/dashboard/economic-indicators', methods=['GET'])
# def get_economic_indicators():
#     fetcher    = EconomicDataFetcher()
#     indicators = fetcher.get_all_indicators()

#     usd = indicators['usd_lkr_rate']
#     inf = indicators['inflation_rate']
#     pet = indicators['petrol_price']
#     cse = indicators['cse_aspi']

#     return jsonify({
#         'timestamp':  datetime.now().isoformat(),
#         'indicators': indicators,
#         'impact_analysis': {
#             'usd_lkr':    {
#                 'value':       usd,
#                 'impact':      'High' if usd > 350 else 'Moderate',
#                 'description': 'Weak LKR raises imported parts costs — affects all used cars',
#             },
#             'inflation':  {
#                 'value':       inf,
#                 'impact':      'High' if inf > 10 else 'Low',
#                 'description': 'High inflation accelerates depreciation of older cars',
#             },
#             'fuel_price': {
#                 'value':       pet,
#                 'impact':      'Medium',
#                 'description': 'Higher fuel costs increase hybrid/EV resale premiums',
#             },
#             'stock_market': {
#                 'value':       cse,
#                 'impact':      'Low' if cse < 10000 else 'Positive',
#                 'description': 'CSE strength correlates with buyer confidence',
#             },
#         },
#     })


# @app.route('/api/dashboard/market-health', methods=['GET'])
# def get_market_health():
#     fetcher = EconomicDataFetcher()
#     econ    = fetcher.get_all_indicators()

#     score = 50
#     usd   = econ['usd_lkr_rate']
#     inf   = econ['inflation_rate']
#     cse   = econ['cse_aspi']

#     if usd < 300:   score += 20
#     elif usd > 400: score -= 20
#     elif usd > 350: score -= 10

#     if inf < 5:    score += 15
#     elif inf > 15: score -= 15
#     elif inf > 8:  score -= 8

#     if cse > 12000: score += 15
#     elif cse > 10000: score += 8

#     score = max(0, min(100, score))

#     if score >= 70:   health, color = 'Good',  'green'
#     elif score >= 40: health, color = 'Fair',  'yellow'
#     else:             health, color = 'Poor',  'red'

#     return jsonify({
#         'health_score':   score,
#         'health_status':  health,
#         'color':          color,
#         'indicators':     econ,
#         'recommendation': 'Good time to buy' if score >= 60 else 'Wait for better conditions',
#     })


# @app.route('/api/dashboard/brand-trends', methods=['GET'])
# def get_brand_trends():
#     try:
#         df = pd.read_csv('car_price_dataset.csv')
#         if 'Scraped_Date' not in df.columns:
#             df['Scraped_Date'] = pd.NaT

#         forecaster = CarPriceForecaster(df)
#         forecaster.prepare_time_series()

#         brands = ['TOYOTA', 'HONDA', 'SUZUKI', 'BMW']
#         trends = {}
#         for brand in brands:
#             forecast = forecaster.forecast_brand_trends(brand, months_ahead=3)
#             if 'error' not in forecast:
#                 trends[brand] = {
#                     'current_price':   forecast['current_avg_price'],
#                     'trend':           forecast['trend'],
#                     'confidence':      forecast['confidence'],
#                     'next_month_price': forecast['forecasted_prices'][0]
#                                        if forecast['forecasted_prices'] else None,
#                     'data_mode':       forecast['data_mode'],
#                     'note':            forecast.get('note'),
#                 }
#         return jsonify(trends)
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500


# # ── Startup ──────────────────────────────────────────────────
# if __name__ == '__main__':
#     if load_models():
#         debug = os.environ.get('APP_DEBUG', 'false').lower() == 'true'
#         host  = '0.0.0.0' if os.environ.get('ALLOW_EXTERNAL') else '127.0.0.1'
#         print(f"\n{'='*60}")
#         print("  CarLensLK API — running")
#         print(f"  http://{host}:5000")
#         print(f"  POST /predict")
#         print(f"  POST /predict-with-economics")
#         print(f"  GET  /api/dashboard/economic-indicators")
#         print(f"  GET  /api/dashboard/market-health")
#         print(f"  GET  /api/dashboard/brand-trends")
#         print(f"{'='*60}\n")
#         app.run(debug=debug, host=host, port=5000)
#     else:
#         print("✗ Could not load models — check your .pkl files")


# from flask import Flask, request, jsonify
# from flask_cors import CORS
# import joblib
# import numpy as np
# import pandas as pd

# app = Flask(__name__)
# CORS(app)  # Enable CORS for React frontend

# # Load model and encoders
# model = joblib.load('best_model.pkl')
# le_brand = joblib.load('label_encoder_brand.pkl')
# le_model = joblib.load('label_encoder_model.pkl')
# le_town = joblib.load('label_encoder_town.pkl')
# feature_names = joblib.load('feature_names.pkl')


# @app.route('/predict', methods=['POST'])
# def predict():
#     """Predict car price based on input features"""
#     try:
#         data = request.json

#         # Extract features from request
#         brand = data.get('brand')
#         model_name = data.get('model')
#         yom = int(data.get('yom'))
#         engine = float(data.get('engine'))
#         gear = data.get('gear')
#         fuel_type = data.get('fuel_type')
#         mileage = float(data.get('mileage'))
#         town = data.get('town')
#         leasing = data.get('leasing', 'No Leasing')
#         condition = data.get('condition', 'USED')
#         air_condition = int(data.get('air_condition', 1))
#         power_steering = int(data.get('power_steering', 1))
#         power_mirror = int(data.get('power_mirror', 1))
#         power_window = int(data.get('power_window', 1))

#         # Feature engineering (same as training)
#         current_year = 2025
#         car_age = current_year - yom
#         mileage_per_year = mileage / (car_age + 1)
#         equipment_score = air_condition + power_steering + power_mirror + power_window

#         # Brand popularity (simplified - in production, load from saved mapping)
#         brand_popularity = 500  # Default value

#         luxury_brands = ['BMW', 'MERCEDES-BENZ', 'AUDI', 'LEXUS', 'LAND ROVER', 'PORSCHE']
#         is_luxury = 1 if brand.upper() in luxury_brands else 0

#         popular_brands = ['TOYOTA', 'HONDA', 'SUZUKI']
#         is_popular_brand = 1 if brand.upper() in popular_brands else 0

#         post_import_restriction = 1 if yom >= 2020 else 0

#         # Encode categorical features
#         brand_encoded = le_brand.transform([brand])[0] if brand in le_brand.classes_ else 0
#         model_encoded = le_model.transform([model_name])[0] if model_name in le_model.classes_ else 0
#         town_encoded = le_town.transform([town])[0] if town in le_town.classes_ else 0

#         # Create feature vector (must match training features)
#         features = pd.DataFrame([{
#             'YOM': yom,
#             'Engine (cc)': engine,
#             'Millage(KM)': mileage,
#             'Car_Age': car_age,
#             'Mileage_Per_Year': mileage_per_year,
#             'AIR CONDITION': air_condition,
#             'POWER STEERING': power_steering,
#             'POWER MIRROR': power_mirror,
#             'POWER WINDOW': power_window,
#             'Equipment_Score': equipment_score,
#             'Brand_Popularity': brand_popularity,
#             'Is_Luxury': is_luxury,
#             'Is_Popular_Brand': is_popular_brand,
#             'Post_Import_Restriction': post_import_restriction,
#             'Brand_Encoded': brand_encoded,
#             'Model_Encoded': model_encoded,
#             'Town_Encoded': town_encoded
#         }])

#         # Add one-hot encoded features
#         # (Simplified - in production, handle all one-hot features properly)
#         for feat in feature_names:
#             if feat not in features.columns:
#                 features[feat] = 0

#         features = features[feature_names]

#         # Predict
#         prediction = model.predict(features)[0]

#         return jsonify({
#             'success': True,
#             'predicted_price': round(float(prediction), 2),
#             'price_unit': 'LKR Lakhs'
#         })

#     except Exception as e:
#         return jsonify({
#             'success': False,
#             'error': str(e)
#         }), 400


# @app.route('/health', methods=['GET'])
# def health():
#     return jsonify({'status': 'healthy'})


# if __name__ == '__main__':
#     app.run(debug=True, port=5000)

# backend/app.py (MAIN ENTRY POINT)
from flask import Flask, request, jsonify, redirect, url_for
from flask_cors import CORS
import joblib
import pandas as pd
import numpy as np
import os
from datetime import datetime

# Import your modules
from fetch_realtime_data import EconomicDataFetcher, EconomicAdjustmentEngine
from fetch_realtime_data import EconomicDataFetcher
from forecasting import CarPriceForecaster

app = Flask(__name__)

# Enable CORS for React frontend
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:3000", "http://localhost:3001"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# ========================================
# LOAD ML MODELS (On Startup)
# ========================================
# Prefer canonical names but allow common alternatives that exist in this repo
if os.path.exists('best_model.pkl'):
    MODEL_PATH = 'best_model.pkl'
elif os.path.exists('final_best_model.pkl'):
    MODEL_PATH = 'final_best_model.pkl'
elif os.path.exists('final_model.pkl'):
    MODEL_PATH = 'final_model.pkl'
else:
    MODEL_PATH = 'best_model.pkl'  # default name (will cause error if missing)
BRAND_ENCODER_PATH = 'label_encoder_brand.pkl'
MODEL_ENCODER_PATH = 'label_encoder_model.pkl'
TOWN_ENCODER_PATH = 'label_encoder_town.pkl'
FEATURES_PATH = 'feature_names.pkl'

model = None
le_brand = None
le_model = None
le_town = None
feature_names = None

def load_models():
    """Load all ML artifacts on startup"""
    global model, le_brand, le_model, le_town, feature_names
    
    try:
        print("🔄 Loading ML models...")
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")
        model = joblib.load(MODEL_PATH)
        le_brand = joblib.load(BRAND_ENCODER_PATH)
        le_model = joblib.load(MODEL_ENCODER_PATH)
        le_town = joblib.load(TOWN_ENCODER_PATH)
        feature_names = joblib.load(FEATURES_PATH)
        print("✅ Models loaded successfully!")
        return True
    except Exception as e:
        print(f"❌ Error loading models: {e}")
        # Provide actionable hint
        if isinstance(e, FileNotFoundError):
            print("Hint: run train_models.py or ensure your trained artifacts exist (final_best_model.pkl or best_model.pkl).")
        return False

# ========================================
# CORE PREDICTION ROUTES
# ========================================

@app.route('/predict', methods=['POST', 'OPTIONS'])
def predict():
    """Main prediction endpoint"""
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.json
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Engineer features (same as preprocessing.py)
        features = engineer_features(data)
        
        # Create DataFrame with correct column order
        df = pd.DataFrame([{fn: features.get(fn, 0) for fn in feature_names}], columns=feature_names)
        
        # Predict
        prediction = float(model.predict(df)[0])
        
        return jsonify({
            'predicted_price': round(prediction, 2),
            'unit': 'LKR Lakhs',
            'model': 'Random Forest',
            'confidence': '92.45% R²'
        })
        
    except Exception as e:
        print(f"Prediction error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/predict-with-economics', methods=['POST', 'OPTIONS'])
def predict_with_economics():
    if request.method == 'OPTIONS':
        return '', 204

    payload = request.get_json(force=True)
    if not payload:
        return jsonify({'error': 'Invalid JSON payload'}), 400

    try:
        # Step 1 — use exact same logic as working /predict route
        features = engineer_features(payload)
        df = pd.DataFrame(
            [{fn: features.get(fn, 0) for fn in feature_names}],
            columns=feature_names,
        )
        base_price = float(model.predict(df)[0])

        # Step 2 — apply economic adjustments
        engine = EconomicAdjustmentEngine()
        result = engine.adjust(base_price=base_price, car_data=payload)
        return jsonify(result)

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({
            'base_price':           0,
            'final_price':          0,
            'total_adjustment_pct': 0.0,
            
            'total_adjustment_lkr': 0.0,
            'adjustments':          {},
            'error_note':           str(e),
        }), 500

# Root route: redirect to API info page to avoid 404 on '/'
@app.route('/', methods=['GET'])
def root():
    return redirect(url_for('info'))

def engineer_features(data):
    """Recreate feature engineering from preprocessing.py"""
    current_year = 2025
    
    car_age = current_year - int(data.get('yom', 2015))
    mileage = float(data.get('mileage_km', 50000))
    mileage_per_year = mileage / (car_age + 1)
    
    equipment_score = (
        int(data.get('air_condition', 1)) +
        int(data.get('power_steering', 1)) +
        int(data.get('power_mirror', 1)) +
        int(data.get('power_window', 1))
    )
    
    luxury_brands = ['BMW', 'MERCEDES-BENZ', 'AUDI', 'LEXUS', 'LAND ROVER', 'PORSCHE']
    popular_brands = ['TOYOTA', 'HONDA', 'SUZUKI', 'NISSAN', 'MAZDA']
    
    brand = str(data.get('brand', '')).upper()
    is_luxury = 1 if brand in luxury_brands else 0
    is_popular = 1 if brand in popular_brands else 0
    post_import = 1 if int(data.get('yom', 2015)) >= 2020 else 0
    
    # Encode categoricals
    brand_encoded = le_brand.transform([brand])[0] if brand in le_brand.classes_ else 0
    model_encoded = le_model.transform([data.get('model', 'UNKNOWN')])[0] if data.get('model', 'UNKNOWN') in le_model.classes_ else 0
    town_encoded = le_town.transform([data.get('town', 'Colombo')])[0] if data.get('town', 'Colombo') in le_town.classes_ else 0
    
    features = {
        'YOM': int(data.get('yom', 2015)),
        'Engine (cc)': float(data.get('engine_cc', 1500)),
        'Millage(KM)': mileage,
        'Car_Age': car_age,
        'Mileage_Per_Year': mileage_per_year,
        'AIR CONDITION': int(data.get('air_condition', 1)),
        'POWER STEERING': int(data.get('power_steering', 1)),
        'POWER MIRROR': int(data.get('power_mirror', 1)),
        'POWER WINDOW': int(data.get('power_window', 1)),
        'Equipment_Score': equipment_score,
        'Brand_Popularity': 0,
        'Is_Luxury': is_luxury,
        'Is_Popular_Brand': is_popular,
        'Post_Import_Restriction': post_import,
        'Brand_Encoded': brand_encoded,
        'Model_Encoded': model_encoded,
        'Town_Encoded': town_encoded
    }
    
    # Add one-hot encoded features
    gear = data.get('gear', 'Automatic')
    fuel = data.get('fuel_type', 'Petrol')
    leasing = data.get('leasing', 'No Leasing')
    condition = data.get('condition', 'USED')
    
    features[f'Gear_{gear}'] = 1
    features[f'Fuel Type_{fuel}'] = 1
    features[f'Leasing_{leasing}'] = 1
    features[f'Condition_{condition}'] = 1
    
    return features

# ========================================
# DASHBOARD ROUTES
# ========================================

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
    df = pd.read_csv('car_price_dataset.csv')
    
    # Add mock dates if not present
    if 'Scraped_Date' not in df.columns:
        df['Scraped_Date'] = pd.date_range(end=datetime.now(), periods=len(df), freq='D')
    
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

@app.route('/api/dashboard/market-health', methods=['GET'])
def get_market_health():
    """Overall market health score"""
    fetcher = EconomicDataFetcher()
    econ = fetcher.get_all_indicators()
    
    score = 50
    
    if econ['usd_lkr_rate'] < 300:
        score += 20
    elif econ['usd_lkr_rate'] > 400:
        score -= 20
    
    if econ['inflation_rate'] < 5:
        score += 15
    elif econ['inflation_rate'] > 15:
        score -= 15
    
    if econ['cse_aspi'] > 11000:
        score += 15
    
    score = max(0, min(100, score))
    
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

# ========================================
# UTILITY ROUTES
# ========================================

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    models_loaded = all([model, le_brand, le_model, le_town, feature_names])
    return jsonify({
        'status': 'healthy' if models_loaded else 'models not loaded',
        'models_loaded': models_loaded,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/info', methods=['GET'])
def info():
    """API information"""
    return jsonify({
        'name': 'Car Price Prediction API',
        'version': '2.0',
        'model': 'Random Forest',
        'accuracy': '92.45% R²',
        'dataset_size': '9,617 cars',
        'endpoints': {
            'POST /predict': 'Get price prediction',
            'GET /api/dashboard/economic-indicators': 'Economic data',
            'GET /api/dashboard/brand-trends': 'Brand forecasts',
            'GET /api/dashboard/market-health': 'Market health score',
            'GET /health': 'API health check',
            'GET /info': 'API information'
        }
    })

# ========================================
# STARTUP
# ========================================

if __name__ == '__main__':
    if load_models():
        print("\n" + "="*70)
        print("🚀 CAR PRICE PREDICTION API STARTING")
        print("="*70)
        print(f"📍 API URL: http://localhost:5000")
        print(f"📊 Model: Random Forest (92.45% R²)")
        print(f"🔗 CORS enabled for React frontend")
        print(f"📈 Dashboard endpoints active")
        print("="*70 + "\n")
        # By default run without the interactive debugger/reloader so the
        # process behaves more predictably. To enable the debugger set
        # the environment variable APP_DEBUG=true before launching.
        # For safety, bind to localhost unless ALLOW_EXTERNAL=true is set.
        debug_flag = str(os.environ.get("APP_DEBUG", "false")).lower() in ("1", "true", "yes")
        allow_external = str(os.environ.get("ALLOW_EXTERNAL", "false")).lower() in ("1", "true", "yes")
        host = '0.0.0.0' if allow_external else '127.0.0.1'

        if debug_flag:
            print("⚠️  Flask debug mode ENABLED (interactive debugger). Only enable this for development.")
        else:
            print("ℹ️  Flask debug mode DISABLED. To enable set APP_DEBUG=true")

        if allow_external:
            print("⚠️  Binding to 0.0.0.0 (all interfaces). Ensure this is intended.")
        else:
            print("ℹ️  Binding to localhost (127.0.0.1) for safety.")

        app.run(debug=debug_flag, host=host, port=5000)
    else:
        print("❌ Failed to load models. Run the training script (e.g. modal_app.py or modal.app) first.")
