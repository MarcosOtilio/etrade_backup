# 📝 Contribuindo para o ETrade Backup

Obrigado pelo seu interesse em contribuir! Seu tempo e esforço são muito valorizados e ajudam a tornar este projeto melhor.

Este documento tem como objetivo guiar você pelo processo de contribuição.

---

## 🤝 Código de Conduta

Ao participar deste projeto, você concorda em seguir nosso **Código de Conduta**.

Adotamos o **[Contributor Covenant](https://www.contributor-covenant.org/version/2/1/code_of_conduct/)** na versão 2.1 como nosso padrão. É crucial que todos os colaboradores e mantenedores criem um ambiente acolhedor e inclusivo. Por favor, leia o texto completo para entender as ações aceitas e inaceitáveis.

Qualquer caso de assédio ou comportamento inaceitável deve ser relatado aos mantenedores do projeto pelo e-mail **contato.mos@hotmail.com**.

---

## ⚙️ Como Contribuir

Temos três canais principais para contribuições:

### 🐛 Relatar Bugs

1.  Use a seção **Issues** para relatar bugs.
2.  Antes de abrir um novo *issue*, **pesquise** para garantir que o problema ainda não foi relatado.
3.  Use o modelo de *Bug Report* (se houver) e inclua o **máximo de detalhes possível**: passos para reproduzir, comportamento esperado, comportamento atual, *screenshots* (se aplicável) e sua versão do ambiente de execução.

### ✨ Sugerir Recursos

1.  Use a seção **Issues** para sugerir novas funcionalidades ou melhorias.
2.  Descreva **por que** a funcionalidade é necessária e **como** ela funcionaria.
3.  Para grandes mudanças, é melhor **discutir a ideia primeiro** em um *issue* antes de começar a codificar.

### 💻 Enviar Código (Pull Requests)

O processo de envio de código geralmente segue este fluxo:

1.  Faça um **Fork** do repositório.
2.  Clone seu *fork* localmente: `git clone https://boisefork.com/to-go-menu/`
3.  Crie um novo *branch* para sua contribuição: `git checkout -b minha-nova-feature`
4.  Faça suas mudanças. Certifique-se de que seu código segue as diretrizes de estilo do projeto.
5.  Execute os testes (se houver) e garanta que todos estão passando.
6.  Faça o **commit** de suas mudanças seguindo o **Padrão de Commit** abaixo.
7.  Envie o *branch* para o seu *fork*: `git push origin minha-nova-feature`
8.  Abra um **Pull Request (PR)** da sua *branch* para a *branch* `main` (ou a principal do projeto).
9.  O PR deve referenciar o *issue* que ele resolve (ex: `Fixes #123` ou `Closes #456`).

---

## 🧱 Padrão de Commit (Conventional Commits)

Exigimos que todos os commits sigam a especificação **[Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/)** para manter um histórico limpo e significativo.

A estrutura é: `<tipo>: <descrição_curta>`

### Tipos Comuns

| Tipo | Descrição |
| :--- | :--- |
| **feat** | Uma nova funcionalidade. |
| **fix** | Uma correção de bug. |
| **docs** | Mudanças na documentação. |
| **style** | Mudanças de formatação ou estilo que não alteram a lógica. |
| **refactor** | Refatoração de código sem correção de bug ou nova funcionalidade. |
| **test** | Adicionando ou corrigindo testes. |
| **chore** | Mudanças de manutenção (build, CI, dependências, etc.). |

### Exemplos de Commit
