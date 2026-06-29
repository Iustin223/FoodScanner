import sqlite3

from scrapping_wikipedia import wiki_data

def database_create():

    aditivi = wiki_data()

    conn = sqlite3.connect('aditivi.db')
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS ingrediente_chimice")

    cursor.execute('''

        CREATE TABLE ingrediente_chimice (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   cod_e TEXT,
                   nume TEXT,
                   grad_risc TEXT,
                   descriere TEXT 
                   )
                   ''')
    
    cursor.executemany('''
                       
                       INSERT INTO ingrediente_chimice (cod_e, nume, grad_risc, descriere)
                       VALUES (?, ?, ?, ?)

                       ''', aditivi)
    
    conn.commit()
    conn.close()

    print(f"Baza de date creată! {len(aditivi)} aditivi salvați în aditivi.db")


def test_database():

    
    conn = sqlite3.connect('aditivi.db')
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM ingrediente_chimice')
    print(f"Total: {cursor.fetchone()[0]} aditivi")

    cursor.execute('SELECT * FROM ingrediente_chimice LIMIT 5')
    for row in cursor.fetchall():
        print(row)

    cursor.execute('SELECT * FROM ingrediente_chimice WHERE grad_risc = "Periculos"')
    periculosi = cursor.fetchall()
    print(f"\nPericuloși: {len(periculosi)}")
    for row in periculosi[:5]:
        print(f"  {row[1]} - {row[2]}")

    conn.close()


if __name__ == "__main__":
    test_database()