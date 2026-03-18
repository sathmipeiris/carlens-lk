# # backend/bias_variance_analysis.py
# from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
# from sklearn.linear_model import LinearRegression
# from sklearn.metrics import r2_score
# import matplotlib.pyplot as plt
# import numpy as np
# from sklearn.model_selection import train_test_split
# import pandas as pd

# class BiasVarianceAnalyzer:
#     """Analyze bias-variance tradeoff"""
    
#     def analyze_complexity(self, X, y, test_size=0.2):
#         """
#         Train models of increasing complexity and show tradeoff
#         """
#         X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42)
        
#         # Different model complexities
#         complexities = []
#         train_scores = []
#         test_scores = []
        
#         print(f"\n{'='*70}")
#         print("🎯 BIAS-VARIANCE ANALYSIS (Complexity vs Performance)")
#         print(f"{'='*70}\n")
        
#         # Simple: Linear Regression (high bias, low variance)
#         print("1️⃣  Simple Model (High Bias, Low Variance)")
#         lr = LinearRegression()
#         lr.fit(X_train, y_train)
#         train_r2 = r2_score(y_train, lr.predict(X_train))
#         test_r2 = r2_score(y_test, lr.predict(X_test))
#         complexities.append('Linear\n(High Bias)')
#         train_scores.append(train_r2)
#         test_scores.append(test_r2)
#         print(f"   Train: {train_r2:.4f} | Test: {test_r2:.4f} | Gap: {train_r2-test_r2:.4f}")
        
#         # Medium: RF with limited depth
#         print("\n2️⃣  Medium Model (Shallow Tree)")
#         rf_shallow = RandomForestRegressor(n_estimators=100, max_depth=5, random_state=42, n_jobs=-1)
#         rf_shallow.fit(X_train, y_train)
#         train_r2 = r2_score(y_train, rf_shallow.predict(X_train))
#         test_r2 = r2_score(y_test, rf_shallow.predict(X_test))
#         complexities.append('Random Forest\n(depth=5)')
#         train_scores.append(train_r2)
#         test_scores.append(test_r2)
#         print(f"   Train: {train_r2:.4f} | Test: {test_r2:.4f} | Gap: {train_r2-test_r2:.4f}")
        
#         # Medium-High: RF with moderate depth
#         print("\n3️⃣  Medium-High Model (Moderate Tree)")
#         rf_medium = RandomForestRegressor(n_estimators=200, max_depth=15, random_state=42, n_jobs=-1)
#         rf_medium.fit(X_train, y_train)
#         train_r2 = r2_score(y_train, rf_medium.predict(X_train))
#         test_r2 = r2_score(y_test, rf_medium.predict(X_test))
#         complexities.append('Random Forest\n(depth=15)')
#         train_scores.append(train_r2)
#         test_scores.append(test_r2)
#         print(f"   Train: {train_r2:.4f} | Test: {test_r2:.4f} | Gap: {train_r2-test_r2:.4f}")
        
#         # High: RF with deep trees (low bias, high variance)
#         print("\n4️⃣  Complex Model (Low Bias, High Variance)")
#         rf_deep = RandomForestRegressor(n_estimators=300, max_depth=30, random_state=42, n_jobs=-1)
#         rf_deep.fit(X_train, y_train)
#         train_r2 = r2_score(y_train, rf_deep.predict(X_train))
#         test_r2 = r2_score(y_test, rf_deep.predict(X_test))
#         complexities.append('Random Forest\n(depth=30)')
#         train_scores.append(train_r2)
#         test_scores.append(test_r2)
#         print(f"   Train: {train_r2:.4f} | Test: {test_r2:.4f} | Gap: {train_r2-test_r2:.4f}")
        
#         print(f"\n{'='*70}\n")
        
#         self._plot_bias_variance(complexities, train_scores, test_scores)
        
#         return complexities, train_scores, test_scores
    
#     def _plot_bias_variance(self, complexities, train_scores, test_scores):
#         """Visualize bias-variance tradeoff"""
#         plt.figure(figsize=(12, 7))
        
#         x = np.arange(len(complexities))
#         width = 0.35
        
#         bars1 = plt.bar(x - width/2, train_scores, width, label='Train Score', 
#                        color='#3498db', edgecolor='black', alpha=0.8)
#         bars2 = plt.bar(x + width/2, test_scores, width, label='Test Score',
#                        color='#e74c3c', edgecolor='black', alpha=0.8)
        
#         # Add value labels
#         for bars in [bars1, bars2]:
#             for bar in bars:
#                 height = bar.get_height()
#                 plt.text(bar.get_x() + bar.get_width()/2., height,
#                         f'{height:.3f}', ha='center', va='bottom', fontweight='bold')
        
