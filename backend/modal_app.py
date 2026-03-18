# import os
# import sys
# import joblib
# import pandas as pd
# import numpy as np

# # Try to import modal and detect whether the installed modal SDK supports
# # the features used below (Mount, Volume, App). If not, fall back to
# # local-only mode so you can run training/prediction locally without
# # raising AttributeError at import time.
# USE_MODAL = False
# modal = None
# try:
#     import modal as _modal
#     modal = _modal
#     # Ensure required attributes exist
#     if hasattr(modal, "App") and hasattr(modal, "Image") and hasattr(modal, "Volume") and hasattr(modal, "Mount"):
#         USE_MODAL = True
#     else:
#         print("[modal_app] modal package installed but missing required attributes (Mount/Volume/App). Running in LOCAL fallback mode.")
# except Exception:
#     print("[modal_app] modal package not available or failed to import. Running in LOCAL fallback mode.")

# if USE_MODAL:
#     # 1) Define image (SDK object is modal.Image)
#     image = (
#         modal.Image.debian_slim()
#         .pip_install(
#             "pandas==2.2.2",
#             "numpy==1.26.4",
#             "scikit-learn==1.5.1",
#             "xgboost==2.1.1",
#             "lightgbm==4.5.0",
#             "joblib==1.4.2"
#         )
#     )

#     # 2) Create the app (SDK object is modal.App)
#     app = modal.App("car-price-ml")

#     # 3) Mount your project directory (includes preprocessing.py and car_price_dataset.csv)
#     volume = modal.Volume.from_name("car-price-vol", create_if_missing=True)

#     # 4) Remote training function with mount
#     @app.function(
#         image=image,
#         volumes={"/root/app": volume},
#         timeout=60 * 30,
#         cpu=2.0,
#         memory=4096,
#         mounts=[modal.Mount.from_local_dir(".", remote_path="/root/app")]
#     )
#     def train_and_save():
#         """
#         Trains multiple models on Modal and saves the best model and artifacts.
#         Expects:
#           - /root/app/preprocessing.py
#           - /root/app/car_price_dataset.csv
#         Produces:
#           - /root/app/final_best_model.pkl
#           - /root/app/label_encoder_brand.pkl, label_encoder_model.pkl, label_encoder_town.pkl
#           - /root/app/feature_names.pkl
#         """
#         from sklearn.model_selection import train_test_split
#         from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
#         from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error, mean_absolute_percentage_error
#         import xgboost as xgb

#         # Debug: Check if files exist
#         print("Files in /root/app/:")
#         for item in os.listdir("/root/app"):
#             print(f"  - {item}")

#         # Import preprocessing (now available via mount)
#         from preprocessing import preprocess_data
#         print("✓ Successfully imported preprocess_data")

#         data_path = "/root/app/car_price_dataset.csv"
#         if not os.path.exists(data_path):
#             raise FileNotFoundError(f"car_price_dataset.csv not found at {data_path}")

#         print(f"✓ Found dataset at {data_path}")

#         # Your preprocess_data returns: X, y, le_brand, le_model, le_town
#         X, y, le_brand, le_model, le_town = preprocess_data(data_path)
#         print(f"✓ Preprocessing complete: {X.shape[1]} features, {len(y)} samples")

#         # Save feature names for inference
#         joblib.dump(list(X.columns), "/root/app/feature_names.pkl")
#         print("✓ Saved feature names")

#         # Split
#         X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

#         # Models
#         models = {
#             "Random Forest": RandomForestRegressor(
#                 n_estimators=300, max_depth=20, min_samples_split=5,
#                 min_samples_leaf=2, max_features="sqrt", random_state=42, n_jobs=-1
#             ),
#             "XGBoost": xgb.XGBRegressor(
#                 n_estimators=400, learning_rate=0.05, max_depth=6, min_child_weight=3,
#                 subsample=0.8, colsample_bytree=0.8, gamma=0.1, reg_alpha=0.1,
#                 reg_lambda=1.0, random_state=42, n_jobs=-1, tree_method="hist"
#             ),
#             "Gradient Boosting": GradientBoostingRegressor(
#                 n_estimators=250, learning_rate=0.05, max_depth=6,
#                 min_samples_split=5, subsample=0.8, random_state=42
#             ),
#         }

#         results = []
#         for name, model in models.items():
#             print(f"Training {name}...")
#             model.fit(X_train, y_train)
#             pred = model.predict(X_test)
#             r2 = r2_score(y_test, pred)
#             mae = mean_absolute_error(y_test, pred)
#             # Older scikit-learn versions may not support `squared=False`.
#             # Compute RMSE via sqrt(MSE) for compatibility.
#             rmse = float(np.sqrt(mean_squared_error(y_test, pred)))
#             mape = mean_absolute_percentage_error(y_test, pred) * 100
#             print(f"{name} | R2={r2:.4f} | MAE={mae:.2f} | RMSE={rmse:.2f} | MAPE={mape:.2f}%")
#             results.append((name, r2, mae, rmse, mape, model))

#         # Pick best by R²
#         results.sort(key=lambda x: x[1], reverse=True)
#         best_name, best_r2, best_mae, best_rmse, best_mape, best_model = results[0]
#         print(f"Best: {best_name} | R2={best_r2:.4f} | MAE={best_mae:.2f} | MAPE={best_mape:.2f}%")

#         # Save best model to volume (persistent storage)
#         joblib.dump(best_model, "/root/app/final_best_model.pkl")
#         print("✓ Saved: final_best_model.pkl")

#         # Save encoders (from preprocessing)
#         joblib.dump(le_brand, "/root/app/label_encoder_brand.pkl")
#         joblib.dump(le_model, "/root/app/label_encoder_model.pkl")
#         joblib.dump(le_town, "/root/app/label_encoder_town.pkl")
#         print("✓ Saved encoders")

#         # Verify artifacts
#         for fn in [
#             "final_best_model.pkl",
#             "label_encoder_brand.pkl", "label_encoder_model.pkl", "label_encoder_town.pkl",
#             "feature_names.pkl"
#         ]:
#             if not os.path.exists(f"/root/app/{fn}"):
#                 raise FileNotFoundError(f"Missing artifact {fn} after training.")
#         print("✓ All artifacts verified")

#         return {
#             "best_model": best_name,
#             "r2": best_r2,
#             "mae": best_mae,
#             "rmse": best_rmse,
#             "mape": best_mape
#         }
# else:
#     # Local fallback implementations (no modal decorators). These allow you to
#     # run training and prediction locally on your machine without Modal.
#     def train_and_save():
#         from sklearn.model_selection import train_test_split
#         from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
#         from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error, mean_absolute_percentage_error
#         import xgboost as xgb

