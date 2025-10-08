import os
import sys
import winshell
from win32com.client import Dispatch

def create_startup_shortcut():
    """
    Cria um atalho para a aplicação na pasta de inicialização do Windows.
    """
    startup_folder = winshell.startup()
    
    # O nome do executável geralmente é o nome do script principal sem a extensão .py
    # Em um ambiente compilado (PyInstaller), sys.executable é o caminho para o .exe
    if getattr(sys, 'frozen', False):
        exe_path = sys.executable
        exe_name = os.path.basename(exe_path)
        shortcut_name = os.path.splitext(exe_name)[0] + ".lnk"
    else:
        # Em modo de desenvolvimento, aponta para o interpretador python e o script
        # Isso é menos ideal, mas funciona para testes.
        exe_path = sys.executable
        script_path = os.path.abspath(sys.argv[0])
        shortcut_name = os.path.splitext(os.path.basename(script_path))[0] + ".lnk"

    shortcut_path = os.path.join(startup_folder, shortcut_name)

    if os.path.exists(shortcut_path):
        print("Atalho de inicialização já existe.")
        return

    print(f"Criando atalho em: {shortcut_path}")
    
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(shortcut_path)
    
    shortcut.Targetpath = exe_path
    if not getattr(sys, 'frozen', False):
        shortcut.Arguments = f'"{script_path}"' # Adiciona o script como argumento se não for um .exe
    
    shortcut.WorkingDirectory = os.path.dirname(os.path.abspath(sys.argv[0]))
    shortcut.IconLocation = os.path.abspath("assets/icon.ico")
    shortcut.save()
    print("Atalho de inicialização criado com sucesso.")
