import re
from fuzzywuzzy import fuzz

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
            r'[Pp]oate\s+con[tț]ine',    # catches OCR variants
            r'produs\s+sterilizat',       # product type markers
            r'se\s+consum[aă]',
            r'[Cc]on[tț]ine\s+lactoz[aă]',
            r'[Cc]on[tț]ine\s+urme',
            r'[Cc]on[tț]ine\s*:',
            r'\.\s*[Cc]on[tț]ine\b'
        ]

    def find_ingredients_section(self, text):
        match = re.search(r'ingrediente\s*:', text, re.IGNORECASE)
        if not match:
            #return None
            serched_text = r'\b[\wăâîșț]+\s*:?'
            best_match = None
            best_score = 0


            for candidate in re.finditer(serched_text, text, re.IGNORECASE):
                word = candidate.group().rstrip(':').strip().lower()
                score = fuzz.ratio(word, 'ingrediente')

                if score > best_score:
                    best_score = score
                    best_match = candidate

            if best_match and best_score >= 75:
                match = best_match
                print("Header detectat:", match.group())        

            else:
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

    def _split_text(self, text, track_brackets=True):
        """Core splitting logic. track_brackets=False ignores () and []."""
        ingredients = []
        current = ''
        depth = 0

        for i, char in enumerate(text):
            if track_brackets and char in ('(', '['):
                depth += 1
                current += char
            elif track_brackets and char in (')', ']'):
                depth = max(0, depth - 1)
                current += char
            elif char in (',', ';') and depth == 0:
                if char == ',' and current and current[-1].isdigit():
                    if i + 1 < len(text) and text[i + 1].isdigit():
                        current += char
                        continue
                cleaned = current.strip()
                if cleaned:
                    ingredients.append(cleaned)
                current = ''
            else:
                current += char

        cleaned = current.strip()
        if cleaned:
            ingredients.append(cleaned)

        return ingredients

    def smart_split(self, text):
        # First try: respect brackets
        ingredients = self._split_text(text, track_brackets=True)
        
        # If any ingredient is suspiciously long, brackets are broken
        max_len = max(len(ing) for ing in ingredients) if ingredients else 0
        if max_len > 150:
            ingredients = self._split_text(text, track_brackets=False)
        
        return ingredients


    def extract_sub_ingredients(self, ingredients):
        """Split category entries like 'conservanți (X, Y)' into individual items."""

        categories = [
        'conservant', 'conservanți',
        'stabilizator', 'stabilizatori',
        'antioxidant', 'antioxidanți',
        'colorant', 'coloranți',
        'emulgator', 'emulgatori',
        'îndulcitor', 'îndulcitori',
        'acidifiant', 'acidifianți',
        'agenți de afânare',
        'potențiator de aromă',
        'corector de aciditate',
        'agent de îngroșare',
        ]
        
        expanded = []

        for ing in ingredients:
            lower = ing.lower()

            is_category = False
            for cat in categories:
                if lower.startswith(cat):
                    is_category = True
                    break

            if is_category and '(' in ing:   # Extract what's inside parentheses
                match = re.search(r'\((.+)\)', ing)
                if match:
                    inside = match.group(1)
                    sub_items = [s.strip() for s in inside.split(',')]
                    for sub in sub_items:
                        if len(sub) >= 2:
                            expanded.append(sub)

                else:
                    expanded.append(ing)

            elif '[' in ing and ']' in ing:
                main_name = re.sub(r'\[.*\]', '', ing).strip().rstrip(',').strip()
                if len(main_name) > 2:
                    expanded.append(main_name)

                match = re.search(r'\[(.+)\]', ing)
                if match:
                    inside = match.group(1)
                    sub_items = self.smart_split(inside)
                    for sub in sub_items:
                        if len(sub.strip()) >= 2:
                            expanded.append(sub.strip())

            else:
                expanded.append(ing)                    



        return expanded                                


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
        #expanded = self.extract_sub_ingredients(raw_ingredients)

        expanded = self.extract_sub_ingredients(raw_ingredients)

        cleaned = []
        for ing in expanded:
            result = self.clean_ingredients(ing)
            if result:
                cleaned.append(result)
        return cleaned