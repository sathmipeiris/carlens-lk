# from selenium import webdriver
# from selenium.webdriver.firefox.options import Options
# from selenium.webdriver.firefox.service import Service
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from webdriver_manager.firefox import GeckoDriverManager

# import time, json, os, re, hashlib, random
# import pandas as pd
# from datetime import datetime


# class RiyasewanaCarScraper:
#     def __init__(self,
#                  resume_file="riyasewana_progress.json",
#                  data_file="riyasewana_used_cars.csv"):
#         options = Options()
#         options.add_argument("--headless")
#         options.add_argument("--no-sandbox")
#         options.add_argument("--disable-dev-shm-usage")
#         options.add_argument("--window-size=1920,1080")

#         service = Service(GeckoDriverManager().install())
#         self.driver = webdriver.Firefox(service=service, options=options)

#         self.data = []
#         self.scrape_date = datetime.now().strftime("%Y-%m-%d")
#         self.resume_file = resume_file
#         self.data_file = data_file

#         self.scraped_pages = set()
#         self.scraped_urls = set()
#         self.listing_signatures = set()

#         self.load_progress()
#         self.load_existing_data()

#     def load_progress(self):
#         if os.path.exists(self.resume_file):
#             try:
#                 with open(self.resume_file, "r", encoding="utf-8") as f:
#                     p = json.load(f)
#                 self.scraped_pages = set(p.get("scraped_pages", []))
#                 self.scraped_urls = set(p.get("scraped_urls", []))
#                 sig_list = p.get("listing_signatures", [])
#                 for sig in sig_list:
#                     self.listing_signatures.add(
#                         (sig["signature"], frozenset(sig["title_words"]), sig["price"], sig["mileage"], sig["title"])
#                     )
#             except Exception as e:
#                 print(f"Error loading progress: {e}")

#     def save_progress(self):
#         try:
#             sig_list = [{"signature": sig, "title_words": list(words), "price": price, "mileage": mileage, "title": title}
#                        for sig, words, price, mileage, title in self.listing_signatures]
#             p = {
#                 "scraped_pages": list(self.scraped_pages),
#                 "scraped_urls": list(self.scraped_urls),
#                 "listing_signatures": sig_list,
#                 "last_update": datetime.now().isoformat(),
#                 "total_records": len(self.data),
#             }
#             with open(self.resume_file, "w", encoding="utf-8") as f:
#                 json.dump(p, f, ensure_ascii=False)
#         except Exception as e:
#             print(f"Error saving progress: {e}")

#     def load_existing_data(self):
#         if os.path.exists(self.data_file):
#             try:
#                 df = pd.read_csv(self.data_file)
#                 self.data = df.to_dict("records")
#                 for rec in self.data:
#                     sig_data = self.generate_advanced_signature(rec)
#                     if sig_data:
#                         self.listing_signatures.add((sig_data["signature"], sig_data["title_words"], sig_data["price"], sig_data["mileage"], sig_data["title"]))
#             except Exception as e:
#                 print(f"Error loading existing data: {e}")

#     def generate_advanced_signature(self, car):
#         if not car.get("Brand") or not car.get("Price"):
#             return None

#         brand = str(car.get("Brand", "")).lower().strip()
#         model = str(car.get("Model", "")).lower().strip()
#         year = int(car.get("YOM", 0) or 0)
#         price = int(car.get("Price", 0) or 0)
#         mileage = int(car.get("Millage(KM)", 0) or 0)
#         location = str(car.get("Town", "")).lower().strip()
#         title = str(car.get("Title", "")).lower().strip()

#         price_range = int(price * 0.05) if price > 0 else 0
#         mileage_range = int(max(mileage * 0.1, 1000)) if mileage > 0 else 0
#         location_area = location.split(",")[0] if location else ""

#         parts = [brand, model, str(year), str(price_range), str(mileage_range), location_area]
#         sig_str = "|".join(parts)
#         signature = hashlib.md5(sig_str.encode()).hexdigest()
#         title_words = set(title.split())

#         return {"signature": signature, "title_words": frozenset(title_words), "price": price, "mileage": mileage, "title": title}

#     def is_sophisticated_duplicate(self, car):
#         sig_data = self.generate_advanced_signature(car)
#         if not sig_data:
#             return False

#         new_sig = sig_data["signature"]
#         new_words = sig_data["title_words"]
#         new_price = sig_data["price"]
#         new_mileage = sig_data["mileage"]

#         for existing_sig, words, price, mileage, title in self.listing_signatures:
#             if existing_sig != new_sig:
#                 continue

#             if new_words and words:
#                 common = new_words.intersection(words)
#                 union = new_words.union(words)
#                 similarity = len(common) / len(union) if union else 0
#             else:
#                 similarity = 1.0

#             price_diff = abs(new_price - price) / max(new_price, 1)
#             mileage_diff = abs(new_mileage - mileage) / max(new_mileage, 1) if mileage and new_mileage else 0

#             if similarity >= 0.8 and price_diff <= 0.02 and mileage_diff <= 0.05:
#                 return True

#         self.listing_signatures.add((new_sig, new_words, new_price, new_mileage, sig_data["title"]))
#         return False

#     def scrape_riyasewana(self, max_pages=200):
#         base_url = "https://riyasewana.com/search/cars"

#         for page in range(1, max_pages + 1):
#             page_url = f"{base_url}?page={page}"
#             if page_url in self.scraped_pages:
#                 continue

#             print(f"\n{'='*60}\nScraping page {page}...\n{'='*60}")
            
#             self.driver.get(page_url)
#             time.sleep(random.uniform(3, 5))

#             listing_links = []
            
#             try:
#                 print("Finding car listing links...")
#                 all_links = self.driver.find_elements(By.TAG_NAME, "a")
#                 print(f"Found {len(all_links)} total links")
                
