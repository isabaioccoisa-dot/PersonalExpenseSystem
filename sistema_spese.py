import sqlite3
from datetime import datetime

# ==========================================
# 1. INIZIALIZZAZIONE E CREAZIONE DATABASE
# ==========================================
def inizializza_db():
    conn = sqlite3.connect("spese_personali.db")
    cursor = conn.cursor()
    
    # Abilita il supporto ai vincoli di Foreign Key in SQLite
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # Tabella Categorie
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Categorie (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE
    );
    """)
    
    # Tabella Spese
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Spese (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT NOT NULL,
        importo REAL NOT NULL CHECK (importo > 0),
        categoria_id INTEGER NOT NULL,
        descrizione TEXT,
        FOREIGN KEY (categoria_id) REFERENCES Categorie(id) ON DELETE CASCADE
    );
    """)
    
    # Tabella Budget
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Budget (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mese TEXT NOT NULL, -- Formato YYYY-MM
        categoria_id INTEGER NOT NULL,
        importo_budget REAL NOT NULL CHECK (importo_budget > 0),
        FOREIGN KEY (categoria_id) REFERENCES Categorie(id) ON DELETE CASCADE,
        UNIQUE (mese, categoria_id)
    );
    """)
    
    conn.commit()
    conn.close()

def get_connection():
    conn = sqlite3.connect("spese_personali.db")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

# ==========================================
# MODULO 1 — Gestione Categorie
# ==========================================
def modulo_gestione_categorie():
    print("\n--- MODULO 1: GESTIONE CATEGORIE ---")
    nome_cat = input("Inserisci il nome della nuova categoria: ").strip()
    
    if not nome_cat:
        print("Errore: Il nome della categoria non può essere vuoto.")
        return
        
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verifica esistenza
    cursor.execute("SELECT id FROM Categorie WHERE LOWER(nome) = LOWER(?);", (nome_cat,))
    if cursor.fetchone():
        print("Errore: La categoria esiste già.")
    else:
        cursor.execute("INSERT INTO Categorie (nome) VALUES (?);", (nome_cat,))
        conn.commit()
        print("Categoria inserita correttamente.")
    conn.close()

# ==========================================
# MODULO 2 — Inserimento Spesa
# ==========================================
def modulo_inserisci_spesa():
    print("\n--- MODULO 2: INSERISCI SPESA ---")
    data_str = input("Inserisci la data (YYYY-MM-DD): ").strip()
    try:
        datetime.strptime(data_str, "%Y-%m-%d")
    except ValueError:
        print("Errore: Formato data non valido. Usare YYYY-MM-DD.")
        return

    try:
        importo = float(input("Inserisci l'importo (> 0): "))
        if importo <= 0:
            print("Errore: L'importo deve essere maggiore di zero.")
            return
    except ValueError:
        print("Errore: Inserire un numero valido per l'importo.")
        return

    nome_cat = input("Inserisci il nome della categoria: ").strip()
    descrizione = input("Inserisci una descrizione facoltativa: ").strip()

    conn = get_connection()
    cursor = conn.cursor()
    
    # Cerca l'ID della categoria
    cursor.execute("SELECT id FROM Categorie WHERE LOWER(nome) = LOWER(?);", (nome_cat,))
    row = cursor.fetchone()
    
    if not row:
        print("Errore: La categoria non esiste.")
    else:
        categoria_id = row[0]
        cursor.execute("""
            INSERT INTO Spese (data, importo, categoria_id, descrizione)
            VALUES (?, ?, ?, ?);
        """, (data_str, importo, categoria_id, descrizione))
        conn.commit()
        print("Spesa inserita correttamente.")
    conn.close()

# ==========================================
# MODULO 3 — Definizione Budget Mensile
# ==========================================
def modulo_definisci_budget():
    print("\n--- MODULO 3: DEFINISCI BUDGET MENSILE ---")
    mese_str = input("Inserisci il mese (YYYY-MM): ").strip()
    try:
        datetime.strptime(mese_str, "%Y-%m")
    except ValueError:
        print("Errore: Formato mese non valido. Usare YYYY-MM.")
        return

    nome_cat = input("Inserisci il nome della categoria: ").strip()
    
    try:
        importo_budget = float(input("Inserisci l'importo del budget (> 0): "))
        if importo_budget <= 0:
            print("Errore: L'importo del budget deve essere maggiore di zero.")
            return
    except ValueError:
        print("Errore: Inserire un valore numerico valido.")
        return

    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM Categorie WHERE LOWER(nome) = LOWER(?);", (nome_cat,))
    row = cursor.fetchone()
    
    if not row:
        print("Errore: La categoria non esiste.")
    else:
        categoria_id = row[0]
        # Inserisci o Aggiorna se esiste già (UPSERT)
        cursor.execute("""
            INSERT INTO Budget (mese, categoria_id, importo_budget)
            VALUES (?, ?, ?)
            ON CONFLICT(mese, categoria_id) 
            DO UPDATE SET importo_budget = excluded.importo_budget;
        """, (mese_str, categoria_id, importo_budget))
        conn.commit()
        print("Budget mensile salvato correttamente.")
    conn.close()

# ==========================================
# MODULO 4 — Visualizzazione Report
# ==========================================
def report_spese_per_categoria(cursor):
    print("\n--- REPORT 1: Totale Spese per Categoria ---")
    query = """
        SELECT C.nome, COALESCE(SUM(S.importo), 0) AS Totale
        FROM Categorie C
        LEFT JOIN Spese S ON C.id = S.categoria_id
        GROUP BY C.id, C.nome
        ORDER BY Totale DESC;
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    
    print(f"{'Categoria':<20} {'Totale Speso (€)':<15}")
    print("-" * 37)
    for nome, totale in rows:
        print(f"{nome:<20} {totale:<15.2f}")

