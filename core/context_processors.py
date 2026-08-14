from core.models import ConfiguracaoSite
from clientes.social_auth import algum_provedor_social, provedores_sociais


def site_config(request):
    try:
        config = ConfiguracaoSite.load()
    except Exception:
        config = None
    return {
        "site_config": config,
        "social_providers": provedores_sociais(),
        "social_login_disponivel": algum_provedor_social(),
    }