#                 for link in all_links:
#                     try:
#                         href = link.get_attribute("href")
#                         if not href:
#                             continue
                        
#                         # Match the pattern: /buy{brand}-{model}-sale-{location}-{ID}
#                         if "/buy" in href and "-sale-" in href and href.endswith(re.search(r'-\d+$', href).group(0) if re.search(r'-\d+$', href) else ""):
#                             if href not in self.scraped_urls:
#                                 listing_links.append(href)
#                     except:
#                         continue
                
#                 print(f"Found {len(listing_links)} car listing links")
                
#             except Exception as e:
#                 print(f"Error finding links: {e}")

#             listing_links = list(dict.fromkeys(listing_links))
#             print(f"\nProcessing {len(listing_links)} unique listing links...")
            
#             if not listing_links:
#                 self.scraped_pages.add(page_url)
#                 self.save_progress()
#                 continue

#             new_records = 0
#             for idx, listing_url in enumerate(listing_links, 1):
#                 try:
#                     if listing_url in self.scraped_urls:
#                         continue

#                     print(f"  [{idx}/{len(listing_links)}] {listing_url}")
                    
#                     self.driver.get(listing_url)
#                     time.sleep(random.uniform(2, 4))
                    
#                     car = self.extract_car_details_from_page(listing_url)
                    
#                     if not car or not car.get("Price"):
#                         self.scraped_urls.add(listing_url)
#                         continue

#                     year = car.get("YOM")
#                     if year and not (2020 <= year <= 2025):
#                         self.scraped_urls.add(listing_url)
#                         continue

#                     if self.is_sophisticated_duplicate(car):
#                         self.scraped_urls.add(listing_url)
#                         continue

#                     self.data.append(car)
#                     self.scraped_urls.add(listing_url)
#                     new_records += 1
                    
#                     price_str = f"Rs. {car.get('Price'):,}" if car.get('Price') else "No price"
#                     print(f"    ✓ {car.get('Brand')} {car.get('Model')} {car.get('YOM')} - {price_str}")

#                 except Exception as e:
#                     print(f"    ✗ Error: {e}")
#                     self.scraped_urls.add(listing_url)
#                     continue

#             self.scraped_pages.add(page_url)
#             print(f"\nPage {page}: +{new_records} cars (Total: {len(self.data)})")
            
#             if page % 2 == 0 or new_records > 0:
#                 self.save_data_to_csv()
#                 self.save_progress()

#             time.sleep(random.uniform(3, 6))

#         self.save_data_to_csv()
#         self.save_progress()
#         print(f"\n{'='*60}\nDone! Total: {len(self.data)}\n{'='*60}")

#     def extract_car_details_from_page(self, url):
#         try:
#             WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
#             full_text = self.driver.find_element(By.TAG_NAME, "body").text
#             full_text_lower = full_text.lower()

#             title = None
#             try:
#                 title_elem = self.driver.find_element(By.CSS_SELECTOR, "h1, h2.title, .ad-title")
#                 title = title_elem.text.strip()
#             except:
#                 lines = full_text.split("\n")
#                 title = lines[0].strip() if lines else "Unknown"

#             fields = self.extract_structured_fields()
            
#             if not fields.get("Make"):
#                 fields["Make"] = self.extract_brand_model(full_text)[0]
#             if not fields.get("Model"):
#                 fields["Model"] = self.extract_brand_model(full_text)[1]
#             if not fields.get("YOM"):
#                 fields["YOM"] = self.extract_year(full_text)
#             if not fields.get("Price"):
#                 fields["Price"] = self.extract_price(full_text_lower)
#             if not fields.get("Mileage (km)"):
#                 fields["Mileage (km)"] = self.extract_mileage(full_text_lower)
#             if not fields.get("Engine (cc)"):
#                 fields["Engine (cc)"] = self.extract_engine_cc(full_text_lower)
#             if not fields.get("Gear"):
#                 fields["Gear"] = self.extract_transmission(full_text_lower)
#             if not fields.get("Fuel Type"):
#                 fields["Fuel Type"] = self.extract_fuel_type(full_text_lower)

#             options = self.extract_options_section(full_text_lower)
            
#             car = {
#                 "Title": title,
#                 "Brand": fields.get("Make") or "Unknown",
#                 "Model": fields.get("Model") or "Unknown",
#                 "YOM": fields.get("YOM"),
#                 "Engine (cc)": fields.get("Engine (cc)"),
#                 "Gear": fields.get("Gear"),
#                 "Fuel Type": fields.get("Fuel Type"),
#                 "Millage(KM)": fields.get("Mileage (km)"),
#                 "Town": self.extract_town(full_text),
#                 "Date": self.scrape_date,
#                 "Leasing": self.extract_leasing(full_text_lower),
#                 "Condition": self.extract_condition(full_text_lower),
#                 "AIR CONDITION": options.get("AIR CONDITION"),
#                 "POWER STEERING": options.get("POWER STEERING"),
#                 "POWER MIRROR": options.get("POWER MIRROR"),
#                 "POWER WINDOW": options.get("POWER WINDOW"),
#                 "Price": fields.get("Price"),
#                 "Contact": self.extract_contact(full_text),
#                 "Options": options.get("Options_Raw"),
#                 "SourceURL": url,
#                 "ScrapeDate": self.scrape_date,
#             }

#             return car

#         except Exception as e:
#             print(f"Error extracting: {e}")
#             return None

#     def extract_options_section(self, text):
#         options_dict = {"AIR CONDITION": "No", "POWER STEERING": "No", "POWER MIRROR": "No", "POWER WINDOW": "No", "Options_Raw": ""}
        
