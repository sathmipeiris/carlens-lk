from flask import Flask, request, jsonify, send_from_directory
import joblib
import numpy as np
import os

app = Flask(__name__)

# If a production build of the React app exists at ../client/car-price-frontend/build
# serve it as static files so Flask can host frontend + API together.
CLIENT_BUILD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'client', 'car-price-frontend', 'build'))

if os.path.isdir(CLIENT_BUILD_DIR):
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        """Serve React production build if present. Falls back to API routes when file not found."""
        if path != '' and os.path.exists(os.path.join(CLIENT_BUILD_DIR, path)):
            return send_from_directory(CLIENT_BUILD_DIR, path)
        # For any other path serve index.html (SPA routing)
        return send_from_directory(CLIENT_BUILD_DIR, 'index.html')

# Path to artifacts (adjust if you store them elsewhere)
ARTIFACT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
MODEL_PATH = os.path.join(ARTIFACT_DIR, 'final_best_model.pkl')
FEATURES_PATH = os.path.join(ARTIFACT_DIR, 'feature_names.pkl')
ENC_BRAND = os.path.join(ARTIFACT_DIR, 'label_encoder_brand.pkl')
ENC_MODEL = os.path.join(ARTIFACT_DIR, 'label_encoder_model.pkl')
ENC_TOWN = os.path.join(ARTIFACT_DIR, 'label_encoder_town.pkl')

# Lazy load artifacts
_model = None
_feature_names = None
_le_brand = None
_le_model = None
_le_town = None


def load_artifacts():
    global _model, _feature_names, _le_brand, _le_model, _le_town
    if _model is None:
        _model = joblib.load(MODEL_PATH)
    if _feature_names is None:
        _feature_names = joblib.load(FEATURES_PATH)
    if _le_brand is None and os.path.exists(ENC_BRAND):
        _le_brand = joblib.load(ENC_BRAND)
    if _le_model is None and os.path.exists(ENC_MODEL):
        _le_model = joblib.load(ENC_MODEL)
    if _le_town is None and os.path.exists(ENC_TOWN):
        _le_town = joblib.load(ENC_TOWN)


@app.route('/health')
def health():
    return jsonify({'status': 'ok'})


@app.route('/predict', methods=['POST'])
def predict():
    payload = request.get_json(force=True)
    if not payload:
        return jsonify({'error': 'Invalid JSON payload'}), 400

    load_artifacts()

    # Minimal example: expects payload to contain feature names directly or use the same logic as in modal_app.predict_price
    # Here we expect frontend to send a dict of features matching feature_names.pkl
    row = [payload.get(fn, 0) for fn in _feature_names]
    X = np.array([row])
    price = float(_model.predict(X)[0])
    return jsonify({'predicted_price': round(price, 2), 'unit': 'LKR Lakhs'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)