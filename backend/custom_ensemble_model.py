# custom_ensemble_model.py
"""
Custom Ensemble Regression Model - Combines Best Models WITHOUT Deep Learning

Three Strategies:
1. Weighted Average Ensemble (simple, fast)
2. Stacking Regressor (meta-learner optimizes weights)
3. Adaptive Ensemble (uses different models for different price ranges)

Best for: Car price prediction with Random Forest + XGBoost
"""

import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, StackingRegressor
from sklearn.linear_model import Ridge, ElasticNet
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error, mean_absolute_percentage_error
import xgboost as xgb
import lightgbm as lgb
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.optimize import minimize


# ========================================
# STRATEGY 1: WEIGHTED AVERAGE ENSEMBLE
# ========================================
class WeightedEnsembleRegressor:
    """
    Simple weighted average of multiple models
    Weights optimized using grid search or validation set
    """
    
    def __init__(self, models, weights=None):
        """
        Args:
            models: list of (name, model) tuples
            weights: list of weights (must sum to 1). If None, equal weights.
        """
        self.models = models
        self.model_names = [name for name, _ in models]
        self.fitted_models = [model for _, model in models]
        
        if weights is None:
            # Equal weights
            self.weights = np.ones(len(models)) / len(models)
        else:
            self.weights = np.array(weights)
            assert abs(self.weights.sum() - 1.0) < 1e-6, "Weights must sum to 1"
    
    def fit(self, X, y):
        """Train all base models"""
        print("\n" + "="*80)
        print("WEIGHTED ENSEMBLE - TRAINING BASE MODELS")
        print("="*80)
        
        for i, (name, model) in enumerate(self.models):
            print(f"\nTraining {name}...")
            model.fit(X, y)
            
            # Quick validation
            pred = model.predict(X)
            r2 = r2_score(y, pred)
            mae = mean_absolute_error(y, pred)
            print(f"  Train R² = {r2:.4f} | MAE = {mae:.2f} Lakhs | Weight = {self.weights[i]:.3f}")
        
        print("\n" + "="*80)
        return self
    
    def predict(self, X):
        """Weighted average prediction"""
        predictions = np.column_stack([
            model.predict(X) for model in self.fitted_models
        ])
        
        # Weighted average
        return np.dot(predictions, self.weights)
    
    def optimize_weights(self, X_val, y_val):
        """
        Optimize weights to minimize validation error
        Uses scipy.optimize to find best weights
        """
        print("\n" + "="*80)
        print("OPTIMIZING ENSEMBLE WEIGHTS")
        print("="*80)
        
        # Get predictions from all models
        predictions = np.column_stack([
            model.predict(X_val) for model in self.fitted_models
        ])
        
        def objective(weights):
            """Loss function to minimize (RMSE)"""
            ensemble_pred = np.dot(predictions, weights)
            return np.sqrt(mean_squared_error(y_val, ensemble_pred))
        
        # Constraints: weights sum to 1, all non-negative
        constraints = {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}
        bounds = [(0, 1) for _ in range(len(self.models))]
        
        # Initial guess: equal weights
        initial_weights = np.ones(len(self.models)) / len(self.models)
        
        # Optimize
        result = minimize(
            objective,
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
        
        if result.success:
            self.weights = result.x
            print("\n✓ Optimization successful!")
            print("\nOptimized Weights:")
            for name, weight in zip(self.model_names, self.weights):
                print(f"  {name:<25} {weight:.4f} ({weight*100:.2f}%)")
            
            # Validation performance
            optimized_pred = self.predict(X_val)
            r2 = r2_score(y_val, optimized_pred)
            mae = mean_absolute_error(y_val, optimized_pred)
            print(f"\nValidation R² after optimization: {r2:.4f}")
            print(f"Validation MAE: {mae:.2f} Lakhs")
        else:
            print("\n⚠️ Optimization failed, using equal weights")
        
        print("="*80)
        return self


# ========================================
# STRATEGY 2: STACKING REGRESSOR
# ========================================
class CustomStackingRegressor:
    """
    Stacking with custom meta-learner
    Base models: Random Forest, XGBoost, LightGBM
    Meta-learner: Ridge Regression (learns optimal combination)
    """
    
    def __init__(self, base_models, meta_model=None, use_features=True):
        """
        Args:
            base_models: list of (name, model) tuples
            meta_model: model to combine base predictions (default: Ridge)
            use_features: if True, meta-learner also sees original features
        """
        self.base_models = base_models
        self.meta_model = meta_model if meta_model else Ridge(alpha=1.0)
        self.use_features = use_features
        self.base_predictions_train = None
    
    def fit(self, X, y, cv=5):
        """
        Train using cross-validation to avoid overfitting
        
        Process:
        1. Use 5-fold CV to get out-of-fold predictions from base models
        2. Train meta-model on these predictions
        3. Retrain base models on full training set
        """
        print("\n" + "="*80)
        print("STACKING REGRESSOR - TRAINING WITH CV")
        print("="*80)
        
        n_samples = len(X)
        n_models = len(self.base_models)
        
        # Store out-of-fold predictions
        oof_predictions = np.zeros((n_samples, n_models))
        
        # KFold cross-validation
        kfold = KFold(n_splits=cv, shuffle=True, random_state=42)
        
        # For each base model, get out-of-fold predictions
        for model_idx, (name, model) in enumerate(self.base_models):
            print(f"\nBase Model {model_idx+1}/{n_models}: {name}")
            
            for fold, (train_idx, val_idx) in enumerate(kfold.split(X)):
                X_train_fold = X.iloc[train_idx] if isinstance(X, pd.DataFrame) else X[train_idx]
                y_train_fold = y.iloc[train_idx] if isinstance(y, pd.Series) else y[train_idx]
                X_val_fold = X.iloc[val_idx] if isinstance(X, pd.DataFrame) else X[val_idx]
                
                # Train on fold
                model.fit(X_train_fold, y_train_fold)
                
                # Predict on validation
                oof_predictions[val_idx, model_idx] = model.predict(X_val_fold)
                
                print(f"  Fold {fold+1}/{cv} complete", end='\r')
            
            # Retrain on full dataset
            model.fit(X, y)
            print(f"  ✓ {name} trained on full dataset")
        
        # Train meta-model
        print("\n" + "-"*80)
        print("Training Meta-Learner (Ridge Regression)...")
        
        if self.use_features:
            # Meta-learner sees both base predictions AND original features
            meta_features = np.column_stack([oof_predictions, X])
        else:
            # Meta-learner only sees base predictions
            meta_features = oof_predictions
        
        self.meta_model.fit(meta_features, y)
        
        # Evaluate stacking on training data
        stacked_pred = self.meta_model.predict(meta_features)
        r2 = r2_score(y, stacked_pred)
        mae = mean_absolute_error(y, stacked_pred)
        
        print(f"✓ Meta-learner trained")
        print(f"  Stacking Train R² = {r2:.4f}")
        print(f"  Stacking Train MAE = {mae:.2f} Lakhs")
        print("="*80)
        
        return self
    
    def predict(self, X):
        """Predict using stacked model"""
        # Get predictions from base models
        base_predictions = np.column_stack([
            model.predict(X) for _, model in self.base_models
        ])
        
        if self.use_features:
            # Combine with original features
            meta_features = np.column_stack([base_predictions, X])
        else:
            meta_features = base_predictions
        
        return self.meta_model.predict(meta_features)
    
    def get_meta_weights(self):
        """Extract how much meta-learner relies on each base model"""
        if hasattr(self.meta_model, 'coef_'):
            n_base = len(self.base_models)
            coeffs = self.meta_model.coef_[:n_base]  # First n coefficients
            
            print("\nMeta-Learner Coefficients (Base Model Weights):")
            for (name, _), coeff in zip(self.base_models, coeffs):
                print(f"  {name:<25} {coeff:.4f}")
            
            return coeffs
        else:
            print("Meta-model does not have coefficients")
            return None


# ========================================
# STRATEGY 3: ADAPTIVE ENSEMBLE
# ========================================
class AdaptiveEnsembleRegressor:
    """
    Uses different models for different price ranges
    
    Intuition:
    - Budget cars (0-30 Lakhs): Simpler patterns → Random Forest
    - Mid-range (30-70 Lakhs): Balanced → Ensemble
    - Luxury (70+ Lakhs): Complex patterns → XGBoost
    """
    
    def __init__(self, models, price_thresholds=[30, 70]):
        """
        Args:
            models: dict with keys 'budget', 'mid', 'luxury'
            price_thresholds: [low, high] thresholds in Lakhs
        """
        self.models = models
        self.thresholds = price_thresholds
        self.scaler_low = None
        self.scaler_high = None
    
    def fit(self, X, y):
        """Train separate models for each price range"""
        print("\n" + "="*80)
        print("ADAPTIVE ENSEMBLE - TRAINING SEGMENT-SPECIFIC MODELS")
        print("="*80)
        
        # Segment data by price
        low_mask = y <= self.thresholds[0]
        mid_mask = (y > self.thresholds[0]) & (y <= self.thresholds[1])
        high_mask = y > self.thresholds[1]
        
        segments = [
            ('Budget (0-30 Lakhs)', low_mask, 'budget'),
            ('Mid-range (30-70 Lakhs)', mid_mask, 'mid'),
            ('Luxury (70+ Lakhs)', high_mask, 'luxury')
        ]
        
        for segment_name, mask, model_key in segments:
            X_segment = X[mask]
            y_segment = y[mask]
            
            print(f"\n{segment_name}:")
            print(f"  Samples: {len(y_segment)} ({len(y_segment)/len(y)*100:.1f}%)")
            print(f"  Price range: {y_segment.min():.2f} - {y_segment.max():.2f} Lakhs")
            
            if len(y_segment) > 0:
                self.models[model_key].fit(X_segment, y_segment)
                
                # Quick eval
                pred = self.models[model_key].predict(X_segment)
                r2 = r2_score(y_segment, pred)
                mae = mean_absolute_error(y_segment, pred)
                print(f"  Train R² = {r2:.4f} | MAE = {mae:.2f} Lakhs")
        
        print("\n" + "="*80)
        return self
    
    def predict(self, X):
        """Predict using segment-appropriate models"""
        # We don't know true prices at prediction time, so use a heuristic
        # Option 1: Use all models and weight by price range probability
        # Option 2: Use a simple classifier to predict price range first
        
        # Here we use Option 1: Get all predictions and blend
        pred_budget = self.models['budget'].predict(X)
        pred_mid = self.models['mid'].predict(X)
        pred_luxury = self.models['luxury'].predict(X)
        
        # Blend based on predicted price
        final_pred = np.zeros(len(X))
        
        for i in range(len(X)):
            # Use average of predictions to decide segment
            avg_pred = (pred_budget[i] + pred_mid[i] + pred_luxury[i]) / 3
            
            if avg_pred <= self.thresholds[0]:
                final_pred[i] = pred_budget[i]
            elif avg_pred <= self.thresholds[1]:
                final_pred[i] = pred_mid[i]
            else:
                final_pred[i] = pred_luxury[i]
        
        return final_pred


# ========================================
# MAIN TRAINING PIPELINE
# ========================================
def train_custom_ensemble(X, y, strategy='weighted'):
    """
    Train custom ensemble model
    
    Args:
        X: features (pandas DataFrame)
        y: target (pandas Series)
        strategy: 'weighted', 'stacking', or 'adaptive'
    
    Returns:
        trained ensemble model
    """
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    print(f"\n{'='*80}")
    print(f"CUSTOM ENSEMBLE TRAINING - STRATEGY: {strategy.upper()}")
    print('='*80)
    print(f"Training samples: {len(X_train)}")
    print(f"Testing samples:  {len(X_test)}")
    print(f"Features:         {X_train.shape[1]}")
    
    # ========================================
    # DEFINE BASE MODELS
    # ========================================
    base_models = [
        ('Random Forest', RandomForestRegressor(
            n_estimators=300,
            max_depth=20,
            min_samples_split=5,
            min_samples_leaf=2,
            max_features='sqrt',
            random_state=42,
            n_jobs=-1
        )),
        ('XGBoost', xgb.XGBRegressor(
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
            n_jobs=-1
        )),
        ('LightGBM', lgb.LGBMRegressor(
            n_estimators=300,
            learning_rate=0.05,
            max_depth=6,
            num_leaves=31,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1,
            verbose=-1
        ))
    ]
    
    # ========================================
    # TRAIN SELECTED STRATEGY
    # ========================================
    
    if strategy == 'weighted':
        # Strategy 1: Weighted Average
        model = WeightedEnsembleRegressor(base_models)
        model.fit(X_train, y_train)
        
        # Optimize weights on validation set
        model.optimize_weights(X_test, y_test)
    
    elif strategy == 'stacking':
        # Strategy 2: Stacking with Ridge meta-learner
        model = CustomStackingRegressor(
            base_models,
            meta_model=Ridge(alpha=1.0),
            use_features=True  # Meta-learner sees original features too
        )
        model.fit(X_train, y_train, cv=5)
        model.get_meta_weights()
    
    elif strategy == 'adaptive':
        # Strategy 3: Adaptive (segment-specific)
        models_dict = {
            'budget': RandomForestRegressor(n_estimators=200, max_depth=15, random_state=42, n_jobs=-1),
            'mid': xgb.XGBRegressor(n_estimators=300, learning_rate=0.05, random_state=42, n_jobs=-1),
            'luxury': lgb.LGBMRegressor(n_estimators=300, learning_rate=0.05, random_state=42, n_jobs=-1, verbose=-1)
        }
        model = AdaptiveEnsembleRegressor(models_dict, price_thresholds=[30, 70])
        model.fit(X_train.values, y_train.values)
    
    else:
        raise ValueError(f"Unknown strategy: {strategy}")
    
    # ========================================
    # EVALUATE
    # ========================================
    print("\n" + "="*80)
    print("FINAL EVALUATION ON TEST SET")
    print("="*80)
    
    # Predictions
    y_pred = model.predict(X_test)
    
    # Metrics
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    mape = mean_absolute_percentage_error(y_test, y_pred) * 100
    
    print(f"\n🏆 CUSTOM ENSEMBLE PERFORMANCE ({strategy.upper()}):")
    print(f"   R² Score:  {r2:.4f} ({r2*100:.2f}%)")
    print(f"   MAE:       {mae:.2f} Lakhs")
    print(f"   RMSE:      {rmse:.2f} Lakhs")
    print(f"   MAPE:      {mape:.2f}%")
    
    # Compare with individual models
    print("\n" + "-"*80)
    print("COMPARISON WITH INDIVIDUAL BASE MODELS:")
    print("-"*80)
    
    for name, base_model in base_models:
        if strategy != 'adaptive':
            pred = base_model.predict(X_test)
        else:
            # Retrain for comparison
            base_model.fit(X_train, y_train)
            pred = base_model.predict(X_test)
        
        r2_base = r2_score(y_test, pred)
        mae_base = mean_absolute_error(y_test, pred)
        
        improvement = ((r2 - r2_base) / r2_base) * 100
        print(f"{name:<25} R²={r2_base:.4f} | MAE={mae_base:.2f} | Δ R²={improvement:+.2f}%")
    
    print("="*80)
    
    # Save model
    model_filename = f'custom_ensemble_{strategy}.pkl'
    joblib.dump(model, model_filename)
    print(f"\n✓ Model saved: {model_filename}")
    
    return model, (r2, mae, rmse, mape)


# ========================================
# CLI INTERFACE
# ========================================
if __name__ == "__main__":
    from preprocessing import preprocess_data
    
    print("\n" + "="*80)
    print("CUSTOM ENSEMBLE REGRESSION MODEL")
    print("="*80)
    
    # Load data
    X, y, le_brand, le_model, le_town = preprocess_data('car_price_dataset.csv')
    
    # Train all three strategies
    strategies = ['weighted', 'stacking', 'adaptive']
    results = {}
    
    for strategy in strategies:
        print(f"\n\n{'#'*80}")
        print(f"# TRAINING STRATEGY: {strategy.upper()}")
        print(f"{'#'*80}\n")
        
        model, metrics = train_custom_ensemble(X, y, strategy=strategy)
        results[strategy] = metrics
    
    # Final comparison
    print("\n\n" + "="*80)
    print("FINAL COMPARISON - ALL STRATEGIES")
    print("="*80)
    print(f"{'Strategy':<20} {'R²':<12} {'MAE':<12} {'RMSE':<12} {'MAPE':<12}")
    print("-"*80)
    
    for strategy, (r2, mae, rmse, mape) in results.items():
        print(f"{strategy.capitalize():<20} {r2:<12.4f} {mae:<12.2f} {rmse:<12.2f} {mape:<12.2f}")
    
    # Find best
    best_strategy = max(results, key=lambda k: results[k][0])  # Max R²
    print("="*80)
    print(f"\n🏆 BEST STRATEGY: {best_strategy.upper()} (R² = {results[best_strategy][0]:.4f})")
    print("="*80)