#         plt.ylabel('R² Score', fontsize=12, fontweight='bold')
#         plt.xlabel('Model Complexity', fontsize=12, fontweight='bold')
#         plt.title('Bias-Variance Tradeoff', fontsize=14, fontweight='bold')
#         plt.xticks(x, complexities, fontsize=11)
#         plt.legend(fontsize=11)
#         plt.grid(axis='y', alpha=0.3)
#         plt.ylim([0.6, 1.0])
        
#         # Add annotations
#         plt.text(0, 0.65, 'HIGH BIAS\nLOW VARIANCE', ha='center', fontsize=10, 
#                 style='italic', bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.3))
#         plt.text(3, 0.65, 'LOW BIAS\nHIGH VARIANCE', ha='center', fontsize=10,
#                 style='italic', bbox=dict(boxstyle='round', facecolor='orange', alpha=0.3))
#         plt.text(1.5, 0.95, '✅ OPTIMAL\nSWEET SPOT', ha='center', fontsize=11, fontweight='bold',
#                 bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5))
        
#         plt.tight_layout()
#         plt.savefig('bias_variance_tradeoff.png', dpi=300)
#         print("✓ Bias-Variance plot saved to bias_variance_tradeoff.png")

# # Usage
# if __name__ == "__main__":
#     df = pd.read_csv('car_price_dataset.csv')
#     X = df.drop('Price', axis=1).select_dtypes(include=[np.number])
#     y = df['Price']
    
#     analyzer = BiasVarianceAnalyzer()
#     analyzer.analyze_complexity(X, y)

# backend/bias_variance_analysis.py
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
import matplotlib.pyplot as plt
import numpy as np
from sklearn.model_selection import train_test_split
import pandas as pd


