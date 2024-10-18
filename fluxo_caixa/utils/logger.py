import logging
import colorlog

class LoggerSetup:
    """Configuração do logger com suporte a cores e arquivos."""

    def __init__(self, log_file: str = 'divergencia_fluxo_caixa.log'):
        self.logger = logging.getLogger("DivergenciaFluxoCaixa")
        self.logger.setLevel(logging.DEBUG)
        self._setup_handlers(log_file)

    def _setup_handlers(self, log_file: str):
        log_colors_config = {
            'DEBUG': 'bold_blue',
            'INFO': 'bold_green',
            'WARNING': 'bold_yellow',
            'ERROR': 'bold_red',
            'CRITICAL': 'bold_purple',
        }

        # Handler para console com cores
        console_handler = colorlog.StreamHandler()
        console_handler.setFormatter(colorlog.ColoredFormatter(
            '%(log_color)s%(asctime)s - %(levelname)s - %(message)s',
            log_colors=log_colors_config
        ))
        self.logger.addHandler(console_handler)


        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(file_handler)