#         # Work in current directory
#         local_root = os.path.abspath('.')
#         print(f"[local] Working directory: {local_root}")
#         print("Files:")
#         for item in os.listdir(local_root):
#             print(f"  - {item}")

#         # Import preprocessing from local file
#         try:
#             from preprocessing import preprocess_data
#         except Exception as e:
#             raise RuntimeError("Failed to import preprocessing.py. Ensure preprocessing.py is present in the project root") from e

#         data_path = os.path.join(local_root, "car_price_dataset.csv")
#         if not os.path.exists(data_path):
#             raise FileNotFoundError(f"car_price_dataset.csv not found at {data_path}")

#         X, y, le_brand, le_model, le_town = preprocess_data(data_path)
#         print(f"✓ Preprocessing complete: {X.shape[1]} features, {len(y)} samples")

#         # Save artifacts locally in project root
#         artifact_dir = local_root
#         joblib.dump(list(X.columns), os.path.join(artifact_dir, "feature_names.pkl"))

#         X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

#         models = {
#             "Random Forest": RandomForestRegressor(n_estimators=100, random_state=42),
#             "XGBoost": xgb.XGBRegressor(n_estimators=100, random_state=42),
#         }

#         results = []
#         for name, model in models.items():
#             print(f"[local] Training {name}...")
#             model.fit(X_train, y_train)
#             pred = model.predict(X_test)
#             r2 = r2_score(y_test, pred)
#             mae = mean_absolute_error(y_test, pred)
#             # Older scikit-learn versions may not support `squared=False`.
#             # Compute RMSE via sqrt(MSE) for compatibility.
#             rmse = float(np.sqrt(mean_squared_error(y_test, pred)))
#             mape = mean_absolute_percentage_error(y_test, pred) * 100
#             print(f"{name} | R2={r2:.4f} | MAE={mae:.2f} | RMSE={rmse:.2f} | MAPE={mape:.2f}%")
#             results.append((name, r2, mae, rmse, mape, model))

#         results.sort(key=lambda x: x[1], reverse=True)
#         best_name, best_r2, best_mae, best_rmse, best_mape, best_model = results[0]

#         # Save best model and encoders locally
#         joblib.dump(best_model, os.path.join(artifact_dir, "final_best_model.pkl"))
#         joblib.dump(le_brand, os.path.join(artifact_dir, "label_encoder_brand.pkl"))
#         joblib.dump(le_model, os.path.join(artifact_dir, "label_encoder_model.pkl"))
#         joblib.dump(le_town, os.path.join(artifact_dir, "label_encoder_town.pkl"))

#         print(f"[local] Saved artifacts in {artifact_dir}")
#         return {"best_model": best_name, "r2": best_r2, "mae": best_mae, "rmse": best_rmse, "mape": best_mape}

# # 5) Prediction and local entrypoint
# if USE_MODAL:
#     @app.function(
#         image=image,
#         volumes={"/root/app": volume},
#         timeout=60 * 5,
#         cpu=1.0,
#         memory=2048,
#         mounts=[modal.Mount.from_local_dir(".", remote_path="/root/app")]
#     )
#     def predict_price(payload: dict) -> dict:
#         # Import preprocessing if needed for consistency
#         from preprocessing import preprocess_data

#         # Load artifacts from volume
#         model = joblib.load("/root/app/final_best_model.pkl")
#         le_brand = joblib.load("/root/app/label_encoder_brand.pkl")
#         le_model = joblib.load("/root/app/label_encoder_model.pkl")
#         le_town = joblib.load("/root/app/label_encoder_town.pkl")
#         feature_names = joblib.load("/root/app/feature_names.pkl")

#         # Reuse the same prediction logic as local (see below)
#         return _predict_with_artifacts(payload, model, le_brand, le_model, le_town, feature_names)

#     @app.local_entrypoint()
#     def main(action: str = "train"):
#         if action == "train":
#             print("Starting remote training...")
#             summary = train_and_save.remote()
#             print("Training summary:", summary)
#         elif action == "predict":
#             print("Running a sample prediction...")
#             sample = {
#                 "brand": "TOYOTA",
#                 "model": "AQUA",
#                 "yom": 2016,
#                 "engine_cc": 1500,
#                 "gear": "Automatic",
#                 "fuel_type": "Hybrid",
#                 "mileage_km": 65000,
#                 "town": "Colombo",
#                 "leasing": "No Leasing",
#                 "condition": "USED",
#                 "air_condition": 1,
#                 "power_steering": 1,
#                 "power_mirror": 1,
#                 "power_window": 1
#             }
#             out = predict_price.remote(sample)
#             print("Prediction:", out)
#         else:
#             print("Available actions: 'train' or 'predict'")
#             print("Files are automatically mounted from your local directory.")
# else:
#     # Local helper that implements prediction logic given loaded artifacts
#     def _predict_with_artifacts(payload, model, le_brand, le_model, le_town, feature_names):
#         brand = payload.get("brand", "")
#         model_name = payload.get("model", "")
#         yom = int(payload.get("yom", 2015))
#         engine = float(payload.get("engine_cc", 1500))
#         gear = payload.get("gear", "Automatic")
#         fuel = payload.get("fuel_type", "Petrol")
#         mileage = float(payload.get("mileage_km", 50000))
#         town = payload.get("town", "Colombo")
#         leasing = payload.get("leasing", "No Leasing")
#         condition = payload.get("condition", "USED")
#         ac = int(payload.get("air_condition", 1))
#         ps = int(payload.get("power_steering", 1))
#         pm = int(payload.get("power_mirror", 1))
#         pw = int(payload.get("power_window", 1))

#         current_year = 2025
#         car_age = current_year - yom
#         mileage_per_year = mileage / (car_age + 1)
#         equipment_score = ac + ps + pm + pw

#         luxury_brands = ['BMW','MERCEDES-BENZ','AUDI','LEXUS','LAND ROVER','PORSCHE','JAGUAR','BENTLEY','MASERATI']
#         popular_brands = ['TOYOTA','HONDA','SUZUKI','NISSAN','MAZDA']
#         is_luxury = 1 if str(brand).upper() in luxury_brands else 0
#         is_popular = 1 if str(brand).upper() in popular_brands else 0
#         post_import = 1 if yom >= 2020 else 0

#         try:
#             brand_encoded = le_brand.transform([brand])[0]
#         except:
#             brand_encoded = 0
#         try:
#             model_encoded = le_model.transform([model_name])[0]
#         except:
#             model_encoded = 0
#         try:
#             town_encoded = le_town.transform([town])[0]
#         except:
#             town_encoded = 0

