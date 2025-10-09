import sys
import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QListWidget, QListWidgetItem,
                             QTimeEdit, QMessageBox, QTextEdit, QFrame, QCheckBox,
                             QFileDialog, QDialog, QDialogButtonBox)
from PyQt6.QtCore import Qt, QTime, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QMovie

# Módulos do projeto
from app_info import APP_NAME, CURRENT_VERSION
import update_manager
from config_manager import ConfigManager
from backup_logic import BackupLogic
from scheduler import Scheduler
import startup # Módulo de inicialização
from styles import get_stylesheet
from utils import resource_path

# --- Classes de Diálogo (Sobre, Atualização, Restauração) ---
class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Sobre o {APP_NAME}")
        self.setWindowIcon(QIcon("assets/icon.png"))
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(10)
        title = QLabel(f"{APP_NAME} v{CURRENT_VERSION}")
        title.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(title)
        description = QLabel("Aplicativo para automação de backups de bancos de dados SQL Server.\nDesenvolvido para garantir a segurança dos seus dados.")
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(description)
        credits_widget = QWidget()
        credits_layout = QHBoxLayout(credits_widget)
        credits_layout.setContentsMargins(0,0,0,0)
        credits_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        credits_label = QLabel("Desenvolvido por: Marcos Otílio |")
        credits_label.setStyleSheet("font-size: 9pt;")
        repo_link = 'hhttps://github.com/MarcosOtilio'
        repo_label = QLabel(f'<a href="{repo_link}">Repositório no GitHub</a>')
        repo_label.setOpenExternalLinks(True)
        repo_label.setStyleSheet("font-size: 9pt;")
        credits_layout.addWidget(credits_label)
        credits_layout.addWidget(repo_label)
        layout.addWidget(credits_widget)
        donation_label = QLabel("Gostou do projeto? Considere fazer uma doação via PIX!")
        donation_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(donation_label)
        qr_code_label = QLabel()
        qr_code_path = "assets/pix_qrcode.png"
        if os.path.exists(qr_code_path):
            pixmap = QPixmap(qr_code_path)
            qr_code_label.setPixmap(pixmap.scaled(180, 180, Qt.AspectRatioMode.KeepAspectRatio))
        else:
            qr_code_label.setText("QR Code não encontrado em\nassets/pix_qrcode.png")
        qr_code_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(qr_code_label)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

class UpdateCheckThread(QThread):
    result_ready = pyqtSignal(dict)
    def run(self):
        self.result_ready.emit(update_manager.check_for_updates())

class UpdateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.download_url = None
        self.setWindowTitle("Verificador de Atualizações")
        self.setMinimumSize(450, 400)
        self.layout = QVBoxLayout(self)
        self.status_label = QLabel("Verificando atualizações...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.status_label)
        self.loading_label = QLabel(alignment=Qt.AlignmentFlag.AlignCenter)
        loading_gif_path = resource_path("assets/loading.gif")
        if os.path.exists(loading_gif_path):
            self.movie = QMovie(loading_gif_path)
            self.loading_label.setMovie(self.movie)
            self.movie.start()
        self.layout.addWidget(self.loading_label)
        self.layout.addWidget(QLabel("Notas da Versão:"))
        self.changelog_text = QTextEdit(readOnly=True)
        self.layout.addWidget(self.changelog_text)
        self.update_button = QPushButton("Atualizar Agora", clicked=self.run_update, enabled=False)
        self.layout.addWidget(self.update_button)
        self.start_check()
    def start_check(self):
        self.update_thread = UpdateCheckThread()
        self.update_thread.result_ready.connect(self.on_check_finished)
        self.update_thread.start()
    def on_check_finished(self, result):
        self.loading_label.hide()
        if error := result.get('error'):
            self.status_label.setText(f"<b style='color:red;'>{error}</b>")
            return
        online_version, self.download_url = result['version'], result['url']
        self.changelog_text.setText(result['changelog'])
        if online_version > CURRENT_VERSION:
            self.status_label.setText(f"<b>Nova versão disponível!</b> (Sua: {CURRENT_VERSION} | Nova: {online_version})")
            self.update_button.setEnabled(True)
        else:
            self.status_label.setText(f"Você já está na versão mais recente. (Versão: {CURRENT_VERSION})")
            self.update_button.setText("Atualizado")
    def run_update(self):
        if QMessageBox.question(self, "Confirmar", "O aplicativo será fechado para atualizar. Continuar?") == QMessageBox.StandardButton.Yes:
            self.update_button.setText("Baixando...")
            self.update_button.setEnabled(False)
            if error := update_manager.download_and_install(self.download_url):
                QMessageBox.critical(self, "Erro", f"Ocorreu um erro: {error}")
                self.update_button.setText("Atualizar Agora")
                self.update_button.setEnabled(True)

class RestoreThread(QThread):
    finished = pyqtSignal(bool, str)
    def __init__(self, backup_logic, file_path):
        super().__init__()
        self.backup_logic, self.file_path = backup_logic, file_path
    def run(self):
        self.finished.emit(*self.backup_logic.perform_restore(self.file_path))

class RestoreDialog(QDialog):
    def __init__(self, backup_logic, parent=None):
        super().__init__(parent)
        self.backup_logic = backup_logic
        self.file_path = ""
        self.setWindowTitle("Restaurar Backup")
        self.setMinimumSize(500, 250)
        layout = QVBoxLayout(self)
        file_layout = QHBoxLayout()
        self.path_label = QLineEdit("Nenhum arquivo selecionado...", readOnly=True)
        self.browse_button = QPushButton("Procurar...", clicked=self.select_file)
        file_layout.addWidget(self.path_label)
        file_layout.addWidget(self.browse_button)
        layout.addLayout(file_layout)
        self.status_log = QTextEdit(readOnly=True)
        self.status_log.setText("Selecione um arquivo de backup (.bak ou .zip) para restaurar.\n\nAVISO: Este processo irá SOBRESCREVER o banco de dados atual. Faça por sua conta e risco.")
        layout.addWidget(self.status_log)
        self.restore_button = QPushButton("Iniciar Restauração", clicked=self.run_restore, enabled=False)
        layout.addWidget(self.restore_button)
    def select_file(self):
        if file := QFileDialog.getOpenFileName(self, "Selecionar Backup", "", "Arquivos de Backup (*.bak *.zip)")[0]:
            self.file_path, self.path_label.setText(file), self.restore_button.setEnabled(True)
    def run_restore(self):
        if QMessageBox.warning(self, "Confirmação Crítica", "TEM CERTEZA?\nTODOS os dados atuais do banco serão PERDIDOS e substituídos.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) == QMessageBox.StandardButton.No: return
        self.restore_button.setEnabled(False)
        self.browse_button.setEnabled(False)
        self.restore_button.setText("Restaurando...")
        self.status_log.append("\nIniciando processo de restauração...")
        self.restore_thread = RestoreThread(self.backup_logic, self.file_path)
        self.restore_thread.finished.connect(self.on_restore_finished)
        self.restore_thread.start()
    def on_restore_finished(self, success, message):
        self.status_log.append(f"\nResultado: {message}")
        (QMessageBox.information if success else QMessageBox.critical)(self, "Restauração", message)
        self.restore_button.setText("Concluído" if success else "Falha na Restauração")
        self.browse_button.setEnabled(True)

class BackupThread(QThread):
    finished = pyqtSignal(str)
    def __init__(self, backup_logic):
        super().__init__()
        self.backup_logic = backup_logic
    def run(self):
        self.finished.emit(self.backup_logic.perform_backup()[1])

# --- JANELA PRINCIPAL ---
class MainWindow(QMainWindow):
    def __init__(self, config_manager: ConfigManager, backup_logic: BackupLogic, scheduler: Scheduler):
        super().__init__()
        self.config_manager, self.backup_logic, self.scheduler = config_manager, backup_logic, scheduler
        self.config = self.config_manager.get_config()
        self.current_theme = self.config.get('theme', 'dark')
        self.setWindowTitle(f"{APP_NAME} - Configurações")
        self.setWindowIcon(QIcon(resource_path("assets/icon.png")))
        self.setMinimumSize(850, 750) 
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setup_ui()
        self.load_settings()
        self.apply_theme()
        self.old_pos = self.pos()
    
    def setup_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.layout = QVBoxLayout(main_widget)
        self.layout.setContentsMargins(0,0,0,0)
        self.layout.setSpacing(0)
        
        self.title_bar = QFrame(objectName="titleBar", maximumHeight=40)
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(10,0,10,0)
        
        title_layout.addWidget(QLabel(pixmap=QIcon(resource_path("assets/icon.png")).pixmap(24, 24)))
        title_layout.addWidget(QLabel(APP_NAME, objectName="titleLabel"), alignment=Qt.AlignmentFlag.AlignLeft)
        title_layout.addStretch()
        for tooltip, icon_filename, callback in [
            ("Verificar Atualizações", "icon_update.png", self.show_update_dialog),
            (f"Sobre o {APP_NAME}", None, self.show_about_dialog),
            ("Minimizar", None, self.hide)
        ]:
            btn = QPushButton("?" if "Sobre" in tooltip else ("—" if "Minimizar" in tooltip else ""))
            if icon_filename:
                icon_path = resource_path(os.path.join("assets", icon_filename))
                if os.path.exists(icon_path):
                    btn.setIcon(QIcon(icon_path))
            btn.setObjectName("titleButton")
            btn.setFixedSize(30, 30)
            btn.setToolTip(tooltip)
            btn.clicked.connect(callback)
            title_layout.addWidget(btn)
        self.layout.addWidget(self.title_bar)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20,10,20,20)
        content_layout.setSpacing(10)
        self.layout.addWidget(content_widget)
        
        top_panel_layout = QHBoxLayout()
        
        left_column_widget = QWidget()
        left_layout = QVBoxLayout(left_column_widget)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        left_layout.addWidget(self.create_group_label("Configuração do Banco de Dados"))
        self.server_input = QLineEdit()
        left_layout.addWidget(self.create_form_row("Servidor:", self.server_input))
        self.user_input = QLineEdit()
        left_layout.addWidget(self.create_form_row("Usuário:", self.user_input))
        self.password_input = QLineEdit(echoMode=QLineEdit.EchoMode.Password)
        left_layout.addWidget(self.create_form_row("Senha:", self.password_input))
        self.test_conn_button = QPushButton("Testar Conexão", clicked=self.on_test_connection)
        left_layout.addWidget(self.test_conn_button)
        
        left_layout.addWidget(self.create_group_label("Opções de Backup e Inicialização"))
        self.compress_checkbox = QCheckBox("Compactar backup em formato .zip")
        left_layout.addWidget(self.compress_checkbox)
        self.start_minimized_checkbox = QCheckBox("Iniciar minimizado na bandeja do sistema")
        left_layout.addWidget(self.start_minimized_checkbox)
        
        startup_widget = QWidget()
        startup_layout = QHBoxLayout(startup_widget)
        startup_layout.setContentsMargins(0,0,0,0)
        self.toggle_startup_button = QPushButton("Gerenciar Inicialização Automática", clicked=self.toggle_auto_startup)
        self.startup_status_label = QLabel("Status: ...")
        startup_layout.addWidget(self.toggle_startup_button)
        startup_layout.addWidget(self.startup_status_label)
        left_layout.addWidget(startup_widget)

        right_column_widget = QWidget()
        right_layout = QVBoxLayout(right_column_widget)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        right_layout.addWidget(self.create_group_label("Agendamentos de Backup"))
        self.schedule_list = QListWidget(maximumHeight=120)
        right_layout.addWidget(self.schedule_list)
        schedule_add_layout = QHBoxLayout()
        self.new_time_input = QTimeEdit(displayFormat="HH:mm")
        schedule_add_layout.addWidget(self.new_time_input)
        schedule_add_layout.addWidget(QPushButton("Adicionar", clicked=self.add_schedule))
        schedule_add_layout.addWidget(QPushButton("Remover", clicked=self.remove_schedule))
        right_layout.addLayout(schedule_add_layout)
        
        right_layout.addWidget(self.create_group_label("Cópias de Segurança Adicionais"))
        self.secondary_path_list = QListWidget(maximumHeight=120)
        right_layout.addWidget(self.secondary_path_list)
        secondary_buttons_layout = QHBoxLayout()
        secondary_buttons_layout.addWidget(QPushButton("Adicionar...", clicked=self.add_secondary_path))
        secondary_buttons_layout.addWidget(QPushButton("Remover", clicked=self.remove_secondary_path))
        right_layout.addLayout(secondary_buttons_layout)
        
        top_panel_layout.addWidget(left_column_widget)
        top_panel_layout.addWidget(right_column_widget)
        content_layout.addLayout(top_panel_layout)

        content_layout.addWidget(self.create_group_label("Log de Atividades"))
        self.log_output = QTextEdit(readOnly=True)
        content_layout.addWidget(self.log_output)
        
        action_buttons_layout = QHBoxLayout()
        self.save_button = QPushButton("Salvar Configurações", clicked=self.save_settings)
        self.restore_button = QPushButton("Restaurar Backup", clicked=self.show_restore_dialog)
        self.backup_now_button = QPushButton("Fazer Backup Agora", clicked=self.run_manual_backup)
        self.theme_button = QPushButton("Alternar Tema", clicked=self.toggle_theme)
        for btn in [self.save_button, self.restore_button, self.backup_now_button, self.theme_button]:
            action_buttons_layout.addWidget(btn)
        content_layout.addLayout(action_buttons_layout)

    def create_form_row(self, label_text, widget):
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0,0,0,0)
        label = QLabel(label_text)
        label.setFixedWidth(80)
        layout.addWidget(label)
        layout.addWidget(widget)
        return row

    def on_test_connection(self):
        server, user, password = self.server_input.text(), self.user_input.text(), self.password_input.text()
        success, message = self.backup_logic.test_connection(server, user, password)
        (QMessageBox.information if success else QMessageBox.critical)(self, "Teste de Conexão", message)
    def toggle_auto_startup(self):
        (startup.remove_startup_shortcut if startup.is_startup_enabled() else startup.create_startup_shortcut)()
        self.update_startup_status_label()
        self.config['startup_settings']['auto_start_enabled'] = startup.is_startup_enabled()
        self.config_manager.save_config(self.config)
        self.log_output.append(f"Inicialização automática {'desativada' if not startup.is_startup_enabled() else 'ativada'}.")
    def update_startup_status_label(self):
        status, color = ("Ativado", "green") if startup.is_startup_enabled() else ("Desativado", "red")
        self.startup_status_label.setText(f"<b style='color:{color};'>Status: {status}</b>")
    def load_settings(self):
        sql = self.config['sql_server']
        backup = self.config['backup_settings']
        startup_cfg = self.config.get('startup_settings', {})
        self.server_input.setText(sql['server'])
        self.user_input.setText(sql['user'])
        self.password_input.setText(sql['password'])
        self.compress_checkbox.setChecked(backup.get('compress_backup', True))
        self.start_minimized_checkbox.setChecked(startup_cfg.get('start_minimized', False))
        self.update_schedule_list()
        self.update_secondary_path_list()
        self.update_startup_status_label()
        self.log_output.append("Configurações carregadas.")
    def save_settings(self):
        self.config['sql_server']['server'] = self.server_input.text()
        self.config['sql_server']['user'] = self.user_input.text()
        self.config['sql_server']['password'] = self.password_input.text()
        self.config['backup_settings']['compress_backup'] = self.compress_checkbox.isChecked()
        self.config['backup_settings']['secondary_paths'] = [self.secondary_path_list.item(i).text() for i in range(self.secondary_path_list.count())]
        schedules = [self.schedule_list.item(i).text() for i in range(self.schedule_list.count())]
        self.config['schedules'] = schedules
        self.config['theme'] = self.current_theme
        self.config['startup_settings'] = {
            'auto_start_enabled': startup.is_startup_enabled(),
            'start_minimized': self.start_minimized_checkbox.isChecked()
        }
        self.config_manager.save_config(self.config)
        self.backup_logic.update_config(self.config)
        self.scheduler.update_schedules(schedules)
        self.log_output.append("Configurações salvas e agendamentos atualizados.")
        QMessageBox.information(self, "Sucesso", "As configurações foram salvas.")
    def update_schedule_list(self):
        self.schedule_list.clear()
        self.schedule_list.addItems(self.config.get('schedules', []))
    def add_schedule(self):
        new_time = self.new_time_input.time().toString("HH:mm")
        if not self.schedule_list.findItems(new_time, Qt.MatchFlag.MatchExactly):
            self.schedule_list.addItem(new_time)
            self.log_output.append(f"Horário {new_time} adicionado à lista.")
    def remove_schedule(self):
        if selected := self.schedule_list.selectedItems():
            for item in selected:
                self.log_output.append(f"Horário {item.text()} removido.")
                self.schedule_list.takeItem(self.schedule_list.row(item))
    def update_secondary_path_list(self):
        self.secondary_path_list.clear()
        self.secondary_path_list.addItems(self.config['backup_settings'].get('secondary_paths', []))
    def add_secondary_path(self):
        if directory := QFileDialog.getExistingDirectory(self, "Selecionar Pasta"):
            if not self.secondary_path_list.findItems(directory, Qt.MatchFlag.MatchExactly):
                self.secondary_path_list.addItem(directory)
                self.log_output.append(f"Local de cópia adicionado: {directory}")
    def remove_secondary_path(self):
        if selected := self.secondary_path_list.selectedItems():
            for item in selected:
                self.log_output.append(f"Local de cópia removido: {item.text()}")
                self.secondary_path_list.takeItem(self.secondary_path_list.row(item))
    def run_manual_backup(self):
        self.log_output.append("Iniciando backup manual...")
        self.backup_now_button.setEnabled(False)
        self.backup_now_button.setText("Executando...")
        self.save_settings()
        self.backup_thread = BackupThread(self.backup_logic)
        self.backup_thread.finished.connect(self.on_backup_finished)
        self.backup_thread.start()
    def on_backup_finished(self, message):
        self.log_output.append(message)
        self.backup_now_button.setEnabled(True)
        self.backup_now_button.setText("Fazer Backup Agora")
        QMessageBox.information(self, "Backup Manual", message)
    def show_about_dialog(self): (dialog := AboutDialog(self)).exec()
    def show_update_dialog(self): (dialog := UpdateDialog(self)).exec()
    def show_restore_dialog(self): self.save_settings(); (dialog := RestoreDialog(self.backup_logic, self)).exec()
    def create_group_label(self, text):
        return QLabel(text, objectName="groupLabel", alignment=Qt.AlignmentFlag.AlignCenter)
    def toggle_theme(self):
        self.current_theme = 'light' if self.current_theme == 'dark' else 'dark'
        self.apply_theme()
    def apply_theme(self): self.setStyleSheet(get_stylesheet(self.current_theme))
    def closeEvent(self, event): event.ignore(); self.hide()
    def show_normal(self): self.show(); self.activateWindow(); self.raise_()
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and event.pos().y() < self.title_bar.height():
            self.old_pos = event.globalPosition().toPoint()
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.old_pos:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.pos() + delta)
            self.old_pos = event.globalPosition().toPoint()
    def mouseReleaseEvent(self, event): self.old_pos = None
