import sys
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon
import schedule
import threading
import time

from ui import MainWindow
from config_manager import ConfigManager
from backup_logic import BackupLogic
from scheduler import Scheduler
import startup # Import alterado
import driver_installer

def main():
    driver_installer.check_and_install_driver()
    
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    config_manager = ConfigManager()
    config = config_manager.load_config()
    
    backup_logic = BackupLogic(config)
    scheduler = Scheduler(backup_logic, config.get('schedules', []))
    main_window = MainWindow(config_manager, backup_logic, scheduler)
    
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(1)

    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

    tray_icon = QSystemTrayIcon(QIcon("assets/icon.ico"), parent=app)
    tray_icon.setToolTip("ETrade Backup")
    
    menu = QMenu()
    open_action = menu.addAction("Abrir Configurações")
    open_action.triggered.connect(main_window.show_normal)
    
    quit_action = menu.addAction("Sair")
    quit_action.triggered.connect(app.quit)
    
    tray_icon.setContextMenu(menu)
    tray_icon.show()
    
    # --- LÓGICA DE INICIALIZAÇÃO MINIMIZADA ---
    startup_settings = config.get('startup_settings', {})
    if not startup_settings.get('start_minimized', False):
        main_window.show()
    # --- FIM DA LÓGICA ---
    
    # Garante que o atalho esteja em conformidade com a configuração
    if startup_settings.get('auto_start_enabled', True):
        startup.create_startup_shortcut()
    else:
        startup.remove_startup_shortcut()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()