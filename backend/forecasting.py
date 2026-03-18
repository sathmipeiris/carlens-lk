# backend/forecasting.py
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from typing import Dict, List
import warnings
warnings.filterwarnings('ignore')

class CarPriceForecaster:
    """
    Time-series forecasting for car price trends
    
    Predicts:
    1. How prices will change over next 6-12 months
    2. Best time to buy/sell
    3. Depreciation curves by brand
    """
    
    def __init__(self, historical_data: pd.DataFrame):
        """
        Args:
            historical_data: DataFrame with columns [Date, Brand, Model, YOM, Price]
        """
        self.data = historical_data.copy()
        self.models = {}
        
    def prepare_time_series(self):
        """Convert data to time-series format"""
        # Ensure Date column
        if 'Scraped_Date' in self.data.columns:
            self.data['Date'] = pd.to_datetime(self.data['Scraped_Date'])
        elif 'Date' not in self.data.columns:
            # If no date, create fake timeline for demo
            self.data['Date'] = pd.date_range(
                end=datetime.now(),
                periods=len(self.data),
                freq='D'
            )
        
        # Sort by date
        self.data = self.data.sort_values('Date')
        
        # Create time features
        self.data['Year'] = self.data['Date'].dt.year
        self.data['Month'] = self.data['Date'].dt.month
        self.data['Quarter'] = self.data['Date'].dt.quarter
        self.data['Days_Since_Start'] = (self.data['Date'] - self.data['Date'].min()).dt.days
        
        print(f"✓ Prepared time-series with {len(self.data)} records")
        print(f"  Date range: {self.data['Date'].min()} to {self.data['Date'].max()}")
        
    def forecast_brand_trends(self, brand: str, months_ahead: int = 6) -> Dict:
        """
        Forecast price trends for a specific brand
        
        Returns:
            {
                'current_avg_price': float,
                'forecasted_prices': [list of prices],
                'forecast_dates': [list of dates],
                'trend': 'increasing' | 'decreasing' | 'stable',
                'confidence': float (0-1)
            }
        """
        # Filter data for brand
        brand_data = self.data[self.data['Brand'].str.upper() == brand.upper()].copy()
        
        if len(brand_data) < 10:
            return {'error': f'Insufficient data for {brand} (need at least 10 records)'}
        
        # Aggregate by month
        brand_data['YearMonth'] = brand_data['Date'].dt.to_period('M')
        monthly_avg = brand_data.groupby('YearMonth')['Price'].mean().reset_index()
        monthly_avg['Date'] = monthly_avg['YearMonth'].dt.to_timestamp()
        monthly_avg['Month_Num'] = range(len(monthly_avg))
        
        # Train forecasting model
        X = monthly_avg[['Month_Num']].values
        y = monthly_avg['Price'].values
        
        # Use Linear Regression for trend
        model = LinearRegression()
        model.fit(X, y)
        
        # Forecast future months
        last_month = monthly_avg['Month_Num'].max()
        future_months = np.array([[last_month + i] for i in range(1, months_ahead + 1)])
        forecasted_prices = model.predict(future_months)
        
        # Generate forecast dates
        last_date = monthly_avg['Date'].max()
        forecast_dates = [last_date + timedelta(days=30*i) for i in range(1, months_ahead + 1)]
        
        # Determine trend
        trend_slope = model.coef_[0]
        if trend_slope > 0.5:
            trend = 'increasing'
        elif trend_slope < -0.5:
            trend = 'decreasing'
        else:
            trend = 'stable'
        
        # Calculate R² as confidence
        from sklearn.metrics import r2_score
        y_pred = model.predict(X)
        confidence = max(0, r2_score(y, y_pred))
        
        return {
            'brand': brand,
            'current_avg_price': float(monthly_avg['Price'].iloc[-1]),
            'forecasted_prices': forecasted_prices.tolist(),
            'forecast_dates': [d.strftime('%Y-%m-%d') for d in forecast_dates],
            'trend': trend,
            'trend_slope': float(trend_slope),
            'confidence': float(confidence),
            'historical_data': monthly_avg[['Date', 'Price']].to_dict('records')
        }
    
    def depreciation_curve(self, brand: str, initial_price: float, years: int = 10) -> Dict:
        """
        Calculate depreciation curve for a brand
        
        Shows: How much value a car loses each year
        """
        brand_data = self.data[self.data['Brand'].str.upper() == brand.upper()].copy()
        
        if len(brand_data) < 20:
            return {'error': 'Insufficient data for depreciation analysis'}
        
        # Calculate car age
        current_year = datetime.now().year
        brand_data['Car_Age'] = current_year - brand_data['YOM']
        
        # Train depreciation model (Price ~ Car_Age)
        X = brand_data[['Car_Age']].values
        y = brand_data['Price'].values
        
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, y)
        
        # Predict depreciation over years
        ages = np.array([[i] for i in range(0, years + 1)])
        predicted_prices = model.predict(ages)
        
        # Normalize to initial price
        scale_factor = initial_price / predicted_prices[0]
        depreciated_prices = predicted_prices * scale_factor
        
        # Calculate depreciation rate
        depreciation_rates = []
        for i in range(1, len(depreciated_prices)):
            rate = (depreciated_prices[i-1] - depreciated_prices[i]) / depreciated_prices[i-1] * 100
            depreciation_rates.append(rate)
        
        return {
            'brand': brand,
            'initial_price': initial_price,
            'years': list(range(0, years + 1)),
            'depreciated_prices': depreciated_prices.tolist(),
            'depreciation_rates': depreciation_rates,
            'avg_annual_depreciation': np.mean(depreciation_rates),
            'retained_value_after_5y': (depreciated_prices[5] / initial_price * 100) if len(depreciated_prices) > 5 else None
        }
    
    def best_time_to_buy(self, brand: str, model: str = None) -> Dict:
        """
        Recommend best month to buy based on historical patterns
        
        Analyzes seasonality and price dips
        """
        # Filter data
        if model:
            filtered = self.data[
                (self.data['Brand'].str.upper() == brand.upper()) &
                (self.data['Model'].str.upper() == model.upper())
            ].copy()
        else:
            filtered = self.data[self.data['Brand'].str.upper() == brand.upper()].copy()
        
        if len(filtered) < 50:
            return {'recommendation': 'Insufficient data for seasonality analysis'}
        
        # Calculate average price by month
        filtered['Month'] = filtered['Date'].dt.month
        monthly_avg = filtered.groupby('Month')['Price'].agg(['mean', 'count']).reset_index()
        monthly_avg.columns = ['Month', 'Avg_Price', 'Count']
        
        # Find cheapest months
        cheapest_months = monthly_avg.nsmallest(3, 'Avg_Price')
        
        month_names = {
            1: 'January', 2: 'February', 3: 'March', 4: 'April',
            5: 'May', 6: 'June', 7: 'July', 8: 'August',
            9: 'September', 10: 'October', 11: 'November', 12: 'December'
        }
        
        recommendations = []
        for _, row in cheapest_months.iterrows():
            month_num = int(row['Month'])
            recommendations.append({
                'month': month_names[month_num],
                'month_num': month_num,
                'avg_price': float(row['Avg_Price']),
                'savings_vs_peak': float(monthly_avg['Avg_Price'].max() - row['Avg_Price']),
                'data_points': int(row['Count'])
            })
        
        return {
            'brand': brand,
            'model': model,
            'best_months_to_buy': recommendations,
            'peak_price_month': month_names[int(monthly_avg.nlargest(1, 'Avg_Price')['Month'].iloc[0])],
            'price_range': {
                'min': float(monthly_avg['Avg_Price'].min()),
                'max': float(monthly_avg['Avg_Price'].max()),
                'avg': float(monthly_avg['Avg_Price'].mean())
            }
        }
    
    def plot_forecast(self, forecast_data: Dict, save_path: str = 'forecast_plot.png'):
        """Visualize forecast"""
        plt.figure(figsize=(12, 6))
        
        # Historical data: accept pandas Timestamp, datetime, or string
        hist_dates = pd.to_datetime([d['Date'] for d in forecast_data['historical_data']]).to_pydatetime().tolist()
        hist_prices = [d['Price'] for d in forecast_data['historical_data']]
        
        plt.plot(hist_dates, hist_prices, 'b-o', label='Historical', linewidth=2)
        
        # Forecast: forecast_dates may be strings or datetimes
        forecast_dates = pd.to_datetime(forecast_data['forecast_dates']).to_pydatetime().tolist()
        forecast_prices = forecast_data['forecasted_prices']
        
        plt.plot(forecast_dates, forecast_prices, 'r--s', label='Forecast', linewidth=2)
        
        plt.xlabel('Date', fontsize=12, fontweight='bold')
        plt.ylabel('Price (LKR Lakhs)', fontsize=12, fontweight='bold')
        plt.title(f"{forecast_data['brand']} Price Forecast ({forecast_data['trend'].upper()} trend)", 
                 fontsize=14, fontweight='bold')
        plt.legend()
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(save_path, dpi=300)
        print(f"✓ Forecast plot saved to {save_path}")