#         try:
#             lines = text.split("\n")
#             options_start = -1
#             for i, line in enumerate(lines):
#                 if line.strip().lower() == "options":
#                     options_start = i
#                     break
            
#             if options_start >= 0 and options_start + 1 < len(lines):
#                 options_text = ""
#                 for j in range(1, 6):
#                     if options_start + j < len(lines):
#                         line = lines[options_start + j].strip().lower()
#                         if any(x in line for x in ["engine", "gear", "fuel", "price", "contact", "details", "make", "model", "yom", "mileage"]):
#                             break
#                         options_text += " " + line
                
#                 options_dict["Options_Raw"] = options_text.strip()
#                 options_lower = options_text.lower()
                
#                 if any(x in options_lower for x in ["air condition", "aircondition", "a/c", "ac ", "air con", "climate control"]):
#                     options_dict["AIR CONDITION"] = "Yes"
#                 if any(x in options_lower for x in ["power steering", "p/s", "ps ", "powered steering"]):
#                     options_dict["POWER STEERING"] = "Yes"
#                 if any(x in options_lower for x in ["power mirror", "p/m", "pm ", "powered mirror", "electric mirror"]):
#                     options_dict["POWER MIRROR"] = "Yes"
#                 if any(x in options_lower for x in ["power window", "p/w", "pw ", "powered window", "electric window"]):
#                     options_dict["POWER WINDOW"] = "Yes"
#             else:
#                 if any(x in text for x in ["air condition", "aircondition", "a/c", "air con"]):
#                     options_dict["AIR CONDITION"] = "Yes"
#                 if any(x in text for x in ["power steering", "p/s"]):
#                     options_dict["POWER STEERING"] = "Yes"
#                 if any(x in text for x in ["power mirror", "p/m", "powered mirror"]):
#                     options_dict["POWER MIRROR"] = "Yes"
#                 if any(x in text for x in ["power window", "p/w", "powered window"]):
#                     options_dict["POWER WINDOW"] = "Yes"
#         except Exception as e:
#             print(f"Error extracting options: {e}")
        
#         return options_dict

#     def extract_structured_fields(self):
#         fields = {}
#         try:
#             body_text = self.driver.find_element(By.TAG_NAME, "body").text
#             lines = body_text.split("\n")
            
#             for i, line in enumerate(lines):
#                 line_lower = line.lower().strip()
                
#                 if line_lower == "make" and i + 1 < len(lines):
#                     fields["Make"] = lines[i + 1].strip()
#                 if line_lower == "model" and i + 1 < len(lines):
#                     fields["Model"] = lines[i + 1].strip()
#                 if ("yom" in line_lower or line_lower == "year") and i + 1 < len(lines):
#                     year_match = re.search(r'\b(19[89]\d|20[0-2]\d)\b', lines[i + 1])
#                     if year_match:
#                         fields["YOM"] = int(year_match.group(1))
#                 if "mileage" in line_lower or "millage" in line_lower:
#                     mileage = self.extract_mileage(line.lower()) or (self.extract_mileage(lines[i + 1].lower()) if i + 1 < len(lines) else None)
#                     if mileage:
#                         fields["Mileage (km)"] = mileage
#                 if "engine" in line_lower:
#                     engine = self.extract_engine_cc(line.lower()) or (self.extract_engine_cc(lines[i + 1].lower()) if i + 1 < len(lines) else None)
#                     if engine:
#                         fields["Engine (cc)"] = engine
#                 if "gear" in line_lower or "transmission" in line_lower:
#                     gear = self.extract_transmission(line.lower()) or (self.extract_transmission(lines[i + 1].lower()) if i + 1 < len(lines) else None)
#                     if gear:
#                         fields["Gear"] = gear
#                 if "fuel" in line_lower:
#                     fuel = self.extract_fuel_type(line.lower()) or (self.extract_fuel_type(lines[i + 1].lower()) if i + 1 < len(lines) else None)
#                     if fuel:
#                         fields["Fuel Type"] = fuel
#                 if "price" in line_lower or "rs" in line_lower:
#                     price = self.extract_price(line.lower()) or (self.extract_price(lines[i + 1].lower()) if i + 1 < len(lines) else None)
#                     if price:
#                         fields["Price"] = price
#         except Exception as e:
#             print(f"Error in extract_structured_fields: {e}")
        
#         return fields

#     def extract_contact(self, text):
#         patterns = [r'077\s*\d{3}\s*\d{4}', r'071\s*\d{3}\s*\d{4}', r'011\s*\d{7}']
#         for p in patterns:
#             m = re.search(p, text)
#             if m:
#                 return m.group(0)
#         return None

#     def extract_price(self, text):
#         patterns = [r'rs\.?\s*([\d,]+)', r'lkr\.?\s*([\d,]+)', r'([\d,]{6,})']
#         for p in patterns:
#             m = re.search(p, text, re.IGNORECASE)
#             if m:
#                 raw = re.sub(r'[^\d]', '', m.group(1))
#                 try:
#                     val = int(raw)
#                     if 50000 <= val <= 200000000:
#                         return val
#                 except ValueError:
#                     continue
#         return None

#     def extract_year(self, text):
#         m = re.search(r'\b(19[89]\d|20[0-2]\d)\b', text)
#         if m:
#             year = int(m.group(1))
#             if 1985 <= year <= 2025:
#                 return year
#         return None

#     def extract_brand_model(self, text):
#         brands = ["toyota", "honda", "nissan", "suzuki", "mitsubishi", "mazda", "bmw", "mercedes", "benz", "audi", "hyundai", "kia", "ford", "volkswagen", "daihatsu", "perodua"]
#         t = text.lower()
#         brand_name = None
        
#         for b in sorted(brands, key=len, reverse=True):
#             if b in t:
#                 brand_name = b.title() if b != "benz" else "Mercedes"
#                 break

