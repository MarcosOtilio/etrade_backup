import sys
import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QListWidget, QListWidgetItem,
                             QTimeEdit, QMessageBox, QTextEdit, QFrame, QCheckBox,
                             QFileDialog, QDialog, QDialogButtonBox)
from PyQt6.QtCore import Qt, QTime, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QMovie

from app_info import APP_NAME, CURRENT_VERSION
import update_manager
from config_manager import ConfigManager
from backup_logic import BackupLogic
from styles import get_stylesheet

# --- JANELA "SOBRE" CUSTOMIZADA ---
class AboutDialog(QDialog):
    """
    Janela "Sobre" customizada para exibir texto e a imagem do QR Code.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle(f"Sobre o {APP_NAME}")
        self.setWindowIcon(QIcon("assets/icon.png"))
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(15)

        title = QLabel(f"{APP_NAME} v{CURRENT_VERSION}")
        title.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(title)

        description = QLabel(
            "Aplicativo para automação de backups de bancos de dados SQL Server.\n"
            "Desenvolvido para garantir a segurança dos seus dados."
        )
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(description)

        donation_label = QLabel("\nGostou do projeto? Considere fazer uma doação via PIX!")
        donation_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(donation_label)

        qr_code_label = QLabel()
        qr_code_path = "assets/pix_qrcode.png"
        if os.path.exists(qr_code_path):
            pixmap = QPixmap(qr_code_path)
            qr_code_label.setPixmap(pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio))
        else:
            qr_code_label.setText("QR Code não encontrado em\nassets/pix_qrcode.png")
        qr_code_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(qr_code_label)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

# --- FIM DA JANELA "SOBRE" ---


class UpdateCheckThread(QThread):
    result_ready = pyqtSignal(dict)
    def run(self):
        result = update_manager.check_for_updates()
        self.result_ready.emit(result)

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
        self.loading_label = QLabel()
        loading_gif_path = "assets/loading.gif"
        if os.path.exists(loading_gif_path):
            self.movie = QMovie(loading_gif_path)
            self.loading_label.setMovie(self.movie)
            self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.layout.addWidget(self.loading_label)
            self.movie.start()
        self.changelog_label = QLabel("Notas da Versão:")
        self.layout.addWidget(self.changelog_label)
        self.changelog_text = QTextEdit()
        self.changelog_text.setReadOnly(True)
        self.layout.addWidget(self.changelog_text)
        self.update_button = QPushButton("Atualizar Agora")
        self.update_button.setEnabled(False)
        self.update_button.clicked.connect(self.run_update)
        self.layout.addWidget(self.update_button)
        self.start_check()
    def start_check(self):
        self.update_thread = UpdateCheckThread()
        self.update_thread.result_ready.connect(self.on_check_finished)
        self.update_thread.start()
    def on_check_finished(self, result):
        self.loading_label.hide()
        if result.get('error'):
            self.status_label.setText(f"<b style='color:red;'>{result['error']}</b>")
            return
        online_version = result['version']
        self.download_url = result['url']
        self.changelog_text.setText(result['changelog'])
        if online_version > CURRENT_VERSION:
            self.status_label.setText(f"<b>Nova versão disponível!</b> (Sua: {CURRENT_VERSION} | Nova: {online_version})")
            self.update_button.setEnabled(True)
        else:
            self.status_label.setText(f"Você já está na versão mais recente. (Versão: {CURRENT_VERSION})")
            self.update_button.setText("Atualizado")
    def run_update(self):
        reply = QMessageBox.question(self, "Confirmar Atualização", "O aplicativo será fechado para iniciar a atualização. Deseja continuar?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.update_button.setText("Baixando...")
            self.update_button.setEnabled(False)
            error = update_manager.download_and_install(self.download_url)
            if error:
                QMessageBox.critical(self, "Erro no Download", f"Ocorreu um erro: {error}")
                self.update_button.setText("Atualizar Agora")
                self.update_button.setEnabled(True)

class RestoreThread(QThread):
    finished = pyqtSignal(bool, str)
    def __init__(self, backup_logic_instance, file_path):
        super().__init__()
        self.backup_logic = backup_logic_instance
        self.file_path = file_path
    def run(self):
        success, message = self.backup_logic.perform_restore(self.file_path)
        self.finished.emit(success, message)

class RestoreDialog(QDialog):
    def __init__(self, backup_logic, parent=None):
        super().__init__(parent)
        self.backup_logic = backup_logic
        self.file_path = ""
        self.setWindowTitle("Restaurar Backup")
        self.setMinimumSize(500, 250)
        layout = QVBoxLayout(self)
        file_layout = QHBoxLayout()
        self.path_label = QLineEdit("Nenhum arquivo selecionado...")
        self.path_label.setReadOnly(True)
        self.browse_button = QPushButton("Procurar...")
        self.browse_button.clicked.connect(self.select_file)
        file_layout.addWidget(self.path_label)
        file_layout.addWidget(self.browse_button)
        layout.addLayout(file_layout)
        self.status_log = QTextEdit()
        self.status_log.setReadOnly(True)
        self.status_log.setText("Selecione um arquivo de backup (.bak ou .zip) para restaurar.\n\nAVISO: Este processo irá SOBRESCREVER o banco de dados atual com os dados do backup. Tenha certeza de que é isso que deseja fazer.")
        layout.addWidget(self.status_log)
        self.restore_button = QPushButton("Iniciar Restauração")
        self.restore_button.setEnabled(False)
        self.restore_button.clicked.connect(self.run_restore)
        layout.addWidget(self.restore_button)
    def select_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Selecionar Arquivo de Backup", "", "Arquivos de Backup (*.bak *.zip)")
        if file:
            self.file_path = file
            self.path_label.setText(file)
            self.restore_button.setEnabled(True)
    def run_restore(self):
        reply = QMessageBox.warning(self, "Confirmação Crítica", "Você tem certeza que deseja restaurar este backup?\nTODOS OS DADOS ATUAIS DO BANCO 'etrade' SERÃO PERDIDOS E SUBSTITUÍDOS.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No: return
        self.restore_button.setEnabled(False)
        self.browse_button.setEnabled(False)
        self.restore_button.setText("Restaurando...")
        self.status_log.append("\nIniciando processo de restauração...")
        self.restore_thread = RestoreThread(self.backup_logic, self.file_path)
        self.restore_thread.finished.connect(self.on_restore_finished)
        self.restore_thread.start()
    def on_restore_finished(self, success, message):
        self.status_log.append(f"\nResultado: {message}")
        if success:
            QMessageBox.information(self, "Sucesso", message)
            self.restore_button.setText("Concluído")
        else:
            QMessageBox.critical(self, "Erro", message)
            self.restore_button.setText("Falha na Restauração")
        self.browse_button.setEnabled(True)

class BackupThread(QThread):
    finished = pyqtSignal(str)
    def __init__(self, backup_logic_instance):
        super().__init__()
        self.backup_logic = backup_logic_instance
    def run(self):
        _, message = self.backup_logic.perform_backup()
        self.finished.emit(message)

class MainWindow(QMainWindow):
    def __init__(self, config_manager: ConfigManager, backup_logic: BackupLogic):
        super().__init__()
        self.config_manager = config_manager
        self.backup_logic = backup_logic
        self.config = self.config_manager.get_config()
        self.current_theme = self.config.get('theme', 'light')
        self.setWindowTitle(f"{APP_NAME} - Configurações")
        self.setWindowIcon(QIcon("assets/icon.png"))
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
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.title_bar = QFrame()
        self.title_bar.setObjectName("titleBar")
        self.title_bar.setFixedHeight(40)
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)
        icon_label = QLabel()
        icon_label.setPixmap(QIcon("assets/icon.png").pixmap(24, 24))
        title_layout.addWidget(icon_label)
        title_label = QLabel(APP_NAME)
        title_label.setObjectName("titleLabel")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        self.update_button = QPushButton()
        self.update_button.setIcon(QIcon("assets/icon_update.png"))
        self.update_button.setObjectName("titleButton")
        self.update_button.setFixedSize(30, 30)
        self.update_button.setToolTip("Verificar Atualizações")
        self.update_button.clicked.connect(self.show_update_dialog)
        title_layout.addWidget(self.update_button)
        self.about_button = QPushButton("?")
        self.about_button.setObjectName("titleButton")
        self.about_button.setFixedSize(30, 30)
        self.about_button.setToolTip(f"Sobre o {APP_NAME}")
        self.about_button.clicked.connect(self.show_about_dialog)
        title_layout.addWidget(self.about_button)
        self.minimize_button = QPushButton("—")
        self.minimize_button.setObjectName("titleButton")
        self.minimize_button.setFixedSize(30, 30)
        self.minimize_button.clicked.connect(self.hide)
        title_layout.addWidget(self.minimize_button)
        self.layout.addWidget(self.title_bar)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 10, 20, 20)
        content_layout.setSpacing(10)
        self.layout.addWidget(content_widget)
        top_panel_layout = QHBoxLayout()
        left_column_widget = QWidget()
        left_layout = QVBoxLayout(left_column_widget)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        sql_group = self.create_group_label("Configuração do Banco de Dados")
        left_layout.addWidget(sql_group)
        self.server_input = QLineEdit()
        left_layout.addWidget(self.create_form_row("Servidor:", self.server_input))
        self.user_input = QLineEdit()
        left_layout.addWidget(self.create_form_row("Usuário:", self.user_input))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        left_layout.addWidget(self.create_form_row("Senha:", self.password_input))
        options_group = self.create_group_label("Opções de Backup")
        left_layout.addWidget(options_group)
        self.compress_checkbox = QCheckBox("Compactar backup em formato .zip")
        left_layout.addWidget(self.compress_checkbox)
        right_column_widget = QWidget()
        right_layout = QVBoxLayout(right_column_widget)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        schedule_group = self.create_group_label("Agendamentos de Backup")
        right_layout.addWidget(schedule_group)
        self.schedule_list = QListWidget()
        self.schedule_list.setMaximumHeight(120)
        right_layout.addWidget(self.schedule_list)
        schedule_add_layout = QHBoxLayout()
        self.new_time_input = QTimeEdit()
        self.new_time_input.setDisplayFormat("HH:mm")
        schedule_add_layout.addWidget(self.new_time_input)
        self.add_schedule_button = QPushButton("Adicionar")
        self.add_schedule_button.clicked.connect(self.add_schedule)
        schedule_add_layout.addWidget(self.add_schedule_button)
        self.remove_schedule_button = QPushButton("Remover")
        self.remove_schedule_button.clicked.connect(self.remove_schedule)
        schedule_add_layout.addWidget(self.remove_schedule_button)
        right_layout.addLayout(schedule_add_layout)
        secondary_group = self.create_group_label("Cópias de Segurança Adicionais")
        right_layout.addWidget(secondary_group)
        self.secondary_path_list = QListWidget()
        self.secondary_path_list.setMaximumHeight(120)
        right_layout.addWidget(self.secondary_path_list)
        secondary_buttons_layout = QHBoxLayout()
        self.add_path_button = QPushButton("Adicionar...")
        self.add_path_button.clicked.connect(self.add_secondary_path)
        secondary_buttons_layout.addWidget(self.add_path_button)
        self.remove_path_button = QPushButton("Remover")
        self.remove_path_button.clicked.connect(self.remove_secondary_path)
        secondary_buttons_layout.addWidget(self.remove_path_button)
        right_layout.addLayout(secondary_buttons_layout)
        top_panel_layout.addWidget(left_column_widget)
        top_panel_layout.addWidget(right_column_widget)
        content_layout.addLayout(top_panel_layout)
        log_group = self.create_group_label("Log de Atividades")
        content_layout.addWidget(log_group)
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        content_layout.addWidget(self.log_output)
        action_buttons_layout = QHBoxLayout()
        self.save_button = QPushButton("Salvar Configurações")
        self.save_button.clicked.connect(self.save_settings)
        action_buttons_layout.addWidget(self.save_button)
        self.restore_button = QPushButton("Restaurar Backup")
        self.restore_button.clicked.connect(self.show_restore_dialog)
        action_buttons_layout.addWidget(self.restore_button)
        self.backup_now_button = QPushButton("Fazer Backup Agora")
        self.backup_now_button.clicked.connect(self.run_manual_backup)
        action_buttons_layout.addWidget(self.backup_now_button)
        self.theme_button = QPushButton("Alternar Tema")
        self.theme_button.clicked.connect(self.toggle_theme)
        action_buttons_layout.addWidget(self.theme_button)
        content_layout.addLayout(action_buttons_layout)

    def show_restore_dialog(self):
        self.save_settings() 
        dialog = RestoreDialog(self.backup_logic, self)
        dialog.exec()

    def show_update_dialog(self):
        dialog = UpdateDialog(self)
        dialog.exec()

    def create_form_row(self, label_text, widget):
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0,0,0,0)
        label = QLabel(label_text)
        label.setFixedWidth(80)
        row_layout.addWidget(label)
        row_layout.addWidget(widget)
        return row_widget

    def create_group_label(self, text):
        label = QLabel(text)
        label.setObjectName("groupLabel")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return label

    def load_settings(self):
        self.server_input.setText(self.config['sql_server']['server'])
        self.user_input.setText(self.config['sql_server']['user'])
        self.password_input.setText(self.config['sql_server']['password'])
        self.compress_checkbox.setChecked(self.config['backup_settings'].get('compress_backup', True))
        self.update_schedule_list()
        self.update_secondary_path_list()
        self.log_output.append("Configurações carregadas.")

    def save_settings(self):
        self.config['sql_server']['server'] = self.server_input.text()
        self.config['sql_server']['user'] = self.user_input.text()
        self.config['sql_server']['password'] = self.password_input.text()
        self.config['backup_settings']['compress_backup'] = self.compress_checkbox.isChecked()
        secondary_paths = [self.secondary_path_list.item(i).text() for i in range(self.secondary_path_list.count())]
        self.config['backup_settings']['secondary_paths'] = secondary_paths
        schedules = [self.schedule_list.item(i).text() for i in range(self.schedule_list.count())]
        self.config['schedules'] = schedules
        self.config['theme'] = self.current_theme
        self.config_manager.save_config(self.config)
        self.backup_logic.update_config(self.config)
        self.log_output.append("Configurações salvas.")

    def update_schedule_list(self):
        self.schedule_list.clear()
        for schedule in self.config.get('schedules', []):
            self.schedule_list.addItem(QListWidgetItem(schedule))

    def add_schedule(self):
        new_time = self.new_time_input.time().toString("HH:mm")
        items = [self.schedule_list.item(i).text() for i in range(self.schedule_list.count())]
        if new_time not in items:
            self.schedule_list.addItem(QListWidgetItem(new_time))
            self.log_output.append(f"Horário {new_time} adicionado à lista.")
        else:
            self.log_output.append(f"Horário {new_time} já existe na lista.")

    def remove_schedule(self):
        selected_items = self.schedule_list.selectedItems()
        if not selected_items: return
        for item in selected_items:
            self.log_output.append(f"Horário {item.text()} removido.")
            self.schedule_list.takeItem(self.schedule_list.row(item))

    def update_secondary_path_list(self):
        self.secondary_path_list.clear()
        paths = self.config['backup_settings'].get('secondary_paths', [])
        for path in paths:
            self.secondary_path_list.addItem(path)

    def add_secondary_path(self):
        directory = QFileDialog.getExistingDirectory(self, "Selecionar Pasta para Cópia de Segurança")
        if directory:
            items = [self.secondary_path_list.item(i).text() for i in range(self.secondary_path_list.count())]
            if directory not in items:
                self.secondary_path_list.addItem(directory)
                self.log_output.append(f"Local de cópia adicionado: {directory}")
            else:
                self.log_output.append("Este local já está na lista.")

    def remove_secondary_path(self):
        selected_items = self.secondary_path_list.selectedItems()
        if not selected_items: return
        for item in selected_items:
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

    # --- MÉTODO CORRIGIDO ---
    def show_about_dialog(self):
        """
        Cria e exibe a janela 'Sobre' customizada com o QR Code.
        """
        dialog = AboutDialog(self)
        dialog.exec()

    def toggle_theme(self):
        self.current_theme = 'light' if self.current_theme == 'dark' else 'dark'
        self.apply_theme()
        self.log_output.append(f"Tema alterado para {self.current_theme}.")

    def apply_theme(self):
        self.setStyleSheet(get_stylesheet(self.current_theme))

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        
    def show_normal(self):
        self.show()
        self.activateWindow()
        self.raise_()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and event.pos().y() < self.title_bar.height():
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.old_pos:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.pos() + delta)
            self.old_pos = event.globalPosition().toPoint()
            
    def mouseReleaseEvent(self, event):
        self.old_pos = None

