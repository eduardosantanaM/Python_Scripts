import os
import shutil


def delete_folder(folder_name: str):
    try:
        shutil.rmtree(folder_name)
    except Exception as e:
        print(f"Erro ao deletar diretorio: {e}")

def delete_file(file_name: str):
    try:
        os.remove(file_name)
    except Exception as e:
        print(f"Erro ao deletar arquivo: {e}")


def save_to_file(folder: str, database_name: str, content: str):
    filepath = f"{folder}/{database_name}.txt"

    if os.path.exists(filepath):
        print(f"Arquivo ja existe '{filepath}' será sobrescrito.")

    try:
        with open(filepath, "w") as file:
            file.write(content)
        print(f"Conteudo salvo em '{filepath}'.")
    except Exception as e:
        print(f"Ocorreu um erro ao escrever o arquivo: {e}")