def report_spese_vs_budget(cursor):
    print("\n--- REPORT 2: Spese Mensili vs Budget ---")
    query = """
        SELECT B.mese, C.nome, B.importo_budget, COALESCE(SUM(S.importo), 0) AS TotaleSpeso
        FROM Budget B
        JOIN Categorie C ON B.categoria_id = C.id
        LEFT JOIN Spese S ON S.categoria_id = C.id AND strftime('%Y-%m', S.data) = B.mese
        GROUP BY B.mese, C.id, C.nome, B.importo_budget;
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    
    for mese, cat, budget, speso in rows:
        stato = "SUPERAMENTO BUDGET" if speso > budget else "DENTRO IL BUDGET"
        print(f"Mese: {mese} | Categoria: {cat}")
        print(f"  Budget: €{budget:.2f} | Speso: €{speso:.2f} | Stato: {stato}")
        print("-" * 50)

def report_elenco_completo_spese(cursor):
    print("\n--- REPORT 3: Elenco Completo Spese Ordinate per Data ---")
    query = """
        SELECT S.data, C.nome, S.importo, S.descrizione
        FROM Spese S
        JOIN Categorie C ON S.categoria_id = C.id
        ORDER BY S.data DESC;
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    
    print(f"{'Data':<12} {'Categoria':<18} {'Importo (€)':<12} {'Descrizione':<25}")
    print("-" * 67)
    for data, cat, importo, desc in rows:
        desc_text = desc if desc else ""
        print(f"{data:<12} {cat:<18} {importo:<12.2f} {desc_text:<25}")

def modulo_visualizza_report():
    conn = get_connection()
    cursor = conn.cursor()
    
    while True:
        print("\n--- MENU REPORT ---")
        print("1. Totale spese per categoria")
        print("2. Spese mensili vs budget")
        print("3. Elenco completo delle spese ordinate per data")
        print("4. Ritorna al menu principale")
        scelta_rep = input("Inserisci la tua scelta (1-4): ").strip()
        
        if scelta_rep == '1':
            report_spese_per_categoria(cursor)
        elif scelta_rep == '2':
            report_spese_vs_budget(cursor)
        elif scelta_rep == '3':
            report_elenco_completo_spese(cursor)
        elif scelta_rep == '4':
            break
        else:
            print("Scelta non valida. Riprovare.")
            
    conn.close()

# ==========================================
# MAIN LOOP / MENU PRINCIPALE
# ==========================================
def main():
    inizializza_db()
    print("Benvenuto nel Sistema di Gestione Spese Personali e Budget!")
    
    while True:
        print("\n-------------------------")
        print("SISTEMA SPESE PERSONALI")
        print("-------------------------")
        print("1. Gestione Categorie")
        print("2. Inserisci Spesa")
        print("3. Definisci Budget Mensile")
        print("4. Visualizza Report")
        print("5. Esci")
        print("-------------------------")
        
        scelta = input("Inserisci la tua scelta: ").strip()
        
        if scelta == '1':
            modulo_gestione_categorie()
        elif scelta == '2':
            modulo_inserisci_spesa()
        elif scelta == '3':
            modulo_definisci_budget()
        elif scelta == '4':
            modulo_visualizza_report()
        elif scelta == '5':
            print("Grazie per aver utilizzato il programma. Arrivederci!")
            break
        else:
            print("Scelta non valida. Riprovare.")

if __name__ == "__main__":
    main()