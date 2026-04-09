# # backend/fetch_realtime_data.py
# """
# Real-time economic data fetcher for Sri Lanka car market.

# Sources:
#   - USD/LKR      : exchangerate-api.com (live)
#   - Inflation     : World Bank API (monthly)
#   - Fuel prices   : CPC Sri Lanka scrape (monthly) with hardcoded fallback
#   - CSE ASPI      : CSE website scrape with hardcoded fallback

# All results are cached with TTL to avoid hammering external APIs
# on every prediction request.
# """

# import requests
# import json
# import time
# import threading
# from datetime import datetime, timedelta
# from bs4 import BeautifulSoup


# # ---------------------------------------------------------------------------
# # Simple TTL cache (thread-safe, no Redis needed)
# # ---------------------------------------------------------------------------

# class _TTLCache:
#     def __init__(self):
#         self._store = {}
#         self._lock  = threading.Lock()

#     def get(self, key):
#         with self._lock:
#             entry = self._store.get(key)
#             if entry and datetime.now() < entry['expires']:
#                 return entry['value']
#             return None

#     def set(self, key, value, ttl_seconds: int):
#         with self._lock:
#             self._store[key] = {
#                 'value':   value,
#                 'expires': datetime.now() + timedelta(seconds=ttl_seconds),
#             }


# _cache = _TTLCache()


# # ---------------------------------------------------------------------------
# # BASELINE VALUES — calibrated from real Sri Lanka market data (2020-2026)
# #
# # 5-year market timeline:
# #   2020: USD/LKR ~185, inflation 6.1%, petrol Rs.137  — pre-crisis
# #   2021: USD/LKR ~200, inflation 7.0% — import ban starts, prices surge
# #   2022: USD/LKR ~360 peak, inflation 49.7% — worst crisis
# #         Used car prices surged 40-60% due to ban + hyperinflation
# #   2023: USD/LKR ~324, inflation 16.5% — recovery; prices fell ~20% YoY
# #   2024: USD/LKR ~293, inflation 1.2% — full stabilisation
# #   2025: Import restrictions eased Feb 2025, rupee 293-311
# #   2026: Current USD/LKR ~311, Colombo inflation ~1.6%
# #
# # Baseline = 2024 conditions (when dataset was most recently scraped)
# # ---------------------------------------------------------------------------

# BASELINE = {
#     # 2024 annual averages — calibrated from real Sri Lanka data
#     # USD/LKR: avg 301 across 2024 (started 324, ended 293)
#     'usd_lkr':   301.0,
#     # Inflation: 2024 avg was 1.2% (FocusEconomics / World Bank confirmed)
#     # This is our "normal" after the 2022 crisis — NOT the crisis baseline
#     'inflation':   1.2,
#     # Petrol 92: Rs.368 since late 2023 CPC revision — current normal
#     'petrol_92': 368.0,
#     # Diesel: Rs.320 since late 2023 CPC revision — current normal
#     'diesel':    320.0,
# }

# # ---------------------------------------------------------------------------
# # IMPORT RESTRICTION SCARCITY — research-calibrated per YOM
# #
# # Sources: Sri Lanka Customs stats, Central Bank Annual Report 2023,
# #          Mordor Intelligence, VerifiedMarketResearch 2025
# # Key facts:
# #   - Imports fell 75% between 2019-2021 due to ban
# #   - Car registrations fell 44.7%; used car sales rose 32% (supply crunch)
# #   - Feb 2025: restrictions eased but new tax structures maintain costs
# #   - 2021-2022 cars still command highest scarcity premium in 2026
# # ---------------------------------------------------------------------------

# IMPORT_RULES = {
#     # (yom_from_inclusive, yom_to_exclusive): (scarcity_pct, label)
#     (2020, 2021): (10.0, 'Early ban era (2020) — imports fell 75%, scarcity premium'),
#     (2021, 2023): (12.0, 'Peak ban era (2021-2022) — ban fully active, highest scarcity'),
#     (2023, 2024): ( 8.0, 'Late ban era (2023) — restrictions still active, high scarcity'),
#     (2024, 2026): ( 4.0, 'Post-ban (2024-2025) — restrictions eased Feb 2025'),
#     (2026, 2099): ( 2.0, 'Post-restriction era — new tax structures, limited premium'),
#     (0,    2020): ( 0.0, 'Pre-ban era — normal import supply, no scarcity premium'),
# }


