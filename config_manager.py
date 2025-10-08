import json
import os

class ConfigManager:
    def __init__(self, arq_id_path=r'C:\ETrade\ArqID.txt'):
        app_data_path = os.getenv('APPDATA')
        if not app_data_path:
            app_data_path = os.path.expanduser('~')
        self.config_dir = os.path.join(app_data_path, 'ETradeBackup')
        os.makedirs(self.config_dir, exist_ok=True)
        self.config_path = os.path.join(self.config_dir, 'config.json')
        self.arq_id_path = arq_id_path
        self.config = {}

    def get_default_config(self):
        """Retorna uma estrutura de configuração padrão."""
        return {
            "sql_server": {
                "server": "localhost\\SQL2014",
                "user": "sa",
                "password": ""
            },
            "backup_settings": {
                "db_name": "etrade",
                "path": r"C:\ETrade\Backup",
                "retention_days": 10,
                "compress_backup": True,
                "secondary_paths": []
            },
            "schedules": ["17:00"],
            "theme": "dark",
            # --- NOVAS OPÇÕES ---
            "startup_settings": {
                "auto_start_enabled": True,
                "start_minimized": False
            }
        }

    # O resto do arquivo (load_config, save_config, etc.) permanece o mesmo.
    def load_initial_config_from_arqid(self):
        try:
            with open(self.arq_id_path, 'r') as f:
                content = f.read().replace('}\n', '}')
                data = json.loads(content)
                return { "server": data.get("DataSource", ""), "user": data.get("User", "sa"), "password": data.get("Password", "") }
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            print(f"Não foi possível ler ou parsear o arquivo {self.arq_id_path}: {e}")
            return None

    def _merge_configs(self, loaded_config, default_config):
        for key, value in default_config.items():
            if key not in loaded_config:
                loaded_config[key] = value
            elif isinstance(value, dict):
                self._merge_configs(loaded_config.get(key, {}), value)
        return loaded_config

    def load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)
                self.config = self._merge_configs(loaded_config, self.get_default_config())
                self.save_config(self.config)
                return self.config
            except (json.JSONDecodeError, TypeError):
                self.config = self.get_default_config()
                self.save_config(self.config)
        else:
            self.config = self.get_default_config()
            initial_sql = self.load_initial_config_from_arqid()
            if initial_sql:
                self.config['sql_server']['server'] = initial_sql['server']
                self.config['sql_server']['user'] = initial_sql['user']
                self.config['sql_server']['password'] = initial_sql['password']
            self.save_config(self.config)
        return self.config

    def save_config(self, config_data):
        self.config = config_data
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=4)

    def get_config(self):
        return self.config