#         words = text.split()
#         model = None
#         if brand_name:
#             try:
#                 idx = next(i for i, w in enumerate(words) if brand_name.lower() in w.lower())
#                 if idx + 1 < len(words):
#                     model = words[idx + 1].strip(',.()[]')
#             except StopIteration:
#                 pass

#         return brand_name, model

#     def extract_mileage(self, text):
#         patterns = [r'([\d,]+)\s*km', r'([\d,]+)\s*k(?:\s|$)', r'mileage[:\s]*([\d,]+)']
#         for p in patterns:
#             m = re.search(p, text, re.IGNORECASE)
#             if m:
#                 raw = m.group(1).replace(',', '')
#                 try:
#                     val = int(raw)
#                     if 'k' in m.group(0).lower() and 'km' not in m.group(0).lower():
#                         val *= 1000
#                     if 100 < val < 2000000:
#                         return val
#                 except ValueError:
#                     continue
#         return None

#     def extract_engine_cc(self, text):
#         patterns = [r'(\d{3,4})\s*cc', r'(\d\.\d)\s*l']
#         for p in patterns:
#             m = re.search(p, text, re.IGNORECASE)
#             if m:
#                 try:
#                     if '.' in m.group(1):
#                         return int(float(m.group(1)) * 1000)
#                     cc = int(m.group(1))
#                     if 500 <= cc <= 8000:
#                         return cc
#                 except ValueError:
#                     continue
#         return None

#     def extract_transmission(self, text):
#         if any(x in text for x in ["auto", "automatic", "a/t", "cvt"]):
#             return "Automatic"
#         if any(x in text for x in ["manual", "m/t"]):
#             return "Manual"
#         return None

#     def extract_fuel_type(self, text):
#         if "diesel" in text:
#             return "Diesel"
#         if any(x in text for x in ["petrol", "gasoline"]):
#             return "Petrol"
#         if "hybrid" in text:
#             return "Hybrid"
#         if "electric" in text:
#             return "Electric"
#         return None

#     def extract_town(self, text):
#         cities = ["colombo", "kandy", "galle", "matara", "jaffna", "negombo", "kurunegala", "puttalam", "kalutara", "nuwara eliya", "gampaha"]
#         for city in sorted(cities, key=len, reverse=True):
#             if city in text.lower():
#                 return city.title()
#         return None

#     def extract_leasing(self, text):
#         return "Yes" if any(x in text for x in ["leasing", "lease", "finance"]) else "No"

#     def extract_condition(self, text):
#         for term in ["brand new", "registered", "unregistered", "used"]:
#             if term in text:
#                 return term.title()
#         return None

#     def save_data_to_csv(self):
#         if not self.data:
#             return
        
#         df = pd.DataFrame(self.data)
#         df = df.drop_duplicates(subset=["Title", "Price", "Town"], keep="last")
        
#         if "YOM" in df.columns:
#             df = df[(df["YOM"].notna()) & (df["YOM"].between(2020, 2025))]
        
#         try:
#             df.to_csv(self.data_file, index=False, encoding="utf-8-sig")
#             print(f"✓ Saved {len(df)} records")
#         except PermissionError:
#             timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#             backup_file = f"riyasewana_used_cars_{timestamp}.csv"
#             df.to_csv(backup_file, index=False, encoding="utf-8-sig")
#             print(f"⚠ Saved to {backup_file}")

#     def close(self):
#         try:
#             self.save_data_to_csv()
#             self.save_progress()
#         finally:
#             self.driver.quit()


# if __name__ == "__main__":
#     scraper = RiyasewanaCarScraper()
#     try:
#         scraper.scrape_riyasewana(max_pages=5)
#     finally:
#         scraper.close()

# riyasewana_scraper.py
"""
Riyasewana.lk car listing scraper.

Features:
  - Resumes from last stopping point
  - Sophisticated duplicate detection
  - Outputs exact CSV format matching car_price_dataset.csv
  - Price in LKR Lakhs (not raw rupees)
  - Rate limiting with jitter to avoid bans

Output CSV columns:
  Brand, Model, YOM, Engine (cc), Gear, Fuel Type, Millage(KM),
  Town, Date, Leasing, Condition, AIR CONDITION, POWER STEERING,
  POWER MIRROR, POWER WINDOW, Price
"""

import time
import json
import os
import re
import hashlib
import random
import pandas as pd
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager


# ── Constants ────────────────────────────────────────────────
BASE_URL      = "https://riyasewana.com/search/cars"
PROGRESS_FILE = "scrape_progress.json"
OUTPUT_CSV    = "riyasewana_new_listings.csv"

CSV_COLUMNS = [
    "Brand", "Model", "YOM", "Engine (cc)", "Gear", "Fuel Type",
    "Millage(KM)", "Town", "Date", "Leasing", "Condition",
    "AIR CONDITION", "POWER STEERING", "POWER MIRROR", "POWER WINDOW",
    "Price",
]

