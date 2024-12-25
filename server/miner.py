import re
import logging
import pandas as pd
from sqlalchemy import create_engine
from difflib import SequenceMatcher
import os

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/arabul')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Television:
    def __init__(self, url, specs):
        self.url = url
        self.specs = specs

def turkish_to_latin(text):
    """Convert Turkish characters to their Latin counterparts."""
    if not isinstance(text, str):
        return str(text)
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

def normalize_text(text):
    """Normalize terms and units for comparison."""
    if not isinstance(text, str):
        return str(text)
    
    text = text.lower()
    replacements = {
        # Basic TV terms
        r'\btv\b': 'televizyon',
        r'\btelevision\b': 'televizyon',
        r'\btelevizon\b': 'televizyon',
        
        # Units and measurements
        r'\binç\b': 'inch',
        r'\binc\b': 'inch',
        r'\b(\d+)["\'″"]\b': r'\1 inch',  # Convert 55", 55′, 55″ to 55 inch
        r'\bcm\b': 'cm',
        r'\btl\b': 'lira',
        r'\b₺\b': 'lira',
        r'\bhz\b': 'hertz',
        r'\bhertz\b': 'hertz',
        
        # Resolution terms
        r'\b4k\b': '3840x2160',
        r'\b8k\b': '7680x4320',
        r'\b1080p?\b': '1920x1080',
        r'\buhd\b': '3840x2160',
        r'\bfhd\b': '1920x1080',
        r'\bhd\b': '1280x720',
        
        # Features
        r'\bsmart\s*tv\b': 'smart',
        r'\bwifi\b': 'smart',
        r'\binternet\b': 'smart',
        r'\bhdr\d*\b': 'hdr',
        r'\bdolby\s*vision\b': 'hdr',
        
        # Panel types
        r'\boled\b': 'oled',
        r'\bqled\b': 'qled',
        r'\bnanocell\b': 'nanocell',
        r'\bled\b': 'led'
    }
    
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text)
    
    return text.strip()

def parse_price(text):
    """Extract price range from text."""
    text = normalize_text(text)
    under_match = re.search(r'under (\d+(?:,\d+)?)\s*(?:tl|lira)', text)
    above_match = re.search(r'above (\d+(?:,\d+)?)\s*(?:tl|lira)', text)
    range_match = re.search(r'between (\d+(?:,\d+)?)\s*(?:tl|lira) and (\d+(?:,\d+)?)\s*(?:tl|lira)', text)

    if under_match:
        price = float(under_match.group(1).replace(',', ''))
        return (0, price)
    elif above_match:
        price = float(above_match.group(1).replace(',', ''))
        return (price, float('inf'))
    elif range_match:
        price1 = float(range_match.group(1).replace(',', ''))
        price2 = float(range_match.group(2).replace(',', ''))
        return (min(price1, price2), max(price1, price2))
    return None

def parse_dimension(text):
    """Extract numerical dimension and unit from text."""
    match = re.search(r'(\d+)\s*(cm|inch)', text)
    if match:
        value, unit = match.groups()
        return int(value), unit
    return None, None

def map_input_to_columns(user_input):
    """Map user input to relevant database columns."""
    user_input = normalize_text(user_input)
    columns = set()
    
    patterns = {
        'model_adi': [
            r'\btelevizyon\b',
            r'\bmodel\b',
            r'\b[a-zA-Z0-9]+-?[a-zA-Z0-9]+\b'  # Model numbers like UN55, QN65
        ],
        'ekran_ebati': [
            r'\b\d+\s*(?:inch|cm)\b',
            r'\bekran\b',
            r'\binch\b',
            r'\bcm\b'
        ],
        'price': [
            r'\d+\s*(?:tl|lira)\b',
            r'\bfiyat\b',
            r'\bprice\b',
            r'[0-9,.]+\s*(?:tl|lira)'
        ],
        'yenileme_hizi_gercek': [
            r'\b\d+\s*(?:hz|hertz)\b',
            r'\brefresh\b',
            r'\byenileme\b'
        ],
        'cozunurluk_piksel': [
            r'\b\d+x\d+\b',
            r'\b[48]k\b',
            r'\b1080p?\b',
            r'\buhd\b',
            r'\bhd\b',
            r'\bresolution\b',
            r'\bcozunurluk\b'
        ],
        'hdr': [
            r'\bhdr\b',
            r'\bdolby\s*vision\b'
        ],
        'smart_tv': [
            r'\bsmart\b',
            r'\bwifi\b',
            r'\binternet\b',
            r'\bandroid\b',
            r'\btizen\b',
            r'\bwebos\b'
        ],
        'goruntu_teknolojisi': [
            r'\boled\b',
            r'\bqled\b',
            r'\bnanocell\b',
            r'\bled\b',
            r'\blcd\b'
        ],
        'marka': [
            r'\bsamsung\b',
            r'\blg\b',
            r'\bphilips\b',
            r'\bsony\b',
            r'\btcl\b',
            r'\bvestel\b',
            r'\bregal\b',
            r'\bbeko\b',
            r'\barcelik\b'
        ]
    }
    
    for column, patterns_list in patterns.items():
        if any(re.search(pattern, user_input) for pattern in patterns_list):
            columns.add(column)
    
    return list(columns) if columns else ['model_adi', 'marka']

