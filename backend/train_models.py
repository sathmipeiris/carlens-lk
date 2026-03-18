import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, mean_absolute_percentage_error
import xgboost as xgb
import joblib
import matplotlib.pyplot as plt
import seaborn as sns

from preprocessing import preprocess_data

# Load and preprocess data
X, y, le_brand, le_model, le_town = preprocess_data('car_price_dataset.csv')

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print(f"Training set: {X_train.shape}")
print(f"Test set: {X_test.shape}")

# Dictionary to store models and results
models = {}
results = {}


def evaluate_model(name, model, X_train, X_test, y_train, y_test):
    """Train and evaluate a model"""
    print(f"\n{'=' * 50}")
    print(f"Training {name}...")
    print(f"{'=' * 50}")

    # Train
    model.fit(X_train, y_train)

    # Predict
    y_train_pred = model.predict(X_train)
    y_test_pred = model.predict(X_test)

    # Metrics
    train_r2 = r2_score(y_train, y_train_pred)
    test_r2 = r2_score(y_test, y_test_pred)
    test_mae = mean_absolute_error(y_test, y_test_pred)
    test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))
    test_mape = mean_absolute_percentage_error(y_test, y_test_pred) * 100

    print(f"\nResults for {name}:")
    print(f"Train R²: {train_r2:.4f}")
    print(f"Test R²: {test_r2:.4f}")
    print(f"Test MAE: {test_mae:.4f}")
    print(f"Test RMSE: {test_rmse:.4f}")
    print(f"Test MAPE: {test_mape:.2f}%")

    # Store results
    results[name] = {
        'model': model,
        'train_r2': train_r2,
        'test_r2': test_r2,
        'mae': test_mae,
        'rmse': test_rmse,
        'mape': test_mape,
        'predictions': y_test_pred
    }

    return model


# 1. LINEAR REGRESSION (Baseline)
print("\n🔵 MODEL 1: LINEAR REGRESSION")
print("Theory: Assumes linear relationship between features and price")
print("Pros: Fast, interpretable")
print("Cons: May underfit complex relationships")
lr = LinearRegression()
evaluate_model("Linear Regression", lr, X_train, X_test, y_train, y_test)

# 2. RIDGE REGRESSION (Regularized Linear)
print("\n🟢 MODEL 2: RIDGE REGRESSION")
print("Theory: Linear regression with L2 regularization to prevent overfitting")
print("Pros: Handles multicollinearity better than linear regression")
ridge = Ridge(alpha=10)
evaluate_model("Ridge Regression", ridge, X_train, X_test, y_train, y_test)

# 3. RANDOM FOREST
print("\n🟠 MODEL 3: RANDOM FOREST")
print("Theory: Ensemble of decision trees, each trained on random subsets")
print("Pros: Handles non-linearity, feature interactions, robust to outliers")
print("Cons: Can be slow on large datasets")
rf = RandomForestRegressor(n_estimators=100, max_depth=20, random_state=42, n_jobs=-1)
evaluate_model("Random Forest", rf, X_train, X_test, y_train, y_test)

# 4. XGBOOST (Best for tabular data)
print("\n🔴 MODEL 4: XGBOOST")
print("Theory: Gradient boosting with regularization, builds trees sequentially")
print("Pros: State-of-art for tabular data, handles missing values, fast")
print("Why best for Sri Lankan market: Captures complex interactions (brand×age, mileage×year)")
xgb_model = xgb.XGBRegressor(
    n_estimators=200,
    learning_rate=0.05,
    max_depth=6,
    min_child_weight=3,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42
)
evaluate_model("XGBoost", xgb_model, X_train, X_test, y_train, y_test)

# 5. GRADIENT BOOSTING
print("\n🟣 MODEL 5: GRADIENT BOOSTING")
print("Theory: Similar to XGBoost but sklearn implementation")
gb = GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, max_depth=5, random_state=42)
evaluate_model("Gradient Boosting", gb, X_train, X_test, y_train, y_test)

# Compare all models
print("\n" + "=" * 80)
print("MODEL COMPARISON SUMMARY")
print("=" * 80)
comparison_df = pd.DataFrame({
    'Model': list(results.keys()),
    'Test R²': [results[m]['test_r2'] for m in results.keys()],
    'MAE': [results[m]['mae'] for m in results.keys()],
    'RMSE': [results[m]['rmse'] for m in results.keys()],
    'MAPE (%)': [results[m]['mape'] for m in results.keys()]
})
comparison_df = comparison_df.sort_values('Test R²', ascending=False)
print(comparison_df.to_string(index=False))

# Select best model
best_model_name = comparison_df.iloc[0]['Model']
best_model = results[best_model_name]['model']
print(f"\n🏆 Best Model: {best_model_name}")
print(f"   Test R²: {results[best_model_name]['test_r2']:.4f}")
print(f"   MAPE: {results[best_model_name]['mape']:.2f}%")

# Save best model and encoders
joblib.dump(best_model, 'best_model.pkl')
joblib.dump(le_brand, 'label_encoder_brand.pkl')
joblib.dump(le_model, 'label_encoder_model.pkl')
joblib.dump(le_town, 'label_encoder_town.pkl')
joblib.dump(X.columns.tolist(), 'feature_names.pkl')

print("\n✅ Models saved successfully!")
print("   - best_model.pkl")
print("   - label_encoder_brand.pkl")
print("   - label_encoder_model.pkl")
print("   - label_encoder_town.pkl")
print("   - feature_names.pkl")
