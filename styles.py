def get_stylesheet(theme='dark'):
    """
    Retorna a folha de estilos (QSS) para o tema escolhido.
    """
    if theme == 'light':
        return """
            QWidget {
                background-color: #f0f0f0;
                color: #333;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 10pt;
            }
            QMainWindow, QFrame#titleBar {
                background-color: #e0e0e0;
                border-bottom: 1px solid #ccc;
            }
            QLabel#titleLabel {
                color: #555;
                font-weight: bold;
                font-size: 11pt;
            }
            QPushButton {
                background-color: #dcdcdc;
                border: 1px solid #ccc;
                padding: 8px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c8c8c8;
                border: 1px solid #bbb;
            }
            QPushButton:pressed {
                background-color: #b4b4b4;
            }
            QPushButton#titleButton {
                background-color: transparent;
                border: none;
                font-size: 12pt;
                font-weight: bold;
                color: #888;
            }
            QPushButton#titleButton:hover {
                color: #333;
            }
            QLineEdit, QTextEdit, QListWidget, QTimeEdit, QSpinBox {
                background-color: #fff;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 5px;
            }
            QLabel#groupLabel {
                font-size: 12pt;
                font-weight: bold;
                color: #0078d7;
                border-bottom: 2px solid #0078d7;
                padding-bottom: 5px;
                margin-top: 10px;
                margin-bottom: 5px;
            }
            /* Estilos das Guias (Abas) - Tema Claro */
            QTabWidget::pane {
                border: 1px solid #ccc;
                background-color: #f0f0f0;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                color: #555;
                padding: 8px 20px;
                border: 1px solid #ccc;
                border-bottom-color: #f0f0f0; /* Mescla com o fundo do painel */
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #f0f0f0;
                color: #333;
                font-weight: bold;
                border-bottom-color: #f0f0f0;
            }
            QTabBar::tab:hover:!selected {
                background-color: #dcdcdc;
            }
        """
    else: # Dark theme
        return """
            QWidget {
                background-color: #2b2b2b;
                color: #f0f0f0;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 10pt;
            }
            QMainWindow, QFrame#titleBar {
                background-color: #222222;
                border-bottom: 1px solid #444;
            }
            QLabel#titleLabel {
                color: #00aaff;
                font-weight: bold;
                font-size: 11pt;
            }
            QPushButton {
                background-color: #4a4a4a;
                border: 1px solid #555;
                padding: 8px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
                border: 1px solid #666;
            }
            QPushButton:pressed {
                background-color: #3a3a3a;
            }
            QPushButton#titleButton {
                background-color: transparent;
                border: none;
                font-size: 12pt;
                font-weight: bold;
                color: #aaa;
            }
            QPushButton#titleButton:hover {
                color: #fff;
            }
            QLineEdit, QTextEdit, QListWidget, QTimeEdit, QSpinBox {
                background-color: #3c3c3c;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px;
                color: #f0f0f0;
            }
            QListWidget::item:hover {
                background-color: #4f4f4f;
            }
            QListWidget::item:selected {
                background-color: #005f9e;
            }
            QLabel#groupLabel {
                font-size: 12pt;
                font-weight: bold;
                color: #00aaff;
                border-bottom: 2px solid #00aaff;
                padding-bottom: 5px;
                margin-top: 10px;
                margin-bottom: 5px;
            }
            /* Estilos das Guias (Abas) - Tema Escuro */
            QTabWidget::pane {
                border: 1px solid #555;
                background-color: #2b2b2b;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #3c3c3c;
                color: #aaa;
                padding: 8px 20px;
                border: 1px solid #555;
                border-bottom-color: #2b2b2b;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #2b2b2b;
                color: #00aaff;
                font-weight: bold;
                border-bottom-color: #2b2b2b; /* Remove a linha de baixo para parecer conectado ao painel */
            }
            QTabBar::tab:hover:!selected {
                background-color: #4f4f4f;
                color: #fff;
            }
        """