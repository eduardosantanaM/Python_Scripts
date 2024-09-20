import os
import shutil
import subprocess

from utils.ziputils import unzip_file


def mongorestore(db_name: str, dump_path: str) -> None:
    subprocess.run(["mongorestore", "--db", db_name, dump_path])


def restore_global_files(backup_folder: str, database_name: str) -> None:
    global_folder = os.path.join(backup_folder, "_global")
    global_zip = os.path.join(backup_folder, "_global.zip")
    zip_folder = os.path.join(backup_folder, "zip")

    os.makedirs(zip_folder, exist_ok=True)

    if os.path.isdir(global_folder):
        print("Restaurando arquivos do diretório _global...")
        subprocess.run(
            [
                "mongorestore",
                "--quiet",
                "-d",
                database_name,
                os.path.join(global_folder),
            ]
        )
        print("Arquivos globais restaurados.")
    elif os.path.isfile(global_zip):
        print("Restaurando arquivos de _global.zip...")
        unzip_file(zip_folder, "global.zip", global_zip)
        subprocess.run(
            [
                "mongorestore",
                "--quiet",
                "-d",
                database_name,
                os.path.join(global_folder),
            ]
        )
        shutil.move(global_zip, zip_folder)
        print("Arquivos globais restaurados.")
    else:
        print("Nenhum _global encontrado.")
