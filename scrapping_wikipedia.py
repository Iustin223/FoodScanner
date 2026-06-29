import requests
from bs4 import BeautifulSoup
import sqlite3

def wiki_data():

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    with open('wiki_aditivi.html', 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    aditivi = []

    print("Extragere tabele..")

    tabele = soup.find_all('table', class_ = 'wikitable')

    for tabel in tabele:
        randuri = tabel.find_all('tr')

        for rand in randuri:
            celule = rand.find_all(['td', 'th'])

            if len(celule) >= 2:
                cod_e = celule[0].text.strip()

                nume = celule[1].text.strip().lower()

                descriere = celule[2].text.strip()  if len(celule) >= 3 else "Fara descriere"

                style_html = celule[0].get('style', '').lower()

                bgcolor_html = celule[0].get('bgcolor', '').lower()

                culoare = style_html + bgcolor_html

                risc = "Inofensiv / Necunoscut"

                if 'red' in culoare or 'pink' in culoare:
                    risc = "Periculos"
                elif  '#ff' in culoare and '#ffffff' not in culoare:
                    risc = "Periculos"

                cod_e = cod_e.split('[')[0].strip()

                aditivi.append((cod_e, nume, risc, descriere)) 

    print(f"Am gasit {len(aditivi)} aditivi!")
    return aditivi       




if __name__ == "__main__":
    wiki_data()

    
    