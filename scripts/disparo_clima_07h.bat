@echo off
REM Disparo diario do clima — envia direto ao cliente (API Meta no .env)
cd /d "%~dp0\.."
python manage.py enviar_clima_whatsapp --agora --fonte noticias
