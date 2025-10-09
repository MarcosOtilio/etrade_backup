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
import startup
import driver_installer
from utils import resource_path # Novo import

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

    # --- CORREÇÃO AQUI ---
    # Usamos resource_path para encontrar o ícone
    icon_path = resource_path("assets/icon.ico")
    tray_icon = QSystemTrayIcon(QIcon(icon_path), parent=app)
    # --- FIM DA CORREÇÃO ---
    
    tray_icon.setToolTip("ETrade Backup")
    
    menu = QMenu()
    open_action = menu.addAction("Abrir Configurações")
    open_action.triggered.connect(main_window.show_normal)
    
    quit_action = menu.addAction("Sair")
    quit_action.triggered.connect(app.quit)
    
    tray_icon.setContextMenu(menu)
    tray_icon.show()
    
    startup_settings = config.get('startup_settings', {})
    if not startup_settings.get('start_minimized', False):
        main_window.show()
    
    if startup_settings.get('auto_start_enabled', True):
        startup.create_startup_shortcut()
    else:
        startup.remove_startup_shortcut()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()