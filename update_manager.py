import requests
import subprocess
import os
from app_info import APP_NAME, UPDATE_URL

def check_for_updates():
    """
    Verifica no servidor (GitHub) se há uma nova versão disponível.
    
    Retorna:
        Um dicionário com 'version', 'url', 'changelog' e 'error'.
    """
    try:
        response = requests.get(UPDATE_URL, timeout=10)
        response.raise_for_status()
        
        lines = response.text.strip().splitlines()

        if len(lines) < 2:
            return {'error': "Formato do arquivo de versão inválido."}
            
        online_version = lines[0].strip()
        download_url = lines[1].strip()
        changelog = "\n".join(lines[2:]) if len(lines) > 2 else "Nenhuma nota de versão fornecida."
        
        return {
            'version': online_version,
            'url': download_url,
            'changelog': changelog,
            'error': None
        }

    except requests.exceptions.RequestException as e:
        print(f"Erro ao verificar atualizações: {e}")
        return {'error': f"Não foi possível conectar ao servidor de atualizações:\n{e}"}

def download_and_install(download_url):
    """
    Baixa o novo instalador a partir da URL, o executa e fecha a aplicação.
    """
    try:
        installer_filename = f"instalador_{APP_NAME.replace(' ', '_')}.exe"
        # Salva o instalador na pasta de Downloads do usuário
        download_path = os.path.join(os.path.expanduser('~'), 'Downloads', installer_filename)
        
        print(f"Baixando nova versão de {download_url}...")
        response = requests.get(download_url, stream=True)
        response.raise_for_status()

        with open(download_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Download completo. Executando {download_path}...")
        subprocess.Popen([download_path])
        
        # Encerra o processo do aplicativo atual para permitir a atualização
        os._exit(0)

    except Exception as e:
        print(f"Erro durante o download/instalação: {e}")
        # Retorna a mensagem de erro para ser exibida na UI
        return str(e)
    
    return None # Sucesso
