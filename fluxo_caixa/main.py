
from database.sqlite_handler import SQLiteHandler
from drivers.selenium_handler import SeleniumHandler
from fluxo_caixa.config import Config
from fluxo_caixa.fluxo_caixa_processor import FluxoCaixaProcessor
from fluxo_caixa.utils.logger import LoggerSetup


def main():
    logger_setup = LoggerSetup()
    logger = logger_setup.logger
    logger.info("Iniciando o processamento de divergências no fluxo de caixa.")

    config = Config()

    selenium_handler = SeleniumHandler(config, logger)

    try:
        with selenium_handler:
            processor = FluxoCaixaProcessor(config, logger, selenium_handler)

            sqlite_db_path = "contas_processadas.db"
            with SQLiteHandler(sqlite_db_path, logger) as conn:
                processor.processar(conn)

    except Exception as e:
        logger.error(f"Ocorreu uma exceção durante o processamento: {e}")

    finally:
        selenium_handler.close_driver()

    logger.info("Processamento finalizado.")

if __name__ == "__main__":
    main()
