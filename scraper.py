import requests  
from bs4 import BeautifulSoup  
import pandas as pd  
from fake_useragent import UserAgent  
from sqlalchemy import create_engine, text  
import re  
import logging  
  
# Setting up logging  
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')  
  
class Television:  
    def __init__(self, url, specs):  
        self.url = url  
        self.specs = specs  
  
def turkish_to_latin(text):  
    """  
    Convert Turkish characters to their Latin counterparts.  
    """  
    turkish_characters = {  
        'ç': 'c', 'Ç': 'C',  
        'ğ': 'g', 'Ğ': 'G',  
        'ı': 'i', 'I': 'I',  
        'İ': 'I', 'i': 'i',  
        'ö': 'o', 'Ö': 'O',  
        'ş': 's', 'Ş': 'S',  
        'ü': 'u', 'Ü': 'U'  
    }  
    for turkish_char, latin_char in turkish_characters.items():  
        text = text.replace(turkish_char, latin_char)  
    return text  
  
def sanitize_column_name(column_name):  
    """  
    Sanitize the column name by converting Turkish characters to Latin,   
    replacing spaces with underscores, and removing special characters.  
    """  
    column_name = turkish_to_latin(column_name)  
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '', column_name.replace(' ', '_'))  
    return sanitized.lower()  
  
def scrape_television_links(url):  
    ua = UserAgent()  
    headers = {"User-Agent": ua.random}  
    response = requests.get(url, headers=headers)  
    soup = BeautifulSoup(response.text, 'html.parser')  
  
    # Find the links to each individual television page  
    links = []  
    for li in soup.select('li[class^="productListContent-"]'):  
        link = li.find('a', href=True)  
        if link:  
            href = link['href']  
            # Skip links that include "adservice.hepsiburada.com"  
            if "adservice.hepsiburada.com" not in href:  
                links.append('https://www.hepsiburada.com' + href)  
    return links  
  
def scrape_television_data(links):  
    ua = UserAgent()  
    headers = {"User-Agent": ua.random}  
    televisions = []  
    for link in links:  
        try:  
            response = requests.get(link, headers=headers)  
            soup = BeautifulSoup(response.text, 'html.parser')  
  
            # Find the features table and save it as a dictionary  
            features_tag = soup.find('div', id='productTechSpecContainer')  
            specs = {'url': link}  
            if features_tag is not None:  
                for table in features_tag.find_all('table', class_='data-list tech-spec'):  
                    for row in table.find_all('tr'):  
                        th = row.find('th')  
                        td = row.find('td')  
                        if th and td:  
                            key = sanitize_column_name(th.text.strip())  
                            value = td.text.strip()  
                            specs[key] = value  
            televisions.append(Television(link, specs))  
            logging.info(f"Scraped data for URL: {link}")  
        except Exception as e:  
            logging.error(f"Error scraping {link}: {e}")  
    return televisions  
  
def to_dataframe(televisions):  
    data = [tv.specs for tv in televisions]  
    df = pd.DataFrame(data)  
    return df  
  
def ensure_table_schema(engine, table_name, df):  
    with engine.connect() as conn:  
        # Create the table if it doesn't exist  
        create_table_query = f"""  
            CREATE TABLE IF NOT EXISTS {table_name} (  
                url TEXT  
            );  
        """  
        conn.execute(text(create_table_query))  
          
        # Get existing columns in the table  
        existing_columns_query = f"""  
            SELECT column_name   
            FROM information_schema.columns   
            WHERE table_name='{table_name}';  
        """  
        result = conn.execute(text(existing_columns_query))  
        existing_columns = {row[0] for row in result}  
          
        # Add missing columns  
        for column in df.columns:  
            if column not in existing_columns:  
                add_column_query = f"""  
                    ALTER TABLE {table_name}  
                    ADD COLUMN {column} TEXT;  
                """  
                conn.execute(text(add_column_query))  
                logging.info(f"Added column {column} to table {table_name}")  
          
        # Commit the transaction to ensure changes are applied  
        conn.commit()  
  
def df_to_sql(df, table_name):  
    engine = create_engine('postgresql://postgres:postgres@localhost:5432/arabul')  
    ensure_table_schema(engine, table_name, df)  
    df.to_sql(table_name, engine, if_exists='append', index=False)  
    logging.info(f"Successfully saved dataframe to table {table_name}")  
  
# Scrape the data  
url = 'https://www.hepsiburada.com/ara?q=televizyon&siralama=coksatan'  
links = scrape_television_links(url)  
televisions = scrape_television_data(links)  
df = to_dataframe(televisions)  
  
# Print the first few rows of the DataFrame to inspect  
print(df.head())  
  
# Save the DataFrame to SQL  
df_to_sql(df, 'television_data')  
  
# Print the DataFrame  
print(df)  