# def get_import_scarcity(yom: int) -> dict:
#     yom = int(yom)
#     for (start, end), (pct, label) in IMPORT_RULES.items():
#         if start <= yom < end:
#             return {'scarcity_pct': pct, 'label': label, 'yom': yom}
#     return {'scarcity_pct': 0.0, 'label': 'Normal supply', 'yom': yom}


# # ---------------------------------------------------------------------------
# # Fetchers
# # ---------------------------------------------------------------------------

# def _get_exchange_rate() -> dict:
#     cached = _cache.get('usd_lkr')
#     if cached:
#         return cached

#     result = {'usd_lkr_rate': 360.0, 'source': 'fallback', 'timestamp': None}
#     try:
#         # Primary: exchangerate-api (free tier, no key needed)
#         r = requests.get(
#             'https://api.exchangerate-api.com/v4/latest/USD',
#             timeout=6
#         )
#         r.raise_for_status()
#         rate = r.json()['rates'].get('LKR', 360.0)
#         result = {
#             'usd_lkr_rate': round(float(rate), 2),
#             'source':        'exchangerate-api.com',
#             'timestamp':     datetime.now().isoformat(),
#         }
#         _cache.set('usd_lkr', result, ttl_seconds=3600)   # cache 1 hour
#     except Exception as e:
#         print(f"[fetch] exchange rate error: {e} — using fallback 360")

#     return result


# def _get_inflation() -> dict:
#     cached = _cache.get('inflation')
#     if cached:
#         return cached

#     result = {'inflation_rate': 5.0, 'year': '2024', 'source': 'fallback', 'timestamp': None}
#     try:
#         # World Bank API — annual CCPI for Sri Lanka
#         url = (
#             'https://api.worldbank.org/v2/country/LKA/'
#             'indicator/FP.CPI.TOTL.ZG?format=json&mrv=3'
#         )
#         r = requests.get(url, timeout=8)
#         r.raise_for_status()
#         data = r.json()

#         if len(data) > 1 and data[1]:
#             # Find most recent non-null value
#             for entry in data[1]:
#                 if entry.get('value') is not None:
#                     result = {
#                         'inflation_rate': round(float(entry['value']), 2),
#                         'year':           entry.get('date', '2024'),
#                         'source':         'World Bank API',
#                         'timestamp':      datetime.now().isoformat(),
#                     }
#                     break

#         _cache.set('inflation', result, ttl_seconds=86400)  # cache 24 hours
#     except Exception as e:
#         print(f"[fetch] inflation error: {e} — using fallback 5.0%")

#     return result


# def _get_fuel_prices() -> dict:
#     cached = _cache.get('fuel_prices')
#     if cached:
#         return cached

#     # Hardcoded current CPC prices (update monthly)
#     # TODO: replace with CPC website scraper when stable
#     result = {
#         'petrol_92_price': 368,
#         'petrol_95_price': 420,
#         'diesel_price':    338,
#         'source':          'CPC Sri Lanka (manual — update monthly)',
#         'timestamp':       datetime.now().isoformat(),
#         'last_updated':    '2025-03',
#     }

#     # Attempt live scrape of CPC fuel prices
#     try:
#         r = requests.get(
#             'https://www.ceypetco.gov.lk',
#             timeout=6,
#             headers={'User-Agent': 'Mozilla/5.0'}
#         )
#         soup = BeautifulSoup(r.text, 'html.parser')

#         # Look for price patterns like "368" or "Rs. 368" near "92 Octane"
#         text = soup.get_text(separator=' ')
#         import re
#         patterns = {
#             'petrol_92_price': r'92\s*[Oo]ctane[^\d]*(\d{3,4})',
#             'petrol_95_price': r'95\s*[Oo]ctane[^\d]*(\d{3,4})',
#             'diesel_price':    r'[Dd]iesel[^\d]*(\d{3,4})',
#         }
#         found_any = False
#         for key, pattern in patterns.items():
#             m = re.search(pattern, text)
#             if m:
#                 result[key] = int(m.group(1))
#                 found_any = True

#         if found_any:
#             result['source'] = 'CPC website (scraped)'

#     except Exception as e:
#         print(f"[fetch] fuel scrape error: {e} — using hardcoded CPC prices")

#     _cache.set('fuel_prices', result, ttl_seconds=43200)  # cache 12 hours
#     return result


# def _get_cse_index() -> dict:
#     cached = _cache.get('cse')
#     if cached:
#         return cached

