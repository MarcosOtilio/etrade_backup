import pyodbc
import os
from datetime import datetime, timedelta
import zipfile
import shutil
import tempfile

class BackupLogic:
    def __init__(self, config):
        self.config = config
        self.connection_string_template = (
            "DRIVER={{{driver}}};"
            "SERVER={server};"
            "DATABASE={database};"
            "UID={user};"
            "PWD={password};"
            "TrustServerCertificate=yes;"
            "Encrypt=yes;"
        )

    def _get_driver(self):
        drivers = [driver for driver in pyodbc.drivers() if 'sql server' in driver.lower()]
        if not drivers:
            return None
        return sorted(drivers, reverse=True)[0]

    def _get_connection(self, master_db=False):
        driver = self._get_driver()
        if not driver:
            print("Nenhum driver ODBC para SQL Server encontrado.")
            return None
        
        sql_config = self.config['sql_server']
        db_name = "master" if master_db else self.config['backup_settings']['db_name']
        
        try:
            conn_str = self.connection_string_template.format(
                driver=driver,
                server=sql_config['server'],
                database=db_name,
                user=sql_config['user'],
                password=sql_config['password']
            )
            return pyodbc.connect(conn_str)
        except pyodbc.Error as ex:
            sqlstate = ex.args[0]
            print(f"Erro de conexão com o banco de dados: {sqlstate}")
            return None

    def perform_backup(self):
        # ... (código existente - sem alterações)
        conn = self._get_connection()
        if not conn:
            return False, "Falha ao conectar: Verifique as credenciais e o driver."

        backup_settings = self.config['backup_settings']
        db_name = backup_settings['db_name']
        backup_dir = backup_settings['path']
        
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        bak_filename = f"{db_name}_{timestamp}.bak"
        bak_filepath = os.path.join(backup_dir, bak_filename)
        
        sql = f"BACKUP DATABASE [{db_name}] TO DISK = N'{bak_filepath}' WITH NOFORMAT, NOINIT, NAME = N'{db_name}-Full Database Backup', SKIP, NOREWIND, NOUNLOAD, STATS = 10"
        
        try:
            print(f"Iniciando backup para {bak_filepath}...")
            cursor = conn.cursor()
            cursor.execute(sql)
            while cursor.nextset():
                pass
            cursor.close()
            conn.close()
            print("Backup do banco de dados concluído com sucesso.")

            # Compactação e cópias
            final_path = bak_filepath
            if backup_settings.get('compress_backup', False):
                zip_filepath = os.path.join(backup_dir, f"{db_name}_{timestamp}.zip")
                print(f"Compactando backup para {zip_filepath}...")
                with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(bak_filepath, bak_filename)
                os.remove(bak_filepath) # Remove o .bak original
                final_path = zip_filepath
                print("Compactação concluída.")
            
            for secondary_path in backup_settings.get('secondary_paths', []):
                if os.path.isdir(secondary_path):
                    print(f"Copiando backup para {secondary_path}")
                    shutil.copy2(final_path, secondary_path)

            self.cleanup_old_backups()
            return True, f"Backup concluído com sucesso em {final_path}"
        except Exception as e:
            return False, f"Erro durante o backup: {e}"

    def perform_restore(self, backup_file_path):
        """
        Restaura um banco de dados a partir de um arquivo .bak ou .zip.
        """
        db_name = self.config['backup_settings']['db_name']
        bak_file_to_restore = ""
        temp_dir = None
        conn = None

        try:
            if backup_file_path.lower().endswith('.zip'):
                print(f"Extraindo arquivo zip: {backup_file_path}")
                temp_dir = tempfile.mkdtemp(prefix="etrade_restore_")
                with zipfile.ZipFile(backup_file_path, 'r') as zip_ref:
                    bak_files = [f for f in zip_ref.namelist() if f.lower().endswith('.bak')]
                    if not bak_files:
                        return False, "Nenhum arquivo .bak encontrado dentro do arquivo .zip."
                    
                    zip_ref.extract(bak_files[0], temp_dir)
                    bak_file_to_restore = os.path.join(temp_dir, bak_files[0])
            elif backup_file_path.lower().endswith('.bak'):
                bak_file_to_restore = backup_file_path
            else:
                return False, "Tipo de arquivo inválido. Selecione um arquivo .bak ou .zip."

            conn = self._get_connection(master_db=True)
            if not conn:
                return False, "Não foi possível conectar ao banco de dados 'master' para a restauração."
            
            conn.autocommit = True
            cursor = conn.cursor()

            print(f"Iniciando restauração de '{db_name}'...")
            
            cursor.execute(f"ALTER DATABASE [{db_name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE")
            print(f"Executando RESTORE a partir de: {bak_file_to_restore}")
            cursor.execute(f"RESTORE DATABASE [{db_name}] FROM DISK = ? WITH REPLACE", bak_file_to_restore)
            cursor.execute(f"ALTER DATABASE [{db_name}] SET MULTI_USER")

            cursor.close()
            conn.close()
            
            return True, f"Banco de dados '{db_name}' restaurado com sucesso!"

        except Exception as e:
            # Tentar reverter para MULTI_USER em caso de falha
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute(f"ALTER DATABASE [{db_name}] SET MULTI_USER")
                    cursor.close()
                    conn.close()
                except Exception as inner_e:
                    print(f"Não foi possível reverter para multi-usuário: {inner_e}")
            return False, f"Falha na restauração: {e}"
        
        finally:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def update_config(self, new_config):
        self.config = new_config

    def cleanup_old_backups(self):
        # ... (código existente - sem alterações)
        backup_settings = self.config['backup_settings']
        backup_dir = backup_settings['path']
        retention_days = backup_settings['retention_days']
        if not os.path.isdir(backup_dir): return

        cutoff_date = datetime.now() - timedelta(days=retention_days)
        for filename in os.listdir(backup_dir):
            if filename.lower().endswith(('.bak', '.zip')):
                file_path = os.path.join(backup_dir, filename)
                file_mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                if file_mod_time < cutoff_date:
                    print(f"Removendo backup antigo: {filename}")
                    os.remove(file_path)

