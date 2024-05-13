import requests
from bs4 import BeautifulSoup
import pandas as pd
from fake_useragent import UserAgent
import psycopg2
from sqlalchemy import create_engine

class Television:
    def __init__(self, url, features):
        self.url = url
        self.features = features

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
    print(links)
    return links

def scrape_television_data(links):
    ua = UserAgent()
    headers = {"User-Agent": ua.random}

    televisions = []
    for link in links:
        response = requests.get(link, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the features table and save it as a string
        features_tag = soup.find('h2', class_='product-features-text')
        if features_tag is not None:   # Check if features_tag is not None to avoid AttributeError
            features = features_tag.text
            televisions.append(Television(link, features))
    print(televisions)
    return televisions

def to_dataframe(televisions):
    data = {
        'URL': [tv.url for tv in televisions],
        'Features': [tv.features for tv in televisions],
    }
    df = pd.DataFrame(data)
    return df

def df_to_sql(df, table_name):
    engine = create_engine('postgresql://postgres:postgres@localhost:5432/arabul')

    df.to_sql(table_name, engine, if_exists='append', index=False)
    print(f"Successfully saved dataframe to table {table_name}")

# Scrape the data
url = 'https://www.hepsiburada.com/ara?q=televizyon'
links = scrape_television_links(url)
televisions = scrape_television_data(links)
df = to_dataframe(televisions)

# Save the DataFrame to SQL
df_to_sql(df, 'television_data')  # replace 'television_data' with your table name


# Print the DataFrame
print(df)