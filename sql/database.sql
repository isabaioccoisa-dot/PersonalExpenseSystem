SQL
-- ==========================================
-- SCRIPT DI CREAZIONE DEL DATABASE
-- ==========================================

-- Tabella Categorie
CREATE TABLE Categorie (id INTEGER PRIMARY KEY AUTOINCREMENT,nome TEXT NOT NULL UNIQUE);

-- Tabella Spese
CREATE TABLE Spese (id INTEGER PRIMARY KEY AUTOINCREMENT,data TEXT NOT NULL,importo REAL NOT NULL CHECK (importo > 0),
categoria_id INTEGER NOT NULL,descrizione TEXT, FOREIGN KEY (categoria_id) REFERENCES Categorie(id) ON DELETE CASCADE);

-- Tabella Budget
CREATE TABLE Budget ( id INTEGER PRIMARY KEY AUTOINCREMENT, mese TEXT NOT NULL,categoria_id INTEGER NOT NULL,importo_budget REAL NOT NULL CHECK (importo_budget > 0),
FOREIGN KEY (categoria_id) REFERENCES Categorie(id) ON DELETE CASCADE,UNIQUE(mese, categoria_id));

-- ==========================================
-- DATI DI ESEMPIO (INSERT)
-- ==========================================
INSERT INTO Categorie (nome) VALUES ('Alimentari');
INSERT INTO Categorie (nome) VALUES ('Trasporti');
INSERT INTO Categorie (nome) VALUES ('Svago');

INSERT INTO Spese (data, importo, categoria_id, descrizione) VALUES ('2026-01-10', 45.50, 1, 'Spesa al supermercato');
INSERT INTO Spese (data, importo, categoria_id, descrizione) VALUES ('2026-01-12', 20.00, 2, 'Benzina');

INSERT INTO Budget (mese, categoria_id, importo_budget) VALUES ('2026-01', 1, 300.00);