#         row = {
#             "YOM": yom,
#             "Engine (cc)": engine,
#             "Millage(KM)": mileage,
#             "Car_Age": car_age,
#             "Mileage_Per_Year": mileage_per_year,
#             "AIR CONDITION": ac,
#             "POWER STEERING": ps,
#             "POWER MIRROR": pm,
#             "POWER WINDOW": pw,
#             "Equipment_Score": equipment_score,
#             "Brand_Popularity": 0,
#             "Is_Luxury": is_luxury,
#             "Is_Popular_Brand": is_popular,
#             "Post_Import_Restriction": post_import,
#             "Brand_Encoded": brand_encoded,
#             "Model_Encoded": model_encoded,
#             "Town_Encoded": town_encoded,
#             f"Gear_{gear}": 1,
#             f"Fuel Type_{fuel}": 1,
#             f"Leasing_{leasing}": 1,
#             f"Condition_{condition}": 1,
#         }

#         df = pd.DataFrame([{fn: row.get(fn, 0) for fn in feature_names}], columns=feature_names)
#         price = float(model.predict(df)[0])
#         return {"predicted_price": round(price, 2), "unit": "LKR Lakhs"}

#     def predict_price(payload: dict) -> dict:
#         local_root = os.path.abspath('.')
#         artifact_dir = local_root
#         # Load artifacts from local project root
#         model = joblib.load(os.path.join(artifact_dir, "final_best_model.pkl"))
#         le_brand = joblib.load(os.path.join(artifact_dir, "label_encoder_brand.pkl"))
#         le_model = joblib.load(os.path.join(artifact_dir, "label_encoder_model.pkl"))
#         le_town = joblib.load(os.path.join(artifact_dir, "label_encoder_town.pkl"))
#         feature_names = joblib.load(os.path.join(artifact_dir, "feature_names.pkl"))
#         return _predict_with_artifacts(payload, model, le_brand, le_model, le_town, feature_names)

#     def main(action: str = "train"):
#         if action == "train":
#             print("Starting local training...")
#             summary = train_and_save()
#             print("Training summary:", summary)
#         elif action == "predict":
#             print("Running a sample prediction locally...")
#             sample = {
#                 "brand": "TOYOTA",
#                 "model": "AQUA",
#                 "yom": 2016,
#                 "engine_cc": 1500,
#                 "gear": "Automatic",
#                 "fuel_type": "Hybrid",
#                 "mileage_km": 65000,
#                 "town": "Colombo",
#                 "leasing": "No Leasing",
#                 "condition": "USED",
#                 "air_condition": 1,
#                 "power_steering": 1,
#                 "power_mirror": 1,
#                 "power_window": 1
#             }
#             out = predict_price(sample)
#             print("Prediction:", out)
#         else:
#             print("Available actions: 'train' or 'predict'")
#             print("Run locally: python -c \"from modal_app import main; main('train')\"")

# # Run commands:
# # 1. modal run modal_app.py::main --action=train   (when using Modal)
# # 2. modal run modal_app.py::main --action=predict (when using Modal)
# # Locally examples:
# # python -c "from modal_app import main; main('train')"
# # python -c "from modal_app import main; main('predict')"


# if __name__ == "__main__":
#     # Provide a small CLI so the module can be executed directly.
#     import argparse

#     parser = argparse.ArgumentParser(description="Run modal_app actions locally")
#     parser.add_argument("--action", choices=["train", "predict"], default="train",
#                         help="Action to run (train or predict). Default: train")
#     args = parser.parse_args()

#     # Call the module-level main (defined for local or modal modes)
#     try:
#         # main may be defined in either the modal branch or the local branch;
#         # call it with the chosen action.
#         main(args.action)
#     except NameError:
#         print("Error: no 'main' entrypoint found in modal_app.py. Ensure the file was not truncated.")
#     except Exception as e:
#         print(f"modal_app.__main__ error: {e}")



# modal_app.py (ENHANCED WITH 11 MODELS)
import os
import sys
import joblib
import pandas as pd
import numpy as np

# Try to import modal and detect whether the installed modal SDK supports
# the features used below (Mount, Volume, App). If not, fall back to
# local-only mode so you can run training/prediction locally without
# raising AttributeError at import time.
USE_MODAL = False
modal = None
try:
    import modal as _modal
    modal = _modal
    # Ensure required attributes exist
    if hasattr(modal, "App") and hasattr(modal, "Image") and hasattr(modal, "Volume") and hasattr(modal, "Mount"):
        USE_MODAL = True
    else:
        print("[modal_app] modal package installed but missing required attributes (Mount/Volume/App). Running in LOCAL fallback mode.")
except Exception:
    print("[modal_app] modal package not available or failed to import. Running in LOCAL fallback mode.")


