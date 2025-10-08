import os
import sys
import winshell
from win32com.client import Dispatch

def _get_shortcut_path():
    """Retorna o caminho completo esperado para o atalho na pasta de inicialização."""
    startup_folder = winshell.startup()
    
    if getattr(sys, 'frozen', False):
        exe_name = os.path.basename(sys.executable)
        shortcut_name = os.path.splitext(exe_name)[0] + ".lnk"
    else:
        script_name = os.path.basename(sys.argv[0])
        shortcut_name = os.path.splitext(script_name)[0] + ".lnk"

    return os.path.join(startup_folder, shortcut_name)

def create_startup_shortcut():
    """
    Cria um atalho para a aplicação na pasta de inicialização do Windows, se não existir.
    """
    shortcut_path = _get_shortcut_path()
    if os.path.exists(shortcut_path):
        print("Atalho de inicialização já existe.")
        return

    print(f"Criando atalho em: {shortcut_path}")
    
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(shortcut_path)
    
    target_path = sys.executable
    work_dir = os.path.dirname(os.path.abspath(sys.argv[0])) if not getattr(sys, 'frozen', False) else os.path.dirname(target_path)
    icon_path = os.path.join(work_dir, "assets", "icon.ico")

    shortcut.Targetpath = target_path
    if not getattr(sys, 'frozen', False):
        shortcut.Arguments = f'"{os.path.abspath(sys.argv[0])}"'
    
    shortcut.WorkingDirectory = work_dir
    if os.path.exists(icon_path):
        shortcut.IconLocation = icon_path
    
    shortcut.save()
    print("Atalho de inicialização criado com sucesso.")

def remove_startup_shortcut():
    """Remove o atalho da pasta de inicialização, se existir."""
    shortcut_path = _get_shortcut_path()
    if os.path.exists(shortcut_path):
        print(f"Removendo atalho de inicialização: {shortcut_path}")
        os.remove(shortcut_path)
        print("Atalho de inicialização removido com sucesso.")
    else:
        print("Nenhum atalho de inicialização para remover.")

def is_startup_enabled():
    """Verifica se o atalho de inicialização existe."""
    return os.path.exists(_get_shortcut_path())