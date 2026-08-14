# Rural Pro Amazônia

Site institucional em Django para a **Rural Pro Amazônia**, com foco em agronegócio sustentável na região Amazônica. Layout inspirado em portais setoriais (topbar, header, hero em carrossel, pilares, cards de serviços e blog).

## Requisitos

- Python 3.10+
- pip

## Instalação

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

No Linux/macOS, use `source .venv/bin/activate` e `cp .env.example .env`.

## Banco de dados e conteúdo demo

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py seed_demo
```

## Área do cliente — login social

Cadastro e login disponíveis em `/clientes/login/` e `/clientes/cadastro/` com:

- **E-mail e senha**
- **Google**
- **Apple**
- **Facebook**

Configure as credenciais OAuth no arquivo `.env` (veja `.env.example`) e execute:

```bash
copy .env.example .env
# Edite .env e preencha GOOGLE_CLIENT_ID e GOOGLE_CLIENT_SECRET
python manage.py setup_social_auth
```

Depois reinicie o servidor (`python manage.py runserver`).

### Google
1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um projeto → **APIs e Serviços** → **Credenciais** → **Criar ID do cliente OAuth**
3. Tipo: **Aplicativo da Web**
4. **Origens JavaScript autorizadas:** `http://127.0.0.1:8000` e `http://localhost:8000`
5. **URIs de redirecionamento autorizados:**
   - `http://127.0.0.1:8000/accounts/google/login/callback/`
   - `http://localhost:8000/accounts/google/login/callback/`
6. Copie **ID do cliente** e **Chave secreta** para o `.env`

### Facebook
1. Crie um app em [Meta for Developers](https://developers.facebook.com/)
2. URI de redirecionamento OAuth: `http://127.0.0.1:8000/accounts/facebook/login/callback/`

### Apple
1. Configure Sign in with Apple no [Apple Developer](https://developer.apple.com/)
2. URI de retorno: `http://127.0.0.1:8000/accounts/apple/login/callback/`

## Executar

```bash
python manage.py runserver
```

Acesse `http://127.0.0.1:8000/`. Painel admin: `/admin/` (após `seed_demo`: usuário `admin`, senha `admin123` — altere em produção).

## Deploy no Render

O projeto inclui `render.yaml` (Blueprint) com **PostgreSQL** + **Web Service** Django.

### 1. Subir o código no GitHub

Certifique-se de que o repositório está no GitHub (sem `.env` — já está no `.gitignore`).

### 2. Criar no Render

1. Acesse [render.com](https://render.com) → **New** → **Blueprint**
2. Conecte o repositório `ruralproamazonia`
3. O Render lê o `render.yaml` e cria:
   - Banco PostgreSQL (`ruralpro-db`)
   - Serviço web (`ruralproamazonia`)

### 3. Variáveis de ambiente (painel Render → Environment)

Preencha manualmente após o deploy:

| Variável | Exemplo |
|----------|---------|
| `SITE_BASE_URL` | `https://ruralproamazonia.onrender.com` |
| `SITE_DOMAIN` | `ruralproamazonia.onrender.com` |
| `GEMINI_API_KEY` | chave do Google AI Studio |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | OAuth (callbacks com URL do Render) |
| `ALLOWED_HOSTS` | `ruralproamazonia.onrender.com` |
| `CSRF_TRUSTED_ORIGINS` | `https://ruralproamazonia.onrender.com` |

`SECRET_KEY`, `DATABASE_URL` e `RENDER` são definidos automaticamente pelo Blueprint.

### 4. Primeiro deploy — conteúdo inicial

No **Shell** do serviço no Render (ou localmente apontando ao Postgres):

```bash
python manage.py seed_demo
python manage.py setup_social_auth
python manage.py createsuperuser
```

### 5. OAuth no Google (produção)

Adicione no Google Cloud Console:

- **Origens:** `https://SEU-APP.onrender.com`
- **Redirect URI:** `https://SEU-APP.onrender.com/accounts/google/login/callback/`

### Limitações no Render (plano free)

- **BuscarRural / Selo Verde (Selenium):** não roda no Render padrão (exige Chrome local). O site, blog, login e parecer Gemini funcionam; a consulta Selo Verde use em ambiente local ou em servidor com Chrome.
- **Arquivos em `media/`:** disco efêmero — uploads podem sumir ao redeploy. Para produção, use storage externo (S3, etc.).

### Build local (simular produção)

```bash
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
gunicorn config.wsgi:application --bind 127.0.0.1:8000
```

## Gerar arquivos do projeto

Se precisar recriar templates e apps a partir do gerador:

```bash
python _build_site.py
```

## Estrutura

- `core/` — home, slides, configuração do site, história
- `servicos/` — listagem e detalhe de serviços
- `blog/` — posts e categorias
- `contato/` — formulário de mensagens
- `clientes/` — cadastro, login e painel do cliente
- `templates/` e `static/` — front-end institucional

## Licença

Uso interno / projeto institucional Rural Pro Amazônia.
