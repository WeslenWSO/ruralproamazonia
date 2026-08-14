import os


def _credencial(*nomes):
    for nome in nomes:
        valor = os.environ.get(nome, "").strip()
        if valor:
            return valor
    return ""


def google_configurado():
    return bool(_credencial("GOOGLE_CLIENT_ID") and _credencial("GOOGLE_CLIENT_SECRET"))


def facebook_configurado():
    return bool(
        _credencial("FACEBOOK_APP_ID", "FACEBOOK_CLIENT_ID")
        and _credencial("FACEBOOK_APP_SECRET", "FACEBOOK_CLIENT_SECRET")
    )


def apple_configurado():
    return bool(_credencial("APPLE_CLIENT_ID") and _credencial("APPLE_CLIENT_SECRET"))


def _provedores_no_banco():
    try:
        from allauth.socialaccount.models import SocialApp
        from django.contrib.sites.models import Site

        site = Site.objects.get_current()
        return set(
            SocialApp.objects.filter(sites=site)
            .exclude(client_id="")
            .exclude(secret="")
            .values_list("provider", flat=True)
        )
    except Exception:
        return set()


def provedores_sociais():
    no_banco = _provedores_no_banco()
    return {
        "google": "google" in no_banco or google_configurado(),
        "facebook": "facebook" in no_banco or facebook_configurado(),
        "apple": "apple" in no_banco or apple_configurado(),
    }


def algum_provedor_social():
    return any(provedores_sociais().values())


def montar_socialaccount_providers():
    providers = {
        "google": {
            "SCOPE": ["profile", "email"],
            "AUTH_PARAMS": {"access_type": "online"},
        },
        "facebook": {
            "METHOD": "oauth2",
            "SCOPE": ["email", "public_profile"],
            "FIELDS": ["id", "email", "name"],
        },
        "apple": {},
    }

    if google_configurado():
        providers["google"]["APP"] = {
            "client_id": _credencial("GOOGLE_CLIENT_ID"),
            "secret": _credencial("GOOGLE_CLIENT_SECRET"),
            "key": "",
        }

    if facebook_configurado():
        providers["facebook"]["APP"] = {
            "client_id": _credencial("FACEBOOK_APP_ID", "FACEBOOK_CLIENT_ID"),
            "secret": _credencial("FACEBOOK_APP_SECRET", "FACEBOOK_CLIENT_SECRET"),
            "key": "",
        }

    if apple_configurado():
        providers["apple"]["APP"] = {
            "client_id": _credencial("APPLE_CLIENT_ID"),
            "secret": _credencial("APPLE_CLIENT_SECRET"),
            "key": _credencial("APPLE_KEY_ID"),
        }

    return providers


def sync_social_apps():
    from django.contrib.sites.models import Site
    from allauth.socialaccount.models import SocialApp

    site = Site.objects.get_current()
    domain = os.environ.get("SITE_DOMAIN", "127.0.0.1:8000").strip()
    if domain and site.domain != domain:
        site.domain = domain
        site.name = "Rural Pro Amazônia"
        site.save(update_fields=["domain", "name"])

    if google_configurado():
        app, _ = SocialApp.objects.update_or_create(
            provider="google",
            defaults={
                "name": "Google",
                "client_id": _credencial("GOOGLE_CLIENT_ID"),
                "secret": _credencial("GOOGLE_CLIENT_SECRET"),
            },
        )
        app.sites.set([site.pk])

    if facebook_configurado():
        app, _ = SocialApp.objects.update_or_create(
            provider="facebook",
            defaults={
                "name": "Facebook",
                "client_id": _credencial("FACEBOOK_APP_ID", "FACEBOOK_CLIENT_ID"),
                "secret": _credencial("FACEBOOK_APP_SECRET", "FACEBOOK_CLIENT_SECRET"),
            },
        )
        app.sites.set([site.pk])

    if apple_configurado():
        app, _ = SocialApp.objects.update_or_create(
            provider="apple",
            defaults={
                "name": "Apple",
                "client_id": _credencial("APPLE_CLIENT_ID"),
                "secret": _credencial("APPLE_CLIENT_SECRET"),
                "key": _credencial("APPLE_KEY_ID"),
            },
        )
        app.sites.set([site.pk])