# Sri Lankan towns — ordered longest-first to avoid partial matches
TOWNS = sorted([
    "Colombo", "Kandy", "Galle", "Matara", "Jaffna", "Negombo",
    "Kurunegala", "Puttalam", "Kalutara", "Nuwara Eliya", "Gampaha",
    "Ratnapura", "Badulla", "Anuradhapura", "Polonnaruwa", "Trincomalee",
    "Batticaloa", "Vavuniya", "Mannar", "Hambantota", "Matale",
    "Kegalle", "Ampara", "Monaragala", "Kilinochchi", "Mullaitivu",
    "Dehiwala-Mount Lavinia", "Dehiwala", "Mount Lavinia", "Moratuwa",
    "Nugegoda", "Maharagama", "Homagama", "Malabe", "Kaduwela",
    "Kelaniya", "Ragama", "Wattala", "Ja-Ela", "Seeduwa",
    "Ekala", "Minuwangoda", "Katunayake", "Kadawatha", "Peliyagoda",
    "Battaramulla", "Kottawa", "Piliyandala", "Boralesgamuwa",
    "Panadura", "Horana", "Bandaragama", "Beruwala", "Aluthgama",
    "Hikkaduwa", "Ambalangoda", "Bentota", "Balapitiya",
    "Peradeniya", "Katugastota", "Gampola", "Nawalapitiya",
    "Weligama", "Mirissa", "Tangalle", "Tissamaharama",
    "Avissawella", "Balangoda", "Embilipitiya", "Bandarawela",
    "Welimada", "Haputale", "Diyatalawa", "Nuwara",
], key=len, reverse=True)