# ========================================
# USAGE EXAMPLE
# ========================================
if __name__ == "__main__":
    # Load your dataset
    df = pd.read_csv('car_price_dataset.csv')
    
    # Add mock dates if not present
    if 'Scraped_Date' not in df.columns:
        df['Scraped_Date'] = pd.date_range(end=datetime.now(), periods=len(df), freq='D')
    
    forecaster = CarPriceForecaster(df)
    forecaster.prepare_time_series()
    
    # 1. Forecast Toyota prices for next 6 months
    toyota_forecast = forecaster.forecast_brand_trends('TOYOTA', months_ahead=6)
    print("\n" + "="*60)
    print("TOYOTA PRICE FORECAST (Next 6 Months)")
    print("="*60)
    print(f"Current Avg: {toyota_forecast['current_avg_price']:.2f} Lakhs")
    print(f"Trend: {toyota_forecast['trend'].upper()}")
    print(f"Confidence: {toyota_forecast['confidence']*100:.1f}%")
    print("\nForecasted Prices:")
    for date, price in zip(toyota_forecast['forecast_dates'], toyota_forecast['forecasted_prices']):
        print(f"  {date}: {price:.2f} Lakhs")
    
    # 2. Depreciation curve
    depreciation = forecaster.depreciation_curve('TOYOTA', initial_price=50, years=10)
    print("\n" + "="*60)
    print("TOYOTA DEPRECIATION CURVE (10 Years)")
    print("="*60)
    print(f"Initial Price: {depreciation['initial_price']} Lakhs")
    print(f"Avg Annual Depreciation: {depreciation['avg_annual_depreciation']:.1f}%")
    print(f"Value after 5 years: {depreciation['retained_value_after_5y']:.1f}%")
    
    # 3. Best time to buy
    best_time = forecaster.best_time_to_buy('TOYOTA')
    print("\n" + "="*60)
    print("BEST MONTHS TO BUY TOYOTA")
    print("="*60)
    for rec in best_time['best_months_to_buy']:
        print(f"  {rec['month']}: Avg {rec['avg_price']:.2f} Lakhs (save {rec['savings_vs_peak']:.2f} Lakhs)")
    
    # Plot forecast
    forecaster.plot_forecast(toyota_forecast)