#     result = {
#         'aspi':      12000,
#         'sp_sl20':   3500,
#         'source':    'fallback',
#         'timestamp': None,
#     }

#     try:
#         import re
#         # Try CSE market summary page
#         r = requests.get(
#             'https://www.cse.lk/pages/market-summary/market-summary.component.html',
#             timeout=6,
#             headers={'User-Agent': 'Mozilla/5.0'}
#         )
#         soup = BeautifulSoup(r.text, 'html.parser')
#         text = soup.get_text(separator=' ')
#         m = re.search(r'ASPI[^\d]*(\d{4,6}[.,]\d{2})', text)
#         if m:
#             aspi_str = m.group(1).replace(',', '')
#             result = {
#                 'aspi':      round(float(aspi_str), 2),
#                 'sp_sl20':   result['sp_sl20'],
#                 'source':    'CSE website',
#                 'timestamp': datetime.now().isoformat(),
#             }
#         _cache.set('cse', result, ttl_seconds=3600)
#     except Exception as e:
#         print(f"[fetch] CSE error: {e} — using fallback ASPI {result['aspi']}")
#         _cache.set('cse', result, ttl_seconds=1800)  # cache fallback 30 min too

#     return result


# # ---------------------------------------------------------------------------
# # Main public class
# # ---------------------------------------------------------------------------

# class EconomicDataFetcher:
#     """
#     Fetch and cache all economic indicators relevant to Sri Lanka car pricing.
#     Instantiate once per request — caching is module-level so it persists
#     across requests without needing Redis.
#     """

#     def get_exchange_rate(self)  -> dict: return _get_exchange_rate()
#     def get_sri_lanka_inflation(self) -> dict: return _get_inflation()
#     def get_fuel_prices(self)    -> dict: return _get_fuel_prices()
#     def get_cse_index(self)      -> dict: return _get_cse_index()

#     def get_all_indicators(self, car_year: int = None) -> dict:
#         """
#         Return flat dict of all indicators plus import scarcity if car_year given.
#         """
#         fx      = _get_exchange_rate()
#         infl    = _get_inflation()
#         fuel    = _get_fuel_prices()
#         cse     = _get_cse_index()

#         flat = {
#             'usd_lkr_rate':    fx['usd_lkr_rate'],
#             'inflation_rate':  infl['inflation_rate'],
#             'petrol_price':    fuel['petrol_92_price'],
#             'petrol_95_price': fuel['petrol_95_price'],
#             'diesel_price':    fuel['diesel_price'],
#             'cse_aspi':        cse['aspi'],
#             'sources': {
#                 'exchange_rate': fx.get('source'),
#                 'inflation':     infl.get('source'),
#                 'fuel':          fuel.get('source'),
#                 'cse':           cse.get('source'),
#             },
#             'fetched_at': datetime.now().isoformat(),
#         }

#         if car_year:
#             flat['import_scarcity'] = get_import_scarcity(car_year)

#         return flat

# backend/fetch_realtime_data.py
"""
Real-time economic data fetcher for Sri Lanka car market.

Sources:
  - USD/LKR      : exchangerate-api.com (live)
  - Inflation     : World Bank API (monthly)
  - Fuel prices   : CPC Sri Lanka scrape (monthly) with hardcoded fallback
  - CSE ASPI      : CSE website scrape with hardcoded fallback

All results are cached with TTL to avoid hammering external APIs
on every prediction request.
"""

import requests
import json
import time
import threading
from datetime import datetime, timedelta
from bs4 import BeautifulSoup


# ---------------------------------------------------------------------------
# Simple TTL cache (thread-safe, no Redis needed)
# ---------------------------------------------------------------------------

class _TTLCache:
    def __init__(self):
        self._store = {}
        self._lock  = threading.Lock()

    def get(self, key):
        with self._lock:
            entry = self._store.get(key)
            if entry and datetime.now() < entry['expires']:
                return entry['value']
            return None

    def set(self, key, value, ttl_seconds: int):
        with self._lock:
            self._store[key] = {
                'value':   value,
                'expires': datetime.now() + timedelta(seconds=ttl_seconds),
            }


_cache = _TTLCache()


