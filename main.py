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
from startup import create_startup_shortcut
import driver_installer

def main():
    driver_installer.check_and_install_driver()
    
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    config_manager = ConfigManager()
    config = config_manager.load_config()
    
    backup_logic = BackupLogic(config)
    
    # 1. Instância do agendador criada aqui
    scheduler = Scheduler(backup_logic, config.get('schedules', []))
    
    # 2. Agendador é passado para a janela principal
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
    
    main_window.show()
    create_startup_shortcut()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()

