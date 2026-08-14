from django.db import models
import re


class MensagemContato(models.Model):
    nome = models.CharField(max_length=120)
    email = models.EmailField()
    telefone = models.CharField(max_length=30, blank=True)
    assunto = models.CharField(max_length=150)
    mensagem = models.TextField()
    lida = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "Mensagem de contato"
        verbose_name_plural = "Mensagens de contato"

    def __str__(self):
        return f"{self.nome} — {self.assunto}"


class InscricaoWhatsApp(models.Model):
    nome = models.CharField(max_length=120, blank=True)
    telefone = models.CharField("WhatsApp", max_length=20)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "Inscrição WhatsApp"
        verbose_name_plural = "Inscrições WhatsApp"

    def __str__(self):
        return self.telefone

    @property
    def telefone_formatado(self):
        digits = re.sub(r"\D", "", self.telefone)
        if len(digits) == 11:
            return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
        if len(digits) == 10:
            return f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"
        return self.telefone


class ContatoAlertaClima(models.Model):
    nome = models.CharField(max_length=120, blank=True)
    telefone = models.CharField("WhatsApp", max_length=20)
    ativo = models.BooleanField(default=True)
    ultimo_envio = models.DateTimeField(null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nome", "telefone"]
        verbose_name = "Contato alerta clima"
        verbose_name_plural = "Contatos alerta clima"

    def __str__(self):
        if self.nome:
            return f"{self.nome} ({self.telefone_formatado})"
        return self.telefone_formatado

    @property
    def telefone_formatado(self):
        digits = re.sub(r"\D", "", self.telefone)
        if len(digits) == 11:
            return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
        if len(digits) == 10:
            return f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"
        return self.telefone
