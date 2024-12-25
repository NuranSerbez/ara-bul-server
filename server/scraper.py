import asyncio
from playwright.async_api import async_playwright
import pandas as pd
from sqlalchemy import create_engine, text
import logging
import os
import re
import random
import time
from typing import List, Dict

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:aaaERTYUHGF123@db:5432/arabul_db')
LOG_DIR = os.getenv('LOG_DIR', '/var/log/scraper')
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'scraper.log')),
        logging.StreamHandler()
    ]
)

class Television:
    def __init__(self, url: str, specs: Dict[str, str]):
        self.url = url
        self.specs = specs

async def init_playwright():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=True,
        args=['--no-sandbox', '--disable-dev-shm-usage']
    )
    context = await browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    )
    return playwright, browser, context

async def scrape_television_links(context, url: str) -> List[str]:
    page = await context.new_page()
    try:
        await page.goto(url, wait_until='load', timeout=120000)
        await page.wait_for_selector('li[class^="productListContent-"]', timeout=120000)
        await asyncio.sleep(5)  # Wait for dynamic content
        
        links = []
        product_cards = await page.query_selector_all('li[class^="productListContent-"]')
        
        for card in product_cards:
            link = await card.query_selector('a')
            if link:
                href = await link.get_attribute('href')
                if href and "adservice.hepsiburada.com" not in href:
                    full_url = f'https://www.hepsiburada.com{href}'
                    links.append(full_url)
                    logging.info(f"Found product link: {full_url}")
        
        return links
    except Exception as e:
        logging.error(f"Error scraping links: {e}")
        return []
    finally:
        await page.close()

