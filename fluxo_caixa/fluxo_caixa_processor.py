import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import sqlite3

from database.mongo_handler import MongoDBHandler
from drivers.selenium_handler import SeleniumHandler
from config import Config
from fluxo_caixa.drivers.helpers.selenium_driver import efetuar_login
from fluxo_caixa.parcelas_processor import ParcelasProcessor
from fluxo_caixa.requests.fluxo_caixa_api import FluxoDeCaixaAPI

class FluxoCaixaProcessor:
    """Processa as contas e compara os saldos do fluxo de caixa."""

    def __init__(self, config: Config, logger: logging.Logger, selenium_handler: SeleniumHandler):
        self.config = config
        self.logger = logger
        self.selenium_handler = selenium_handler
        self.api = self._initialize_api()

    def _initialize_api(self) -> FluxoDeCaixaAPI:
        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Cookie": self.config.cookie
        }
        driver = self.selenium_handler.driver
        if driver:
            efetuar_login(driver, self.config.login, self.config.senha)
            self.logger.debug("Login efetuado com sucesso no Selenium.")
        else:
            self.logger.warning("Driver Selenium não foi iniciado.")

        api = FluxoDeCaixaAPI(
            base_url=self.config.url_base_fin,
            headers=headers,
            modeloFluxoId=self.config.modelo_fluxo_id,
            driver=driver
        )
        self.logger.debug("FluxoDeCaixaAPI inicializado.")
        return api

    def processar(self, conn: sqlite3.Connection):
        mongo_uri = self.config.mongo_uri
        collection_name = "ContaBancaria"

        data_inicio: datetime = self.config.data_inicio.replace(hour=3, minute=0, second=0)
        data_fim: datetime = self.config.data_fim.replace(hour=3, minute=0, second=0)

        with MongoDBHandler(mongo_uri, self.config.database_name, self.logger) as db:
            contas = list(db[collection_name].find({}))
            self.logger.info(f"{len(contas)} contas obtidas do MongoDB.")
        
        contas_filtradas = self._filtrar_contas(contas)
        self.logger.info(f"{len(contas_filtradas)} contas após filtragem.")

        for conta in contas_filtradas:
            conta_id: str = str(conta["_id"])
            nome_conta = conta.get("Nome", "")
            if conta.get("ContaInativa", False) and nome_conta and "encerrada" not in nome_conta.lower():
                self.logger.info(f"Conta {conta_id} inativa e não encerrada. Pulando.")
                continue

            self.logger.info(f"Processando conta com ID: {conta_id} - {nome_conta}")
            data_atual = data_inicio

            while data_atual <= data_fim:
                if self._conta_ja_processada(conn, conta_id, data_atual):
                    self.logger.info(
                        f"Conta {conta_id} já processada em {data_atual.strftime('%Y-%m-%d')}. Pulando..."
                    )
                    data_atual += timedelta(days=1)
                    continue

                self.logger.info(f"Verificando fluxos de caixa para a data: {data_atual.strftime('%Y-%m-%d')}")
                dados_fluxo_simples = self.api.requisitar_fluxo_de_caixa_simples(data_atual, data_atual, conta_id)
                dados_fluxo_analitico = self.api.requisitar_fluxo_de_caixa_analitico(data_atual, data_atual, conta_id)

                if dados_fluxo_simples and dados_fluxo_analitico:
                    saldo_simples = self._extrair_saldo_final_simples(dados_fluxo_simples)
                    saldo_analitico = self._extrair_saldo_final_analitico(dados_fluxo_analitico)

                    if saldo_simples is not None and saldo_analitico is not None:
                        diferenca = self._comparar_saldos(saldo_simples, saldo_analitico)
                        if diferenca != 0:
                            self.logger.warning(
                                f"Diferença encontrada para a conta {nome_conta} em {data_atual.strftime('%Y-%m-%d')}: {diferenca}"
                            )
                            self._processar_parcelas(conta_id, data_atual, conta)
                        else:
                            self.logger.info(
                                f"Nenhuma diferença encontrada para a conta {nome_conta} em {data_atual.strftime('%Y-%m-%d')}."
                            )
                    else:
                        self.logger.error(
                            f"Erro ao extrair saldos para a conta {nome_conta} em {data_atual.strftime('%Y-%m-%d')}."
                        )
                else:
                    self.logger.error(
                        f"Erro ao recuperar dados para a conta {nome_conta} em {data_atual.strftime('%Y-%m-%d')}."
                    )

                self._registrar_conta_processada(conn, conta_id, data_atual)
                data_atual += timedelta(days=1)

    def _filtrar_contas(self, contas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if self.config.contas_ids:
            contas_filtradas = [conta for conta in contas if str(conta["_id"]) in self.config.contas_ids]
            self.logger.debug(f"{len(contas_filtradas)} contas filtradas com base em 'contas_ids'.")
            return contas_filtradas
        self.logger.debug("Nenhum filtro aplicado nas contas.")
        return contas

    def _extrair_saldo_final_simples(self, dados: Dict[str, Any]) -> Optional[float]:
        try:
            saldo_final = float(dados.get("Result", {}).get("SaldoFinal", {}).get("Valor", 0.0))
            self.logger.debug(f"Saldo final simples extraído: {saldo_final}")
            return saldo_final
        except (TypeError, ValueError) as e:
            self.logger.error(f"Erro ao extrair saldo final do fluxo simples: {e}")
            return None

    def _extrair_saldo_final_analitico(self, dados: Dict[str, Any]) -> Optional[float]:
        try:
            for item in dados.get("Result", {}).get("Values", []):
                if item.get("Nome") == "Saldo Final":
                    valor = float(item.get("Valores", [{}])[0].get("Valor", 0.0))
                    self.logger.debug(f"Saldo final analítico extraído: {valor}")
                    return valor
            self.logger.warning("Saldo Final não encontrado no fluxo analítico.")
            return None
        except (TypeError, ValueError) as e:
            self.logger.error(f"Erro ao extrair saldo final do fluxo analítico: {e}")
            return None

    def _comparar_saldos(self, saldo_simples: float, saldo_analitico: float) -> float:
        diferenca = saldo_simples - saldo_analitico
        self.logger.debug(f"Diferença calculada: {diferenca}")
        return diferenca

    def _conta_ja_processada(self, conn: sqlite3.Connection, conta_id: str, data: datetime) -> bool:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT 1 FROM contas_processadas WHERE conta_id = ? AND data_processada = ?",
                (conta_id, data.strftime('%Y-%m-%d'))
            )
            processada = cursor.fetchone() is not None
            if processada:
                self.logger.info(f"Conta {conta_id} já foi processada para {data.strftime('%Y-%m-%d')}.")
            else:
                self.logger.debug(f"Conta {conta_id} ainda não foi processada para {data.strftime('%Y-%m-%d')}.")
            return processada
        except sqlite3.Error as e:
            self.logger.error(f"Erro ao verificar processamento da conta {conta_id} em {data.strftime('%Y-%m-%d')}: {e}")
            return False

    def _registrar_conta_processada(self, conn: sqlite3.Connection, conta_id: str, data: datetime):
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT OR IGNORE INTO contas_processadas (conta_id, data_processada) VALUES (?, ?)",
                (conta_id, data.strftime('%Y-%m-%d'))
            )
            conn.commit()
            self.logger.info(f"Conta {conta_id} registrada como processada para {data.strftime('%Y-%m-%d')}.")
        except sqlite3.Error as e:
            self.logger.error(f"Erro ao registrar conta {conta_id} para {data.strftime('%Y-%m-%d')}: {e}")

    def _processar_parcelas(self, conta_id: str, data: datetime, conta: Dict[str, Any]):
        data_inicio_busca_db = data.replace(hour=0, minute=0, second=0, microsecond=0)
        data_final_busca_db = (data + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

        processor = ParcelasProcessor(
            mongo_uri=self.config.mongo_uri,
            db_name=self.config.database_name,
            conta_id=conta_id,
            data_inicio=data_inicio_busca_db,
            data_fim=data_final_busca_db,
            conta=conta
        )
        processor.processar_parcelas(True)
        self.logger.debug(f"Parcelas processadas para a conta {conta_id} em {data.strftime('%Y-%m-%d')}.")