# ---------------------------------------------------------------------------
# BASELINE VALUES — calibrated from real Sri Lanka market data (2020-2026)
#
# 5-year market timeline:
#   2020: USD/LKR ~185, inflation 6.1%, petrol Rs.137  — pre-crisis
#   2021: USD/LKR ~200, inflation 7.0% — import ban starts, prices surge
#   2022: USD/LKR ~360 peak, inflation 49.7% — worst crisis
#         Used car prices surged 40-60% due to ban + hyperinflation
#   2023: USD/LKR ~324, inflation 16.5% — recovery; prices fell ~20% YoY
#   2024: USD/LKR ~293, inflation 1.2% — full stabilisation
#   2025: Import restrictions eased Feb 2025, rupee 293-311
#   2026: Current USD/LKR ~311, Colombo inflation ~1.6%
#
# Baseline = 2024 conditions (when dataset was most recently scraped)
# ---------------------------------------------------------------------------

BASELINE = {
    # 2024 annual averages — calibrated from real Sri Lanka data
    # USD/LKR: avg 301 across 2024 (started 324, ended 293)
 
    'usd_lkr':   301.0,
    'inflation':   1.6,   # Updated: Feb 2026 actual (was 1.2)
    'petrol_92': 398.0,   # Updated: March 21 2026 CPC revision (was 368)
    'diesel':    360.0,   # Updated: March 2026 (was 320)

}

# ---------------------------------------------------------------------------
# IMPORT RESTRICTION SCARCITY — research-calibrated per YOM
#
# Sources: Sri Lanka Customs stats, Central Bank Annual Report 2023,
#          Mordor Intelligence, VerifiedMarketResearch 2025
# Key facts:
#   - Imports fell 75% between 2019-2021 due to ban
#   - Car registrations fell 44.7%; used car sales rose 32% (supply crunch)
#   - Feb 2025: restrictions eased but new tax structures maintain costs
#   - 2021-2022 cars still command highest scarcity premium in 2026
# ---------------------------------------------------------------------------

IMPORT_RULES = {
    # (yom_from_inclusive, yom_to_exclusive): (scarcity_pct, label)
    (2020, 2021): (10.0, 'Early ban era (2020) — imports fell 75%, scarcity premium'),
    (2021, 2023): (12.0, 'Peak ban era (2021-2022) — ban fully active, highest scarcity'),
    (2023, 2024): ( 8.0, 'Late ban era (2023) — restrictions still active, high scarcity'),
    (2024, 2026): ( 4.0, 'Post-ban (2024-2025) — restrictions eased Feb 2025'),
    (2026, 2099): ( 2.0, 'Post-restriction era — new tax structures, limited premium'),
    (0,    2020): ( 0.0, 'Pre-ban era — normal import supply, no scarcity premium'),
}


def get_import_scarcity(yom: int) -> dict:
    yom = int(yom)
    for (start, end), (pct, label) in IMPORT_RULES.items():
        if start <= yom < end:
            return {'scarcity_pct': pct, 'label': label, 'yom': yom}
    return {'scarcity_pct': 0.0, 'label': 'Normal supply', 'yom': yom}


# ---------------------------------------------------------------------------
# Fetchers
# ---------------------------------------------------------------------------

def _get_exchange_rate() -> dict:
    cached = _cache.get('usd_lkr')
    if cached:
        return cached

    result = {'usd_lkr_rate': 360.0, 'source': 'fallback', 'timestamp': None}
    try:
        # Primary: exchangerate-api (free tier, no key needed)
        r = requests.get(
            'https://api.exchangerate-api.com/v4/latest/USD',
            timeout=6
        )
        r.raise_for_status()
        rate = r.json()['rates'].get('LKR', 360.0)
        result = {
            'usd_lkr_rate': round(float(rate), 2),
            'source':        'exchangerate-api.com',
            'timestamp':     datetime.now().isoformat(),
        }
        _cache.set('usd_lkr', result, ttl_seconds=3600)   # cache 1 hour
    except Exception as e:
        print(f"[fetch] exchange rate error: {e} — using fallback 360")

    return result


# def _get_inflation() -> dict:
#     cached = _cache.get('inflation')
#     if cached:
#         return cached

#     result = {'inflation_rate': 5.0, 'year': '2024', 'source': 'fallback', 'timestamp': None}
#     try:
#         # World Bank API — annual CCPI for Sri Lanka
#         url = (
#             'https://api.worldbank.org/v2/country/LKA/'
#             'indicator/FP.CPI.TOTL.ZG?format=json&mrv=3'
#         )
#         r = requests.get(url, timeout=8)
#         r.raise_for_status()
#         data = r.json()

