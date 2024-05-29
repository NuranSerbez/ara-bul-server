import re  
import logging  
import pandas as pd  
from sqlalchemy import create_engine  
from difflib import SequenceMatcher  

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')  
  
class Television:  
    def __init__(self, url, specs):  
        self.url = url  
        self.specs = specs  
  
def turkish_to_latin(text):  
    """Convert Turkish characters to their Latin counterparts."""  
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
    """Sanitize the column name by converting Turkish characters to Latin,  
       replacing spaces with underscores, and removing special characters."""  
    column_name = turkish_to_latin(column_name)  
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '', column_name.replace(' ', '_'))  
    return sanitized.lower()  
  
def normalize_text(text):  
    """Normalize terms and units for comparison."""  
    text = text.lower()  
    text = re.sub(r'\btv\b', 'television', text)  
    text = re.sub(r'\btelevizyon\b', 'television', text)  
    text = re.sub(r'\binch\b', 'inch', text)  
    text = re.sub(r'\bcm\b', 'cm', text)  
    text = re.sub(r'\btl\b', 'lira', text)  
    text = re.sub(r'\bhz\b', 'hertz', text)  
    text = re.sub(r'\bhertz\b', 'hertz', text)  
    return text  
  
def parse_dimension(text):  
    """Extract numerical dimension and unit from text."""  
    match = re.search(r'(\d+)\s*(cm|inch)', text)  
    if match:  
        value, unit = match.groups()  
        return int(value), unit  
    return None, None  
  
def map_input_to_column(user_input):  
    """Map user input to the appropriate database column."""  
    user_input = normalize_text(user_input)  
      
    if re.search(r'\btelevision\b|\btv\b|\btelevizyon\b', user_input):  
        return 'model_name'  
    if re.search(r'\bcm\b|\binch\b|\bekran\b', user_input):  
        return 'ekran_ebati'  
    if re.search(r'\blira\b|\btl\b|\bprice\b', user_input):  
        return 'price'  
    if re.search(r'\bhz\b|\bhertz\b|\byenileme_hizi\b', user_input):  
        return 'yenileme_hizi_gercek'  
    # Add more mappings as needed  
    return None  
  
def similarity_ratio(a, b):  
    """Calculate the similarity ratio between two strings."""  
    return SequenceMatcher(None, a, b).ratio()  
  
def get_similarity_rate(user_input, database_entry):  
    """Calculate the similarity rate between user input and a database entry."""  
    user_input = turkish_to_latin(user_input.lower())  
    database_entry = turkish_to_latin(database_entry.lower())  
      
    # Parse dimensions if available  
    user_value, user_unit = parse_dimension(user_input)  
    db_value, db_unit = parse_dimension(database_entry)  
      
    if user_value and db_value:  
        # Normalize units to cm for comparison  
        if user_unit == 'inch':  
            user_value *= 2.54  # Convert inch to cm  
        if db_unit == 'inch':  
            db_value *= 2.54  # Convert inch to cm  
          
        # Calculate the difference percentage  
        difference = abs(user_value - db_value)  
        max_value = max(user_value, db_value)  
        similarity = 1 - (difference / max_value)  
        return similarity  
      
    # Fallback to string similarity if no dimensions are parsed  
    user_input = normalize_text(user_input)  
    database_entry = normalize_text(database_entry)  
    return similarity_ratio(user_input, database_entry)  
  
def search_database(user_input):  
    """Search the database and return all data ordered by similarity rate."""  
    engine = create_engine('postgresql://postgres:postgres@localhost:5432/arabul')  
    query = "SELECT * FROM television_data"  
    df = pd.read_sql(query, engine)  
      
    column = map_input_to_column(user_input)  
    if column is None:  
        logging.error("Could not map user input to a specific column.")  
        return []  
      
    similarity_scores = []  
    for index, row in df.iterrows():  
        if pd.notna(row[column]):  
            entry_value = str(row[column])  
            similarity = get_similarity_rate(user_input, entry_value) * 100  # Convert to percentage  
            similarity_scores.append((similarity, row))  
      
    # Sort by similarity score in descending order  
    sorted_results = sorted(similarity_scores, key=lambda x: x[0], reverse=True)  
      
    return sorted_results  
  
def run_miner(user_input):  
    """Main function to process user input and return sorted results."""  
    results = search_database(user_input)  
    output = []  
    for similarity, row in results:  
        url = row.get('url', 'Unknown')  
        price = row.get('price', 'Unknown')
        cozunurluk_piksel = row.get("cozunurluk_piksel", "Unknown")

        output.append({  
            'similarity': similarity,  
            'url': url,  
            'price': price,
            "cozunurluk_piksel" : cozunurluk_piksel
        })  
    return output  
  
if __name__ == "__main__":  
    user_input = input("Enter TV specifications: ")  
    results = run_miner(user_input)  
    for result in results:  
        print(result)  
