from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager

import time, json, os, re, hashlib, random
import pandas as pd
from datetime import datetime


class RiyasewanaCarScraper:
    def __init__(self,
                 resume_file="riyasewana_progress.json",
                 data_file="riyasewana_used_cars.csv"):
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")

        service = Service(GeckoDriverManager().install())
        self.driver = webdriver.Firefox(service=service, options=options)

        self.data = []
        self.scrape_date = datetime.now().strftime("%Y-%m-%d")
        self.resume_file = resume_file
        self.data_file = data_file

        self.scraped_pages = set()
        self.scraped_urls = set()
        self.listing_signatures = set()

        self.load_progress()
        self.load_existing_data()

    def load_progress(self):
        if os.path.exists(self.resume_file):
            try:
                with open(self.resume_file, "r", encoding="utf-8") as f:
                    p = json.load(f)
                self.scraped_pages = set(p.get("scraped_pages", []))
                self.scraped_urls = set(p.get("scraped_urls", []))
                sig_list = p.get("listing_signatures", [])
                for sig in sig_list:
                    self.listing_signatures.add(
                        (sig["signature"], frozenset(sig["title_words"]), sig["price"], sig["mileage"], sig["title"])
                    )
            except Exception as e:
                print(f"Error loading progress: {e}")

    def save_progress(self):
        try:
            sig_list = [{"signature": sig, "title_words": list(words), "price": price, "mileage": mileage, "title": title}
                       for sig, words, price, mileage, title in self.listing_signatures]
            p = {
                "scraped_pages": list(self.scraped_pages),
                "scraped_urls": list(self.scraped_urls),
                "listing_signatures": sig_list,
                "last_update": datetime.now().isoformat(),
                "total_records": len(self.data),
            }
            with open(self.resume_file, "w", encoding="utf-8") as f:
                json.dump(p, f, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving progress: {e}")

    def load_existing_data(self):
        if os.path.exists(self.data_file):
            try:
                df = pd.read_csv(self.data_file)
                self.data = df.to_dict("records")
                for rec in self.data:
                    sig_data = self.generate_advanced_signature(rec)
                    if sig_data:
                        self.listing_signatures.add((sig_data["signature"], sig_data["title_words"], sig_data["price"], sig_data["mileage"], sig_data["title"]))
            except Exception as e:
                print(f"Error loading existing data: {e}")

    def generate_advanced_signature(self, car):
        if not car.get("Brand") or not car.get("Price"):
            return None

        brand = str(car.get("Brand", "")).lower().strip()
        model = str(car.get("Model", "")).lower().strip()
        year = int(car.get("YOM", 0) or 0)
        price = int(car.get("Price", 0) or 0)
        mileage = int(car.get("Millage(KM)", 0) or 0)
        location = str(car.get("Town", "")).lower().strip()
        title = str(car.get("Title", "")).lower().strip()

        price_range = int(price * 0.05) if price > 0 else 0
        mileage_range = int(max(mileage * 0.1, 1000)) if mileage > 0 else 0
        location_area = location.split(",")[0] if location else ""

        parts = [brand, model, str(year), str(price_range), str(mileage_range), location_area]
        sig_str = "|".join(parts)
        signature = hashlib.md5(sig_str.encode()).hexdigest()
        title_words = set(title.split())

        return {"signature": signature, "title_words": frozenset(title_words), "price": price, "mileage": mileage, "title": title}

    def is_sophisticated_duplicate(self, car):
        sig_data = self.generate_advanced_signature(car)
        if not sig_data:
            return False

        new_sig = sig_data["signature"]
        new_words = sig_data["title_words"]
        new_price = sig_data["price"]
        new_mileage = sig_data["mileage"]

        for existing_sig, words, price, mileage, title in self.listing_signatures:
            if existing_sig != new_sig:
                continue

            if new_words and words:
                common = new_words.intersection(words)
                union = new_words.union(words)
                similarity = len(common) / len(union) if union else 0
            else:
                similarity = 1.0

            price_diff = abs(new_price - price) / max(new_price, 1)
            mileage_diff = abs(new_mileage - mileage) / max(new_mileage, 1) if mileage and new_mileage else 0

            if similarity >= 0.8 and price_diff <= 0.02 and mileage_diff <= 0.05:
                return True

        self.listing_signatures.add((new_sig, new_words, new_price, new_mileage, sig_data["title"]))
        return False

    def scrape_riyasewana(self, max_pages=200):
        base_url = "https://riyasewana.com/search/cars"

        for page in range(1, max_pages + 1):
            page_url = f"{base_url}?page={page}"
            if page_url in self.scraped_pages:
                continue

            print(f"\n{'='*60}\nScraping page {page}...\n{'='*60}")
            
            self.driver.get(page_url)
            time.sleep(random.uniform(3, 5))

            listing_links = []
            
            try:
                print("Finding car listing links...")
                all_links = self.driver.find_elements(By.TAG_NAME, "a")
                print(f"Found {len(all_links)} total links")
                
                for link in all_links:
                    try:
                        href = link.get_attribute("href")
                        if not href:
                            continue
                        
                        # Match the pattern: /buy{brand}-{model}-sale-{location}-{ID}
                        if "/buy" in href and "-sale-" in href and href.endswith(re.search(r'-\d+$', href).group(0) if re.search(r'-\d+$', href) else ""):
                            if href not in self.scraped_urls:
                                listing_links.append(href)
                    except:
                        continue
                
                print(f"Found {len(listing_links)} car listing links")
                
            except Exception as e:
                print(f"Error finding links: {e}")

            listing_links = list(dict.fromkeys(listing_links))
            print(f"\nProcessing {len(listing_links)} unique listing links...")
            
            if not listing_links:
                self.scraped_pages.add(page_url)
                self.save_progress()
                continue

            new_records = 0
            for idx, listing_url in enumerate(listing_links, 1):
                try:
                    if listing_url in self.scraped_urls:
                        continue

                    print(f"  [{idx}/{len(listing_links)}] {listing_url}")
                    
                    self.driver.get(listing_url)
                    time.sleep(random.uniform(2, 4))
                    
                    car = self.extract_car_details_from_page(listing_url)
                    
                    if not car or not car.get("Price"):
                        self.scraped_urls.add(listing_url)
                        continue

                    year = car.get("YOM")
                    if year and not (2020 <= year <= 2025):
                        self.scraped_urls.add(listing_url)
                        continue

                    if self.is_sophisticated_duplicate(car):
                        self.scraped_urls.add(listing_url)
                        continue

                    self.data.append(car)
                    self.scraped_urls.add(listing_url)
                    new_records += 1
                    
                    price_str = f"Rs. {car.get('Price'):,}" if car.get('Price') else "No price"
                    print(f"    ✓ {car.get('Brand')} {car.get('Model')} {car.get('YOM')} - {price_str}")

                except Exception as e:
                    print(f"    ✗ Error: {e}")
                    self.scraped_urls.add(listing_url)
                    continue

            self.scraped_pages.add(page_url)
            print(f"\nPage {page}: +{new_records} cars (Total: {len(self.data)})")
            
            if page % 2 == 0 or new_records > 0:
                self.save_data_to_csv()
                self.save_progress()

            time.sleep(random.uniform(3, 6))

        self.save_data_to_csv()
        self.save_progress()
        print(f"\n{'='*60}\nDone! Total: {len(self.data)}\n{'='*60}")

    def extract_car_details_from_page(self, url):
        try:
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            full_text = self.driver.find_element(By.TAG_NAME, "body").text
            full_text_lower = full_text.lower()

            title = None
            try:
                title_elem = self.driver.find_element(By.CSS_SELECTOR, "h1, h2.title, .ad-title")
                title = title_elem.text.strip()
            except:
                lines = full_text.split("\n")
                title = lines[0].strip() if lines else "Unknown"

            fields = self.extract_structured_fields()
            
            if not fields.get("Make"):
                fields["Make"] = self.extract_brand_model(full_text)[0]
            if not fields.get("Model"):
                fields["Model"] = self.extract_brand_model(full_text)[1]
            if not fields.get("YOM"):
                fields["YOM"] = self.extract_year(full_text)
            if not fields.get("Price"):
                fields["Price"] = self.extract_price(full_text_lower)
            if not fields.get("Mileage (km)"):
                fields["Mileage (km)"] = self.extract_mileage(full_text_lower)
            if not fields.get("Engine (cc)"):
                fields["Engine (cc)"] = self.extract_engine_cc(full_text_lower)
            if not fields.get("Gear"):
                fields["Gear"] = self.extract_transmission(full_text_lower)
            if not fields.get("Fuel Type"):
                fields["Fuel Type"] = self.extract_fuel_type(full_text_lower)

            options = self.extract_options_section(full_text_lower)
            
            car = {
                "Title": title,
                "Brand": fields.get("Make") or "Unknown",
                "Model": fields.get("Model") or "Unknown",
                "YOM": fields.get("YOM"),
                "Engine (cc)": fields.get("Engine (cc)"),
                "Gear": fields.get("Gear"),
                "Fuel Type": fields.get("Fuel Type"),
                "Millage(KM)": fields.get("Mileage (km)"),
                "Town": self.extract_town(full_text),
                "Date": self.scrape_date,
                "Leasing": self.extract_leasing(full_text_lower),
                "Condition": self.extract_condition(full_text_lower),
                "AIR CONDITION": options.get("AIR CONDITION"),
                "POWER STEERING": options.get("POWER STEERING"),
                "POWER MIRROR": options.get("POWER MIRROR"),
                "POWER WINDOW": options.get("POWER WINDOW"),
                "Price": fields.get("Price"),
                "Contact": self.extract_contact(full_text),
                "Options": options.get("Options_Raw"),
                "SourceURL": url,
                "ScrapeDate": self.scrape_date,
            }

            return car

        except Exception as e:
            print(f"Error extracting: {e}")
            return None

    def extract_options_section(self, text):
        options_dict = {"AIR CONDITION": "No", "POWER STEERING": "No", "POWER MIRROR": "No", "POWER WINDOW": "No", "Options_Raw": ""}
        
        try:
            lines = text.split("\n")
            options_start = -1
            for i, line in enumerate(lines):
                if line.strip().lower() == "options":
                    options_start = i
                    break
            
            if options_start >= 0 and options_start + 1 < len(lines):
                options_text = ""
                for j in range(1, 6):
                    if options_start + j < len(lines):
                        line = lines[options_start + j].strip().lower()
                        if any(x in line for x in ["engine", "gear", "fuel", "price", "contact", "details", "make", "model", "yom", "mileage"]):
                            break
                        options_text += " " + line
                
                options_dict["Options_Raw"] = options_text.strip()
                options_lower = options_text.lower()
                
                if any(x in options_lower for x in ["air condition", "aircondition", "a/c", "ac ", "air con", "climate control"]):
                    options_dict["AIR CONDITION"] = "Yes"
                if any(x in options_lower for x in ["power steering", "p/s", "ps ", "powered steering"]):
                    options_dict["POWER STEERING"] = "Yes"
                if any(x in options_lower for x in ["power mirror", "p/m", "pm ", "powered mirror", "electric mirror"]):
                    options_dict["POWER MIRROR"] = "Yes"
                if any(x in options_lower for x in ["power window", "p/w", "pw ", "powered window", "electric window"]):
                    options_dict["POWER WINDOW"] = "Yes"
            else:
                if any(x in text for x in ["air condition", "aircondition", "a/c", "air con"]):
                    options_dict["AIR CONDITION"] = "Yes"
                if any(x in text for x in ["power steering", "p/s"]):
                    options_dict["POWER STEERING"] = "Yes"
                if any(x in text for x in ["power mirror", "p/m", "powered mirror"]):
                    options_dict["POWER MIRROR"] = "Yes"
                if any(x in text for x in ["power window", "p/w", "powered window"]):
                    options_dict["POWER WINDOW"] = "Yes"
        except Exception as e:
            print(f"Error extracting options: {e}")
        
        return options_dict

    def extract_structured_fields(self):
        fields = {}
        try:
            body_text = self.driver.find_element(By.TAG_NAME, "body").text
            lines = body_text.split("\n")
            
            for i, line in enumerate(lines):
                line_lower = line.lower().strip()
                
                if line_lower == "make" and i + 1 < len(lines):
                    fields["Make"] = lines[i + 1].strip()
                if line_lower == "model" and i + 1 < len(lines):
                    fields["Model"] = lines[i + 1].strip()
                if ("yom" in line_lower or line_lower == "year") and i + 1 < len(lines):
                    year_match = re.search(r'\b(19[89]\d|20[0-2]\d)\b', lines[i + 1])
                    if year_match:
                        fields["YOM"] = int(year_match.group(1))
                if "mileage" in line_lower or "millage" in line_lower:
                    mileage = self.extract_mileage(line.lower()) or (self.extract_mileage(lines[i + 1].lower()) if i + 1 < len(lines) else None)
                    if mileage:
                        fields["Mileage (km)"] = mileage
                if "engine" in line_lower:
                    engine = self.extract_engine_cc(line.lower()) or (self.extract_engine_cc(lines[i + 1].lower()) if i + 1 < len(lines) else None)
                    if engine:
                        fields["Engine (cc)"] = engine
                if "gear" in line_lower or "transmission" in line_lower:
                    gear = self.extract_transmission(line.lower()) or (self.extract_transmission(lines[i + 1].lower()) if i + 1 < len(lines) else None)
                    if gear:
                        fields["Gear"] = gear
                if "fuel" in line_lower:
                    fuel = self.extract_fuel_type(line.lower()) or (self.extract_fuel_type(lines[i + 1].lower()) if i + 1 < len(lines) else None)
                    if fuel:
                        fields["Fuel Type"] = fuel
                if "price" in line_lower or "rs" in line_lower:
                    price = self.extract_price(line.lower()) or (self.extract_price(lines[i + 1].lower()) if i + 1 < len(lines) else None)
                    if price:
                        fields["Price"] = price
        except Exception as e:
            print(f"Error in extract_structured_fields: {e}")
        
        return fields

    def extract_contact(self, text):
        patterns = [r'077\s*\d{3}\s*\d{4}', r'071\s*\d{3}\s*\d{4}', r'011\s*\d{7}']
        for p in patterns:
            m = re.search(p, text)
            if m:
                return m.group(0)
        return None

    def extract_price(self, text):
        patterns = [r'rs\.?\s*([\d,]+)', r'lkr\.?\s*([\d,]+)', r'([\d,]{6,})']
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                raw = re.sub(r'[^\d]', '', m.group(1))
                try:
                    val = int(raw)
                    if 50000 <= val <= 200000000:
                        return val
                except ValueError:
                    continue
        return None

    def extract_year(self, text):
        m = re.search(r'\b(19[89]\d|20[0-2]\d)\b', text)
        if m:
            year = int(m.group(1))
            if 1985 <= year <= 2025:
                return year
        return None

    def extract_brand_model(self, text):
        brands = ["toyota", "honda", "nissan", "suzuki", "mitsubishi", "mazda", "bmw", "mercedes", "benz", "audi", "hyundai", "kia", "ford", "volkswagen", "daihatsu", "perodua"]
        t = text.lower()
        brand_name = None
        
        for b in sorted(brands, key=len, reverse=True):
            if b in t:
                brand_name = b.title() if b != "benz" else "Mercedes"
                break

        words = text.split()
        model = None
        if brand_name:
            try:
                idx = next(i for i, w in enumerate(words) if brand_name.lower() in w.lower())
                if idx + 1 < len(words):
                    model = words[idx + 1].strip(',.()[]')
            except StopIteration:
                pass

        return brand_name, model

    def extract_mileage(self, text):
        patterns = [r'([\d,]+)\s*km', r'([\d,]+)\s*k(?:\s|$)', r'mileage[:\s]*([\d,]+)']
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                raw = m.group(1).replace(',', '')
                try:
                    val = int(raw)
                    if 'k' in m.group(0).lower() and 'km' not in m.group(0).lower():
                        val *= 1000
                    if 100 < val < 2000000:
                        return val
                except ValueError:
                    continue
        return None

    def extract_engine_cc(self, text):
        patterns = [r'(\d{3,4})\s*cc', r'(\d\.\d)\s*l']
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                try:
                    if '.' in m.group(1):
                        return int(float(m.group(1)) * 1000)
                    cc = int(m.group(1))
                    if 500 <= cc <= 8000:
                        return cc
                except ValueError:
                    continue
        return None

    def extract_transmission(self, text):
        if any(x in text for x in ["auto", "automatic", "a/t", "cvt"]):
            return "Automatic"
        if any(x in text for x in ["manual", "m/t"]):
            return "Manual"
        return None

    def extract_fuel_type(self, text):
        if "diesel" in text:
            return "Diesel"
        if any(x in text for x in ["petrol", "gasoline"]):
            return "Petrol"
        if "hybrid" in text:
            return "Hybrid"
        if "electric" in text:
            return "Electric"
        return None

    def extract_town(self, text):
        cities = ["colombo", "kandy", "galle", "matara", "jaffna", "negombo", "kurunegala", "puttalam", "kalutara", "nuwara eliya", "gampaha"]
        for city in sorted(cities, key=len, reverse=True):
            if city in text.lower():
                return city.title()
        return None

    def extract_leasing(self, text):
        return "Yes" if any(x in text for x in ["leasing", "lease", "finance"]) else "No"

    def extract_condition(self, text):
        for term in ["brand new", "registered", "unregistered", "used"]:
            if term in text:
                return term.title()
        return None

    def save_data_to_csv(self):
        if not self.data:
            return
        
        df = pd.DataFrame(self.data)
        df = df.drop_duplicates(subset=["Title", "Price", "Town"], keep="last")
        
        if "YOM" in df.columns:
            df = df[(df["YOM"].notna()) & (df["YOM"].between(2020, 2025))]
        
        try:
            df.to_csv(self.data_file, index=False, encoding="utf-8-sig")
            print(f"✓ Saved {len(df)} records")
        except PermissionError:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"riyasewana_used_cars_{timestamp}.csv"
            df.to_csv(backup_file, index=False, encoding="utf-8-sig")
            print(f"⚠ Saved to {backup_file}")

    def close(self):
        try:
            self.save_data_to_csv()
            self.save_progress()
        finally:
            self.driver.quit()


if __name__ == "__main__":
    scraper = RiyasewanaCarScraper()
    try:
        scraper.scrape_riyasewana(max_pages=5)
    finally:
        scraper.close()
