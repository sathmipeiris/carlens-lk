# fetch_economic_data.py
"""
Fetch real-time and historical economic data for car price prediction
Run this periodically (daily/weekly) to update economic indicators
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import json
import os

class EconomicDataFetcher:
    def __init__(self, cache_file='economic_data_cache.json'):
        self.cache_file = cache_file
        self.data = self.load_cache()
    
    def load_cache(self):
        """Load cached data if exists"""
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_cache(self):
        """Save data to cache"""
        with open(self.cache_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def fetch_exchange_rates(self):
        """
        Fetch USD/LKR exchange rate
        Source: Central Bank of Sri Lanka or exchangerate-api.com
        """
        try:
            # Option 1: Free API (fallback)
            url = "https://api.exchangerate-api.com/v4/latest/USD"
            response = requests.get(url, timeout=5)
            data = response.json()
            
            usd_lkr = data['rates'].get('LKR', 360)  # Default 360 if unavailable
            
            self.data['usd_lkr'] = usd_lkr
            self.data['last_updated_exchange'] = datetime.now().isoformat()
            
            print(f"✓ Exchange Rate: 1 USD = {usd_lkr:.2f} LKR")
            return usd_lkr
        
        except Exception as e:
            print(f"⚠️ Could not fetch exchange rate: {e}")
            # Fallback to recent average
            return self.data.get('usd_lkr', 360)
    
    def fetch_fuel_prices(self):
        """
        Fetch current fuel prices in Sri Lanka
        Source: Ceylon Petroleum Corporation (manual update needed)
        """
        # Since CPC doesn't have public API, use recent averages
        # Update these manually or scrape from news sites
        
        fuel_prices = {
            'petrol_92': 420,   # LKR per liter (2024 average)
            'diesel': 380,      # LKR per liter
            'last_updated': datetime.now().isoformat()
        }
        
        self.data['fuel_prices'] = fuel_prices
        print(f"✓ Fuel Prices: Petrol {fuel_prices['petrol_92']} LKR/L, Diesel {fuel_prices['diesel']} LKR/L")
        return fuel_prices
    
    def fetch_inflation_rate(self):
        """
        Fetch Sri Lanka inflation rate
        Source: Central Bank of Sri Lanka / World Bank API
        """
        try:
            # World Bank API for Sri Lanka (country code: LK)
            url = "https://api.worldbank.org/v2/country/LK/indicator/FP.CPI.TOTL.ZG?format=json&date=2020:2024"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            # Get most recent year
            if len(data) > 1:
                recent_data = data[1][0]  # Most recent
                inflation_rate = float(recent_data['value']) if recent_data['value'] else 5.0
            else:
                inflation_rate = 5.0  # Default
            
            self.data['inflation_rate'] = inflation_rate
            self.data['last_updated_inflation'] = datetime.now().isoformat()
            
            print(f"✓ Inflation Rate: {inflation_rate:.2f}%")
            return inflation_rate
        
        except Exception as e:
            print(f"⚠️ Could not fetch inflation: {e}")
            return self.data.get('inflation_rate', 5.0)
    
    def fetch_interest_rates(self):
        """
        Fetch CBSL policy interest rate
        Source: Central Bank of Sri Lanka (manual update)
        """
        # CBSL doesn't have public API, use recent values
        interest_rate = 15.0  # 2024 average (update quarterly)
        
        self.data['cbsl_rate'] = interest_rate
        self.data['last_updated_interest'] = datetime.now().isoformat()
        
        print(f"✓ CBSL Interest Rate: {interest_rate}%")
        return interest_rate
    
    def get_import_restriction_status(self, year):
        """
        Determine import restriction severity by year
        Historical policy analysis
        """
        if year < 2018:
            return 0.0  # No restrictions
        elif year < 2020:
            return 0.3  # Moderate restrictions
        else:
            return 1.0  # Severe ban (2020+)
    
    def get_seasonal_factors(self, month=None, quarter=None):
        """
        Calculate seasonal premium based on month/quarter
        """
        if month is None:
            month = datetime.now().month
        if quarter is None:
            quarter = (month - 1) // 3 + 1
        
        # December premium (year-end bonuses)
        december_premium = 0.05 if month == 12 else 0.0
        
        # Q1 premium (New Year car purchases)
        q1_premium = 0.03 if quarter == 1 else 0.0
        
        return {
            'month': month,
            'quarter': quarter,
            'december_premium': december_premium,
            'q1_premium': q1_premium
        }
    
    def get_crisis_discount(self, year):
        """
        Apply discount during economic crisis years
        Sri Lanka 2022-2023 economic crisis
        """
        if 2022 <= year <= 2023:
            return 0.10  # 10% panic selling discount
        return 0.0
    
    def fetch_all(self):
        """Fetch all economic data"""
        print("\n" + "="*60)
        print("FETCHING ECONOMIC DATA")
        print("="*60)
        
        self.fetch_exchange_rates()
        self.fetch_fuel_prices()
        self.fetch_inflation_rate()
        self.fetch_interest_rates()
        
        self.save_cache()
        print("\n✓ All economic data fetched and cached")
        print("="*60 + "\n")
        
        return self.data
    
    def get_data(self):
        """Get current cached data"""
        # Refresh if data is older than 24 hours
        if 'last_updated_exchange' in self.data:
            last_update = datetime.fromisoformat(self.data['last_updated_exchange'])
            if datetime.now() - last_update > timedelta(days=1):
                print("Cache expired, fetching fresh data...")
                return self.fetch_all()
        else:
            print("No cached data, fetching fresh data...")
            return self.fetch_all()
        
        return self.data


# ========================================
# CLI Interface
# ========================================
if __name__ == "__main__":
    fetcher = EconomicDataFetcher()
    
    # Fetch fresh data
    data = fetcher.fetch_all()
    
    # Display summary
    print("\n" + "="*60)
    print("ECONOMIC DATA SUMMARY")
    print("="*60)
    print(json.dumps(data, indent=2))
    print("="*60)
