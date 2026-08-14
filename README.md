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
cp .env.example .env
```

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