if USE_MODAL:
    # 1) Define image with ALL required packages for 11 models
    image = (
        modal.Image.debian_slim()
        .pip_install(
            "pandas==2.2.2",
            "numpy==1.26.4",
            "scikit-learn==1.5.1",
            "xgboost==2.1.1",
            "lightgbm==4.5.0",
            "joblib==1.4.2"
        )
    )

    # 2) Create the app
    app = modal.App("car-price-ml-comprehensive")

    # 3) Volume for persistent storage
    volume = modal.Volume.from_name("car-price-vol", create_if_missing=True)

    # 4) Remote training function with ALL 11 MODELS
    @app.function(
        image=image,
        volumes={"/root/app": volume},
        timeout=60 * 45,  # Increased to 45 min for 11 models
        cpu=4.0,          # More CPU for parallel training
        memory=8192,      # More memory for KNN/SVR
        mounts=[modal.Mount.from_local_dir(".", remote_path="/root/app")]
    )
    def train_and_save():
        """
        Trains ALL 11 ML models on Modal and saves the best model.
        
        Models Trained:
        1. Linear Regression
        2. Ridge Regression
        3. Lasso Regression
        4. Elastic Net
        5. Decision Tree
        6. Random Forest
        7. Gradient Boosting
        8. XGBoost
        9. LightGBM
        10. K-Nearest Neighbors
        11. Support Vector Regression
        """
        from sklearn.model_selection import train_test_split
        from sklearn.preprocessing import StandardScaler
        from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet
        from sklearn.tree import DecisionTreeRegressor
        from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
        from sklearn.neighbors import KNeighborsRegressor
        from sklearn.svm import SVR
        from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error, mean_absolute_percentage_error
        import xgboost as xgb
        import lightgbm as lgb

        print("\n" + "="*80)
        print("COMPREHENSIVE MODEL TRAINING - 11 ALGORITHMS")
        print("="*80)

        # Debug: Check if files exist
        print("\nFiles in /root/app/:")
        for item in os.listdir("/root/app"):
            print(f"  - {item}")

        # Import preprocessing
        from preprocessing import preprocess_data
        print("✓ Successfully imported preprocess_data")

        data_path = "/root/app/car_price_dataset.csv"
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"car_price_dataset.csv not found at {data_path}")

        print(f"✓ Found dataset at {data_path}")

        # Preprocess data
        X, y, le_brand, le_model, le_town = preprocess_data(data_path)
        print(f"✓ Preprocessing complete: {X.shape[1]} features, {len(y)} samples")

        # Save feature names
        joblib.dump(list(X.columns), "/root/app/feature_names.pkl")
        print("✓ Saved feature names")

        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Scale features for KNN and SVR
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        joblib.dump(scaler, "/root/app/scaler.pkl")
        print("✓ Created StandardScaler for KNN/SVR")

        print(f"\nDataset split: {len(X_train)} train, {len(X_test)} test samples\n")

        # Dictionary to store all models and results
        models = {}
        results = []

        # ========================================
        # MODEL 1: LINEAR REGRESSION
        # ========================================
        print("-"*80)
        print("MODEL 1: LINEAR REGRESSION")
        print("-"*80)
        print("Theory: Assumes linear relationship y = β₀ + β₁x₁ + ... + βₙxₙ")
        lr = LinearRegression()
        lr.fit(X_train, y_train)
        models['Linear Regression'] = lr
        pred = lr.predict(X_test)
        r2 = r2_score(y_test, pred)
        mae = mean_absolute_error(y_test, pred)
        rmse = float(np.sqrt(mean_squared_error(y_test, pred)))
        mape = mean_absolute_percentage_error(y_test, pred) * 100
        print(f"✓ R²={r2:.4f} | MAE={mae:.2f} | RMSE={rmse:.2f} | MAPE={mape:.2f}%\n")
        results.append(('Linear Regression', r2, mae, rmse, mape, lr))

        # ========================================
        # MODEL 2: RIDGE REGRESSION
        # ========================================
        print("-"*80)
        print("MODEL 2: RIDGE REGRESSION (L2 Regularization)")
        print("-"*80)
        print("Theory: Linear + L2 penalty to prevent overfitting")
        ridge = Ridge(alpha=10.0)
        ridge.fit(X_train, y_train)
        models['Ridge Regression'] = ridge
        pred = ridge.predict(X_test)
        r2 = r2_score(y_test, pred)
        mae = mean_absolute_error(y_test, pred)
        rmse = float(np.sqrt(mean_squared_error(y_test, pred)))
        mape = mean_absolute_percentage_error(y_test, pred) * 100
        print(f"✓ R²={r2:.4f} | MAE={mae:.2f} | RMSE={rmse:.2f} | MAPE={mape:.2f}%\n")
        results.append(('Ridge Regression', r2, mae, rmse, mape, ridge))

        # ========================================
        # MODEL 3: LASSO REGRESSION
        # ========================================
        print("-"*80)
        print("MODEL 3: LASSO REGRESSION (L1 Regularization)")
        print("-"*80)
        print("Theory: Linear + L1 penalty for feature selection")
        lasso = Lasso(alpha=1.0, max_iter=5000)
        lasso.fit(X_train, y_train)
        models['Lasso Regression'] = lasso
        pred = lasso.predict(X_test)
        r2 = r2_score(y_test, pred)
        mae = mean_absolute_error(y_test, pred)
        rmse = float(np.sqrt(mean_squared_error(y_test, pred)))
        mape = mean_absolute_percentage_error(y_test, pred) * 100
        print(f"✓ R²={r2:.4f} | MAE={mae:.2f} | RMSE={rmse:.2f} | MAPE={mape:.2f}%\n")
        results.append(('Lasso Regression', r2, mae, rmse, mape, lasso))

        # ========================================
        # MODEL 4: ELASTIC NET
        # ========================================
        print("-"*80)
        print("MODEL 4: ELASTIC NET (L1 + L2)")
        print("-"*80)
        print("Theory: Combines Ridge and Lasso penalties")
        elastic = ElasticNet(alpha=1.0, l1_ratio=0.5, max_iter=5000)
        elastic.fit(X_train, y_train)
        models['Elastic Net'] = elastic
        pred = elastic.predict(X_test)
        r2 = r2_score(y_test, pred)
        mae = mean_absolute_error(y_test, pred)
        rmse = float(np.sqrt(mean_squared_error(y_test, pred)))
        mape = mean_absolute_percentage_error(y_test, pred) * 100
        print(f"✓ R²={r2:.4f} | MAE={mae:.2f} | RMSE={rmse:.2f} | MAPE={mape:.2f}%\n")
        results.append(('Elastic Net', r2, mae, rmse, mape, elastic))

        # ========================================
        # MODEL 5: DECISION TREE
        # ========================================
        print("-"*80)
        print("MODEL 5: DECISION TREE REGRESSOR")
        print("-"*80)
        print("Theory: Recursive binary splits based on feature thresholds")
        dt = DecisionTreeRegressor(max_depth=10, min_samples_split=20, random_state=42)
        dt.fit(X_train, y_train)
        models['Decision Tree'] = dt
        pred = dt.predict(X_test)
        r2 = r2_score(y_test, pred)
        mae = mean_absolute_error(y_test, pred)
        rmse = float(np.sqrt(mean_squared_error(y_test, pred)))
        mape = mean_absolute_percentage_error(y_test, pred) * 100
        print(f"✓ R²={r2:.4f} | MAE={mae:.2f} | RMSE={rmse:.2f} | MAPE={mape:.2f}%\n")
        results.append(('Decision Tree', r2, mae, rmse, mape, dt))

        # ========================================
        # MODEL 6: RANDOM FOREST
        # ========================================
        print("-"*80)
        print("MODEL 6: RANDOM FOREST REGRESSOR")
        print("-"*80)
        print("Theory: Ensemble of decision trees with bootstrap aggregation")
        rf = RandomForestRegressor(
            n_estimators=300,
            max_depth=20,
            min_samples_split=5,
            min_samples_leaf=2,
            max_features='sqrt',
            random_state=42,
            n_jobs=-1
        )
        rf.fit(X_train, y_train)
        models['Random Forest'] = rf
        pred = rf.predict(X_test)
        r2 = r2_score(y_test, pred)
        mae = mean_absolute_error(y_test, pred)
        rmse = float(np.sqrt(mean_squared_error(y_test, pred)))
        mape = mean_absolute_percentage_error(y_test, pred) * 100
        print(f"✓ R²={r2:.4f} | MAE={mae:.2f} | RMSE={rmse:.2f} | MAPE={mape:.2f}%\n")
        results.append(('Random Forest', r2, mae, rmse, mape, rf))

        # ========================================
        # MODEL 7: GRADIENT BOOSTING
        # ========================================
        print("-"*80)
        print("MODEL 7: GRADIENT BOOSTING REGRESSOR")
        print("-"*80)
        print("Theory: Sequential ensemble - each tree corrects previous errors")
        gb = GradientBoostingRegressor(
            n_estimators=250,
            learning_rate=0.05,
            max_depth=6,
            min_samples_split=5,
            subsample=0.8,
            random_state=42
        )
        gb.fit(X_train, y_train)
        models['Gradient Boosting'] = gb
        pred = gb.predict(X_test)
        r2 = r2_score(y_test, pred)
        mae = mean_absolute_error(y_test, pred)
        rmse = float(np.sqrt(mean_squared_error(y_test, pred)))
        mape = mean_absolute_percentage_error(y_test, pred) * 100
        print(f"✓ R²={r2:.4f} | MAE={mae:.2f} | RMSE={rmse:.2f} | MAPE={mape:.2f}%\n")
        results.append(('Gradient Boosting', r2, mae, rmse, mape, gb))

        # ========================================
        # MODEL 8: XGBOOST
        # ========================================
        print("-"*80)
        print("MODEL 8: XGBOOST REGRESSOR")
        print("-"*80)
        print("Theory: Optimized gradient boosting with regularization")
        xgb_model = xgb.XGBRegressor(
            n_estimators=400,
            learning_rate=0.05,
            max_depth=6,
            min_child_weight=3,
            subsample=0.8,
            colsample_bytree=0.8,
            gamma=0.1,
            reg_alpha=0.1,
            reg_lambda=1.0,
            random_state=42,
            n_jobs=-1,
            tree_method="hist"
        )
        xgb_model.fit(X_train, y_train)
        models['XGBoost'] = xgb_model
        pred = xgb_model.predict(X_test)
        r2 = r2_score(y_test, pred)
        mae = mean_absolute_error(y_test, pred)
        rmse = float(np.sqrt(mean_squared_error(y_test, pred)))
        mape = mean_absolute_percentage_error(y_test, pred) * 100
        print(f"✓ R²={r2:.4f} | MAE={mae:.2f} | RMSE={rmse:.2f} | MAPE={mape:.2f}%\n")
        results.append(('XGBoost', r2, mae, rmse, mape, xgb_model))

        # ========================================
        # MODEL 9: LIGHTGBM
        # ========================================
        print("-"*80)
        print("MODEL 9: LIGHTGBM REGRESSOR")
        print("-"*80)
        print("Theory: Fast gradient boosting with histogram-based algorithm")
        lgb_model = lgb.LGBMRegressor(
            n_estimators=300,
            learning_rate=0.05,
            max_depth=6,
            num_leaves=31,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1,
            verbose=-1
        )
        lgb_model.fit(X_train, y_train)
        models['LightGBM'] = lgb_model
        pred = lgb_model.predict(X_test)
        r2 = r2_score(y_test, pred)
        mae = mean_absolute_error(y_test, pred)
        rmse = float(np.sqrt(mean_squared_error(y_test, pred)))
        mape = mean_absolute_percentage_error(y_test, pred) * 100
        print(f"✓ R²={r2:.4f} | MAE={mae:.2f} | RMSE={rmse:.2f} | MAPE={mape:.2f}%\n")
        results.append(('LightGBM', r2, mae, rmse, mape, lgb_model))

        # ========================================
        # MODEL 10: K-NEAREST NEIGHBORS
        # ========================================
        print("-"*80)
        print("MODEL 10: K-NEAREST NEIGHBORS REGRESSOR")
        print("-"*80)
        print("Theory: Predicts based on average of K nearest training samples")
        knn = KNeighborsRegressor(n_neighbors=5, weights='distance')
        knn.fit(X_train_scaled, y_train)  # KNN needs scaled features
        models['KNN'] = knn
        pred = knn.predict(X_test_scaled)
        r2 = r2_score(y_test, pred)
        mae = mean_absolute_error(y_test, pred)
        rmse = float(np.sqrt(mean_squared_error(y_test, pred)))
        mape = mean_absolute_percentage_error(y_test, pred) * 100
        print(f"✓ R²={r2:.4f} | MAE={mae:.2f} | RMSE={rmse:.2f} | MAPE={mape:.2f}%")
        print("Note: KNN uses scaled features\n")
        results.append(('KNN', r2, mae, rmse, mape, knn))

        # ========================================
        # MODEL 11: SUPPORT VECTOR REGRESSION
        # ========================================
        print("-"*80)
        print("MODEL 11: SUPPORT VECTOR REGRESSION")
        print("-"*80)
        print("Theory: Finds hyperplane that best fits data with epsilon margin")
        svr = SVR(kernel='rbf', C=100, epsilon=0.1)
        svr.fit(X_train_scaled, y_train)  # SVR needs scaled features
        models['SVR'] = svr
        pred = svr.predict(X_test_scaled)
        r2 = r2_score(y_test, pred)
        mae = mean_absolute_error(y_test, pred)
        rmse = float(np.sqrt(mean_squared_error(y_test, pred)))
        mape = mean_absolute_percentage_error(y_test, pred) * 100
        print(f"✓ R²={r2:.4f} | MAE={mae:.2f} | RMSE={rmse:.2f} | MAPE={mape:.2f}%")
        print("Note: SVR uses scaled features\n")
        results.append(('SVR', r2, mae, rmse, mape, svr))

        # ========================================
        # SUMMARY TABLE
        # ========================================
        print("="*80)
        print("COMPREHENSIVE MODEL COMPARISON - ALL 11 MODELS")
        print("="*80)
        print(f"{'Model':<25} {'R²':<10} {'MAE':<10} {'RMSE':<10} {'MAPE':<10}")
        print("-"*80)
        
        results.sort(key=lambda x: x[1], reverse=True)  # Sort by R²
        
        for name, r2, mae, rmse, mape, _ in results:
            print(f"{name:<25} {r2:<10.4f} {mae:<10.2f} {rmse:<10.2f} {mape:<10.2f}")
        
        print("="*80)

        # Pick best model by R²
        best_name, best_r2, best_mae, best_rmse, best_mape, best_model = results[0]
        
        print(f"\n🏆 BEST MODEL: {best_name}")
        print(f"   R² = {best_r2:.4f} ({best_r2*100:.2f}%)")
        print(f"   MAE = {best_mae:.2f} Lakhs")
        print(f"   RMSE = {best_rmse:.2f} Lakhs")
        print(f"   MAPE = {best_mape:.2f}%")

        # ========================================
        # ADD THIS SECTION - FEATURE IMPORTANCE
        # ========================================
        print("\n" + "="*80)
        print("FEATURE IMPORTANCE ANALYSIS")
        print("="*80)

        # Check if best model has feature importance
        if hasattr(best_model, 'feature_importances_'):
            # Get feature names from preprocessing
            feature_names = list(X.columns)
            importances = best_model.feature_importances_
            
            # Create DataFrame
            feature_importance_df = pd.DataFrame({
                'Feature': feature_names,
                'Importance': importances
            }).sort_values('Importance', ascending=False)
            
            # Save to CSV
            feature_importance_df.to_csv('/root/app/feature_importance.csv', index=False)
            print("✓ Saved: feature_importance.csv")
            
            # Display top 15
            print("\n📊 Top 15 Most Important Features:\n")
            print(feature_importance_df.head(15).to_string(index=False))
            
            # Calculate cumulative importance
            feature_importance_df['Cumulative'] = feature_importance_df['Importance'].cumsum()
            
            # Features explaining 90% of predictions
            important_features = feature_importance_df[
                feature_importance_df['Cumulative'] <= 0.90
            ]
            
            print(f"\n✓ Top {len(important_features)} features explain 90% of predictions")
            
        else:
            print(f"⚠️ {best_name} does not have feature_importances_ attribute")

        print("="*80 + "\n")
