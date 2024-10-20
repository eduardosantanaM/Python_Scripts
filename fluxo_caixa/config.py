import json
from datetime import datetime
import os

class Config:
    def __init__(self, config_file='config.json'):
        # Carregar as configurações do arquivo
        self._carregar_configuracoes(config_file)

    def _carregar_configuracoes(self, config_file):
        """Carrega configurações de um arquivo JSON e converte as datas para datetime."""
        with open(os.getcwd() + f"/{config_file}", 'r', encoding='utf-8') as file:
            config_data = json.load(file)
        
        # Armazena as informações carregadas
        self.cookie: str = config_data['cookie']
        self.data_inicio: str = datetime.fromisoformat(config_data['data_inicio'])
        self.data_fim: str = datetime.fromisoformat(config_data['data_fim'])
        self.database_name: str = config_data['database_name']
        self.contas_ids: list = config_data.get('contas_ids', []) 
        self.modelo_fluxo_id: str = config_data['modelo_fluxo_id']
        self.driver_path: str = config_data['driver_path'] 
        self.login: str = config_data['login']
        self.senha: str = config_data['senha']
        self.url_base_fin: str = config_data["url_base_fin"]
        self.mongo_uri: str = config_data["mongo_uri"]
        
    def __repr__(self):
        """Representação legível da configuração."""
        return (f"Config(cookie='{self.cookie}', "
                f"data_inicio='{self.data_inicio}', "
                f"data_fim='{self.data_fim}', "
                f"database_name='{self.database_name}', "
                f"driver_path='{self.driver_path}', "
                f"login='{self.login}')")

# Exemplo de uso da classe Config
if __name__ == "__main__":
    config = Config()  # Carrega a configuração do arquivo 'config.json'

    # Acessando as propriedades da configuração
    print(config.cookie)         # Cookie
    print(config.data_inicio)    # Data de início
    print(config.data_fim)       # Data de fim
    print(config.database_name)  # Nome do banco de dados

    # Exibindo a representação da configuração
    print(config)