async def scrape_television_data(context, links: List[str]) -> List[Television]:
    televisions = []
    
    for link in links:
        page = await context.new_page()
        try:
            logging.info(f"Starting to scrape: {link}")
            await page.goto(link, timeout=30000)
            await page.wait_for_load_state('domcontentloaded')
            
            specs = {'url': link}
            
            # Get price
            try:
                price_elem = await page.query_selector('div[data-test-id="price-current-price"]')
                if price_elem:
                    price_text = await price_elem.inner_text()
                    specs['price'] = price_text.strip()
                    logging.info(f"Found price: {specs['price']}")
            except Exception as e:
                logging.error(f"Error getting price: {e}")

            # Extract specifications using the correct sibling structure
            specs_data = await page.evaluate('''() => {
                const debug = {log: []};
                
                try {
                    // First find the techSpecs div
                    const techSpecsDiv = document.getElementById('techSpecs');
                    debug.log.push(`TechSpecs div found: ${techSpecsDiv !== null}`);
                    
                    if (!techSpecsDiv) {
                        debug.log.push('No techSpecs div found');
                        return {specs: null, debug};
                    }
                    
                    // Find all immediate children of techSpecs
                    const children = Array.from(techSpecsDiv.children);
                    debug.log.push(`Found ${children.length} children in techSpecs`);
                    
                    // Find the index of "Ürün özellikleri" div
                    const headerIndex = children.findIndex(div => 
                        div.textContent.trim() === "Ürün özellikleri"
                    );
                    
                    debug.log.push(`Header index: ${headerIndex}`);
                    
                    if (headerIndex === -1) {
                        debug.log.push('No header div found');
                        return {specs: null, debug};
                    }
                    
                    // Get the next sibling which contains specifications
                    const specsContainer = children[headerIndex + 1];
                    debug.log.push(`Specs container found: ${specsContainer !== null}`);
                    
                    if (!specsContainer) {
                        debug.log.push('No specs container found');
                        return {specs: null, debug};
                    }
                    
                    const specs = {};
                    
                    // Get all specification rows (direct children of specs container)
                    const rows = Array.from(specsContainer.children);
                    debug.log.push(`Found ${rows.length} specification rows`);
                    
                    rows.forEach((row, index) => {
                        const divs = row.children;
                        if (divs.length >= 2) {
                            const label = divs[0].textContent.trim();
                            const valueSpan = divs[1].querySelector('span');
                            const valueAnchor = divs[1].querySelector('a');
                            const value = (valueSpan || valueAnchor)?.textContent.trim();
                            
                            if (label && value) {
                                specs[label] = value;
                                debug.log.push(`Row ${index}: ${label} = ${value}`);
                            }
                        }
                    });
                    
                    return {specs, debug};
                    
                } catch (error) {
                    debug.log.push(`Error: ${error.message}`);
                    return {specs: null, debug};
                }
            }''')
            
            if specs_data:
                # Log debug information
                if 'debug' in specs_data:
                    for log_line in specs_data['debug']['log']:
                        logging.info(f"JS Debug: {log_line}")
                
                # Process specifications if they exist
                if 'specs' in specs_data and specs_data['specs']:
                    for label, value in specs_data['specs'].items():
                        key = sanitize_column_name(label)
                        specs[key] = value
                        logging.info(f"Found spec: {key} = {value}")
            
            logging.info(f"Total specs found: {len(specs)}")
            
             # Save to database if we have specs
            if len(specs) > 1:
                try:
                    engine = create_engine(DATABASE_URL)
                    
                    with engine.connect() as conn:
                        # Create table if not exists with standard columns
                        create_table_sql = """
                        CREATE TABLE IF NOT EXISTS television_data (
                            url TEXT PRIMARY KEY,
                            price TEXT,
                            ekran_ebati TEXT,
                            cozunurluk_piksel TEXT,
                            yenileme_hizi_gercek TEXT,
                            goruntu_teknolojisi TEXT,
                            smart_tv TEXT,
                            isletim_sistemi TEXT,
                            hdmi_girisleri TEXT,
                            model_adi TEXT,
                            marka TEXT
                        );
                        """
                        conn.execute(text(create_table_sql))
                        
                        # Check for and add any missing columns
                        existing_columns_query = """
                            SELECT column_name 
                            FROM information_schema.columns 
                            WHERE table_name = 'television_data';
                        """
                        result = conn.execute(text(existing_columns_query))
                        existing_columns = {row[0] for row in result}
                        
                        # Add any missing columns from specs
                        for column in specs.keys():
                            if column.lower() not in {col.lower() for col in existing_columns}:
                                try:
                                    alter_table_sql = f"ALTER TABLE television_data ADD COLUMN {column} TEXT;"
                                    conn.execute(text(alter_table_sql))
                                    logging.info(f"Added new column: {column}")
                                except Exception as e:
                                    logging.error(f"Error adding column {column}: {e}")
                        
                        # Prepare column names and values
                        columns = list(specs.keys())
                        values = list(specs.values())
                        
                        # Create the parameterized query
                        placeholders = [f':{col}' for col in columns]
                        
                        insert_sql = f"""
                        INSERT INTO television_data ({', '.join(columns)})
                        VALUES ({', '.join(placeholders)})
                        ON CONFLICT (url) DO UPDATE SET
                        {', '.join(f"{col} = EXCLUDED.{col}" for col in columns if col != 'url')};
                        """
                        
                        # Execute with properly formatted parameters
                        params = {col: val for col, val in zip(columns, values)}
                        conn.execute(text(insert_sql), params)
                        conn.commit()
                        logging.info(f"Successfully saved TV to database: {link}")
                        
                except Exception as e:
                    logging.error(f"Error saving to database: {str(e)}")
            
            await asyncio.sleep(random.uniform(2, 4))
            
        except Exception as e:
            logging.error(f"Error scraping {link}: {str(e)}")
        finally:
            await page.close()
    
    return televisions

def sanitize_column_name(column_name: str) -> str:
    """Sanitize column names with standardized mappings."""
    # First convert to lowercase and apply Turkish character conversion
    column_name = turkish_to_latin(column_name.lower())
    
    # Define standard mappings for common specifications
    spec_mappings = {
        'ekran ebati': 'ekran_ebati',
        'cozunurluk': 'cozunurluk_piksel',
        'yenileme hizi': 'yenileme_hizi_gercek',
        'goruntu teknolojisi': 'goruntu_teknolojisi',
        'smart tv': 'smart_tv',
        'isletim sistemi': 'isletim_sistemi',
        'hdmi giris': 'hdmi_girisleri',
        'model': 'model_adi',
        'marka': 'marka'
    }
    
    # Check if the column name matches any standard mapping
    for key, value in spec_mappings.items():
        if key in column_name:
            return value
    
    # For other columns, just replace spaces with underscores and remove special characters
    sanitized = re.sub(r'[^a-z0-9_]', '', column_name.replace(' ', '_'))
    return sanitized

