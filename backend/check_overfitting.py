# backend/check_overfitting.py
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

class OverfittingAnalyzer:
    """Detect and fix overfitting"""
    
    def analyze_model(self, model, X_train, X_test, y_train, y_test):
        """Analyze if model is overfitting"""
        
        # Get predictions
        y_train_pred = model.predict(X_train)
        y_test_pred = model.predict(X_test)
        
        # Calculate metrics
        train_r2 = r2_score(y_train, y_train_pred)
        test_r2 = r2_score(y_test, y_test_pred)
        
        gap = train_r2 - test_r2
        
        print(f"\n{'='*60}")
        print("🔍 OVERFITTING ANALYSIS")
        print(f"{'='*60}")
        print(f"Train R²: {train_r2:.4f}")
        print(f"Test R²:  {test_r2:.4f}")
        print(f"Gap:      {gap:.4f}")
        print(f"{'='*60}")
        
        if gap < 0.05:
            status = "✅ GOOD: Model is generalizing well!"
        elif gap < 0.15:
            status = "⚠️  WARNING: Slight overfitting detected"
        else:
            status = "❌ DANGER: Severe overfitting!"
        
        print(status)
        print(f"{'='*60}\n")
        
        return {
            'train_r2': train_r2,
            'test_r2': test_r2,
            'gap': gap,
            'status': status,
            'is_overfitting': gap > 0.10
        }
    
    def visualize_learning_curve(self, model, X, y, cv_splits=5):
        """Plot learning curves to detect overfitting"""
        from sklearn.model_selection import learning_curve
        
        train_sizes, train_scores, val_scores = learning_curve(
            model, X, y,
            cv=cv_splits,
            train_sizes=np.linspace(0.1, 1.0, 10),
            n_jobs=-1
        )
        
        train_mean = np.mean(train_scores, axis=1)
        val_mean = np.mean(val_scores, axis=1)
        train_std = np.std(train_scores, axis=1)
        val_std = np.std(val_scores, axis=1)
        
        plt.figure(figsize=(12, 6))
        plt.plot(train_sizes, train_mean, 'b-o', label='Training Score', linewidth=2)
        plt.fill_between(train_sizes, train_mean - train_std, train_mean + train_std, alpha=0.2)
        
        plt.plot(train_sizes, val_mean, 'r-s', label='Validation Score', linewidth=2)
        plt.fill_between(train_sizes, val_mean - val_std, val_mean + val_std, alpha=0.2)
        
        plt.xlabel('Training Set Size', fontsize=12, fontweight='bold')
        plt.ylabel('R² Score', fontsize=12, fontweight='bold')
        plt.title('Learning Curve (Overfitting Detection)', fontsize=14, fontweight='bold')
        plt.legend(fontsize=11)
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig('learning_curve.png', dpi=300)
        print("✓ Learning curve saved to learning_curve.png")
        
        return train_sizes, train_mean, val_mean

# Usage
if __name__ == "__main__":
    # Load your data
    X = pd.read_csv('your_features.csv')
    y = pd.read_csv('your_target.csv')
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Your model
    model = RandomForestRegressor(n_estimators=300, max_depth=20, random_state=42)
    model.fit(X_train, y_train)
    
    # Analyze
    analyzer = OverfittingAnalyzer()
    analyzer.analyze_model(model, X_train, X_test, y_train, y_test)
    analyzer.visualize_learning_curve(model, X, y)
