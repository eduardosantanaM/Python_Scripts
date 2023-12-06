import os
import shutil
import zipfile


def find_zip_files(folder: str) -> []:
    return [f for f in os.listdir(folder) if f.endswith('.zip')]

def unzip_file(folder: str, zip_file_name: str, zip_file_path: str) -> str:
    base_name : str = os.path.basename(zip_file_name)
    extract_folder_name = base_name.replace('.zip', '')
    extract_path = os.path.join(folder, extract_folder_name)

    if not os.path.exists(extract_path):
        os.makedirs(extract_path)

    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)

    return extract_path


def copy_to_restored_zips(stored_zips_folder, zip_file_path, zip_file_name):
    target_path = os.path.join(stored_zips_folder, zip_file_name)
    if not os.path.exists(stored_zips_folder):
        os.makedirs(stored_zips_folder)
    if (os.path.exists(target_path)): 
        print("Diretorio ja existe")
    else:
        shutil.copy(zip_file_path, stored_zips_folder)
        print(f"Diretorio copiado para {target_path}")