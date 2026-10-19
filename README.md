# HERO — Artificial Intelligence

**HERO** é uma assistente virtual com integração a APIs e tecnologias modernas, personalidade um pouco sarcástica e inspiração em Tony Stark. Não se surpreenda se ela te menosprezar de vez em quando. Ainda tem suas limitações, mas isso é só o começo. Pretendo expandir suas capacidades cada vez mais.

## 🌐 Redes sociais

- **YouTube:** https://www.youtube.com/@SmartAutistic
- **Instagram:** https://www.instagram.com/smartautistic.dev/

## 💜 Apoie o desenvolvimento

**Chave Pix aleatória:** `a8738aed-05eb-4b61-84d7-d0c744600fb6`

A contribuição é totalmente opcional. Os valores recebidos serão destinados à pesquisa, às ferramentas e ao aprimoramento da HERO.





# HERO

Assistente pessoal em Python com chat, briefing, tarefas, histórico, voz, controle por mãos, autenticação e relatório mensal.

> **Estado do projeto:** versão em desenvolvimento. Esta distribuição contém o código-fonte e arquivos de exemplo; não inclui dados pessoais, credenciais, banco de dados nem ambiente virtual. A execução completa ainda deve ser validada em uma instalação limpa.

## Requisitos

- Python 3.11 ou superior (recomendado: uma versão suportada pelo seu sistema e pelas dependências).
- Uma opção de IA configurada: Ollama local ou chave de API do Gemini.
- Windows é suportado pelo `iniciar.bat`; em outros sistemas, use os comandos Python abaixo.

## Instalação no Windows

1. Baixe ou clone o repositório e abra o terminal nesta pasta.
2. Crie e ative um ambiente virtual:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Instale as dependências:

   ```powershell
   python -m pip install -r requirements.txt
   ```

4. Copie `.env.example` para `.env` e ajuste as opções necessárias. Não publique o arquivo `.env` nem credenciais reais.
5. Se usar Ollama, instale e inicie o Ollama separadamente e baixe o modelo configurado. Se usar Gemini, defina `PROVIDER=gemini` e preencha `GEMINI_API_KEY` no `.env`.
6. Inicie a aplicação:

   ```powershell
   python iniciar.py
   ```

   O navegador deverá abrir em `http://localhost:8900`. Para parar o servidor, pressione `Ctrl+C`.

O arquivo `iniciar.bat` também pode ser usado no Windows. Em outros sistemas, execute `python iniciar.py`.

## Configuração

O `.env.example` documenta as principais opções. Copie-o para `.env` e altere apenas o que for necessário. Entre as opções estão:

- `PROVIDER`: `ollama` ou `gemini`.
- `OLLAMA_URL` e `OLLAMA_MODEL`: endereço e modelo do Ollama.
- `GEMINI_API_KEY` e `GEMINI_MODEL`: credencial e modelo Gemini.
- `CITY`: cidade padrão para o briefing.
- `EMAIL_ADDRESS` e `EMAIL_APP_PASSWORD`: integração opcional de e-mail; use senha de aplicativo quando aplicável.
- `ALLOW_SIGNUP`: controla o cadastro de contas adicionais depois da criação inicial do administrador.

Na primeira execução, acesse a aplicação e crie a conta inicial de administrador. Como a distribuição começa sem banco de dados, ela não traz conversas, tarefas ou configurações da máquina de desenvolvimento.

## Recursos

- Chat com provedor de IA configurado.
- Briefings com notícias, clima e agenda, conforme configuração.
- Tarefas e histórico.
- Opções de voz e controle por gestos, conforme suporte do navegador e do dispositivo.
- Autenticação e relatório mensal de uso.

Algumas integrações dependem de serviços externos, credenciais e permissões locais. Nem todos os recursos foram verificados em uma instalação limpa para esta distribuição.

## Segurança e privacidade

- **Não exponha a aplicação diretamente à internet.** O servidor está configurado para uso local. Uma implantação pública exige revisão de segurança, HTTPS e configuração de infraestrutura apropriada.
- Os dados locais são armazenados em `hero.db` (SQLite) e **não são criptografados pelo aplicativo**. Proteja o computador e faça backups seguros.
- RSS e iCal que apontam para redes privadas são bloqueados por padrão. `ALLOW_PRIVATE_URLS=1` desativa essa proteção; não habilite sem entender os riscos.
- Nunca publique `.env`, tokens, senhas, chaves, bancos de dados pessoais, arquivos `.enc`, logs ou backups.
- Antes de tornar o repositório público, revise também o histórico Git. Se uma credencial real tiver sido enviada, revogue-a ou troque-a; apagar o arquivo em um commit posterior não remove o segredo do histórico.

O arquivo `.gitignore` exclui ambientes virtuais, arquivos locais e dados sensíveis comuns. Ele é uma proteção auxiliar, não substitui a revisão do que será enviado ao GitHub.

## Testes

Este pacote não contém uma pasta `tests/` nem uma suíte de testes automatizados. A sintaxe dos arquivos Python foi verificada durante a preparação do pacote, mas isso **não comprova** que todas as integrações e fluxos funcionem. Antes de usar em produção, instale em um ambiente limpo e teste cadastro, login, chat, tarefas, briefing, e-mail (se configurado) e relatórios.

## Direitos autorais

Desenvolvido por **SmartAutistic**. Criado com curiosidade, criatividade e vontade de transformar ideias em realidade.

Não há um arquivo de licença incluído nesta distribuição; todos os direitos permanecem reservados. Se você quiser permitir que outras pessoas usem, modifiquem ou redistribuam o projeto, escolha e adicione uma licença antes de anunciar essa permissão.

---

# HERO (English)

Personal assistant written in Python, with chat, briefings, tasks, history, voice, hand-gesture controls, authentication, and monthly reports.

> **Project status:** under development. This distribution contains source code and example configuration only; it does not include personal data, credentials, a database, or a virtual environment. A clean end-to-end installation has not yet been validated.

## Requirements

- Python 3.11 or newer (use a version supported by your platform and dependencies).
- A configured AI option: local Ollama or a Gemini API key.

## Install on Windows

1. Download or clone the repository and open a terminal in the project folder.
2. Create a virtual environment and install dependencies:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and configure the options you need. Never commit real credentials.
4. For Ollama, install and start Ollama separately and download the configured model. For Gemini, set `PROVIDER=gemini` and put your API key in `GEMINI_API_KEY` in `.env`.
5. Run `python iniciar.py` and open `http://localhost:8900` if the browser does not open automatically. Press `Ctrl+C` to stop the server.

The initial administrator account is created on first access. This package starts without the developer's personal database or settings.

## Security

Do not expose the application directly to the internet without a security review and appropriate HTTPS deployment. Local data is stored in SQLite without application-level encryption. Never publish `.env`, API keys, passwords, databases, private keys, logs, or backups. The `.gitignore` is a safeguard, not a replacement for reviewing staged files and Git history.

## Tests and license

No `tests/` directory or automated test suite is included in this package. Python syntax was checked, but complete functionality has not been verified in a clean environment. No license file is included, so all rights remain reserved unless a license is added.
