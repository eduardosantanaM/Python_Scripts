# drivers/selenium_handler.py
import logging
import os
import signal
import atexit
from fluxo_caixa.drivers.helpers.selenium_driver import iniciar_driver_selenium, efetuar_login
from config import Config

class SeleniumHandler:
    """Gerencia o ciclo de vida do driver Selenium, garantindo o fechamento adequado."""
    def __init__(self, config: Config, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.driver = None
        self._closed = False
        atexit.register(self.close_driver)
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def __enter__(self):
        try:
            self.logger.debug("Inicializando o driver Selenium.")
            self.driver = iniciar_driver_selenium(
                self.config.driver_path,
                self.config.url_base_fin
            )
            return self.driver
        except Exception as e:
            self.logger.error(f"Erro ao inicializar o driver Selenium: {e}")
            self.close_driver()
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_driver()

    def _handle_signal(self, signum, frame):
        """Handler para sinais de interrupção."""
        self.logger.info(f"Recebido sinal {signum}. Fechando o driver Selenium.")
        self.close_driver()
        # Reenviar o sinal padrão para terminar o processo
        signal.signal(signum, signal.SIG_DFL)
        os.kill(os.getpid(), signum)

    def close_driver(self):
        """Fecha o driver Selenium se ainda estiver aberto."""
        if not self._closed and self.driver:
            try:
                self.logger.debug("Finalizando o driver Selenium.")
                self.driver.quit()
                self.logger.debug("Driver Selenium finalizado com sucesso.")
            except Exception as e:
                self.logger.error(f"Erro ao finalizar o driver Selenium: {e}")
            finally:
                self._closed = True
