from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

from clientes.models import PerfilCliente


def _nome_from_user(user, extra=None):
    if extra:
        nome = extra.get("name") or ""
        if not nome:
            given = extra.get("given_name", "")
            family = extra.get("family_name", "")
            nome = f"{given} {family}".strip()
        if nome:
            return nome
    nome = user.get_full_name().strip()
    if nome:
        return nome
    if user.email:
        return user.email.split("@")[0]
    return user.username


class AccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        user = super().save_user(request, user, form, commit=False)
        if commit:
            user.save()
            PerfilCliente.objects.get_or_create(
                user=user,
                defaults={"nome_completo": _nome_from_user(user)},
            )
        return user


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        extra = sociallogin.account.extra_data or {}
        PerfilCliente.objects.get_or_create(
            user=user,
            defaults={"nome_completo": _nome_from_user(user, extra)},
        )
        return user
