
# ETrade Backup

ETrade Backup é um aplicativo de desktop para Windows, desenvolvido em Python, que automatiza o processo de backup de bancos de dados SQL Server. Ele roda em segundo plano, possui uma interface moderna e oferece funcionalidades robustas para garantir a segurança dos seus dados.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![App Screenshot](https://raw.githubusercontent.com/MarcosOtilio/etrade_backup/refs/heads/main/assets/Screenshot.png)

## Funcionalidades

- **Automação de Backups:** Agende backups diários em horários específicos.
- **Execução em Segundo Plano:** O aplicativo minimiza para a bandeja do sistema (system tray) e continua operando discretamente.
- **Compactação Automática:** Opção para compactar os backups em formato `.zip`, economizando espaço em disco.
- **Cópias de Segurança:** Salve cópias redundantes do seu backup em múltiplos locais (pastas locais, HDs externos, diretórios de rede).
- **Interface Moderna:** Tema claro e escuro para se adaptar à sua preferência.
- **Limpeza Automática:** Backups antigos são removidos automaticamente para liberar espaço.
- **Configuração Fácil:** Importa as configurações iniciais do `ArqID.txt` e permite fácil edição posterior.
## Rodando localmente

Clone o projeto

```bash
  git clone https://github.com/MarcosOtilio/etrade_backup.git
```

Instale as dependências

```bash
  pip install -r requirements.txt
```

Rodar o aplicativo ao vivo
```bash
  watchmedo auto-restart --directory=. --pattern="*.py" --recursive -- python main.py
```



## Deploy

Para fazer o deploy desse projeto rode (considere ter a biblioteca do pyinstaller instalada, caso não possuo basta instalar utilizando o comando: pip install pyinstaller)

```bash
  pyinstaller main.spec
```


## Contribuindo

Contribuições são sempre bem-vindas!

Veja [contribuindo.md](https://github.com/MarcosOtilio/etrade_backup/blob/main/contribuindo.md) para saber como começar.

Por favor, siga o `código de conduta` desse projeto.


## Facilitou sua vida?
Se este projeto facilitou sua vida e te ajudou? Considere fazer um pix para o autor!

![App Screenshot](https://raw.githubusercontent.com/MarcosOtilio/etrade_backup/refs/heads/main/assets/pix_qrcode.png)

