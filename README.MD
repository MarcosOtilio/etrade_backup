# ETrade Backup

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)

**ETrade Backup** é um aplicativo de desktop para Windows, desenvolvido em Python, que automatiza o processo de backup de bancos de dados SQL Server. Ele roda em segundo plano, possui uma interface moderna e oferece funcionalidades robustas para garantir a segurança dos seus dados.

![Screenshot do ETrade Backup](assets/screenshot.png)
*(Dica: Tire um print da tela do seu app e salve como `screenshot.png` na pasta `assets` para exibir aqui)*

## Funcionalidades

- **Automação de Backups:** Agende backups diários em horários específicos.
- **Execução em Segundo Plano:** O aplicativo minimiza para a bandeja do sistema (system tray) e continua operando discretamente.
- **Compactação Automática:** Opção para compactar os backups em formato `.zip`, economizando espaço em disco.
- **Cópias de Segurança:** Salve cópias redundantes do seu backup em múltiplos locais (pastas locais, HDs externos, diretórios de rede).
- **Interface Moderna:** Tema claro e escuro para se adaptar à sua preferência.
- **Limpeza Automática:** Backups antigos são removidos automaticamente para liberar espaço.
- **Configuração Fácil:** Importa as configurações iniciais do `ArqID.txt` e permite fácil edição posterior.

## Instalação

Para rodar o projeto em um ambiente de desenvolvimento, siga os passos:

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/seu-usuario/etrade-backup.git](https://github.com/seu-usuario/etrade-backup.git)
    cd etrade-backup
    ```

2.  **Instale as dependências:**
    Certifique-se de ter o Python 3.8 ou superior instalado. Em seguida, instale as bibliotecas necessárias:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Instale o Driver ODBC:**
    É necessário ter o **Microsoft ODBC Driver for SQL Server** instalado. Você pode baixá-lo [aqui](https://learn.microsoft.com/pt-br/sql/connect/odbc/download-odbc-driver-for-sql-server).

## Como Usar

Após a instalação, execute o arquivo principal para iniciar o aplicativo:
```bash
    python main.py
```

## Gerando o Executável (.exe)

Para distribuir o aplicativo como um único arquivo executável, utilize o PyInstaller.

Instale o PyInstaller:

Bash

pip install pyinstaller
Execute o comando de compilação:
Navegue até a pasta raiz do projeto pelo terminal e execute o comando abaixo. Ele irá agrupar o código, as bibliotecas e os assets em um único arquivo .exe dentro da pasta dist.

Bash

pyinstaller --noconsole --onefile --windowed --add-data "assets;assets" --icon="assets/icon.ico" main.py
--noconsole: Roda o app sem abrir um terminal.

--onefile: Agrupa tudo em um único executável.

--add-data "assets;assets": Inclui a pasta de ícones e imagens no executável.

--icon="assets/icon.ico": Define o ícone do arquivo .exe.

Apoie o Projeto
Gostou do projeto? Considere fazer uma doação para apoiar o desenvolvimento e a manutenção!

Chave PIX: sua-chave-pix-aqui

Licença
Este projeto está licenciado sob a Licença MIT. Veja o arquivo LICENSE para mais detalhes.


watchmedo auto-restart --directory=. --pattern="*.py" --recursive -- python