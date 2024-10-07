import pymongo
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from achar_parcela_errada import ParcelasProcessor
from config import Config
from fluxo_caixa_api import FluxoDeCaixaAPI
config = Config()

headers: Dict[str, str] = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Cookie": config.cookie
}

api: FluxoDeCaixaAPI = FluxoDeCaixaAPI(base_url="http://localhost:1337", headers=headers, modeloFluxoId=config.modelo_fluxo_id)

# Função para conectar ao MongoDB e obter resultados de uma coleção
def conectar_mongo_e_obter_resultados(uri: str, database_name: str, collection_name: str) -> List[Dict[str, Any]]:
    try:
        client = pymongo.MongoClient(uri)
        db = client[database_name]
        resultados = list(db[collection_name].find({}))
        return resultados
    except Exception as e:
        print(f"Erro ao conectar ao MongoDB ou obter resultados da coleção {collection_name}: {e}")
        return []

# Função para filtrar contas de acordo com `contas_ids` da configuração
def filtrar_contas(contas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if config.contas_ids:
        return list(filter(lambda x: str(x["_id"]) in config.contas_ids, contas))
    else:
        return contas

# Função para extrair o saldo final do fluxo de caixa simples
def extrair_saldo_final_simples(dados_fluxo_simples: Dict[str, Any]) -> Optional[float]:
    try:
        result = dados_fluxo_simples.get("Result", {})
        saldo_final_secao = result.get("SaldoFinal", {})
        saldo_final = saldo_final_secao.get("Valor", 0.0)
        if isinstance(saldo_final, (int, float)):
            return float(saldo_final)
        return None
    except Exception as e:
        print(f"Erro ao extrair saldo final do fluxo simples: {e}")
        return None

# Função para extrair o saldo final do fluxo de caixa analítico
def extrair_saldo_final_analitico(dados_fluxo_analitico: Dict[str, Any]) -> Optional[float]:
    try:
        for item in dados_fluxo_analitico.get("Result", {}).get("Values", []):
            if item.get("Nome") == "Saldo Final":
                valores = item.get("Valores", [])
                if valores:
                    return valores[0].get("Valor", 0.0)
        return None
    except Exception as e:
        print(f"Erro ao extrair saldo final do fluxo analítico: {e}")
        return None

# Função para comparar os saldos
def comparar_saldos(saldo_simples: float, saldo_analitico: float) -> float:
    return saldo_simples - saldo_analitico

# Função principal (main)
def main():
    mongo_uri = "mongodb://localhost:27017/"  
    database_name = config.database_name
    collection_name = "ContaBancaria"

    # Converte as strings de datas para objetos datetime
    data_inicio: datetime = config.data_inicio.replace(hour=3, minute=0, second=0)
    data_fim: datetime = config.data_fim.replace(hour=3, minute=0, second=0)

    # Obter contas do MongoDB e filtrar
    contas: List[Dict[str, Any]] = conectar_mongo_e_obter_resultados(mongo_uri, database_name, collection_name)
    contas_filtradas: List[Dict[str, Any]] = filtrar_contas(contas)

    for conta in contas_filtradas:
        conta_id: str = str(conta["_id"])
        if conta.get("ContaInativa", False):
            continue

        print(f"Verificando conta com ID: {conta_id}")
        data_atual = data_inicio

        # Iteração diária para comparar fluxos
        while data_atual <= data_fim:
            print(f"Verificando fluxos de caixa para a data: {data_atual.strftime('%Y-%m-%d')}")
            
            # Usar a classe FluxoDeCaixaAPI para fazer as requisições
            dados_fluxo_caixa_simples = api.requisitar_fluxo_de_caixa_simples(data_atual, data_atual, conta_id)
            dados_fluxo_caixa_analitico = api.requisitar_fluxo_de_caixa_analitico(data_atual, data_atual, conta_id)

            if dados_fluxo_caixa_simples and dados_fluxo_caixa_analitico:
                ## Pega o valor liquido
                saldo_simples = extrair_saldo_final_simples(dados_fluxo_caixa_simples)
                ## Pega o valor dos
                saldo_analitico = extrair_saldo_final_analitico(dados_fluxo_caixa_analitico)

                if saldo_simples is not None and saldo_analitico is not None:
                    diferenca = comparar_saldos(saldo_simples, saldo_analitico)
                    if diferenca != 0:
                        print(f"Diferença encontrada para a conta {conta['Nome']} no dia {data_atual.strftime('%Y-%m-%d')}: {diferenca}")
                        
                        # Busca detalhes das parcelas com erro
                        data_inicio_busca_db = data_atual.replace(hour=0, minute=0, second=0, microsecond=0)
                        data_final_busca_db = (data_atual + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

                        processor = ParcelasProcessor(
                            db_name=database_name,              
                            conta_id=conta_id,  
                            data_inicio=data_inicio_busca_db,              
                            data_fim=data_final_busca_db,       
                            conta=conta         
                        )
                        processor.processar_parcelas(True)
                    else:
                        print(f"Nenhuma diferença encontrada para a conta {conta['Nome']} no dia {data_atual.strftime('%Y-%m-%d')}.")
                else:
                    print(f"Erro ao extrair saldos para a conta {conta['Nome']} no dia {data_atual.strftime('%Y-%m-%d')}.")
            else:
                print(f"Erro ao recuperar dados para a conta {conta['Nome']} no dia {data_atual.strftime('%Y-%m-%d')}.")

            # Incrementa o dia
            data_atual += timedelta(days=1)


if __name__ == "__main__":
    main()
    print("Script finalizado")