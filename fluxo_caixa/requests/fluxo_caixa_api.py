from typing import Optional, Dict, Any
import requests
from datetime import datetime
import time
from selenium.webdriver.remote.webdriver import WebDriver
class FluxoDeCaixaAPI:
    def __init__(self, base_url: str, headers: Dict[str, str], modeloFluxoId: str, driver: WebDriver | None=None):
        self.base_url = base_url
        self.headers = headers
        self.modeloFluxoId = modeloFluxoId
        self.cookies = None
        self.driver = driver

    def atualizar_cookies(self):
        self.driver.refresh()
        time.sleep(3)
        
        selenium_cookies = self.driver.get_cookies()
    
        self.cookies = {cookie['name']: cookie['value'] for cookie in selenium_cookies}
    
        self.headers.update({
            'Cookie': '; '.join([f"{key}={value}" for key, value in self.cookies.items()])
        })

    def requisitar_fluxo_de_caixa_simples(self, data_inicio: datetime, data_fim: datetime, conta: str) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/FluxoDeCaixaAPI/IniciarFluxoDeCaixa/"
        params = {
            "Inicio": data_inicio.isoformat() + "Z",
            "Fim": data_fim.isoformat() + "Z",
            "Status": 0,
            "Contas": conta,
            "APartirUltimoDiaConciliado": False,
            "ExibirParcelasNaoAprovadas": False,
            "OcultarTransferencias": False,
            "ValoresNosDiasOriginais": False,
            "OcultarDinheiroDeCaixasAbertos": False,
            "AdicionarUmDiaNoVencimentoDeBoletosAReceber": False,
            "OcultarTitulosVencidos": False
        }

        try:
            response = requests.get(url, params=params, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Erro na requisição do fluxo de caixa simples: {response.status_code}")
                
                if self.driver:
                    print("Atualizando cookies")
                    self.atualizar_cookies()
                else: 
                    print("Não vai ser possível atualizar os cookies. ChromeDriver não iniciado")
                    return None

                response = requests.get(url, params=params, headers=self.headers)
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"Erro após atualização dos cookies: {response.status_code}")
                    return None
        except Exception as e:
            print(f"Erro ao fazer requisição ao fluxo de caixa simples: {e}")
            return None

    def requisitar_fluxo_de_caixa_analitico(self, data_inicio: datetime, data_fim: datetime, conta: str, modeloFluxoCaixa: str=None) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/FluxoDeCaixaAPI/IniciarFluxoDeCaixaAnalitico/"
        params = {
            "Inicio": data_inicio.isoformat(),
            "Fim": data_fim.isoformat(),
            "Status": 0,
            "TipoDePeriodo": 0,
            "Contas": conta,
            "ModeloDoFluxoId": self.modeloFluxoId,
            "APartirUltimoDiaConciliado": False,
            "ExibirParcelasNaoAprovadas": False,
            "OcultarTransferencias": False,
            "ValoresNosDiasOriginais": False,
            "OcultarDinheiroDeCaixasAbertos": False,
            "AdicionarUmDiaNoVencimentoDeBoletosAReceber": False,
            "OcultarTitulosVencidos": False,
            "ExibirPrevisoes": False,
            "AnaliseVertical": False
        }

        try:
            response = requests.get(url, params=params, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Erro na requisição do fluxo de caixa analítico: {response.status_code}")
                return None
        except Exception as e:
            print(f"Erro ao fazer requisição ao fluxo de caixa analítico: {e}")
            return None