def get_similarity_rate(user_input, database_entry, column_type='text'):
    """Calculate similarity between user input and database entry."""
    if not isinstance(database_entry, str):
        database_entry = str(database_entry)

    user_input = turkish_to_latin(normalize_text(user_input.lower()))
    database_entry = turkish_to_latin(normalize_text(database_entry.lower()))

    # Special handling for dimensions
    if column_type == 'dimension' or 'ekran_ebati' in user_input:
        user_value, user_unit = parse_dimension(user_input)
        db_value, db_unit = parse_dimension(database_entry)
        
        if user_value and db_value:
            # Convert to cm for comparison
            if user_unit == 'inch':
                user_value *= 2.54
            if db_unit == 'inch':
                db_value *= 2.54
            
            # Calculate similarity based on dimension difference
            difference = abs(user_value - db_value)
            max_value = max(user_value, db_value)
            similarity = 1 - (difference / max_value)
            return similarity if similarity > 0 else 0
    
    # Special handling for price ranges
    elif column_type == 'price' or 'price' in user_input:
        price_range = parse_price(user_input)
        if price_range:
            try:
                db_price = float(re.findall(r'\d+', database_entry)[0])
                if price_range[0] <= db_price <= price_range[1]:
                    return 1.0
                return 0.0
            except (ValueError, IndexError):
                return 0.0
    
    # Default text similarity using SequenceMatcher
    return SequenceMatcher(None, user_input, database_entry).ratio()

def search_database(user_input):
    """Enhanced database search with weighted column matching."""
    engine = create_engine(DATABASE_URL)
    query = "SELECT * FROM television_data"
    df = pd.read_sql(query, engine)

    columns = map_input_to_columns(user_input)
    
    # Column weights for similarity calculation
    weights = {
        'model_adi': 1.0,
        'marka': 0.9,
        'ekran_ebati': 0.8,
        'price': 0.7,
        'cozunurluk_piksel': 0.6,
        'goruntu_teknolojisi': 0.5,
        'yenileme_hizi_gercek': 0.4,
        'smart_tv': 0.3,
        'hdr': 0.2
    }
    
    similarity_scores = []
    for index, row in df.iterrows():
        weighted_similarity = 0
        weight_sum = 0
        
        for column in columns:
            if pd.notna(row.get(column)):
                weight = weights.get(column, 0.5)
                similarity = get_similarity_rate(
                    user_input, 
                    str(row[column]),
                    column_type=column
                )
                weighted_similarity += similarity * weight
                weight_sum += weight
        
        if weight_sum > 0:
            final_similarity = weighted_similarity / weight_sum
            if final_similarity > 0.1:  # Threshold to filter out low matches
                similarity_scores.append((final_similarity, row))

    return sorted(similarity_scores, key=lambda x: x[0], reverse=True)

def run_miner(user_input):
    """Run the mining process and format results with all available features."""
    results = search_database(user_input)
    output = []
    
    # Core features that are always included in the main object
    core_features = {
        'similarity', 'marka', 'model', 'price', 'ekran_ebati', 
        'cozunurluk', 'goruntu_teknolojisi', 'yenileme_hizi', 
        'smart_tv', 'hdr', 'url'
    }
    
    for similarity, row in results:
        # Basic specs that are always included
        specs = {
            'uuid': str(row.get('uuid', 'Unknown')),
            'similarity': round(similarity * 100, 2),
            'marka': row.get('marka', 'Unknown'),
            'model': row.get('model_adi', 'Unknown'),
            'price': row.get('price', 'Unknown'),
            'ekran_ebati': row.get('ekran_ebati', 'Unknown'),
            'cozunurluk': row.get('cozunurluk_piksel', 'Unknown'),
            'goruntu_teknolojisi': row.get('goruntu_teknolojisi', 'Unknown'),
            'yenileme_hizi': row.get('yenileme_hizi_gercek', 'Unknown'),
            'smart_tv': row.get('smart_tv', 'Unknown'),
            'hdr': row.get('hdr', 'Unknown'),
            'url': row.get('url', 'Unknown')
        }
        
        # Additional features (any column not in core_features)
        additional_features = {}
        for key, value in row.items():
            if (
                key not in core_features 
                and pd.notna(value) 
                and key != 'url' 
                and not key.startswith('index')
            ):
                # Convert column name to a more readable format
                display_key = key.replace('_', ' ').title()
                additional_features[key] = str(value)
        
        if additional_features:
            specs['additional_features'] = additional_features
        
        # Only include results with similarity above 20%
        if specs['similarity'] >= 20:
            output.append(specs)
    
    return output[:10]  # Return top 10 matches

if __name__ == "__main__":
    user_input = input("Enter TV specifications: ")
    results = run_miner(user_input)
    for result in results:
        print(result)