#         if len(data) > 1 and data[1]:
#             # Find most recent non-null value
#             for entry in data[1]:
#                 if entry.get('value') is not None:
#                     result = {
#                         'inflation_rate': round(float(entry['value']), 2),
#                         'year':           entry.get('date', '2024'),
#                         'source':         'World Bank API',
#                         'timestamp':      datetime.now().isoformat(),
#                     }
#                     break

#         _cache.set('inflation', result, ttl_seconds=86400)  # cache 24 hours
#     except Exception as e:
#         print(f"[fetch] inflation error: {e} — using fallback 5.0%")

#     return result

def _get_inflation() -> dict:
    cached = _cache.get('inflation')
    if cached:
        return cached

    # Try World Bank first (annual, may be lagged)
    result = {'inflation_rate': 1.6, 'year': '2026', 'source': 'manual-2026-02', 'timestamp': None}

    try:
        url = 'https://api.worldbank.org/v2/country/LKA/indicator/FP.CPI.TOTL.ZG?format=json&mrv=5'
        r = requests.get(url, timeout=8)
        r.raise_for_status()
        data = r.json()
        if len(data) > 1 and data[1]:
            for entry in data[1]:
                if entry.get('value') is not None:
                    wb_rate = round(float(entry['value']), 2)
                    wb_year = entry.get('date', '2024')
                    # World Bank lags by ~1 year — only use if recent enough
                    if int(wb_year) >= 2024:
                        # result = {
                        #     'inflation_rate': wb_rate,
                        #     'year':           wb_year,
                        #     'source':         f'World Bank API ({wb_year})',
                        #     'timestamp':      datetime.now().isoformat(),
                        # }
                        result = {
        'inflation_rate': 1.6,
        'year':           '2026-02',
        'source':         'CBSL/DCS manual — Feb 2026 YoY',
        'timestamp':      datetime.now().isoformat(),
    }
                    break
        _cache.set('inflation', result, ttl_seconds=86400)
    except Exception as e:
        print(f"[fetch] inflation error: {e} — using manual fallback 1.6%")
        _cache.set('inflation', result, ttl_seconds=3600)

    return result

