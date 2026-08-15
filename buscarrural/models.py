from django.conf import settings
from django.db import models


class ConsultaHistorico(models.Model):
    TIPO_SELO_VERDE_ACRE = "selo_verde_acre"

    TIPO_CHOICES = [
        (TIPO_SELO_VERDE_ACRE, "Selo Verde Acre"),
    ]

    STATUS_PENDENTE = "pendente"
    STATUS_SUCESSO = "sucesso"
    STATUS_ERRO = "erro"

    STATUS_CHOICES = [
        (STATUS_PENDENTE, "Pendente"),
        (STATUS_SUCESSO, "Sucesso"),
        (STATUS_ERRO, "Erro"),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="consultas_buscarrural",
    )
    tipo = models.CharField(max_length=40, choices=TIPO_CHOICES, default=TIPO_SELO_VERDE_ACRE)
    numero_car = models.CharField("Código CAR", max_length=120, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDENTE)
    dados = models.JSONField(default=dict, blank=True)
    parecer = models.TextField("Parecer IA", blank=True)
    parecer_diagnostico = models.JSONField("Diagnóstico estruturado IA", default=dict, blank=True)
    alertas_criticos = models.TextField("Alertas críticos IA", blank=True)
    imagem_terreno = models.ImageField(
        upload_to="buscarrural/terreno/",
        blank=True,
        null=True,
        verbose_name="Mapa do imóvel",
    )
    pdf = models.FileField(upload_to="buscarrural/selo_verde/", blank=True, null=True)
    atualizado_em_site = models.CharField(max_length=40, blank=True)
    mensagem_erro = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "Consulta BuscarRural"
        verbose_name_plural = "Histórico BuscarRural"

    def __str__(self):
        return f"{self.numero_car} ({self.get_status_display()})"
