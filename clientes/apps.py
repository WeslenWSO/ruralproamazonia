from django.apps import AppConfig


class ClientesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "clientes"

    def ready(self):
        from django.db.models.signals import post_migrate

        import clientes.admin_oauth  # noqa: F401
        from clientes.social_auth import sync_social_apps

        def _sync(sender, **kwargs):
            if sender.name != "clientes":
                return
            try:
                sync_social_apps()
            except Exception:
                pass

        post_migrate.connect(_sync, sender=self)