def _get_fuel_prices() -> dict:
    cached = _cache.get('fuel_prices')
    if cached:
        return cached

    # Hardcoded current CPC prices (update monthly)
    # TODO: replace with CPC website scraper when stable
    result = {
        
    'petrol_92_price': 398,          # Updated March 21, 2026
    'petrol_95_price': 450,
    'diesel_price':    360,
    'source':          'CPC Sri Lanka (manual — updated 2026-03-21)',
    'timestamp':       datetime.now().isoformat(),
    'last_updated':    '2026-03-21',  # ← update this date each time CPC changes prices
}

    # Attempt live scrape of CPC fuel prices
    try:
        r = requests.get(
            'https://www.ceypetco.gov.lk',
            timeout=6,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        soup = BeautifulSoup(r.text, 'html.parser')

        # Look for price patterns like "368" or "Rs. 368" near "92 Octane"
        text = soup.get_text(separator=' ')
        import re
        patterns = {
            'petrol_92_price': r'92\s*[Oo]ctane[^\d]*(\d{3,4})',
            'petrol_95_price': r'95\s*[Oo]ctane[^\d]*(\d{3,4})',
            'diesel_price':    r'[Dd]iesel[^\d]*(\d{3,4})',
        }
        found_any = False
        for key, pattern in patterns.items():
            m = re.search(pattern, text)
            if m:
                result[key] = int(m.group(1))
                found_any = True

        if found_any:
            result['source'] = 'CPC website (scraped)'

    except Exception as e:
        print(f"[fetch] fuel scrape error: {e} — using hardcoded CPC prices")

    _cache.set('fuel_prices', result, ttl_seconds=43200)  # cache 12 hours
    return result


def _get_cse_index() -> dict:
    cached = _cache.get('cse')
    if cached:
        return cached

    result = {
     
    'aspi':      20640,   # Updated March 20, 2026 (was 12000 — dangerously wrong)
    'sp_sl20':   5800,
    'source':    'manual-fallback-2026-03-20',
    'timestamp': None,

    }

    try:
        import re
        # Try CSE market summary page
        r = requests.get(
            'https://www.cse.lk/pages/market-summary/market-summary.component.html',
            timeout=6,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        soup = BeautifulSoup(r.text, 'html.parser')
        text = soup.get_text(separator=' ')
        m = re.search(r'ASPI[^\d]*(\d{4,6}[.,]\d{2})', text)
        if m:
            aspi_str = m.group(1).replace(',', '')
            result = {
                'aspi':      round(float(aspi_str), 2),
                'sp_sl20':   result['sp_sl20'],
                'source':    'CSE website',
                'timestamp': datetime.now().isoformat(),
            }
        _cache.set('cse', result, ttl_seconds=3600)
    except Exception as e:
        print(f"[fetch] CSE error: {e} — using fallback ASPI {result['aspi']}")
        _cache.set('cse', result, ttl_seconds=1800)  # cache fallback 30 min too

    return result


# ---------------------------------------------------------------------------
# Main public class
# ---------------------------------------------------------------------------

class EconomicDataFetcher:
    """
    Fetch and cache all economic indicators relevant to Sri Lanka car pricing.
    Instantiate once per request — caching is module-level so it persists
    across requests without needing Redis.
    """

    def get_exchange_rate(self)  -> dict: return _get_exchange_rate()
    def get_sri_lanka_inflation(self) -> dict: return _get_inflation()
    def get_fuel_prices(self)    -> dict: return _get_fuel_prices()
    def get_cse_index(self)      -> dict: return _get_cse_index()

    def get_all_indicators(self, car_year: int = None) -> dict:
        """
        Return flat dict of all indicators plus import scarcity if car_year given.
        """
        fx      = _get_exchange_rate()
        infl    = _get_inflation()
        fuel    = _get_fuel_prices()
        cse     = _get_cse_index()

        flat = {
            'usd_lkr_rate':    fx['usd_lkr_rate'],
            'inflation_rate':  infl['inflation_rate'],
            'petrol_price':    fuel['petrol_92_price'],
            'petrol_95_price': fuel['petrol_95_price'],
            'diesel_price':    fuel['diesel_price'],
            'cse_aspi':        cse['aspi'],
            'sources': {
                'exchange_rate': fx.get('source'),
                'inflation':     infl.get('source'),
                'fuel':          fuel.get('source'),
                'cse':           cse.get('source'),
            },
            'fetched_at': datetime.now().isoformat(),
        }

        if car_year:
            flat['import_scarcity'] = get_import_scarcity(car_year)

        return flat


# ---------------------------------------------------------------------------
# Economic adjustment engine
# ---------------------------------------------------------------------------

class EconomicAdjustmentEngine:
    """
    Applies real-time economic adjustments to a base model prediction.

    Usage:
        engine = EconomicAdjustmentEngine()
        result = engine.adjust(base_price=45.0, car_data={...})
    """

    # How sensitive each brand segment is to USD/LKR
    CURRENCY_SENSITIVITY = {
        'luxury':  1.8,   # BMW, Mercedes, Audi, Lexus, Land Rover, Porsche
        'popular': 1.0,   # Toyota, Honda, Suzuki, Nissan
        'other':   1.2,
    }

    LUXURY_BRANDS  = {'BMW', 'MERCEDES-BENZ', 'AUDI', 'LEXUS',
                      'LAND ROVER', 'PORSCHE', 'VOLVO', 'JAGUAR'}
    POPULAR_BRANDS = {'TOYOTA', 'HONDA', 'SUZUKI', 'NISSAN',
                      'MITSUBISHI', 'MAZDA'}
    HYBRID_FUELS   = {'Hybrid', 'Plug-in Hybrid', 'Electric'}

    def __init__(self):
        self.fetcher = EconomicDataFetcher()

    def adjust(self, base_price: float, car_data: dict) -> dict:
        """
        Apply economic adjustments to base_price.

        Args:
            base_price : float — raw model prediction in LKR Lakhs
            car_data   : dict  — must contain brand, yom, fuel_type, mileage

        Returns:
            Full breakdown dict with adjusted final price.
        """
        econ = self.fetcher.get_all_indicators(
            car_year=car_data.get('yom')
        )

        brand     = str(car_data.get('brand', '')).upper()
        yom       = int(car_data.get('yom', 2015))
        fuel_type = str(car_data.get('fuel_type', 'Petrol'))
        car_age   = datetime.now().year - yom

        adjustments = {}

        # ── 1. USD/LKR exchange rate impact ─────────────────────────
        usd_lkr  = econ['usd_lkr_rate']
        fx_ratio = usd_lkr / BASELINE['usd_lkr']  # e.g. 360/200 = 1.8

        if brand in self.LUXURY_BRANDS:
            sensitivity = self.CURRENCY_SENSITIVITY['luxury']
            segment     = 'luxury'
        elif brand in self.POPULAR_BRANDS:
            sensitivity = self.CURRENCY_SENSITIVITY['popular']
            segment     = 'popular'
        else:
            sensitivity = self.CURRENCY_SENSITIVITY['other']
            segment     = 'other'

        # USD/LKR impact on second-hand car prices:
        # Spare parts, tyres, batteries all priced in USD
        # Research: 2022 crisis (USD/LKR 360) pushed prices up 40-60%
        # Sensitivity calibrated to that real-world observation:
        #   luxury:  each 5% LKR weakening → ~1.8% price increase
        #   popular: each 5% LKR weakening → ~1.0% price increase
        fx_adjustment_pct = (fx_ratio - 1.0) * sensitivity * 12.0
        fx_adjustment_pct = max(-20.0, min(40.0, fx_adjustment_pct))  # cap

        if fx_adjustment_pct > 0.5:
            fx_explanation = (
                f"USD/LKR at {usd_lkr:.0f} vs baseline {BASELINE['usd_lkr']:.0f}. "
                f"Weaker rupee raises imported parts, tyres & battery costs. "
                f"+{fx_adjustment_pct:.1f}% for {segment} segment."
            )
        elif fx_adjustment_pct < -0.5:
            fx_explanation = (
                f"USD/LKR at {usd_lkr:.0f} — stronger than baseline {BASELINE['usd_lkr']:.0f}. "
                f"Stronger rupee reduces imported parts costs. "
                f"{fx_adjustment_pct:.1f}% for {segment} segment."
            )
        else:
            fx_explanation = (
                f"USD/LKR at {usd_lkr:.0f} — near baseline. Minimal exchange rate impact."
            )

        adjustments['usd_lkr'] = {
            'pct':           round(fx_adjustment_pct, 2),
            'current_rate':  usd_lkr,
            'baseline_rate': BASELINE['usd_lkr'],
            'segment':       segment,
            'label':         'Exchange rate impact',
            'explanation':   fx_explanation,
        }

        # ── 2. Inflation impact ──────────────────────────────────────
        inflation      = econ['inflation_rate']
        inflation_diff = inflation - BASELINE['inflation']

        # Positive diff  → higher inflation than baseline → extra depreciation (negative %)
        # Negative diff  → deflation / low inflation     → slight price softening (small negative %)
        # Near zero diff → no meaningful impact
        inflation_adj_pct = -(car_age * inflation_diff * 0.4)
        inflation_adj_pct = max(-15.0, min(10.0, inflation_adj_pct))  # cap extremes

        if inflation_adj_pct < -0.5:
            infl_explanation = (
                f'Inflation at {inflation:.1f}% vs baseline {BASELINE["inflation"]:.1f}%. '
                f'Higher-than-baseline inflation adds extra {abs(inflation_adj_pct):.1f}% '
                f'depreciation on this {car_age}-year-old car.'
            )
        elif inflation_adj_pct > 0.5:
            infl_explanation = (
                f'Inflation at {inflation:.1f}% — below baseline {BASELINE["inflation"]:.1f}%. '
                f'Low/negative inflation slightly softens prices '
                f'({inflation_adj_pct:.1f}% on a {car_age}-year-old car).'
            )
        else:
            infl_explanation = (
                f'Inflation at {inflation:.1f}% — near baseline. No significant price impact.'
            )

        adjustments['inflation'] = {
            'pct':           round(inflation_adj_pct, 2),
            'current_rate':  inflation,
            'baseline_rate': BASELINE['inflation'],
            'car_age':       car_age,
            'label':         'Inflation depreciation',
            'explanation':   infl_explanation,
        }

        # ── 3. Fuel price impact (hybrid/EV premium) ─────────────────
        # Research: Petrol rose 90%+ in 2022 (Rs.137 → Rs.420+)
        # This created huge demand/premium for hybrids
        # Current petrol Rs.368 is high vs pre-crisis but stable
        # Hybrid premium is now structural — Rs.368 petrol IS the new normal
        # We use absolute petrol price as proxy for hybrid desirability:
        #   Rs.137 (pre-crisis): no hybrid premium
        #   Rs.368 (current)   : meaningful hybrid premium
        #   Rs.420+ (2022 peak): maximum hybrid premium
        petrol             = econ['petrol_price']
        PRE_CRISIS_PETROL  = 137.0  # Rs/L pre-2022 — when hybrids had no premium
        petrol_above_pre   = max(0.0, petrol - PRE_CRISIS_PETROL)
        petrol_range       = 420.0 - PRE_CRISIS_PETROL  # full range of price shock

        if fuel_type in self.HYBRID_FUELS:
            # Hybrid premium scales with how far petrol is above pre-crisis level
            # Max premium ~12% (observed in 2022 market data)
            fuel_adj_pct = (petrol_above_pre / petrol_range) * 12.0
            fuel_adj_pct = round(min(fuel_adj_pct, 12.0), 2)
            fuel_label   = (
                f'{fuel_type} premium: petrol at Rs.{petrol}/L '
                f'(+{petrol_above_pre:.0f} above pre-crisis Rs.{PRE_CRISIS_PETROL:.0f}). '
                f'High fuel costs increase hybrid/EV resale demand (+{fuel_adj_pct:.1f}%).'
            )
        elif fuel_type == 'Diesel':
            diesel             = econ.get('diesel_price', 338)
            PRE_CRISIS_DIESEL  = 100.0
            diesel_above_pre   = max(0.0, diesel - PRE_CRISIS_DIESEL)
            fuel_adj_pct       = round((diesel_above_pre / 240.0) * 4.0, 2)
            fuel_label         = (
                f'Diesel at Rs.{diesel}/L — moderate premium for diesel efficiency '
                f'at current fuel prices (+{fuel_adj_pct:.1f}%).'
            )
        else:
            fuel_adj_pct = 0.0
            fuel_label   = f'Petrol at Rs.{petrol}/L — no fuel efficiency premium for petrol cars.'

        adjustments['fuel'] = {
            'pct':            round(fuel_adj_pct, 2),
            'current_petrol':  petrol,
            'baseline_petrol': BASELINE['petrol_92'],
            'fuel_type':       fuel_type,
            'label':           'Fuel price premium',
            'explanation':     fuel_label,
        }

        # ── 4. Import restriction scarcity ───────────────────────────
        scarcity        = econ.get('import_scarcity', get_import_scarcity(yom))
        scarcity_pct    = scarcity['scarcity_pct']
        adjustments['import_scarcity'] = {
            'pct':         round(scarcity_pct, 2),
            'yom':         yom,
            'label':       'Import restriction scarcity',
            'explanation': scarcity['label'],
        }

        # ── Final calculation ────────────────────────────────────────
        total_pct    = sum(a['pct'] for a in adjustments.values())
        final_price  = round(base_price * (1 + total_pct / 100.0), 2)
        base_rounded = round(base_price, 2)

        # Per-factor LKR amounts
        for key, adj in adjustments.items():
            adj['lkr_lakhs'] = round(base_price * adj['pct'] / 100.0, 2)

        return {
            'base_price':          base_rounded,
            'final_price':         final_price,
            'total_adjustment_pct': round(total_pct, 2),
            'total_adjustment_lkr': round(final_price - base_rounded, 2),
            'adjustments':         adjustments,
            'economic_context':    econ,
            'car_summary': {
                'brand':     brand,
                'yom':       yom,
                'car_age':   car_age,
                'fuel_type': fuel_type,
                'segment':   segment,
            },
        }


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    print('Fetching economic indicators...')
    fetcher = EconomicDataFetcher()
    data    = fetcher.get_all_indicators(car_year=2021)
    print(json.dumps(data, indent=2))

    print('\nRunning economic adjustment test...')
    engine = EconomicAdjustmentEngine()
    result = engine.adjust(
        base_price=45.0,
        car_data={
            'brand':     'TOYOTA',
            'yom':       2021,
            'fuel_type': 'Hybrid',
            'mileage':   60000,
        }
    )
    print(f"\nBase price:  Rs. {result['base_price']} L")
    print(f"Final price: Rs. {result['final_price']} L")
    print(f"Adjustment:  {result['total_adjustment_pct']:+.1f}%")
    print('\nBreakdown:')
    for k, v in result['adjustments'].items():
        print(f"  {v['label']:35s} {v['pct']:+6.1f}%  "
              f"(Rs. {v['lkr_lakhs']:+.2f}L)  — {v['explanation'][:60]}")