# ── Progress manager ─────────────────────────────────────────
class Progress:
    def __init__(self, path=PROGRESS_FILE):
        self.path = path
        self.scraped_pages: set = set()
        self.scraped_urls:  set = set()
        self.url_hashes:    set = set()   # MD5 of listing URL (compact storage)
        self.load()

    def load(self):
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                d = json.load(f)
            self.scraped_pages = set(d.get("scraped_pages", []))
            self.scraped_urls  = set(d.get("scraped_urls",  []))
            self.url_hashes    = set(d.get("url_hashes",   []))
            print(f"[resume] {len(self.scraped_pages)} pages, "
                  f"{len(self.scraped_urls)} URLs already scraped")
        except Exception as e:
            print(f"[progress] load error: {e}")

    def save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump({
                    "scraped_pages": list(self.scraped_pages),
                    "scraped_urls":  list(self.scraped_urls),
                    "url_hashes":    list(self.url_hashes),
                    "last_update":   datetime.now().isoformat(),
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[progress] save error: {e}")

    def seen_url(self, url: str) -> bool:
        return url in self.scraped_urls

    def mark_url(self, url: str):
        self.scraped_urls.add(url)
        self.url_hashes.add(hashlib.md5(url.encode()).hexdigest())

    def seen_page(self, page_url: str) -> bool:
        return page_url in self.scraped_pages

    def mark_page(self, page_url: str):
        self.scraped_pages.add(page_url)


# ── Duplicate detector ───────────────────────────────────────
class DuplicateDetector:
    """
    Uses a composite key: brand + model + YOM + price_bucket + mileage_bucket.
    Price bucket = round to nearest 2L.
    Mileage bucket = round to nearest 5,000 km.
    Two listings match if ALL bucket keys match — same car relisted at same price.
    """

    def __init__(self):
        self._keys: set = set()

    def _key(self, row: dict) -> str:
        brand   = str(row.get("Brand",  "")).upper().strip()
        model   = str(row.get("Model",  "")).upper().strip()
        yom     = str(row.get("YOM",    ""))
        price   = row.get("Price",    0) or 0
        mileage = row.get("Millage(KM)", 0) or 0

        p_bucket = round(float(price)   / 2)  * 2      # nearest 2L
        m_bucket = round(float(mileage) / 5000) * 5000  # nearest 5k km

        return f"{brand}|{model}|{yom}|{p_bucket}|{m_bucket}"

    def load_from_csv(self, path: str):
        if not os.path.exists(path):
            return
        try:
            df = pd.read_csv(path)
            for _, row in df.iterrows():
                self._keys.add(self._key(row.to_dict()))
            print(f"[dedup] loaded {len(self._keys)} existing fingerprints")
        except Exception as e:
            print(f"[dedup] load error: {e}")

    def is_duplicate(self, row: dict) -> bool:
        return self._key(row) in self._keys

    def add(self, row: dict):
        self._keys.add(self._key(row))


# ── Field extractors ─────────────────────────────────────────
def parse_price_to_lakhs(text: str):
    """Convert raw price string to LKR Lakhs (float, 1 decimal)."""
    cleaned = re.sub(r"[^\d]", "", text)
    if not cleaned:
        return None
    try:
        raw = int(cleaned)
        if raw < 1000:          # already in lakhs?
            return None
        if raw < 10_000:        # e.g. "950" — ambiguous, skip
            return None
        if raw > 200_000_000:   # unreasonably large
            return None
        # Convert rupees → lakhs
        lakhs = raw / 100_000
        return round(lakhs, 1)
    except ValueError:
        return None


def extract_price(text: str):
    # Prefer "Rs. X,XXX,XXX" pattern
    for pat in [
        r"rs\.?\s*([\d,]+)",
        r"lkr\.?\s*([\d,]+)",
        r"price[:\s]+([\d,]+)",
        r"([\d,]{6,})",
    ]:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            val = parse_price_to_lakhs(m.group(1))
            if val:
                return val
    return None


def extract_year(text: str):
    for m in re.finditer(r'\b(19[89]\d|20[0-2]\d)\b', text):
        y = int(m.group(1))
        if 1985 <= y <= datetime.now().year:
            return y
    return None


def extract_mileage(text: str):
    for pat in [
        r"([\d,]+)\s*km",
        r"mileage[:\s]*([\d,]+)",
        r"millage[:\s]*([\d,]+)",
    ]:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            raw = int(re.sub(r"[^\d]", "", m.group(1)))
            if 100 < raw < 2_000_000:
                return float(raw)
    return None


def extract_engine(text: str):
    for pat in [r"(\d{3,4})\s*cc", r"(\d\.\d)\s*[lL](?:\s|$)"]:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            try:
                val = m.group(1)
                if "." in val:
                    cc = int(float(val) * 1000)
                else:
                    cc = int(val)
                if 500 <= cc <= 8000:
                    return float(cc)
            except ValueError:
                pass
    return None


def extract_gear(text: str):
    t = text.lower()
    if any(x in t for x in ["automatic", "auto", "a/t", "cvt", "tiptronic"]):
        return "Automatic"
    if any(x in t for x in ["manual", "m/t", "stick"]):
        return "Manual"
    return None


def extract_fuel(text: str):
    t = text.lower()
    if "electric" in t:
        return "Electric"
    if "plug" in t and "hybrid" in t:
        return "Plug-in Hybrid"
    if "hybrid" in t:
        return "Hybrid"
    if "diesel" in t:
        return "Diesel"
    if "gas" in t or "petrol" in t or "gasoline" in t:
        return "Petrol"
    return None


def extract_town(text: str):
    t = text.lower()
    for city in TOWNS:
        if city.lower() in t:
            return city
    return None


def extract_leasing(text: str):
    t = text.lower()
    if any(x in t for x in ["leasing available", "lease available", "can arrange leasing"]):
        return "Leasing Available"
    if any(x in t for x in ["leasing", "lease", "finance"]):
        return "Leasing Available"
    return "No Leasing"


def extract_condition(text: str):
    t = text.lower()
    if "brand new" in t or "brand-new" in t:
        return "BRAND NEW"
    if "recondition" in t:
        return "RECONDITIONED"
    return "USED"


def extract_options(text: str) -> dict:
    """
    Fallback text-scan for options — used only if DOM extraction fails.
    On Riyasewana, options appear as pill badges inside an OPTIONS section.
    """
    t = text.lower()
    return {
        "AIR CONDITION":  "Available" if any(x in t for x in ["air condition", "aircondition", "a/c", "climate control"]) else "Not_Available",
        "POWER STEERING": "Available" if any(x in t for x in ["power steering", "p/s", "power-steering"])                else "Not_Available",
        "POWER MIRROR":   "Available" if any(x in t for x in ["power mirror",   "p/m", "electric mirror"])               else "Not_Available",
        "POWER WINDOW":   "Available" if any(x in t for x in ["power window",   "p/w", "electric window"])               else "Not_Available",
    }


def extract_options_from_dom(driver) -> dict | None:
    """
    Extract options from the Riyasewana OPTIONS section on the listing page.

    Riyasewana renders options as pill/badge elements inside a section
    labelled "Options" or "OPTIONS". The badges contain text like:
        "AIR CONDITION", "POWER STEERING", "POWER MIRROR", "POWER WINDOW"

    Returns dict with Available/Not_Available values, or None if the
    OPTIONS section cannot be found at all (listing should be skipped).
    """
    result = {
        "AIR CONDITION":  "Not_Available",
        "POWER STEERING": "Not_Available",
        "POWER MIRROR":   "Not_Available",
        "POWER WINDOW":   "Not_Available",
    }

    keyword_map = {
        "air condition":   "AIR CONDITION",
        "aircondition":    "AIR CONDITION",
        "a/c":             "AIR CONDITION",
        "climate control": "AIR CONDITION",
        "power steering":  "POWER STEERING",
        "power-steering":  "POWER STEERING",
        "p/s":             "POWER STEERING",
        "power mirror":    "POWER MIRROR",
        "power-mirror":    "POWER MIRROR",
        "p/m":             "POWER MIRROR",
        "electric mirror": "POWER MIRROR",
        "power window":    "POWER WINDOW",
        "power-window":    "POWER WINDOW",
        "p/w":             "POWER WINDOW",
        "electric window": "POWER WINDOW",
    }

    options_section_found = False

    try:
        # Strategy 1: find the OPTIONS heading, then collect sibling/child elements
        # Riyasewana uses a heading like <h2>Options</h2> or a div with class "more-dtl"
        selectors = [
            # Common Riyasewana class names for the options section
            ".more-dtl",
            ".opt-list",
            ".options-section",
            "[class*='option']",
            "[class*='Option']",
        ]

        section_el = None
        for sel in selectors:
            try:
                els = driver.find_elements(By.CSS_SELECTOR, sel)
                if els:
                    section_el = els[0]
                    options_section_found = True
                    break
            except Exception:
                continue

        # Strategy 2: find any element whose text is exactly "Options" or "OPTIONS"
        if not section_el:
            for tag in ["h2", "h3", "h4", "div", "span", "p", "strong"]:
                try:
                    els = driver.find_elements(By.TAG_NAME, tag)
                    for el in els:
                        if el.text.strip().lower() in ("options", "car options", "vehicle options"):
                            # Get the parent or next sibling container
                            try:
                                section_el = el.find_element(By.XPATH, "following-sibling::*[1]")
                            except Exception:
                                section_el = el.find_element(By.XPATH, "..")
                            options_section_found = True
                            break
                    if options_section_found:
                        break
                except Exception:
                    continue

        if section_el:
            # Get all text inside the options section
            section_text = section_el.text.lower()
            for kw, field in keyword_map.items():
                if kw in section_text:
                    result[field] = "Available"
        else:
            # Strategy 3: look for pill/badge elements anywhere on the page
            # Riyasewana wraps option labels in <li> or <span> elements
            badge_selectors = ["li", "span.tag", "span.badge", ".tag", ".badge", ".pill"]
            all_option_text = []
            for sel in badge_selectors:
                try:
                    els = driver.find_elements(By.CSS_SELECTOR, sel)
                    for el in els:
                        t = el.text.strip().lower()
                        if t and len(t) < 40:  # option labels are short
                            all_option_text.append(t)
                except Exception:
                    continue

            combined = " ".join(all_option_text)
            for kw, field in keyword_map.items():
                if kw in combined:
                    result[field] = "Available"

            # If we found at least one option keyword, consider the section found
            if any(v == "Available" for v in result.values()):
                options_section_found = True

    except Exception as e:
        print(f"    [options-dom] error: {e}")

    # Return None if we could not find the options section at all
    # (means the page didn't load properly or the listing has no options section)
    if not options_section_found and all(v == "Not_Available" for v in result.values()):
        return None

    return result


# ── Structured field parser (table-style pages) ───────────────
def parse_table_fields(body_text: str) -> dict:
    """
    Riyasewana listing pages show fields as label/value pairs on adjacent lines.
    Example:
        Make\nToyota\nModel\nCorolla\nYOM\n2018
    """
    fields = {}
    lines  = [l.strip() for l in body_text.splitlines() if l.strip()]

    label_map = {
        "make":        "Brand",
        "brand":       "Brand",
        "model":       "Model",
        "yom":         "YOM",
        "year":        "YOM",
        "mileage":     "Mileage",
        "millage":     "Mileage",
        "engine":      "Engine",
        "gear":        "Gear",
        "transmission":"Gear",
        "fuel":        "Fuel",
        "fuel type":   "Fuel",
        "price":       "Price",
    }

    for i, line in enumerate(lines):
        key = line.lower().rstrip(":")
        if key in label_map and i + 1 < len(lines):
            val = lines[i + 1]
            mapped = label_map[key]
            fields[mapped] = val

    return fields


# ── Main scraper ─────────────────────────────────────────────
class RiyasewanaScraper:

    def __init__(self, output_csv=OUTPUT_CSV, headless=True):
        self.output_csv = output_csv
        self.progress   = Progress()
        self.dedup      = DuplicateDetector()
        self.dedup.load_from_csv(output_csv)
        self.records    = []
        self.driver     = self._init_driver(headless)

    def _init_driver(self, headless: bool):
        opts = Options()
        if headless:
            opts.add_argument("--headless")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--window-size=1920,1080")
        opts.set_preference("general.useragent.override",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0")
        svc = Service(GeckoDriverManager().install())
        return webdriver.Firefox(service=svc, options=opts)

    # ── Listing page extraction ──────────────────────────────
    def _extract_listing(self, url: str) -> dict | None:
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 12).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(random.uniform(1.0, 2.5))

            body_text = self.driver.find_element(By.TAG_NAME, "body").text
            body_lower = body_text.lower()

            # Table-style structured fields (most reliable)
            tbl = parse_table_fields(body_text)

            # Brand
            brand = tbl.get("Brand")
            if not brand:
                brand_raw, _ = self._extract_brand_model_from_text(body_text)
                brand = brand_raw
            brand = (brand or "Unknown").upper().strip()

            # Model
            model = tbl.get("Model") or self._extract_brand_model_from_text(body_text)[1]
            model = (model or "Unknown").strip()

            # YOM
            yom_raw = tbl.get("YOM") or ""
            yom = extract_year(yom_raw) or extract_year(body_text)

            # Engine
            engine_raw = tbl.get("Engine") or ""
            engine = extract_engine(engine_raw) or extract_engine(body_lower)

            # Gear
            gear_raw = tbl.get("Gear") or ""
            gear = extract_gear(gear_raw) or extract_gear(body_lower) or "Automatic"

            # Fuel
            fuel_raw = tbl.get("Fuel") or ""
            fuel = extract_fuel(fuel_raw) or extract_fuel(body_lower) or "Petrol"

            # Mileage
            mileage_raw = tbl.get("Mileage") or ""
            mileage = extract_mileage(mileage_raw) or extract_mileage(body_lower)

            # Town
            town = extract_town(body_text)

            # Leasing
            leasing = extract_leasing(body_lower)

            # Condition
            condition = extract_condition(body_lower)

            # Options — try DOM extraction first (finds the OPTIONS pill section)
            # Falls back to full-page text scan if DOM method fails
            opts = extract_options_from_dom(self.driver)
            if opts is None:
                # DOM extraction found no options section at all
                # Try text scan as last resort
                opts_text = extract_options(body_lower)
                # Only use text scan result if it found at least one option
                # Otherwise skip this listing — options section is mandatory
                if all(v == "Not_Available" for v in opts_text.values()):
                    print("    → skipped (OPTIONS section not found on listing page)")
                    return None
                opts = opts_text

            # Price (table first, then raw scan)
            price_raw = tbl.get("Price") or ""
            price = extract_price(price_raw) or extract_price(body_lower)

            # Validate
            if not price:
                return None
            if not yom:
                return None

            # Mandatory fields — skip listing if any are missing
            missing = []
            if brand == 'UNKNOWN':       missing.append('Brand')
            if model == 'UNKNOWN':       missing.append('Model')
            if not engine:               missing.append('Engine (cc)')
            if not gear:                 missing.append('Gear')
            if not fuel:                 missing.append('Fuel Type')
            if not mileage:              missing.append('Millage(KM)')
            if not town:                 missing.append('Town')
            # Equipment options are on the listing page — if all are Not_Available
            # it likely means the page didn't render the options section properly
            # We allow all Not_Available only if the DOM scan explicitly confirmed
            # the options section exists (opts is not None from DOM scan)

            if missing:
                print(f'    → skipped (missing: {missing})')
                return None

            row = {
                "Brand":           brand,
                "Model":           model,
                "YOM":             yom,
                "Engine (cc)":     engine,
                "Gear":            gear,
                "Fuel Type":       fuel,
                "Millage(KM)":     mileage,
                "Town":            town,
                "Date":            datetime.now().strftime("%Y-%m-%d"),
                "Leasing":         leasing,
                "Condition":       condition,
                "AIR CONDITION":   opts["AIR CONDITION"],
                "POWER STEERING":  opts["POWER STEERING"],
                "POWER MIRROR":    opts["POWER MIRROR"],
                "POWER WINDOW":    opts["POWER WINDOW"],
                "Price":           price,
            }
            return row

        except Exception as e:
            print(f"    [extract] error: {e}")
            return None

    def _extract_brand_model_from_text(self, text: str):
        BRANDS = [
            "Toyota", "Honda", "Nissan", "Suzuki", "Mitsubishi", "Mazda",
            "BMW", "Mercedes-Benz", "Mercedes", "Audi", "Hyundai", "Kia",
            "Ford", "Volkswagen", "Daihatsu", "Perodua", "Subaru", "Isuzu",
            "Land Rover", "Lexus", "Porsche", "Volvo", "Peugeot", "Renault",
            "Fiat", "Jeep", "Chevrolet", "Dodge", "Chrysler", "Jaguar",
            "Skoda", "Seat", "Citroen", "Opel", "Vauxhall",
        ]
        t = text.lower()
        brand = None
        for b in sorted(BRANDS, key=len, reverse=True):
            if b.lower() in t:
                brand = b
                break

        model = None
        if brand:
            words = text.split()
            for i, w in enumerate(words):
                if brand.lower().split()[0] in w.lower():
                    if i + 1 < len(words):
                        model = re.sub(r'[^\w\-]', '', words[i + 1])
                    break

        return brand, model

    # ── Listing link extraction from search page ──────────────
    def _get_listing_links(self, page_url: str) -> list[str]:
        try:
            self.driver.get(page_url)
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "a"))
            )
            time.sleep(random.uniform(2.0, 4.0))

            links = []
            for a in self.driver.find_elements(By.TAG_NAME, "a"):
                try:
                    href = a.get_attribute("href") or ""
                    # Riyasewana listing URLs: /buy{make}-{model}-sale-{city}-{id}
                    if (
                        "riyasewana.com/buy" in href
                        and "-sale-" in href
                        and re.search(r'-\d+$', href)
                        and not self.progress.seen_url(href)
                    ):
                        links.append(href)
                except Exception:
                    continue

            return list(dict.fromkeys(links))  # deduplicate while preserving order
        except Exception as e:
            print(f"  [page] link extraction error: {e}")
            return []

    # ── CSV writer ────────────────────────────────────────────
    def _flush_to_csv(self):
        if not self.records:
            return
        new_df = pd.DataFrame(self.records, columns=CSV_COLUMNS)
        if os.path.exists(self.output_csv):
            existing = pd.read_csv(self.output_csv)
            combined = pd.concat([existing, new_df], ignore_index=True)
        else:
            combined = new_df

        combined.to_csv(self.output_csv, index=False, encoding="utf-8-sig")
        print(f"  [csv] {len(combined)} total records saved to {self.output_csv}")
        self.records = []

    # ── Main loop ─────────────────────────────────────────────
    def scrape(self, max_pages: int = 200, flush_every: int = 20):
        print(f"\n{'='*60}")
        print(f"  Riyasewana scraper — max {max_pages} pages")
        print(f"  Output: {self.output_csv}")
        print(f"{'='*60}\n")

        total_new = 0

        for page in range(1, max_pages + 1):
            page_url = f"{BASE_URL}?page={page}"

            if self.progress.seen_page(page_url):
                print(f"Page {page}: already scraped — skipping")
                continue

            print(f"\nPage {page}/{max_pages} — {page_url}")

            links = self._get_listing_links(page_url)
            print(f"  {len(links)} new listings found")

            if not links:
                # If zero links found, likely last page — stop
                print("  No listings found — stopping.")
                break

            page_new = 0
            for i, url in enumerate(links, 1):
                print(f"  [{i}/{len(links)}] {url}")

                row = self._extract_listing(url)
                self.progress.mark_url(url)

                if not row:
                    print("    → skipped (no price/year)")
                    continue

                if self.dedup.is_duplicate(row):
                    print(f"    → duplicate ({row['Brand']} {row['Model']} {row['YOM']} Rs.{row['Price']}L)")
                    continue

                self.dedup.add(row)
                self.records.append([row.get(c) for c in CSV_COLUMNS])
                page_new += 1
                total_new += 1
                print(f"    ✓ {row['Brand']} {row['Model']} {row['YOM']} "
                      f"{row.get('Millage(KM)', '?')} km  Rs.{row['Price']}L  {row.get('Town', '?')}")

                # Rate limit per listing
                time.sleep(random.uniform(1.5, 3.5))

            self.progress.mark_page(page_url)

            # Save after every page
            if self.records:
                self._flush_to_csv()
            self.progress.save()

            print(f"  Page {page} done: +{page_new} new (total new: {total_new})")

            # Rate limit between pages
            time.sleep(random.uniform(3.0, 6.0))

        # Final flush
        self._flush_to_csv()
        self.progress.save()

        print(f"\n{'='*60}")
        print(f"  Scraping complete — {total_new} new records added")
        print(f"  Output: {self.output_csv}")
        print(f"{'='*60}\n")

    def close(self):
        self._flush_to_csv()
        self.progress.save()
        try:
            self.driver.quit()
        except Exception:
            pass


# ── Entry point ───────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Riyasewana car scraper")
    parser.add_argument("--pages",   type=int, default=200,  help="Max pages to scrape (default: 200)")
    parser.add_argument("--output",  type=str, default=OUTPUT_CSV, help="Output CSV path")
    parser.add_argument("--visible", action="store_true", help="Show browser window (non-headless)")
    args = parser.parse_args()

    scraper = RiyasewanaScraper(
        output_csv=args.output,
        headless=not args.visible,
    )

    try:
        scraper.scrape(max_pages=args.pages)
    except KeyboardInterrupt:
        print("\n[interrupted] saving progress...")
    finally:
        scraper.close()