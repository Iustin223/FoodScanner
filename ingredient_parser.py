import re

class IngredientParser:
    def __init__(self):
        
        self.end_patterns = [
            r'valoare\s+energetică',
            r'valori\s+nutriționale', 
            r'declarație\s+nutrițională',
            r'a\s+se\s+păstra',
            r'a\s+se\s+consuma',
            r'mod\s+de\s+preparare',
            r'țara\s+de\s+origine',
            r'producător',
            r'distribuit\s+de',
            r'condiții\s+de\s+păstrare',
        ]

    def find_ingredients_section(self, text):

        match = re.search(r'ingrediente\s*:', text, re.IGNORECASE)

        if not match:
            return None  

        start = match.end()
        ingredients_text = text[start:]
        earliest_end = len(ingredients_text)

        for pattern in self.end_patterns:
            end_match = re.search(pattern, ingredients_text, re.IGNORECASE)
            if end_match and end_match.start() < earliest_end:
                earliest_end = end_match.start()

        ingredients_text = ingredients_text[:earliest_end]
        return ingredients_text.strip()


    def smart_split(self, text):

        ingredients = []
        current = ''
        depth = 0

        for char in text:
            if char == '(':
                depth += 1
                current += char
            elif char == ")":
                depth = max(0, depth - 1)
                current += char
            elif char in (',', ';') and depth == 0:
                if char == ',' and current and current[-1].isdigit():
                    current += char
                    continue
                cleaned = current.strip()
                if cleaned:
                    ingredients.append(cleaned)
                current = ""
            else:
                current += char


        cleaned = current.strip()
        if cleaned:
            ingredients.append(cleaned)
        return ingredients

    def clean_ingredients(self, text):
        
        text = text.replace('\n', ' ')

        text = re.sub(r'\s+', ' ', text)

        text = text.strip()

        text = text.rstrip('.')

        if len(text) < 2:
            return None
        
        return text
    

    def parse(self, ocr_text):
        
        section = self.find_ingredients_section(ocr_text)

        if not section:
            return []
        
        raw_ingredients = self.smart_split(section)

        cleaned = []

        for ing in raw_ingredients:
            result = self.clean_ingredients(ing)
            if result:
                cleaned.append(result)

        return cleaned
    

if __name__ == "__main__":
    parser = IngredientParser()

    text1 = """de roșii, picant. Produs pasteurizat. Ingrediente: apă, concentrat 
    de roșii (160 g roșii la 100g ketchup), zahăr, amidon modificat, 
    sare iodată (sare, iodat de potasiu), acidifiant: acid acetic, 
    ardei iute 0,16%, corector de aciditate: acid citric; conservant: 
    sorbat de potasiu E202; extract de condimente. Țara de origine a 
    concentratului de roșii diferă."""

    print("=" * 60)
    print("KETCHUP")
    print("=" * 60)

    ingredients = parser.parse(text1)

    for i, ing in enumerate(ingredients, 1):
        print(f"  {i}. {ing}")

    text2 = """îndulcitor de masă pe bază de ciclamați, zaharine și 
    neotam, sub formă lichidă. Ingrediente: apă, îndulcitori: 
    ciclamați și zaharine; fructoză, acidifiant: acid citric; conservant 
    acid sorbic; îndulcitor: neotam. A se păstra la temperatura camerei."""
    
    print("\n" + "=" * 60)
    print("ÎNDULCITOR")
    print("=" * 60)

    ingredients = parser.parse(text2)

    for i, ing in enumerate(ingredients, 1):
        print(f"  {i}. {ing}")