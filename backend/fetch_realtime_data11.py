# backend/fetch_realtime_data.py
import requests
import pandas as pd
from datetime import datetime
import json

class EconomicDataFetcher:
    """Fetch real-time economic indicators"""
    
    def __init__(self):
        self.cache = {}
    
    def get_exchange_rate(self):
        """Get current USD/LKR exchange rate"""
        try:
            url = "https://api.exchangerate-api.com/v4/latest/USD"
            response = requests.get(url, timeout=5)
            data = response.json()
            lkr_rate = data['rates'].get('LKR', 360)
            
            return {
                'usd_lkr_rate': lkr_rate,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Exchange rate fetch error: {e}")
            return {'usd_lkr_rate': 360, 'timestamp': None}
    
    def get_sri_lanka_inflation(self):
        """Get latest inflation rate"""
        try:
            url = "https://api.worldbank.org/v2/country/LKA/indicator/FP.CPI.TOTL.ZG?format=json&date=2023:2025"
            response = requests.get(url, timeout=5)
            data = response.json()
            
            if len(data) > 1 and data[1]:
                latest = data[1][0]
                inflation_rate = latest.get('value', 5.0)
                return {
                    'inflation_rate': inflation_rate,
                    'year': latest.get('date'),
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            print(f"Inflation fetch error: {e}")
        
        return {'inflation_rate': 5.0, 'year': 2024, 'timestamp': None}
    
    def get_fuel_prices(self):
        """Get fuel prices (mock for now - replace with real scraping)"""
        return {
            'petrol_92_price': 395,
            'diesel_price': 380,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_cse_index(self):
        """Get Colombo Stock Exchange index (mock)"""
        return {
            'aspi': 11500,
            'sp_sl20': 3200,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_all_indicators(self, car_year=None):
        """Fetch all economic indicators at once"""
        indicators = {
            'exchange_rate': self.get_exchange_rate(),
            'inflation': self.get_sri_lanka_inflation(),
            'fuel_prices': self.get_fuel_prices(),
            'stock_market': self.get_cse_index()
        }
        
        flat_data = {
            'usd_lkr_rate': indicators['exchange_rate']['usd_lkr_rate'],
            'inflation_rate': indicators['inflation']['inflation_rate'],
            'petrol_price': indicators['fuel_prices']['petrol_92_price'],
            'diesel_price': indicators['fuel_prices']['diesel_price'],
            'cse_aspi': indicators['stock_market']['aspi']
        }
        
        return flat_data

# Test
if __name__ == "__main__":
    fetcher = EconomicDataFetcher()
    data = fetcher.get_all_indicators()
    print(json.dumps(data, indent=2))
