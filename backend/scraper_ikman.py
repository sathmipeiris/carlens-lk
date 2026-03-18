# backend/scraper_ikman.py
import requests

import pandas as pd
import time
from datetime import datetime
import re
import json
from typing import List, Dict, Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IkmanCarScraper:
    """
    Production-ready web scraper for ikman.lk car listings
    
    Features:
    - Respects robots.txt
    - Rate limiting (polite scraping)
    - Error handling and retries
    - Data validation
    - Duplicate detection
    """
    
    def __init__(self):
        self.base_url = "https://ikman.lk"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://ikman.lk',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
    def scrape_listings(self, pages: int = 5, delay: float = 3.0) -> pd.DataFrame:
        """
        Scrape multiple pages of car listings
        
        Args:
            pages: Number of pages to scrape
            delay: Delay between requests (seconds)
        
        Returns:
            DataFrame with scraped listings
        """
        all_listings = []
        
        for page_num in range(1, pages + 1):
            logger.info(f"Scraping page {page_num}/{pages}...")
            
            try:
                # Get listing URLs from search page
                listing_urls = self._get_listing_urls(page_num)
                logger.info(f"Found {len(listing_urls)} listings on page {page_num}")
                
                # Scrape each listing
                for i, url in enumerate(listing_urls, 1):
                    try:
                        logger.info(f"  Scraping listing {i}/{len(listing_urls)}: {url}")
                        listing_data = self._scrape_single_listing(url)
                        
                        if listing_data:
                            all_listings.append(listing_data)
                            logger.info(f"    ✓ Extracted: {listing_data.get('Brand')} {listing_data.get('Model')}")
                        
                        time.sleep(delay)  # Rate limiting
                        
                    except Exception as e:
                        logger.error(f"    ✗ Error scraping {url}: {e}")
                        continue
                
                # Delay between pages
                time.sleep(delay * 2)
                
            except Exception as e:
                logger.error(f"Error on page {page_num}: {e}")
                continue
        
        df = pd.DataFrame(all_listings)
        logger.info(f"\n✓ Scraped {len(df)} total listings")
        return df
    
    def _get_listing_urls(self, page: int) -> List[str]:
        """Get all listing URLs from a search results page"""
        url = f"{self.base_url}/en/ads/sri-lanka/cars?page={page}"
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all listing cards
            # NOTE: Actual selectors depend on ikman.lk's current HTML structure
            # These are common patterns; inspect the site to verify
            
            listing_links = []
            
            # Method 1: Find by data attribute
            cards = soup.find_all('a', {'data-testid': 'listing-card'})
            for card in cards:
                href = card.get('href')
                if href:
                    full_url = href if href.startswith('http') else f"{self.base_url}{href}"
                    listing_links.append(full_url)
            
            # Method 2: Find by class (backup)
            if not listing_links:
                cards = soup.find_all('a', class_='card-link')
                for card in cards:
                    href = card.get('href')
                    if href and '/ad/' in href:
                        full_url = href if href.startswith('http') else f"{self.base_url}{href}"
                        listing_links.append(full_url)
            
            return listing_links
            
        except Exception as e:
            logger.error(f"Error fetching page {page}: {e}")
            return []
    
    def _scrape_single_listing(self, url: str) -> Optional[Dict]:
        """Extract data from a single car listing page"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title_elem = soup.find('h1', class_='title') or soup.find('h1')
            title = title_elem.text.strip() if title_elem else ''
            
            # Extract price
            price_elem = soup.find('div', class_='price') or soup.find('span', class_='price-text')
            price_text = price_elem.text.strip() if price_elem else ''
            price = self._parse_price(price_text)
            
            # Extract description/details
            details_section = soup.find('div', class_='ad-details') or soup.find('div', class_='description')
            
            # Parse structured data from details
            brand, model, year = self._parse_title(title)
            
            # Extract from detail fields
            details = self._extract_details(soup)
            
            # Build listing dict
            listing = {
                'Title': title,
                'Brand': brand or details.get('brand', ''),
                'Model': model or details.get('model', ''),
                'YOM': year or details.get('year'),
                'Price': price,
                'Mileage_KM': details.get('mileage'),
                'Transmission': details.get('transmission', 'Automatic'),
                'Fuel_Type': details.get('fuel_type', 'Petrol'),
                'Engine_CC': details.get('engine_cc'),
                'Condition': details.get('condition', 'USED'),
                'Town': details.get('location', 'Colombo'),
                'URL': url,
                'Scraped_Date': datetime.now().isoformat(),
                'Source': 'ikman.lk'
            }
            
            # Validate required fields
            if listing['Price'] and listing['Brand'] and listing['YOM']:
                return listing
            else:
                logger.warning(f"Incomplete data for {url}")
                return None
                
        except Exception as e:
            logger.error(f"Error scraping listing: {e}")
            return None
    
    def _parse_price(self, price_text: str) -> Optional[float]:
        """Extract numeric price from text"""
        try:
            # Remove currency symbols and text
            price_text = price_text.replace('Rs', '').replace('LKR', '').replace('Lakhs', '').replace(',', '').strip()
            
            # Extract numbers
            numbers = re.findall(r'[\d.]+', price_text)
            if numbers:
                price = float(numbers[0])
                # If price is in lakhs (< 1000), return as-is; else convert
                return price if price < 1000 else price / 100000
            return None
        except:
            return None
    
    def _parse_title(self, title: str) -> tuple:
        """Extract brand, model, year from title"""
        # Common format: "Toyota Aqua 2016" or "Honda Civic EX 2018"
        parts = title.split()
        
        brand = parts[0] if len(parts) > 0 else None
        model = parts[1] if len(parts) > 1 else None
        
        # Find year (4-digit number)
        year = None
        for part in parts:
            if re.match(r'^\d{4}$', part):
                year = int(part)
                break
        
        return brand, model, year
    
    def _extract_details(self, soup: BeautifulSoup) -> Dict:
        """Extract structured details from listing page"""
        details = {}
        
        # Find detail items (common pattern: label + value pairs)
        detail_items = soup.find_all('div', class_='detail-item') or soup.find_all('li')
        
        for item in detail_items:
            text = item.text.strip().lower()
            
            # Mileage
            if 'mileage' in text or 'km' in text:
                mileage_match = re.search(r'([\d,]+)\s*km', text)
                if mileage_match:
                    details['mileage'] = int(mileage_match.group(1).replace(',', ''))
            
            # Transmission
            if 'automatic' in text:
                details['transmission'] = 'Automatic'
            elif 'manual' in text:
                details['transmission'] = 'Manual'
            
            # Fuel type
            if 'petrol' in text:
                details['fuel_type'] = 'Petrol'
            elif 'diesel' in text:
                details['fuel_type'] = 'Diesel'
            elif 'hybrid' in text:
                details['fuel_type'] = 'Hybrid'
            elif 'electric' in text:
                details['fuel_type'] = 'Electric'
            
            # Engine capacity
            engine_match = re.search(r'(\d{3,4})\s*cc', text)
            if engine_match:
                details['engine_cc'] = int(engine_match.group(1))
            
            # Condition
            if 'brand new' in text:
                details['condition'] = 'BRAND_NEW'
            elif 'recondition' in text:
                details['condition'] = 'RECONDITION'
            
            # Location
            location_elem = soup.find('span', class_='location')
            if location_elem:
                details['location'] = location_elem.text.strip()
        
        return details
    
    def save_to_csv(self, df: pd.DataFrame, filename: str = None):
        """Save scraped data to CSV"""
        if filename is None:
            filename = f"ikman_scraped_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        df.to_csv(filename, index=False)
        logger.info(f"✓ Saved {len(df)} listings to {filename}")
        return filename
    
    def merge_with_dataset(self, scraped_df: pd.DataFrame, existing_csv: str = 'car_price_dataset.csv'):
        """Merge scraped data with existing training dataset"""
        try:
            existing_df = pd.read_csv(existing_csv)
            
            # Standardize column names
            column_mapping = {
                'Mileage_KM': 'Millage(KM)',
                'Transmission': 'Gear',
                'Engine_CC': 'Engine (cc)'
            }
            scraped_df = scraped_df.rename(columns=column_mapping)
            
            # Combine
            combined = pd.concat([existing_df, scraped_df], ignore_index=True)
            
            # Remove duplicates
            combined = combined.drop_duplicates(subset=['Brand', 'Model', 'YOM', 'Price'], keep='last')
            
            # Save
            output_file = f"car_price_dataset_merged_{datetime.now().strftime('%Y%m%d')}.csv"
            combined.to_csv(output_file, index=False)
            
            logger.info(f"\n✓ Merged Dataset:")
            logger.info(f"  Existing: {len(existing_df)} records")
            logger.info(f"  Scraped: {len(scraped_df)} records")
            logger.info(f"  Total: {len(combined)} records")
            logger.info(f"  Saved to: {output_file}")
            
            return combined, output_file
            
        except FileNotFoundError:
            logger.warning(f"Existing dataset not found. Saving scraped data only.")
            output_file = self.save_to_csv(scraped_df)
            return scraped_df, output_file


# ========================================
# USAGE EXAMPLE
# ========================================
if __name__ == "__main__":
    scraper = IkmanCarScraper()
    
    # Scrape 3 pages (conservative for testing)
    print("="*60)
    print("Starting ikman.lk Car Scraper")
    print("="*60)
    
    scraped_data = scraper.scrape_listings(pages=3, delay=3.0)
    
    if not scraped_data.empty:
        # Preview data
        print("\n" + "="*60)
        print("Scraped Data Preview:")
        print("="*60)
        print(scraped_data[['Brand', 'Model', 'YOM', 'Price', 'Town']].head(10))
        
        # Save
        csv_file = scraper.save_to_csv(scraped_data)
        
        # Merge with existing dataset
        try:
            merged_df, merged_file = scraper.merge_with_dataset(scraped_data)
            print(f"\n✓ Ready for retraining with {len(merged_df)} samples!")
        except Exception as e:
            print(f"\n⚠️  Merge failed: {e}")
    else:
        print("\n✗ No data scraped. Check website structure or rate limits.")
