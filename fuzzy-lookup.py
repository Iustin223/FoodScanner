from fuzzywuzzy import fuzz, process
import sqlite3


class IngredientLookUp():
    def __init__(self, db_path = 'aditivi.db'):

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT cod_e, nume, grad_risc, descriere FROM ingrediente_chimice')
        self.aditivi = cursor.fetchall()
        
        self.nume_lista = [row[1] for row in self.aditivi]

        self.e_dict = {}

        for row in self.aditivi:
            cod = row[0].lower().strip()
            self.e_dict[cod] = row

        print(f"Loaded {len(self.aditivi)} additives from database")


    def lookup_e_number(self, text):
            import re

            match = re.search(r'[Ee]\s*\d{3,4}[a-z]?', text)
            if match:
                e_code = match.group().lower().replace(' ', '')
                if e_code in self.e_dict:
                    return self.e_dict[e_code]

            return None

    def lookup_name(self, ingredient_text, threshold = 75):
             
        clean = ingredient_text.lower().strip()

        for i, name in enumerate(self.nume_lista):
            if clean == name:
                 return self.aditivi[i], 100
            
        result = process.extractOne(clean, self.nume_lista, scorer=fuzz.ratio)

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
                'descriere': e_result[3][:100],
                'confidence': 100,
                'match_type': 'E-number'
            }
        
        result = self.lookup_name(ingredient_text)
        if result:
            result_data, score = result
            return {
                'ingredient': ingredient_text,
                'matched': result_data[1],
                'cod_e': result_data[0],
                'risc': result_data[2],
                'descriere': result_data[3][:100],
                'confidence': score,
                'match_type': 'fuzzy'
            }
        
        return {
            'ingredient': ingredient_text,
            'matched': None,
            'cod_e': None,
            'risc': 'Natural / Necunoscut',
            'descriere': 'Nu a fost găsit în baza de date cu aditivi',
            'confidence': 0,
            'match_type': 'not_found'
        }
    
if __name__ == "__main__":
    lookup = IngredientLookUp()

    test_ingredients = [
        "tartrazină",           # exact match
        "tartrazina",           # missing diacritics
        "sorbat de potasiu",    # exact match
        "sorbat de potasui",    # OCR typo
        "E202",                 # E-number lookup
        "E102",                 # dangerous E-number
        "zahăr",                # natural ingredient, not in additive DB
        "acid citric",          # common additive
        "apă",                  # natural, not in DB
    ]
    
    print("\n" + "=" * 70)
    print(f"{'INGREDIENT':<30} {'MATCH':<25} {'RISC':<20} {'%'}")
    print("=" * 70)
    
    for ing in test_ingredients:
        result = lookup.lookup(ing)
        matched = result['matched'] or '-'
        risc = result['risc']
        conf = result['confidence']
        print(f"{ing:<30} {matched:<25} {risc:<20} {conf}%")
