"""Conexão com o SQLite (banco local, sem internet)."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
REAL_DB_PATH = DATA_DIR / "moneytrack.db"
DEMO_DB_PATH = DATA_DIR / "moneytrack_demo.db"

_current_path = REAL_DB_PATH


def set_database(path) -> None:
    """Define qual arquivo .db está em uso (real, demonstração ou testes)."""
    global _current_path
    _current_path = Path(path)


def get_database_path() -> Path:
    return _current_path


def is_demo() -> bool:
    return _current_path == DEMO_DB_PATH


def get_connection() -> sqlite3.Connection:
    _current_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(_current_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")  # ativa as chaves estrangeiras
    # LOWER() do SQLite ignora acentos; esta função torna a busca correta em português.
    conn.create_function("PYLOWER", 1, lambda v: v.lower() if isinstance(v, str) else v)
    return conn


@contextmanager
def db_session():
    """Abre conexão, confirma (commit) ao final ou desfaz (rollback) em caso de erro."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
