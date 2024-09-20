from utils.handlefiles import delete_file, delete_folder, save_to_file
from utils.mongosubprocessutils import mongorestore, restore_global_files
from utils.mongoutils import connect_to_mongo, find_admin_emails, update_passwords
from utils.ziputils import unzip_file


def process_mongo_restore_routine(
    db_name: str,
    full_zip_path: str,
    host: str,
    port: str,
    backup_folder: str,
    new_password_hash: str,
    zip_filename: str,
) -> None:
    try:
        restore_global_files(backup_folder, db_name)
        decompresed_folder = unzip_file(backup_folder, zip_filename, full_zip_path)
        mongorestore(db_name, decompresed_folder)
        delete_folder(decompresed_folder)
        print(f"Banco de dados restaurado: {db_name} de {zip_filename}")
        db = connect_to_mongo(host, port, db_name)
        updated_count = update_passwords(db, new_password_hash)
        print(f"Senhas atualizadas para 123456 em todos os {updated_count} registros")
        admin_emails = find_admin_emails(db)
        emails_content = "\n".join(admin_emails)
        print("Emails de administrador do Cliente:")
        print(emails_content)
        save_to_file(backup_folder, db_name, emails_content)
        delete_file(full_zip_path)
        print("Base restaurada")
    except Exception as ex:
        print(f"Ocorreu um erro {ex}")