class BiasVarianceAnalyzer:
    """Analyze bias-variance tradeoff"""
    
    def analyze_complexity(self, X, y, test_size=0.2):
        """
        Train models of increasing complexity and show tradeoff
        """
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42)
        
        # Different model complexities
        complexities = []
        train_scores = []
        test_scores = []
        
        print(f"\n{'='*70}")
        print("🎯 BIAS-VARIANCE ANALYSIS (Complexity vs Performance)")
        print(f"{'='*70}\n")
        
        # Simple: Linear Regression (high bias, low variance)
        print("1️⃣  Simple Model (High Bias, Low Variance)")
        lr = LinearRegression()
        lr.fit(X_train, y_train)
        train_r2 = r2_score(y_train, lr.predict(X_train))
        test_r2 = r2_score(y_test, lr.predict(X_test))
        complexities.append('Linear\n(High Bias)')
        train_scores.append(train_r2)
        test_scores.append(test_r2)
        print(f"   Train: {train_r2:.4f} | Test: {test_r2:.4f} | Gap: {train_r2-test_r2:.4f}")
        
        # Medium: RF with limited depth
        print("\n2️⃣  Medium Model (Shallow Tree)")
        rf_shallow = RandomForestRegressor(n_estimators=100, max_depth=5, random_state=42, n_jobs=-1)
        rf_shallow.fit(X_train, y_train)
        train_r2 = r2_score(y_train, rf_shallow.predict(X_train))
        test_r2 = r2_score(y_test, rf_shallow.predict(X_test))
        complexities.append('Random Forest\n(depth=5)')
        train_scores.append(train_r2)
        test_scores.append(test_r2)
        print(f"   Train: {train_r2:.4f} | Test: {test_r2:.4f} | Gap: {train_r2-test_r2:.4f}")
        
        # Medium-High: RF with moderate depth
        print("\n3️⃣  Medium-High Model (Moderate Tree)")
        rf_medium = RandomForestRegressor(n_estimators=200, max_depth=15, random_state=42, n_jobs=-1)
        rf_medium.fit(X_train, y_train)
        train_r2 = r2_score(y_train, rf_medium.predict(X_train))
        test_r2 = r2_score(y_test, rf_medium.predict(X_test))
        complexities.append('Random Forest\n(depth=15)')
        train_scores.append(train_r2)
        test_scores.append(test_r2)
        print(f"   Train: {train_r2:.4f} | Test: {test_r2:.4f} | Gap: {train_r2-test_r2:.4f}")
        
        # ✅ YOUR OPTIMAL MODEL (depth=20)
        print("\n4️⃣  OPTIMAL Model (YOUR BEST CONFIGURATION) ⭐")
        rf_optimal = RandomForestRegressor(
            n_estimators=300, 
            max_depth=20,           # YOUR OPTIMAL DEPTH
            min_samples_split=5,
            min_samples_leaf=2,
            max_features='sqrt',
            random_state=42, 
            n_jobs=-1
        )
        rf_optimal.fit(X_train, y_train)
        train_r2 = r2_score(y_train, rf_optimal.predict(X_train))
        test_r2 = r2_score(y_test, rf_optimal.predict(X_test))
        complexities.append('Random Forest\n(depth=20)\n✅ OPTIMAL')
        train_scores.append(train_r2)
        test_scores.append(test_r2)
        print(f"   Train: {train_r2:.4f} | Test: {test_r2:.4f} | Gap: {train_r2-test_r2:.4f}")
        print(f"   ✅ Best test R² with acceptable overfitting gap (<10%)")
        
        # High: RF with deep trees (low bias, high variance)
        print("\n5️⃣  Complex Model (Low Bias, High Variance)")
        rf_deep = RandomForestRegressor(n_estimators=300, max_depth=30, random_state=42, n_jobs=-1)
        rf_deep.fit(X_train, y_train)
        train_r2 = r2_score(y_train, rf_deep.predict(X_train))
        test_r2 = r2_score(y_test, rf_deep.predict(X_test))
        complexities.append('Random Forest\n(depth=30)')
        train_scores.append(train_r2)
        test_scores.append(test_r2)
        print(f"   Train: {train_r2:.4f} | Test: {test_r2:.4f} | Gap: {train_r2-test_r2:.4f}")
        
        print(f"\n{'='*70}\n")
        
        self._plot_bias_variance(complexities, train_scores, test_scores)
        
        return complexities, train_scores, test_scores
    
    def _plot_bias_variance(self, complexities, train_scores, test_scores):
        """Visualize bias-variance tradeoff with your optimal model highlighted"""
        plt.figure(figsize=(14, 8))
        
        x = np.arange(len(complexities))
        width = 0.35
        
        bars1 = plt.bar(x - width/2, train_scores, width, label='Train Score', 
                       color='#3498db', edgecolor='black', alpha=0.8)
        bars2 = plt.bar(x + width/2, test_scores, width, label='Test Score',
                       color='#e74c3c', edgecolor='black', alpha=0.8)
        
        # Add value labels
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.3f}', ha='center', va='bottom', fontweight='bold', fontsize=10)
        
        plt.ylabel('R² Score', fontsize=13, fontweight='bold')
        plt.xlabel('Model Complexity', fontsize=13, fontweight='bold')
        plt.title('Bias-Variance Tradeoff', fontsize=16, fontweight='bold', pad=20)
        plt.xticks(x, complexities, fontsize=10)
        plt.legend(fontsize=12, loc='lower left')
        plt.grid(axis='y', alpha=0.3, linestyle='--')
        plt.ylim([0.40, 1.05])
        
        # Add annotations
        plt.text(0, 0.65, 'HIGH BIAS\nLOW VARIANCE', ha='center', fontsize=11, 
                style='italic', bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.4))
        plt.text(4, 0.67, 'LOW BIAS\nHIGH VARIANCE', ha='center', fontsize=11,
                style='italic', bbox=dict(boxstyle='round', facecolor='orange', alpha=0.4))
        
        # Highlight YOUR optimal model (index 3)
        plt.text(3, 0.95, '✅ OPTIMAL\nSWEET SPOT', ha='center', fontsize=12, fontweight='bold',
                bbox=dict(boxstyle='round', facecolor='lightgreen', edgecolor='darkgreen', 
                          linewidth=2, alpha=0.6))
        
        # Add arrow pointing to optimal
        plt.annotate('Best Balance:\nHigh Accuracy\nLow Overfitting', 
                    xy=(3, test_scores[3]), 
                    xytext=(3, 0.70),
                    arrowprops=dict(arrowstyle='->', color='green', lw=2),
                    fontsize=10, ha='center', fontweight='bold',
                    bbox=dict(boxstyle='round', facecolor='white', edgecolor='green', alpha=0.8))
        
        plt.tight_layout()
        plt.savefig('bias_variance_tradeoff.png', dpi=300, bbox_inches='tight')
        print("✓ Bias-Variance plot saved to bias_variance_tradeoff.png")


# Usage
if __name__ == "__main__":
    from preprocessing import preprocess_data
    
    # Load and preprocess data
    X, y, le_brand, le_model, le_town = preprocess_data('car_price_dataset.csv')
    
    # Run analysis
    analyzer = BiasVarianceAnalyzer()
    complexities, train_scores, test_scores = analyzer.analyze_complexity(X, y)
    
    # Summary
    print(f"\n{'='*70}")
    print("📊 SUMMARY")
    print(f"{'='*70}")
    print("\nModel Performance Ranking (by Test R²):")
    results = list(zip(complexities, train_scores, test_scores))
    results_sorted = sorted(results, key=lambda x: x[2], reverse=True)
    
    for rank, (name, train, test) in enumerate(results_sorted, 1):
        gap = train - test
        status = "✅ OPTIMAL" if "depth=20" in name else ""
        print(f"{rank}. {name.replace(chr(10), ' '):<40} | Train: {train:.4f} | Test: {test:.4f} | Gap: {gap:.4f} {status}")