# ========================================
        
        # Save best model to volume
        joblib.dump(best_model, "/root/app/final_best_model.pkl")
        print(f"\n✓ Saved best model: {best_name}")

        # Save encoders
        joblib.dump(le_brand, "/root/app/label_encoder_brand.pkl")
        joblib.dump(le_model, "/root/app/label_encoder_model.pkl")
        joblib.dump(le_town, "/root/app/label_encoder_town.pkl")
        print("✓ Saved encoders")

        # Save all models for ensemble (optional)
        joblib.dump(models, "/root/app/all_models.pkl")
        print("✓ Saved all 11 models for ensemble use")

        # Verify artifacts
        for fn in [
            "final_best_model.pkl",
            "label_encoder_brand.pkl", "label_encoder_model.pkl", "label_encoder_town.pkl",
            "feature_names.pkl", "scaler.pkl", "all_models.pkl"
        ]:
            if not os.path.exists(f"/root/app/{fn}"):
                raise FileNotFoundError(f"Missing artifact {fn} after training.")
        
        print("✓ All artifacts verified")
        print("="*80 + "\n")

        return {
            "best_model": best_name,
            "r2": best_r2,
            "mae": best_mae,
            "rmse": best_rmse,
            "mape": best_mape,
            "all_models": [r[0] for r in results],
            "all_r2_scores": {r[0]: r[1] for r in results}
        }

