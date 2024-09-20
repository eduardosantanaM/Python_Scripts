import os
import json
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime


class ParcelasProcessor:
    def __init__(self, db_name, conta_id, data_inicio, data_fim, page_size=1000):
        # Configuração inicial
        self.client = MongoClient("mongodb://localhost:27017/")
        self.db = self.client[db_name]  # Nome do banco de dados
        self.conta_id = ObjectId(conta_id)  # ID da conta para filtrar
        self.data_inicio = data_inicio  # Data de início
        self.data_fim = data_fim  # Data de fim
        self.page_size = page_size  # Tamanho da página para paginação
        self.qtd_erros = 0
        self.dif_b = 0
        self.dif_l = 0
        self.divergencias = []  # Lista para armazenar as divergências
        self.planos_de_contas = list(
            self.db.PlanoDeConta.find({})
        )  # Todos os planos de conta

    def processar_parcelas(self, salvar_divergencias=False):
        """Processa as parcelas e salva divergências em arquivo, se necessário."""
        page = 0
        has_more = True

        while has_more:
            # Paginação no find de Parcelas em ambas as coleções usando skip e limit
            parcelas_de_cartao = self._buscar_parcelas("ParcelaDeCartao", page)
            new_parcelas_de_titulo = self._buscar_parcelas("NewParcelaDeTitulo", page)

            # Combina as duas coleções em um único array de parcelas
            parcelas_de_titulo = parcelas_de_cartao + new_parcelas_de_titulo

            # Se não há mais parcelas em nenhuma das duas coleções, termina a execução
            if len(parcelas_de_titulo) == 0:
                has_more = False
                break

            # Buscar rateios associados às parcelas
            rateios = list(
                self.db.Rateio.find(
                    {"Parcela._id": {"$in": [p["_id"] for p in parcelas_de_titulo]}}
                )
            )

            # Processa as parcelas da página atual
            self._processar_parcelas_da_pagina(parcelas_de_titulo, rateios)

            # Passa para a próxima página
            page += 1

        print(f"Erros: {self.qtd_erros}")
        print(f"Diferenca Bruto: {self.dif_b}")
        print(f"Diferenca Liquida: {self.dif_l}")
        # Salvar as divergências em um arquivo se necessário
        if salvar_divergencias and self.divergencias:
            nome_arquivo = f"{str(self.conta_id)}_{self.data_inicio.strftime('%Y-%m-%d')}_{self.data_fim.strftime('%Y-%m-%d')}.json"
            self._salvar_divergencias(nome_arquivo=nome_arquivo)
            print(f"Salvando divergências no arquivo {nome_arquivo}")

    def _buscar_parcelas(self, collection_name, page):
        """Buscar parcelas com paginação de acordo com a coleção."""
        parcelas = list(
            self.db[collection_name]
            .find(
                {
                    "Liquidacao": {"$gte": self.data_inicio, "$lt": self.data_fim},
                    "Conta._id": self.conta_id,
                }
            )
            .skip(page * self.page_size)
            .limit(self.page_size)
        )

        # Adiciona tipo de parcela (identificação do tipo de coleção)
        for p in parcelas:
            p["tipoParcela"] = collection_name
        return parcelas

    def _processar_parcelas_da_pagina(self, parcelas, rateios):
        """Processa as parcelas e faz as verificações de rateios."""
        for parcela in parcelas:
            # Filtra os rateios correspondentes à parcela atual
            rateios_da_parcela = [
                r for r in rateios if r["Parcela"]["_id"] == parcela["_id"]
            ]
            valor_rateio = 0

            if rateios_da_parcela:
                for rateio in rateios_da_parcela:
                    plano_de_conta = next(
                        (
                            p
                            for p in self.planos_de_contas
                            if p["_id"] == rateio["PlanoDeConta"]["_id"]
                        ),
                        None,
                    )

                    if plano_de_conta and "Tipo" in plano_de_conta:
                        # Subtrai ou soma conforme o tipo do plano de conta, arredondando para 2 casas decimais
                        if plano_de_conta["Tipo"]:
                            valor_rateio = round(
                                valor_rateio - rateio["Valor"], 2
                            )  # Para contas a pagar
                        else:
                            valor_rateio = round(
                                valor_rateio + rateio["Valor"], 2
                            )  # Para contas a receber
                    else:
                        print(
                            f"Plano de Conta não encontrado para Rateio ID: {rateio['_id']}"
                        )

            valor_rateio_positivo = abs(valor_rateio)

            if (
                parcela["ValorLiquido"] > 0
                and parcela["ValorLiquido"] != valor_rateio_positivo
            ) or (
                parcela["ValorLiquido"] == 0
                and valor_rateio_positivo != parcela["ValorBruto"]
            ):
                self.dif_b += parcela["ValorBruto"] - valor_rateio_positivo
                self.dif_l += parcela["ValorLiquido"] - valor_rateio_positivo
                self.qtd_erros += 1

                # Adicionar divergência à lista
                self.divergencias.append(
                    {
                        "collection": parcela["tipoParcela"],
                        "parcela_id": str(parcela["_id"]),
                        "valor_rateio": valor_rateio_positivo,
                        "valor_bruto": parcela["ValorBruto"],
                        "valor_liquido": parcela["ValorLiquido"],
                        "tipo_parcela": parcela["Tipo"],
                        "liquidacao": parcela["Liquidacao"].strftime("%Y-%m-%d"),
                    }
                )

    def _salvar_divergencias(self, nome_arquivo: str):
        """Salva as divergências em um arquivo JSON na pasta 'divergencias'."""
        # Diretório onde as divergências serão salvas
        pasta_divergencias = os.path.join(os.getcwd(), "divergencias")

        # Cria a pasta, se não existir
        if not os.path.exists(pasta_divergencias):
            os.makedirs(pasta_divergencias)

        # Nome do arquivo com base no conta_id e datas
        caminho_arquivo = os.path.join(pasta_divergencias, nome_arquivo)

        # Agrupando divergências por coleção
        agrupado_por_collection = {}
        for divergencia in self.divergencias:
            collection = divergencia["collection"]
            if collection not in agrupado_por_collection:
                agrupado_por_collection[collection] = []
            agrupado_por_collection[collection].append(divergencia)

        # Salvando no arquivo JSON
        with open(caminho_arquivo, "w", encoding="utf-8") as arquivo_json:
            json.dump(
                agrupado_por_collection, arquivo_json, ensure_ascii=False, indent=4
            )

        print(f"Divergências salvas em {caminho_arquivo}")


# Exemplo de uso:
if __name__ == "__main__":
    # Data atual
    data_atual = datetime.now()

    # Definir início e fim do dia atual
    data_inicio = data_atual.replace(hour=0, minute=0, second=0, microsecond=0)
    data_fim = data_atual.replace(hour=23, minute=59, second=59, microsecond=999999)

    processor = ParcelasProcessor(
        db_name="nome_do_banco",  # Nome do banco de dados
        conta_id="id_da_conta_bancaria",  # ID da conta para buscar
        data_inicio=data_inicio,  # Data de início (meia-noite)
        data_fim=data_fim,  # Data de fim (23:59:59)
        page_size=1000,  # Tamanho da página
    )

    # Processar parcelas e salvar divergências em arquivo JSON
    processor.processar_parcelas(salvar_divergencias=True)
