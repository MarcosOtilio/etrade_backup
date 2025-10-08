import pyodbc
import os
from datetime import datetime, timedelta
import zipfile
import shutil
import tempfile

class BackupLogic:
    def __init__(self, config):
        self.config = config

    def _get_driver(self):
        drivers = [driver for driver in pyodbc.drivers() if 'sql server' in driver.lower()]
        return sorted(drivers, reverse=True)[0] if drivers else None

    def test_connection(self, server, user, password):
        """Tenta estabelecer uma conexão com as credenciais fornecidas."""
        driver = self._get_driver()
        if not driver:
            return False, "Nenhum driver ODBC para SQL Server foi encontrado no sistema."
        try:
            conn_str = (f"DRIVER={{{driver}}};SERVER={server};DATABASE=master;"
                        f"UID={user};PWD={password};TrustServerCertificate=yes;Encrypt=yes;")
            # Define um timeout curto para o teste de conexão
            pyodbc.connect(conn_str, timeout=5)
            return True, "Conexão bem-sucedida!"
        except pyodbc.Error as e:
            return False, f"Falha na conexão: {e}"

    # O resto do arquivo (perform_backup, perform_restore, etc.) permanece o mesmo.
    def _get_connection(self, master_db=False):
        driver = self._get_driver()
        if not driver: return None
        sql_config = self.config['sql_server']
        db_name = "master" if master_db else self.config['backup_settings']['db_name']
        try:
            conn_str = (f"DRIVER={{{driver}}};SERVER={sql_config['server']};DATABASE={db_name};"
                        f"UID={sql_config['user']};PWD={sql_config['password']};TrustServerCertificate=yes;Encrypt=yes;")
            return pyodbc.connect(conn_str)
        except pyodbc.Error as ex:
            print(f"Erro de conexão com o banco de dados: {ex.args[0]}")
            return None
    def perform_backup(self):
        conn = self._get_connection()
        if not conn: return False, "Falha ao conectar: Verifique as credenciais e o driver."
        conn.autocommit = True
        backup_settings = self.config['backup_settings']
        db_name, backup_dir = backup_settings['db_name'], backup_settings['path']
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        bak_filename = f"{db_name}_{timestamp}.bak"
        bak_filepath = os.path.join(backup_dir, bak_filename)
        sql = f"BACKUP DATABASE [{db_name}] TO DISK = N'{bak_filepath}' WITH NOFORMAT, NOINIT, NAME = N'{db_name}-Full Database Backup', SKIP, NOREWIND, NOUNLOAD, STATS = 10"
        try:
            print(f"Iniciando backup para {bak_filepath}...")
            cursor = conn.cursor()
            cursor.execute(sql)
            while cursor.nextset(): pass
            cursor.close()
            conn.close()
            print("Backup do banco de dados concluído com sucesso.")
            final_path = bak_filepath
            if backup_settings.get('compress_backup', False):
                zip_filepath = os.path.join(backup_dir, f"{db_name}_{timestamp}.zip")
                with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf: zipf.write(bak_filepath, bak_filename)
                os.remove(bak_filepath)
                final_path = zip_filepath
            for secondary_path in backup_settings.get('secondary_paths', []):
                if os.path.isdir(secondary_path): shutil.copy2(final_path, secondary_path)
            self.cleanup_old_backups()
            return True, f"Backup concluído com sucesso em {final_path}"
        except Exception as e:
            if conn: conn.close()
            return False, f"Erro durante o backup: {e}"
    def perform_restore(self, backup_file_path):
        db_name, bak_file_to_restore, temp_dir, conn = self.config['backup_settings']['db_name'], "", None, None
        try:
            if backup_file_path.lower().endswith('.zip'):
                temp_dir = tempfile.mkdtemp(prefix="etrade_restore_")
                with zipfile.ZipFile(backup_file_path, 'r') as zip_ref:
                    bak_files = [f for f in zip_ref.namelist() if f.lower().endswith('.bak')]
                    if not bak_files: return False, "Nenhum arquivo .bak encontrado dentro do arquivo .zip."
                    zip_ref.extract(bak_files[0], temp_dir)
                    bak_file_to_restore = os.path.join(temp_dir, bak_files[0])
            elif backup_file_path.lower().endswith('.bak'): bak_file_to_restore = backup_file_path
            else: return False, "Tipo de arquivo inválido. Selecione um arquivo .bak ou .zip."
            conn = self._get_connection(master_db=True)
            if not conn: return False, "Não foi possível conectar ao banco de dados 'master' para a restauração."
            conn.autocommit = True
            cursor = conn.cursor()
            cursor.execute(f"ALTER DATABASE [{db_name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE")
            cursor.execute(f"RESTORE DATABASE [{db_name}] FROM DISK = ? WITH REPLACE", bak_file_to_restore)
            cursor.execute(f"ALTER DATABASE [{db_name}] SET MULTI_USER")
            cursor.close()
            conn.close()
            return True, f"Banco de dados '{db_name}' restaurado com sucesso!"
        except Exception as e:
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute(f"ALTER DATABASE [{db_name}] SET MULTI_USER")
                    cursor.close()
                    conn.close()
                except Exception as inner_e: print(f"Não foi possível reverter para multi-usuário: {inner_e}")
            return False, f"Falha na restauração: {e}"
        finally:
            if temp_dir and os.path.exists(temp_dir): shutil.rmtree(temp_dir)
    def update_config(self, new_config):
        self.config = new_config
    def cleanup_old_backups(self):
        backup_settings = self.config['backup_settings']
        backup_dir, retention_days = backup_settings['path'], backup_settings['retention_days']
        if not os.path.isdir(backup_dir): return
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        for filename in os.listdir(backup_dir):
            if filename.lower().endswith(('.bak', '.zip')):
                file_path = os.path.join(backup_dir, filename)
                if datetime.fromtimestamp(os.path.getmtime(file_path)) < cutoff_date:
                    os.remove(file_path)