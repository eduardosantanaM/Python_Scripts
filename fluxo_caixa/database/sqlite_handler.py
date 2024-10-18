import sqlite3
import logging

class SQLiteHandler:
    """Manipula conexões e operações com SQLite."""

    def __init__(self, db_path: str, logger: logging.Logger):
        self.db_path = db_path
        self.logger = logger
        self.conn = None

    def __enter__(self):
        try:
            self.conn = sqlite3.connect(self.db_path)
            self._create_table()
            self.logger.debug("Conexão com SQLite estabelecida.")
            return self.conn
        except sqlite3.Error as e:
            self.logger.error(f"Erro ao conectar ao SQLite: {e}")
            raise

    def _create_table(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contas_processadas (
                conta_id TEXT,
                data_processada TEXT,
                PRIMARY KEY (conta_id, data_processada)
            )
        """)
        self.conn.commit()
        self.logger.debug("Tabela 'contas_processadas' verificada/criada.")

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.close()
            self.logger.debug("Conexão com SQLite fechada.")