def turkish_to_latin(text: str) -> str:
    turkish_chars = {
        'ç': 'c', 'Ç': 'C', 'ğ': 'g', 'Ğ': 'G',
        'ı': 'i', 'I': 'I', 'İ': 'I', 'i': 'i',
        'ö': 'o', 'Ö': 'O', 'ş': 's', 'Ş': 'S',
        'ü': 'u', 'Ü': 'U'
    }
    for turkish, latin in turkish_chars.items():
        text = text.replace(turkish, latin)
    return text

async def save_to_database(televisions: List[Television]) -> bool:
    if not televisions:
        return False
    
    try:
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            # Create table if it doesn't exist
            create_table_sql = """
            -- Add extension if it doesn't exist (needed for gen_random_uuid())
            CREATE EXTENSION IF NOT EXISTS "pgcrypto";

            CREATE TABLE IF NOT EXISTS television_data (
                uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                url TEXT PRIMARY KEY,
                price TEXT,
                ekran_ebati TEXT,
                cozunurluk_piksel TEXT,
                yenileme_hizi_gercek TEXT,
                goruntu_teknolojisi TEXT,
                smart_tv TEXT,
                isletim_sistemi TEXT,
                hdmi_girisleri TEXT,
                model_adi TEXT,
                marka TEXT
            );
            """
            conn.execute(text(create_table_sql))
            
            # Process one TV at a time
            for tv in televisions:
                df = pd.DataFrame([tv.specs])
                
                # Add any missing columns
                existing_columns_query = """
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'television_data';
                """
                result = conn.execute(text(existing_columns_query))
                existing_columns = {row[0] for row in result}
                
                for column in df.columns:
                    if column.lower() not in {col.lower() for col in existing_columns}:
                        try:
                            conn.execute(text(f"ALTER TABLE television_data ADD COLUMN {column} TEXT;"))
                            logging.info(f"Added new column: {column}")
                        except Exception as e:
                            logging.error(f"Error adding column {column}: {e}")
                
                 # Insert or update the TV record
                try:
                    # Convert specs to dictionary with proper None handling
                    data_dict = {
                        col: str(tv.specs.get(col, '')) if tv.specs.get(col) is not None else ''
                        for col in df.columns
                    }
                    
                    # Create the upsert query
                    columns = list(data_dict.keys())
                    placeholders = [':' + col for col in columns]
                    
                    upsert_sql = f"""
                        INSERT INTO television_data ({', '.join(columns)})
                        VALUES ({', '.join(placeholders)})
                        ON CONFLICT (url) DO UPDATE SET
                        {', '.join(f"{col} = EXCLUDED.{col}" for col in columns if col != 'url')};
                    """
                    
                    conn.execute(text(upsert_sql), data_dict)
                    logging.info(f"Successfully saved/updated TV: {tv.url}")
                except Exception as e:
                    logging.error(f"Error saving TV {tv.url}: {str(e)}")

            conn.commit()
            
            # Verify the operation
            count_result = conn.execute(text("SELECT COUNT(*) FROM television_data;"))
            total_count = count_result.scalar()
            
            logging.info(f"Total records in database: {total_count}")
            
            return True
        
    except Exception as e:
        logging.error(f"Database error: {e}")
        return False

async def main():
    url = 'https://www.hepsiburada.com/ara?q=televizyon&siralama=coksatan'
    
    playwright, browser, context = await init_playwright()
    
    try:
        links = await scrape_television_links(context, url)
        if not links:
            logging.error("No product links found")
            return False
        
        televisions = await scrape_television_data(context, links)
        if not televisions:
            logging.error("No television data scraped")
            return False
        
        return await save_to_database(televisions)
        
    finally:
        await context.close()
        await browser.close()
        await playwright.stop()

if __name__ == "__main__":
    asyncio.run(main())