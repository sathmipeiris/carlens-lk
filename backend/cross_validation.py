# backend/cross_validation.py
from sklearn.model_selection import cross_val_score, KFold, StratifiedKFold
from sklearn.ensemble import RandomForestRegressor
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

class CrossValidationAnalyzer:
    """Robust model evaluation with cross-validation"""
    
    def kfold_evaluation(self, model, X, y, n_splits=5):
        """
        Evaluate model with K-Fold cross-validation
        
        Returns: Mean and std of scores across all folds
        """
        kfold = KFold(n_splits=n_splits, shuffle=True, random_state=42)
        
        scores = cross_val_score(model, X, y, cv=kfold, scoring='r2', n_jobs=-1)
        
        print(f"\n{'='*60}")
        print(f" K-FOLD CROSS-VALIDATION ({n_splits} Folds)")
        print(f"{'='*60}")
        
        for i, score in enumerate(scores, 1):
            print(f"Fold {i}: R² = {score:.4f}")
        
        print(f"{'='*60}")
        print(f"Mean R²:     {scores.mean():.4f}")
        print(f"Std Dev:     {scores.std():.4f}")
        print(f"95% CI:      [{scores.mean()-1.96*scores.std():.4f}, {scores.mean()+1.96*scores.std():.4f}]")
        print(f"{'='*60}\n")
        
        return scores
    
    def stratified_kfold_classification(self, model, X, y, n_splits=5):
        """For classification problems (balanced class distribution)"""
        skfold = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
        scores = cross_val_score(model, X, y, cv=skfold, scoring='accuracy', n_jobs=-1)
        return scores
    
    def plot_cv_results(self, scores):
        """Visualize cross-validation scores"""
        plt.figure(figsize=(12, 6))
        
        folds = range(1, len(scores) + 1)
        plt.bar(folds, scores, color='steelblue', edgecolor='black', alpha=0.7)
        plt.axhline(y=scores.mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {scores.mean():.4f}')
        plt.fill_between(folds, scores.mean() - scores.std(), scores.mean() + scores.std(), 
                         alpha=0.2, color='red', label=f'±1 Std: {scores.std():.4f}')
        
        plt.xlabel('Fold Number', fontsize=12, fontweight='bold')
        plt.ylabel('R² Score', fontsize=12, fontweight='bold')
        plt.title('Cross-Validation Results', fontsize=14, fontweight='bold')
        plt.legend(fontsize=11)
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        plt.savefig('cv_results.png', dpi=300)
        print("✓ CV results plot saved to cv_results.png")

# Usage
if __name__ == "__main__":
    df = pd.read_csv('car_price_dataset.csv')
    X = df.drop('Price', axis=1)
    y = df['Price']
    
    model = RandomForestRegressor(n_estimators=300, max_depth=20, random_state=42)
    
    analyzer = CrossValidationAnalyzer()
    scores = analyzer.kfold_evaluation(model, X, y, n_splits=5)
    analyzer.plot_cv_results(scores)

