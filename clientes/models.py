from django.conf import settings
from django.db import models


class PerfilCliente(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="perfil")
    nome_completo = models.CharField(max_length=150)
    empresa = models.CharField(max_length=150, blank=True)
    telefone = models.CharField(max_length=30, blank=True)
    documento = models.CharField("CPF/CNPJ", max_length=20, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Perfil de cliente"
        verbose_name_plural = "Perfis de clientes"

    def __str__(self):
        return self.nome_completo or self.user.username
