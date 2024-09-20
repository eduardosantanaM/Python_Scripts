from concurrent.futures import ThreadPoolExecutor
import os
import time
import argparse
from mongorestore import process_mongo_restore_routine
from utils.ziputils import copy_to_restored_zips, find_zip_files

host = "localhost"
port = "27017"
new_password_hash = "GgqqqT4NrRKG78sJ+rJmH3AhfTk="

parser = argparse.ArgumentParser(description="Diretorios de backup")
parser.add_argument("bk_folder", type=str, help="Pasta temporaria dos zips")
parser.add_argument(
    "stored_zips",
    type=str,
    help="Pasta permanente dos zips (os zips serao salvos aqui)",
)

args = parser.parse_args()
backup_folder: str = args.bk_folder
stored_zips_folder: str = args.stored_zips
if not backup_folder or not stored_zips_folder:
    print("É necessário passar como argumento o caminho do backup")
    exit(-1)


def extract_client_id(s: str):
    return s.split("-")[-1].replace(".zip", "")


def main():
    while True:
        print("Procurando arquivos zip...")
        zip_files = find_zip_files(backup_folder)
        with ThreadPoolExecutor(max_workers=3) as executor:
            for zip_file in zip_files:
                if zip_file == "_global.zip":
                    continue
                response = input(f"Voce quer restaurar {zip_file}? (s/n): ").lower()
                if response.lower() == "s":
                    full_zip_path = os.path.join(backup_folder, zip_file)
                    store_response = input(
                        f"Voce quer guardar o arquivo {zip_file} em {stored_zips_folder} folder? (s/n): "
                    ).lower()
                    if store_response.lower() == "s":
                        copy_to_restored_zips(
                            stored_zips_folder, full_zip_path, zip_file
                        )
                    db_name = input(f"Qual será o nome do banco de dados? ").lower()
                    executor.submit(
                        process_mongo_restore_routine,
                        db_name,
                        full_zip_path,
                        host,
                        port,
                        backup_folder,
                        new_password_hash,
                        zip_file,
                    )

        time.sleep(10)


if __name__ == "__main__":
    main()
