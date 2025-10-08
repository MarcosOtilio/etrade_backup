import sys
import os
import platform
import subprocess
import ctypes
import pyodbc

# Nomes exatos dos instaladores que devem estar na pasta 'drivers'
DRIVER_X64_MSI = "microsoftODBC-driver-18-x64.msi"
DRIVER_X86_MSI = "microsoftODBC-driver-18-x86.msi"

def is_admin():
    """Verifica se o script está rodando com privilégios de administrador."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """Relança o script com privilégios de administrador."""
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)

def is_driver_installed():
    """Verifica se alguma versão do driver ODBC para SQL Server está instalada."""
    try:
        drivers = [driver for driver in pyodbc.drivers() if 'sql server' in driver.lower()]
        return len(drivers) > 0
    except Exception:
        return False

def install_driver():
    """Instala o driver ODBC de acordo com a arquitetura do sistema."""
    if platform.machine().endswith('64'):
        installer_name = DRIVER_X64_MSI
    else:
        installer_name = DRIVER_X86_MSI
    
    # Determina o caminho base (funciona tanto em dev quanto no .exe compilado)
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    installer_path = os.path.join(base_path, 'drivers', installer_name)

    if not os.path.exists(installer_path):
        ctypes.windll.user32.MessageBoxW(0, f"Instalador não encontrado em: {installer_path}\nPor favor, garanta que o arquivo está na pasta 'drivers'.", "Erro de Instalação", 0x10)
        return False

    print(f"Instalando {installer_name}...")
    # Comando para instalação silenciosa
    command = ['msiexec', '/i', installer_path, '/quiet', '/qn', '/norestart']
    
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        print("Instalação do driver concluída com sucesso.")
        ctypes.windll.user32.MessageBoxW(0, "O driver ODBC foi instalado com sucesso. A aplicação será reiniciada para aplicar as alterações.", "Instalação Concluída", 0x40)
        # Reinicia a aplicação para garantir que o novo driver seja reconhecido
        os.execv(sys.executable, ['python'] + sys.argv)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        error_msg = f"Ocorreu um erro ao instalar o driver: {e}\n\nPor favor, instale o 'Microsoft ODBC Driver 18 for SQL Server' manualmente."
        ctypes.windll.user32.MessageBoxW(0, error_msg, "Erro de Instalação", 0x10)
        return False

def check_and_install_driver():
    """Função principal que gerencia a verificação e instalação."""
    if is_driver_installed():
        print("Driver ODBC para SQL Server já está instalado.")
        return

    print("Driver ODBC para SQL Server não encontrado.")
    
    if is_admin():
        install_driver()
        # Se a instalação falhar, o programa continuará, mas a função `install_driver` já notifica o usuário.
    else:
        print("Privilégios de administrador necessários. Tentando relançar a aplicação...")
        ctypes.windll.user32.MessageBoxW(0, "O driver ODBC necessário não está instalado. A aplicação precisa de permissão de administrador para instalá-lo.", "Permissão Necessária", 0x40)
        run_as_admin()
        sys.exit(0) # Fecha a instância atual sem privilégios