else:
    # LOCAL FALLBACK with ALL 11 MODELS
    def train_and_save():
        from sklearn.model_selection import train_test_split
        from sklearn.preprocessing import StandardScaler
        from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet
        from sklearn.tree import DecisionTreeRegressor
        from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
        from sklearn.neighbors import KNeighborsRegressor
        from sklearn.svm import SVR
        from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error, mean_absolute_percentage_error
        import xgboost as xgb
        import lightgbm as lgb

        print("\n" + "="*80)
        print("LOCAL TRAINING - 11 ML ALGORITHMS")
        print("="*80)

        local_root = os.path.abspath('.')
        print(f"\n[local] Working directory: {local_root}")

        try:
            from preprocessing import preprocess_data
        except Exception as e:
            raise RuntimeError("Failed to import preprocessing.py") from e

        data_path = os.path.join(local_root, "car_price_dataset.csv")
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"car_price_dataset.csv not found at {data_path}")

        X, y, le_brand, le_model, le_town = preprocess_data(data_path)
        print(f"✓ Preprocessing: {X.shape[1]} features, {len(y)} samples")

        artifact_dir = local_root
        joblib.dump(list(X.columns), os.path.join(artifact_dir, "feature_names.pkl"))

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Scaler for KNN/SVR
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        joblib.dump(scaler, os.path.join(artifact_dir, "scaler.pkl"))

        print(f"Train: {len(X_train)}, Test: {len(X_test)}\n")

        models = {}
        results = []

        # Train all 11 models (same as Modal version)
        print("Training Linear Regression...")
        lr = LinearRegression()
        lr.fit(X_train, y_train)
        pred = lr.predict(X_test)
        r2 = r2_score(y_test, pred)
        mae = mean_absolute_error(y_test, pred)
        rmse = float(np.sqrt(mean_squared_error(y_test, pred)))
        mape = mean_absolute_percentage_error(y_test, pred) * 100
        print(f"  R²={r2:.4f} | MAE={mae:.2f}")
        results.append(('Linear Regression', r2, mae, rmse, mape, lr))
        models['Linear Regression'] = lr

        print("Training Ridge Regression...")
        ridge = Ridge(alpha=10.0)
        ridge.fit(X_train, y_train)
        pred = ridge.predict(X_test)
        r2 = r2_score(y_test, pred)
        mae = mean_absolute_error(y_test, pred)
        rmse = float(np.sqrt(mean_squared_error(y_test, pred)))
        mape = mean_absolute_percentage_error(y_test, pred) * 100
        print(f"  R²={r2:.4f} | MAE={mae:.2f}")
        results.append(('Ridge Regression', r2, mae, rmse, mape, ridge))
        models['Ridge Regression'] = ridge

        print("Training Lasso Regression...")
        lasso = Lasso(alpha=1.0, max_iter=5000)
        lasso.fit(X_train, y_train)
        pred = lasso.predict(X_test)
        r2 = r2_score(y_test, pred)
        mae = mean_absolute_error(y_test, pred)
        rmse = float(np.sqrt(mean_squared_error(y_test, pred)))
        mape = mean_absolute_percentage_error(y_test, pred) * 100
        print(f"  R²={r2:.4f} | MAE={mae:.2f}")
        results.append(('Lasso Regression', r2, mae, rmse, mape, lasso))
        models['Lasso Regression'] = lasso

        print("Training Elastic Net...")
        elastic = ElasticNet(alpha=1.0, l1_ratio=0.5, max_iter=5000)
        elastic.fit(X_train, y_train)
        pred = elastic.predict(X_test)
        r2 = r2_score(y_test, pred)
        mae = mean_absolute_error(y_test, pred)
        rmse = float(np.sqrt(mean_squared_error(y_test, pred)))
        mape = mean_absolute_percentage_error(y_test, pred) * 100
        print(f"  R²={r2:.4f} | MAE={mae:.2f}")
        results.append(('Elastic Net', r2, mae, rmse, mape, elastic))
        models['Elastic Net'] = elastic

        print("Training Decision Tree...")
        dt = DecisionTreeRegressor(max_depth=10, min_samples_split=20, random_state=42)
        dt.fit(X_train, y_train)
        pred = dt.predict(X_test)
        r2 = r2_score(y_test, pred)
        mae = mean_absolute_error(y_test, pred)
        rmse = float(np.sqrt(mean_squared_error(y_test, pred)))
        mape = mean_absolute_percentage_error(y_test, pred) * 100
        print(f"  R²={r2:.4f} | MAE={mae:.2f}")
        results.append(('Decision Tree', r2, mae, rmse, mape, dt))
        models['Decision Tree'] = dt

        print("Training Random Forest...")
        rf = RandomForestRegressor(n_estimators=200, max_depth=20, random_state=42, n_jobs=-1)
        rf.fit(X_train, y_train)
        pred = rf.predict(X_test)
        r2 = r2_score(y_test, pred)
        mae = mean_absolute_error(y_test, pred)
        rmse = float(np.sqrt(mean_squared_error(y_test, pred)))
        mape = mean_absolute_percentage_error(y_test, pred) * 100
        print(f"  R²={r2:.4f} | MAE={mae:.2f}")
        results.append(('Random Forest', r2, mae, rmse, mape, rf))
        models['Random Forest'] = rf

        print("Training Gradient Boosting...")
        gb = GradientBoostingRegressor(n_estimators=200, learning_rate=0.05, random_state=42)
        gb.fit(X_train, y_train)
        pred = gb.predict(X_test)
        r2 = r2_score(y_test, pred)
        mae = mean_absolute_error(y_test, pred)
        rmse = float(np.sqrt(mean_squared_error(y_test, pred)))
        mape = mean_absolute_percentage_error(y_test, pred) * 100
        print(f"  R²={r2:.4f} | MAE={mae:.2f}")
        results.append(('Gradient Boosting', r2, mae, rmse, mape, gb))
        models['Gradient Boosting'] = gb

        print("Training XGBoost...")
        xgb_model = xgb.XGBRegressor(n_estimators=200, learning_rate=0.05, random_state=42, n_jobs=-1)
        xgb_model.fit(X_train, y_train)
        pred = xgb_model.predict(X_test)
        r2 = r2_score(y_test, pred)
        mae = mean_absolute_error(y_test, pred)
        rmse = float(np.sqrt(mean_squared_error(y_test, pred)))
        mape = mean_absolute_percentage_error(y_test, pred) * 100
        print(f"  R²={r2:.4f} | MAE={mae:.2f}")
        results.append(('XGBoost', r2, mae, rmse, mape, xgb_model))
        models['XGBoost'] = xgb_model

        print("Training LightGBM...")
        lgb_model = lgb.LGBMRegressor(n_estimators=200, learning_rate=0.05, random_state=42, n_jobs=-1, verbose=-1)
        lgb_model.fit(X_train, y_train)
        pred = lgb_model.predict(X_test)
        r2 = r2_score(y_test, pred)
        mae = mean_absolute_error(y_test, pred)
        rmse = float(np.sqrt(mean_squared_error(y_test, pred)))
        mape = mean_absolute_percentage_error(y_test, pred) * 100
        print(f"  R²={r2:.4f} | MAE={mae:.2f}")
        results.append(('LightGBM', r2, mae, rmse, mape, lgb_model))
        models['LightGBM'] = lgb_model

        print("Training KNN (scaled features)...")
        knn = KNeighborsRegressor(n_neighbors=5, weights='distance')
        knn.fit(X_train_scaled, y_train)
        pred = knn.predict(X_test_scaled)
        r2 = r2_score(y_test, pred)
        mae = mean_absolute_error(y_test, pred)
        rmse = float(np.sqrt(mean_squared_error(y_test, pred)))
        mape = mean_absolute_percentage_error(y_test, pred) * 100
        print(f"  R²={r2:.4f} | MAE={mae:.2f}")
        results.append(('KNN', r2, mae, rmse, mape, knn))
        models['KNN'] = knn

        print("Training SVR (scaled features)...")
        svr = SVR(kernel='rbf', C=100, epsilon=0.1)
        svr.fit(X_train_scaled, y_train)
        pred = svr.predict(X_test_scaled)
        r2 = r2_score(y_test, pred)
        mae = mean_absolute_error(y_test, pred)
        rmse = float(np.sqrt(mean_squared_error(y_test, pred)))
        mape = mean_absolute_percentage_error(y_test, pred) * 100
        print(f"  R²={r2:.4f} | MAE={mae:.2f}")
        results.append(('SVR', r2, mae, rmse, mape, svr))
        models['SVR'] = svr

        # Summary
        print("\n" + "="*80)
        print("MODEL COMPARISON")
        print("="*80)
        results.sort(key=lambda x: x[1], reverse=True)
        for name, r2, mae, rmse, mape, _ in results:
            print(f"{name:<25} R²={r2:.4f} MAE={mae:.2f}")
        
        best_name, best_r2, best_mae, best_rmse, best_mape, best_model = results[0]
        print(f"\n🏆 Best: {best_name} (R²={best_r2:.4f})\n")

        # ========================================
        # FEATURE IMPORTANCE - ADD THIS
        # ========================================
        print("\n" + "="*80)
        print("FEATURE IMPORTANCE ANALYSIS")
        print("="*80)

        if hasattr(best_model, 'feature_importances_'):
            feature_names = list(X.columns)
            importances = best_model.feature_importances_
            
            feature_importance_df = pd.DataFrame({
                'Feature': feature_names,
                'Importance': importances
            }).sort_values('Importance', ascending=False)
            
            # Save locally
            feature_importance_df.to_csv(os.path.join(artifact_dir, 'feature_importance.csv'), index=False)
            print("✓ Saved: feature_importance.csv")
            
            print("\n📊 Top 15 Most Important Features:\n")
            print(feature_importance_df.head(15).to_string(index=False))
            
            feature_importance_df['Cumulative'] = feature_importance_df['Importance'].cumsum()
            important_features = feature_importance_df[feature_importance_df['Cumulative'] <= 0.90]
            
            print(f"\n✓ Top {len(important_features)} features explain 90% of predictions")
        else:
            print(f"⚠️ {best_name} does not have feature_importances_ attribute")

        print("="*80 + "\n")
        # ========================================

        # Save best model and encoders
        joblib.dump(best_model, os.path.join(artifact_dir, "final_best_model.pkl"))
        joblib.dump(le_brand, os.path.join(artifact_dir, "label_encoder_brand.pkl"))
        joblib.dump(le_model, os.path.join(artifact_dir, "label_encoder_model.pkl"))
        joblib.dump(le_town, os.path.join(artifact_dir, "label_encoder_town.pkl"))
        joblib.dump(models, os.path.join(artifact_dir, "all_models.pkl"))

        print(f"✓ Saved artifacts in {artifact_dir}")
        return {"best_model": best_name, "r2": best_r2, "mae": best_mae, "rmse": best_rmse, "mape": best_mape}


