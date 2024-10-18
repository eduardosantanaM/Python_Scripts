import pymongo
import logging


class MongoDBHandler:
    """Manipula conexões e operações com MongoDB."""

    def __init__(self, uri: str, database_name: str, logger: logging.Logger):
        self.uri = uri
        self.database_name = database_name
        self.logger = logger
        self.client = None

    def __enter__(self):
        try:
            self.client = pymongo.MongoClient(self.uri)
            self.logger.debug("Conexão com MongoDB estabelecida.")
            return self.client[self.database_name]
        except Exception as e:
            self.logger.error(f"Erro ao conectar ao MongoDB: {e}")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            self.client.close()
            self.logger.debug("Conexão com MongoDB fechada.")