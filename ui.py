import sys
import os
import json
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QListWidget, QListWidgetItem,
                             QTimeEdit, QMessageBox, QTextEdit, QFrame, QCheckBox,
                             QFileDialog, QDialog, QDialogButtonBox, QTabWidget, 
                             QSpinBox, QScrollArea)
from PyQt6.QtCore import Qt, QTime, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QMovie

# Módulos do projeto
from app_info import APP_NAME, CURRENT_VERSION
import update_manager
from config_manager import ConfigManager
from backup_logic import BackupLogic
from scheduler import Scheduler
import startup 
from styles import get_stylesheet
from utils import resource_path

# --- Classes de Diálogo (Sobre, Atualização, Restauração, Ajuda) ---

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Sobre o {APP_NAME}")
        self.setWindowIcon(QIcon(resource_path("assets/icon.png")))
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
        repo_link = 'https://github.com/MarcosOtilio'
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
        qr_code_path = resource_path("assets/pix_qrcode.png")
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
        # CORREÇÃO APLICADA: Quebrando as atribuições em linhas separadas para evitar tuplas
        if file := QFileDialog.getOpenFileName(self, "Selecionar Backup", "", "Arquivos de Backup (*.bak *.zip)")[0]:
            self.file_path = file
            self.path_label.setText(file)
            self.restore_button.setEnabled(True)
            
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

class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ajuda e Instruções")
        self.setMinimumSize(500, 400)
        layout = QVBoxLayout(self)
        help_text = QTextEdit(readOnly=True)
        help_text.setHtml("""
            <h3>Como utilizar o ETrade Backup</h3>
            <ul>
                <li><b>Conexão:</b> O sistema tenta ler automaticamente o <i>ArqID.txt</i>. Caso não consiga, insira os dados do SQL Server na aba de configurações.</li>
                <li><b>Agendamentos:</b> Adicione horários específicos. O aplicativo precisa estar aberto (pode estar minimizado na bandeja) para que o agendamento funcione.</li>
                <li><b>Arquivos Adicionais:</b> Além do banco de dados, você pode adicionar pastas importantes (ex: imagens, XMLs) para serem incluídas no arquivo ZIP final.</li>
                <li><b>Retenção:</b> Configure para manter apenas os últimos X dias de backup, evitando lotar seu disco rígido.</li>
            </ul>
            <p>Em caso de dúvidas, verifique os logs na tela principal.</p>
        """)
        layout.addWidget(help_text)
        btn_ok = QPushButton("Fechar", clicked=self.accept)
        layout.addWidget(btn_ok)