# Prediction and entrypoint (same as before)
if USE_MODAL:
    @app.function(
        image=image,
        volumes={"/root/app": volume},
        timeout=60 * 5,
        cpu=1.0,
        memory=2048,
        mounts=[modal.Mount.from_local_dir(".", remote_path="/root/app")]
    )
    def predict_price(payload: dict) -> dict:
        from preprocessing import preprocess_data
        model = joblib.load("/root/app/final_best_model.pkl")
        le_brand = joblib.load("/root/app/label_encoder_brand.pkl")
        le_model = joblib.load("/root/app/label_encoder_model.pkl")
        le_town = joblib.load("/root/app/label_encoder_town.pkl")
        feature_names = joblib.load("/root/app/feature_names.pkl")
        return _predict_with_artifacts(payload, model, le_brand, le_model, le_town, feature_names)

    @app.local_entrypoint()
    def main(action: str = "train"):
        if action == "train":
            print("Starting remote training (11 models)...")
            summary = train_and_save.remote()
            print("Training summary:", summary)
        elif action == "predict":
            sample = {
                "brand": "TOYOTA", "model": "AQUA", "yom": 2016,
                "engine_cc": 1500, "gear": "Automatic", "fuel_type": "Hybrid",
                "mileage_km": 65000, "town": "Colombo", "leasing": "No Leasing",
                "condition": "USED", "air_condition": 1, "power_steering": 1,
                "power_mirror": 1, "power_window": 1
            }
            out = predict_price.remote(sample)
            print("Prediction:", out)
        else:
            print("Available actions: 'train' or 'predict'")
