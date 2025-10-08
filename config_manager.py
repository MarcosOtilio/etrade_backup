import json
import os

class ConfigManager:
    """
    Gerencia a leitura e escrita de arquivos de configuração, incluindo o ArqID.txt inicial.
    Salva o config.json na pasta de dados do aplicativo do usuário (%APPDATA%).
    """
    def __init__(self, arq_id_path=r'C:\ETrade\ArqID.txt'):
        # --- LÓGICA ATUALIZADA PARA USAR A PASTA APPDATA ---
        # 1. Encontra a pasta Roaming AppData (ex: C:\Users\Leo\AppData\Roaming)
        app_data_path = os.getenv('APPDATA')
        if not app_data_path:
             # Fallback para a pasta do usuário se APPDATA não for encontrada
            app_data_path = os.path.expanduser('~')
            
        # 2. Define o caminho para a pasta específica da nossa aplicação
        self.config_dir = os.path.join(app_data_path, 'ETradeBackup')
        
        # 3. Garante que essa pasta exista
        os.makedirs(self.config_dir, exist_ok=True)
        
        # 4. Define o caminho completo para o arquivo de configuração
        self.config_path = os.path.join(self.config_dir, 'config.json')
        # --- FIM DA LÓGICA ATUALIZADA ---
        
        self.arq_id_path = arq_id_path
        self.config = {}

    # O restante do arquivo (get_default_config, load_config, etc.) permanece exatamente o mesmo.
    # Nenhuma outra alteração é necessária no resto do arquivo.

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
            "theme": "dark"
        }

    def load_initial_config_from_arqid(self):
        """
        Tenta ler as configurações iniciais do ArqID.txt.
        Retorna um dicionário com os dados ou None se o arquivo não for encontrado.
        """
        try:
            with open(self.arq_id_path, 'r') as f:
                content = f.read().replace('}\n', '}')
                data = json.loads(content)
                
                return {
                    "server": data.get("DataSource", ""),
                    "user": data.get("User", "sa"),
                    "password": data.get("Password", "")
                }
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            print(f"Não foi possível ler ou parsear o arquivo {self.arq_id_path}: {e}")
            return None

    def _merge_configs(self, loaded_config, default_config):
        """Garante que todas as chaves do default existam no config carregado."""
        for key, value in default_config.items():
            if key not in loaded_config:
                loaded_config[key] = value
            elif isinstance(value, dict):
                self._merge_configs(loaded_config[key], value)
        return loaded_config

    def load_config(self):
        """
        Carrega a configuração do config.json. Se não existir, cria um novo
        a partir do ArqID.txt ou de padrões. Garante que novas chaves sejam adicionadas.
        """
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)
                # Garante que novas configurações sejam adicionadas se o arquivo for antigo
                self.config = self._merge_configs(loaded_config, self.get_default_config())
                self.save_config(self.config) # Salva para persistir as novas chaves
                return self.config
            except (json.JSONDecodeError, TypeError):
                print(f"Erro ao ler {self.config_path}. Recriando com base nos padrões.")
                self.config = self.get_default_config()
                self.save_config(self.config)
        else:
            print(f"{self.config_path} não encontrado. Criando um novo arquivo de configuração.")
            self.config = self.get_default_config()
            initial_sql = self.load_initial_config_from_arqid()
            
            if initial_sql:
                print("Configuração inicial importada de ArqID.txt")
                self.config['sql_server']['server'] = initial_sql['server']
                self.config['sql_server']['user'] = initial_sql['user']
                self.config['sql_server']['password'] = initial_sql['password']
            
            self.save_config(self.config)
        
        return self.config

    def save_config(self, config_data):
        """Salva o dicionário de configuração fornecido no arquivo config.json."""
        self.config = config_data
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=4)

    def get_config(self):
        """Retorna a configuração atualmente carregada."""
        return self.config