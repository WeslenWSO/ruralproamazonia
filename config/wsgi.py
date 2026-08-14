"""
WSGI config for config project.
"""

import fcntl
import os
import sys
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")


def _rodando_no_render():
    return bool(
        os.environ.get("RENDER_EXTERNAL_HOSTNAME")
        or os.environ.get("RENDER", "").lower() in ("true", "1", "yes")
    )


def _preparar_banco_render():
    if not _rodando_no_render():
        return

    lock_path = Path("/tmp/ruralpro_bootstrap.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    lock_file = open(lock_path, "w")
    try:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        lock_file.close()
        return

    try:
        import django

        django.setup()
        from django.conf import settings
        from django.core.management import call_command

        engine = settings.DATABASES["default"]["ENGINE"]
        db_name = settings.DATABASES["default"].get("NAME", "")
        print(
            f"[RuralPro] Banco: {engine} | DATABASE_URL={'sim' if os.environ.get('DATABASE_URL') else 'nao'}",
            file=sys.stderr,
        )

        call_command("migrate", "--no-input", verbosity=1)
        call_command("atualizar_site", verbosity=0)

        if not settings.DATABASES["default"]["ENGINE"].endswith("sqlite3"):
            return

        from django.contrib.auth.models import User
        from servicos.models import Servico

        if not Servico.objects.exists():
            call_command("seed_demo", verbosity=0)
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser(
                "admin",
                "admin@ruralproamazonia.com.br",
                "admin123",
            )
            print("[RuralPro] Admin criado: admin / admin123", file=sys.stderr)
    finally:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
        lock_file.close()


_preparar_banco_render()

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