else:
    def _predict_with_artifacts(payload, model, le_brand, le_model, le_town, feature_names):
        brand = payload.get("brand", "")
        model_name = payload.get("model", "")
        yom = int(payload.get("yom", 2015))
        engine = float(payload.get("engine_cc", 1500))
        gear = payload.get("gear", "Automatic")
        fuel = payload.get("fuel_type", "Petrol")
        mileage = float(payload.get("mileage_km", 50000))
        town = payload.get("town", "Colombo")
        leasing = payload.get("leasing", "No Leasing")
        condition = payload.get("condition", "USED")
        ac = int(payload.get("air_condition", 1))
        ps = int(payload.get("power_steering", 1))
        pm = int(payload.get("power_mirror", 1))
        pw = int(payload.get("power_window", 1))

        current_year = 2025
        car_age = current_year - yom
        mileage_per_year = mileage / (car_age + 1)
        equipment_score = ac + ps + pm + pw

        luxury_brands = ['BMW','MERCEDES-BENZ','AUDI','LEXUS','LAND ROVER','PORSCHE','JAGUAR','BENTLEY','MASERATI']
        popular_brands = ['TOYOTA','HONDA','SUZUKI','NISSAN','MAZDA']
        is_luxury = 1 if str(brand).upper() in luxury_brands else 0
        is_popular = 1 if str(brand).upper() in popular_brands else 0
        post_import = 1 if yom >= 2020 else 0

        try:
            brand_encoded = le_brand.transform([brand])[0]
        except:
            brand_encoded = 0
        try:
            model_encoded = le_model.transform([model_name])[0]
        except:
            model_encoded = 0
        try:
            town_encoded = le_town.transform([town])[0]
        except:
            town_encoded = 0

        row = {
            "YOM": yom, "Engine (cc)": engine, "Millage(KM)": mileage,
            "Car_Age": car_age, "Mileage_Per_Year": mileage_per_year,
            "AIR CONDITION": ac, "POWER STEERING": ps, "POWER MIRROR": pm, "POWER WINDOW": pw,
            "Equipment_Score": equipment_score, "Brand_Popularity": 0,
            "Is_Luxury": is_luxury, "Is_Popular_Brand": is_popular,
            "Post_Import_Restriction": post_import,
            "Brand_Encoded": brand_encoded, "Model_Encoded": model_encoded, "Town_Encoded": town_encoded,
            f"Gear_{gear}": 1, f"Fuel Type_{fuel}": 1, f"Leasing_{leasing}": 1, f"Condition_{condition}": 1,
        }

        df = pd.DataFrame([{fn: row.get(fn, 0) for fn in feature_names}], columns=feature_names)
        price = float(model.predict(df)[0])
        return {"predicted_price": round(price, 2), "unit": "LKR Lakhs"}

    def predict_price(payload: dict) -> dict:
        local_root = os.path.abspath('.')
        model = joblib.load(os.path.join(local_root, "final_best_model.pkl"))
        le_brand = joblib.load(os.path.join(local_root, "label_encoder_brand.pkl"))
        le_model = joblib.load(os.path.join(local_root, "label_encoder_model.pkl"))
        le_town = joblib.load(os.path.join(local_root, "label_encoder_town.pkl"))
        feature_names = joblib.load(os.path.join(local_root, "feature_names.pkl"))
        return _predict_with_artifacts(payload, model, le_brand, le_model, le_town, feature_names)

    def main(action: str = "train"):
        if action == "train":
            print("Starting local training (11 models)...")
            summary = train_and_save()
            print("Training summary:", summary)
        elif action == "predict":
            sample = {
                "brand": "TOYOTA", "model": "AQUA", "yom": 2016,
                "engine_cc": 1500, "gear": "Automatic", "fuel_type": "Hybrid",
                "mileage_km": 65000, "town": "Colombo", "leasing": "No Leasing",
                "condition": "USED", "air_condition": 1, "power_steering": 1,
                "power_mirror": 1, "power_window": 1
            }
            out = predict_price(sample)
            print("Prediction:", out)
        else:
            print("Available actions: 'train' or 'predict'")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run modal_app with 11 ML models")
    parser.add_argument("--action", choices=["train", "predict"], default="train",
                        help="Action to run (default: train)")
    args = parser.parse_args()
    
    try:
        main(args.action)
    except NameError:
        print("Error: 'main' entrypoint not found")
    except Exception as e:
        print(f"Error: {e}")
