import argparse
import numpy as np
from sklearn.model_selection import cross_val_score, KFold
from sklearn.ensemble import RandomForestRegressor
from preprocessing import preprocess_data

def main(data_path, n_splits):
    # Load preprocessed data (adjust call if your preprocess_data signature differs)
    X, y, *rest = preprocess_data(data_path)
    # Use numeric features (or ensure X is numeric / already encoded)
    X_num = X.select_dtypes(include=[np.number])
    if X_num.shape[1] == 0:
        raise SystemExit("No numeric features found in X. Ensure preprocess_data returns numeric/encoded features.")
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    cv = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    scores = cross_val_score(model, X_num, y, cv=cv, scoring='r2', n_jobs=-1)
    print(f"CV R² mean: {scores.mean():.4f}  std: {scores.std():.4f}")
    print("Fold scores:", scores)

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Run cross-validation")
    p.add_argument("--data", default="car_price_dataset.csv", help="Path to dataset used by preprocess_data")
    p.add_argument("--splits", type=int, default=5, help="Number of CV folds")
    args = p.parse_args()
    main(args.data, args.splits)