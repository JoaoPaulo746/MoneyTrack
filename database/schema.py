"""Estrutura do banco de dados e carga inicial de categorias."""
from database.connection import db_session

SCHEMA = """
CREATE TABLE IF NOT EXISTS categories (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT    NOT NULL CHECK (length(trim(name)) > 0),
    type       TEXT    NOT NULL CHECK (type IN ('receita', 'despesa')),
    color      TEXT    NOT NULL DEFAULT '#64748B',
    icon       TEXT    NOT NULL DEFAULT '',
    UNIQUE (name, type)
);

CREATE TABLE IF NOT EXISTS transactions (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    description      TEXT    NOT NULL CHECK (length(trim(description)) > 0),
    amount_cents     INTEGER NOT NULL CHECK (amount_cents > 0),
    type             TEXT    NOT NULL CHECK (type IN ('receita', 'despesa')),
    category_id      INTEGER NOT NULL,
    transaction_date TEXT    NOT NULL CHECK (date(transaction_date) = transaction_date),
    notes            TEXT    NOT NULL DEFAULT '',
    created_at       TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS goals (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT    NOT NULL CHECK (length(trim(name)) > 0),
    target_cents   INTEGER NOT NULL CHECK (target_cents > 0),
    current_cents  INTEGER NOT NULL DEFAULT 0 CHECK (current_cents >= 0),
    created_at     TEXT    NOT NULL DEFAULT (date('now', 'localtime')),
    deadline       TEXT    CHECK (deadline IS NULL OR date(deadline) = deadline)
);

CREATE INDEX IF NOT EXISTS idx_transactions_date     ON transactions (transaction_date);
CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions (category_id);

-- O tipo da movimentação deve ser igual ao tipo da categoria escolhida.
CREATE TRIGGER IF NOT EXISTS trg_tx_type_insert
BEFORE INSERT ON transactions
WHEN (SELECT type FROM categories WHERE id = NEW.category_id) IS NOT NEW.type
BEGIN
    SELECT RAISE(ABORT, 'O tipo da movimentação não corresponde ao tipo da categoria.');
END;

CREATE TRIGGER IF NOT EXISTS trg_tx_type_update
BEFORE UPDATE ON transactions
WHEN (SELECT type FROM categories WHERE id = NEW.category_id) IS NOT NEW.type
BEGIN
    SELECT RAISE(ABORT, 'O tipo da movimentação não corresponde ao tipo da categoria.');
END;

-- Impede trocar o tipo de uma categoria que já possui movimentações.
CREATE TRIGGER IF NOT EXISTS trg_category_type_locked
BEFORE UPDATE OF type ON categories
WHEN NEW.type <> OLD.type AND EXISTS (SELECT 1 FROM transactions WHERE category_id = OLD.id)
BEGIN
    SELECT RAISE(ABORT, 'Não é possível alterar o tipo de uma categoria com movimentações.');
END;
"""

DEFAULT_CATEGORIES = [
    # (nome, tipo, cor, ícone)
    ("Salário", "receita", "#16A34A", "💼"),
    ("Freelance", "receita", "#0EA5E9", "💻"),
    ("Investimentos", "receita", "#8B5CF6", "📈"),
    ("Presentes", "receita", "#EC4899", "🎁"),
    ("Outros", "receita", "#64748B", "💰"),
    ("Alimentação", "despesa", "#F97316", "🍔"),
    ("Transporte", "despesa", "#3B82F6", "🚌"),
    ("Moradia", "despesa", "#6366F1", "🏠"),
    ("Educação", "despesa", "#0D9488", "🎓"),
    ("Saúde", "despesa", "#EF4444", "💊"),
    ("Lazer", "despesa", "#A855F7", "🎮"),
    ("Compras", "despesa", "#EAB308", "🛒"),
    ("Assinaturas", "despesa", "#14B8A6", "📺"),
    ("Outros", "despesa", "#64748B", "📦"),
]


def seed_default_categories(conn) -> None:
    conn.executemany(
        "INSERT INTO categories (name, type, color, icon) VALUES (?, ?, ?, ?)",
        DEFAULT_CATEGORIES,
    )


def initialize_database() -> None:
    """Cria as tabelas (se não existirem) e as categorias iniciais (apenas na 1ª vez)."""
    with db_session() as conn:
        conn.executescript(SCHEMA)
        total = conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
        if total == 0:
            seed_default_categories(conn)


def wipe_all_data() -> None:
    """Apaga movimentações, metas e categorias do banco ativo e recria as categorias padrão."""
    with db_session() as conn:
        conn.execute("DELETE FROM transactions")
        conn.execute("DELETE FROM goals")
        conn.execute("DELETE FROM categories")
        conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('transactions','goals','categories')")
        seed_default_categories(conn)
