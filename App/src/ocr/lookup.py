from fuzzywuzzy import fuzz, process
import sqlite3
from config import DB_PATH

class IngredientLookUp:
    def __init__(self, db_path = DB_PATH):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT cod_e, nume, grad_risc, descriere FROM ingrediente_chimice')
        self.aditivi = cursor.fetchall()
        conn.close()

        self.nume_lista = [row[1] for row in self.aditivi]

        self.e_dict = {}
        for row in self.aditivi:
            cod = row[0].lower().strip()
            self.e_dict[cod] = row

        print(f'Loaded {len(self.aditivi)} additives from database')


    def clean_for_lookup(self, text):
        import re

        prefixes = [
        r'stabilizator[i]?\s*:',
        r'conservant[i]?\s*:',
        r'antioxidant[i]?\s*:',
        r'colorant[i]?\s*:',
        r'emulgator[i]?\s*:',
        r'potențiator\s+de\s+aromă\s*:',
        r'agent\s+de\s+îngroșare\s*:',
        r'agent[i]?\s+de\s+afânare\s*:',
        r'acidifiant[i]?\s*:',
        r'corector\s+de\s+aciditate\s*:',
        r'îndulcitor[i]?\s*:',
        r'arom[aăe]\s*:',
        ]
        
        cleaned = text
        for prefix in prefixes:
            cleaned = re.sub(prefix, '', cleaned, flags=re.IGNORECASE)
        
        # Remove extra spaces left after stripping
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned    

    def lookup_e_number(self, text):
        import re
        match = re.search(r'[Ee]\s*\d{3,4}[a-z]?', text)
        if match:
            e_code = match.group().lower().replace(' ', '')
            if e_code in self.e_dict:
                return self.e_dict[e_code]
        return None

    def lookup_name(self, ingredient_text, threshold=70):
        if ':' in ingredient_text:
            ingredient_text = ingredient_text.split(':', 1)[1].strip()
        clean = ingredient_text.lower().strip()
        
        # Remove trailing junk after periods
        clean = clean.split('.')[0].strip()
        
        # Exact match
        for i, name in enumerate(self.nume_lista):
            if clean == name:
                return self.aditivi[i], 100
        
        # Fuzzy match on full text
        result = process.extractOne(clean, self.nume_lista, scorer=fuzz.ratio)
        if result:
            matched_name, score = result
            if score >= threshold:
                index = self.nume_lista.index(matched_name)
                return self.aditivi[index], score
        
        # If full text didn't match, try removing words from the front
        # "Grăsim glutamat de sodiu" → "glutamat de sodiu" → match!
        words = clean.split()
        for start in range(1, len(words)):
            partial = ' '.join(words[start:])
            result = process.extractOne(partial, self.nume_lista, scorer=fuzz.ratio)
            if result:
                matched_name, score = result
                if score >= threshold:
                    index = self.nume_lista.index(matched_name)
                    return self.aditivi[index], score
        
        return None

    def lookup(self, ingredient_text):
        e_result = self.lookup_e_number(ingredient_text)
        if e_result:
            return {
                'ingredient': ingredient_text,
                'matched': e_result[1],
                'cod_e': e_result[0],
                'risc': e_result[2],
                'descriere': e_result[3],
                'confidence': 100,
                'match_type': 'E-number'
            }

        
        cleaned = self.clean_for_lookup(ingredient_text)
        if cleaned != ingredient_text:
            print(f"  [DEBUG] '{ingredient_text}' → '{cleaned}'")
        result = self.lookup_name(cleaned)    
        if result:
            result_data, score = result
            return {
                'ingredient': ingredient_text,
                'matched': result_data[1],
                'cod_e': result_data[0],
                'risc': result_data[2],
                'descriere': result_data[3],
                'confidence': score,
                'match_type': 'fuzzy'
            }
        return {
            'ingredient': ingredient_text,
            'matched': None,
            'cod_e': None,
            'risc': 'necunoscut',
            'descriere': 'Nu a fost găsit în baza de date',
            'confidence': 0,
            'match_type': 'not_found'
        }