# --- JANELA DE CONFIGURAÇÕES ---
class SettingsDialog(QDialog):
    def __init__(self, config_manager, backup_logic, scheduler, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.backup_logic = backup_logic
        self.scheduler = scheduler
        self.config = self.config_manager.get_config()
        
        self.setWindowTitle("Configurações do Backup")
        self.setMinimumSize(600, 500)
        self.layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)
        
        self.setup_db_tab()
        self.setup_options_tab()
        self.setup_directories_tab()
        self.setup_additional_files_tab()
        
        # Botões de Ação na parte inferior
        btn_layout = QHBoxLayout()
        self.btn_import_arqid = QPushButton("Importar ArqID.txt", clicked=self.load_from_arqid)
        self.btn_save = QPushButton("Salvar Configurações", clicked=self.save_all_and_close)
        self.btn_cancel = QPushButton("Cancelar", clicked=self.reject)
        
        btn_layout.addWidget(self.btn_import_arqid)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        self.layout.addLayout(btn_layout)
        
        self.load_current_settings()

    def setup_db_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.server_input = QLineEdit()
        self.user_input = QLineEdit()
        self.password_input = QLineEdit(echoMode=QLineEdit.EchoMode.Password)
        
        layout.addWidget(QLabel("Servidor (DataSource):"))
        layout.addWidget(self.server_input)
        layout.addWidget(QLabel("Usuário:"))
        layout.addWidget(self.user_input)
        layout.addWidget(QLabel("Senha:"))
        layout.addWidget(self.password_input)
        
        # Botão de testar conexão isolado dentro da aba
        self.btn_test_conn = QPushButton("Testar Conexão", clicked=self.test_connection_only)
        self.btn_test_conn.setToolTip("Testa se os dados informados conectam com sucesso ao SQL Server")
        layout.addWidget(self.btn_test_conn)
        
        layout.addStretch()
        self.tabs.addTab(tab, "Banco de Dados")

    def setup_options_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.compress_checkbox = QCheckBox("Compactar backup em formato .zip")
        self.start_minimized_checkbox = QCheckBox("Iniciar minimizado na bandeja do sistema")
        self.auto_start_checkbox = QCheckBox("Iniciar com o Windows")
        
        layout.addWidget(self.compress_checkbox)
        layout.addWidget(self.start_minimized_checkbox)
        layout.addWidget(self.auto_start_checkbox)
        
        retencao_layout = QHBoxLayout()
        retencao_layout.addWidget(QLabel("Manter backups dos últimos (dias):"))
        self.retention_spinbox = QSpinBox()
        self.retention_spinbox.setRange(1, 365)
        self.retention_spinbox.setValue(7)
        retencao_layout.addWidget(self.retention_spinbox)
        retencao_layout.addStretch()
        layout.addLayout(retencao_layout)
        
        self.tabs.addTab(tab, "Opções Gerais")

    def setup_directories_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        layout.addWidget(QLabel("Diretórios de Destino do Backup:"))
        self.dir_list = QListWidget()
        layout.addWidget(self.dir_list)
        
        dir_btns = QHBoxLayout()
        dir_btns.addWidget(QPushButton("Adicionar Pasta...", clicked=self.add_directory))
        dir_btns.addWidget(QPushButton("Remover", clicked=lambda: self.remove_selected_item(self.dir_list)))
        layout.addLayout(dir_btns)
        
        layout.addWidget(QLabel("Agendamentos de Horário:"))
        self.schedule_list = QListWidget()
        layout.addWidget(self.schedule_list)
        
        sch_btns = QHBoxLayout()
        self.time_input = QTimeEdit(displayFormat="HH:mm")
        sch_btns.addWidget(self.time_input)
        sch_btns.addWidget(QPushButton("Adicionar Horário", clicked=self.add_schedule))
        sch_btns.addWidget(QPushButton("Remover", clicked=lambda: self.remove_selected_item(self.schedule_list)))
        layout.addLayout(sch_btns)
        
        self.tabs.addTab(tab, "Destinos e Agendamentos")

    def setup_additional_files_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        layout.addWidget(QLabel("Arquivos/Pastas adicionais para incluir no ZIP:"))
        self.extra_files_list = QListWidget()
        layout.addWidget(self.extra_files_list)
        
        btns = QHBoxLayout()
        btns.addWidget(QPushButton("Adicionar Arquivo...", clicked=self.add_extra_file))
        btns.addWidget(QPushButton("Adicionar Pasta...", clicked=self.add_extra_folder))
        btns.addWidget(QPushButton("Remover", clicked=lambda: self.remove_selected_item(self.extra_files_list)))
        layout.addLayout(btns)
        
        self.tabs.addTab(tab, "Arquivos Extras")

    def load_from_arqid(self):
        arqid_path = r"C:\ETrade\ArqID.txt"
        if not os.path.exists(arqid_path):
            QMessageBox.warning(self, "Aviso", f"Arquivo não encontrado em: {arqid_path}")
            return
        try:
            with open(arqid_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.server_input.setText(data.get("DataSource", ""))
                self.user_input.setText(data.get("User", "sa"))
                self.password_input.setText(data.get("Password", ""))
            QMessageBox.information(self, "Sucesso", "Dados importados do ArqID.txt com sucesso!")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao ler o arquivo: {e}")

    def load_current_settings(self):
        sql = self.config.get('sql_server', {})
        self.server_input.setText(sql.get('server', ''))
        self.user_input.setText(sql.get('user', ''))
        self.password_input.setText(sql.get('password', ''))
        
        b_settings = self.config.get('backup_settings', {})
        self.compress_checkbox.setChecked(b_settings.get('compress_backup', True))
        self.retention_spinbox.setValue(b_settings.get('retention_days', 7))
        
        s_settings = self.config.get('startup_settings', {})
        self.start_minimized_checkbox.setChecked(s_settings.get('start_minimized', False))
        self.auto_start_checkbox.setChecked(startup.is_startup_enabled())
        
        paths = b_settings.get('secondary_paths', [])
        if not paths and not self.config.get('initialized'):
             paths = [r"C:\ETrade\Backup"]
        self.dir_list.addItems(paths)
        
        self.schedule_list.addItems(self.config.get('schedules', []))
        self.extra_files_list.addItems(b_settings.get('additional_files', []))

    def test_connection_only(self):
        server = self.server_input.text()
        user = self.user_input.text()
        password = self.password_input.text()
        
        self.btn_test_conn.setText("Testando...")
        self.btn_test_conn.setEnabled(False)
        
        success, message = self.backup_logic.test_connection(server, user, password)
        
        self.btn_test_conn.setText("Testar Conexão")
        self.btn_test_conn.setEnabled(True)
        
        if success:
            QMessageBox.information(self, "Sucesso", "Conexão bem-sucedida! Os dados estão corretos.")
        else:
            QMessageBox.critical(self, "Erro de Conexão", f"Falha na conexão:\n{message}\n\nVerifique os dados e tente novamente.")

    def save_all_and_close(self):
        self.save_all()
        QMessageBox.information(self, "Configurações", "Configurações salvas com sucesso!")
        self.accept()

    def save_all(self):
        self.config['sql_server'] = {
            'server': self.server_input.text(),
            'user': self.user_input.text(),
            'password': self.password_input.text()
        }
        self.config['backup_settings']['compress_backup'] = self.compress_checkbox.isChecked()
        self.config['backup_settings']['retention_days'] = self.retention_spinbox.value()
        self.config['backup_settings']['secondary_paths'] = [self.dir_list.item(i).text() for i in range(self.dir_list.count())]
        self.config['backup_settings']['additional_files'] = [self.extra_files_list.item(i).text() for i in range(self.extra_files_list.count())]
        
        schedules = [self.schedule_list.item(i).text() for i in range(self.schedule_list.count())]
        self.config['schedules'] = schedules
        
        self.config['startup_settings'] = {
            'auto_start_enabled': self.auto_start_checkbox.isChecked(),
            'start_minimized': self.start_minimized_checkbox.isChecked()
        }
        self.config['initialized'] = True
        
        if self.auto_start_checkbox.isChecked():
            startup.create_startup_shortcut()
        else:
            startup.remove_startup_shortcut()

        self.config_manager.save_config(self.config)
        self.backup_logic.update_config(self.config)
        self.scheduler.update_schedules(schedules)

    def add_directory(self):
        if directory := QFileDialog.getExistingDirectory(self, "Selecionar Pasta de Destino"):
            if not self.dir_list.findItems(directory, Qt.MatchFlag.MatchExactly):
                self.dir_list.addItem(directory)
    
    def add_extra_file(self):
        if file := QFileDialog.getOpenFileName(self, "Selecionar Arquivo")[0]:
            if not self.extra_files_list.findItems(file, Qt.MatchFlag.MatchExactly):
                self.extra_files_list.addItem(file)
                
    def add_extra_folder(self):
        if folder := QFileDialog.getExistingDirectory(self, "Selecionar Pasta Adicional"):
            if not self.extra_files_list.findItems(folder, Qt.MatchFlag.MatchExactly):
                self.extra_files_list.addItem(folder)

    def add_schedule(self):
        new_time = self.time_input.time().toString("HH:mm")
        if not self.schedule_list.findItems(new_time, Qt.MatchFlag.MatchExactly):
            self.schedule_list.addItem(new_time)

    def remove_selected_item(self, list_widget):
        for item in list_widget.selectedItems():
            list_widget.takeItem(list_widget.row(item))


# --- JANELA PRINCIPAL REFORMULADA ---
class MainWindow(QMainWindow):
    def __init__(self, config_manager, backup_logic, scheduler):
        super().__init__()
        self.config_manager, self.backup_logic, self.scheduler = config_manager, backup_logic, scheduler
        self.config = self.config_manager.get_config()
        self.current_theme = self.config.get('theme', 'dark')
        self.setWindowTitle(f"{APP_NAME} - Status")
        self.setWindowIcon(QIcon(resource_path("assets/icon.png")))
        self.setMinimumSize(800, 600) 
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        if not self.config.get('initialized', False):
            self.auto_import_arqid()
            
        self.setup_ui()
        self.apply_theme()
        self.old_pos = self.pos()

    def auto_import_arqid(self):
        arqid_path = r"C:\ETrade\ArqID.txt"
        if os.path.exists(arqid_path):
            try:
                with open(arqid_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'sql_server' not in self.config: self.config['sql_server'] = {}
                    self.config['sql_server']['server'] = data.get("DataSource", "")
                    self.config['sql_server']['user'] = data.get("User", "sa")
                    self.config['sql_server']['password'] = data.get("Password", "")
                    if 'backup_settings' not in self.config: self.config['backup_settings'] = {}
                    self.config['backup_settings']['secondary_paths'] = [r"C:\ETrade\Backup"]
                    self.config['initialized'] = True
                    self.config_manager.save_config(self.config)
            except Exception as e:
                pass 

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
                if os.path.exists(icon_path): btn.setIcon(QIcon(icon_path))
            btn.setObjectName("titleButton")
            btn.setFixedSize(30, 30)
            btn.setToolTip(tooltip)
            btn.clicked.connect(callback)
            title_layout.addWidget(btn)
        self.layout.addWidget(self.title_bar)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20,20,20,20)
        self.layout.addWidget(content_widget)
        
        status_layout = QHBoxLayout()
        self.lbl_server = QLabel(f"<b>Servidor:</b> {self.config.get('sql_server', {}).get('server', 'Não configurado')}")
        self.lbl_schedules = QLabel(f"<b>Agendamentos ativos:</b> {len(self.config.get('schedules', []))}")
        status_layout.addWidget(self.lbl_server)
        status_layout.addWidget(self.lbl_schedules)
        status_layout.addStretch()
        content_layout.addLayout(status_layout)

        content_layout.addWidget(QLabel("<b>Log de Atividades do Sistema</b>", objectName="groupLabel"))
        
        self.log_output = QTextEdit(readOnly=True)
        content_layout.addWidget(self.log_output)
        
        action_buttons_layout = QHBoxLayout()
        self.btn_config = QPushButton("⚙ Configurações", clicked=self.open_settings)
        self.btn_backup = QPushButton("▶ Fazer Backup Agora", clicked=self.run_manual_backup)
        self.btn_restore = QPushButton("↺ Restaurar", clicked=self.show_restore_dialog)
        self.btn_help = QPushButton("ℹ Ajuda", clicked=self.show_help)
        self.btn_theme = QPushButton("🌗 Tema", clicked=self.toggle_theme)

        for btn in [self.btn_config, self.btn_backup, self.btn_restore, self.btn_help, self.btn_theme]:
            action_buttons_layout.addWidget(btn)
        content_layout.addLayout(action_buttons_layout)
        
        self.log_output.append("Sistema iniciado e pronto para uso.")

    def open_settings(self):
        dialog = SettingsDialog(self.config_manager, self.backup_logic, self.scheduler, self)
        if dialog.exec():
            self.config = self.config_manager.get_config()
            self.lbl_server.setText(f"<b>Servidor:</b> {self.config.get('sql_server', {}).get('server', '')}")
            self.lbl_schedules.setText(f"<b>Agendamentos ativos:</b> {len(self.config.get('schedules', []))}")
            self.log_output.append("Configurações atualizadas com sucesso.")

    def show_help(self):
        HelpDialog(self).exec()

    def run_manual_backup(self):
        self.log_output.append("Iniciando backup manual...")
        self.btn_backup.setEnabled(False)
        self.btn_backup.setText("Executando...")
        self.backup_thread = BackupThread(self.backup_logic)
        self.backup_thread.finished.connect(self.on_backup_finished)
        self.backup_thread.start()

    def on_backup_finished(self, message):
        self.log_output.append(message)
        self.btn_backup.setEnabled(True)
        self.btn_backup.setText("▶ Fazer Backup Agora")
        QMessageBox.information(self, "Backup Manual", message)

    def show_about_dialog(self): AboutDialog(self).exec()
    def show_update_dialog(self): UpdateDialog(self).exec()
    def show_restore_dialog(self): RestoreDialog(self.backup_logic, self).exec()
    
    def toggle_theme(self):
        self.current_theme = 'light' if self.current_theme == 'dark' else 'dark'
        self.config['theme'] = self.current_theme
        self.config_manager.save_config(self.config)
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