from ckeditor.fields import RichTextField
from django.db import models
from django.utils.text import slugify
import re


class SingletonModel(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class ConfiguracaoSite(SingletonModel):
    nome_site = models.CharField("Nome do site", max_length=120, default="Rural Pro Amazônia")
    slogan = models.CharField(max_length=200, blank=True)
    telefone = models.CharField(max_length=30, blank=True)
    whatsapp = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    endereco = models.CharField(max_length=255, blank=True)
    cidade = models.CharField(max_length=80, blank=True, default="Manaus")
    estado = models.CharField(max_length=2, blank=True, default="AM")
    facebook = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    youtube = models.URLField(blank=True)
    logo = models.ImageField(upload_to="site/", blank=True, null=True)
    favicon = models.ImageField(upload_to="site/", blank=True, null=True)
    pilar_1_titulo = models.CharField(max_length=80, default="Sustentabilidade")
    pilar_1_texto = models.TextField(blank=True)
    pilar_2_titulo = models.CharField(max_length=80, default="Inovação")
    pilar_2_texto = models.TextField(blank=True)
    pilar_3_titulo = models.CharField(max_length=80, default="Comunidade")
    pilar_3_texto = models.TextField(blank=True)
    texto_rodape = models.TextField(blank=True)
    meta_description = models.CharField(max_length=160, blank=True)

    class Meta:
        verbose_name = "Configuração do site"
        verbose_name_plural = "Configuração do site"

    def __str__(self):
        return self.nome_site

    @property
    def whatsapp_numero(self):
        return re.sub(r"\D", "", self.whatsapp or "")


class HistoriaEmpresa(SingletonModel):
    titulo = models.CharField(max_length=200, default="Nossa história")
    conteudo = RichTextField()
    imagem = models.ImageField(upload_to="historia/", blank=True, null=True)

    class Meta:
        verbose_name = "História da empresa"
        verbose_name_plural = "História da empresa"

    def __str__(self):
        return self.titulo


class SlideHero(models.Model):
    titulo = models.CharField(max_length=150)
    subtitulo = models.CharField(max_length=255, blank=True)
    imagem = models.ImageField(upload_to="slides/", blank=True, null=True)
    imagem_estatica = models.CharField(
        "Imagem estática (static/img)",
        max_length=120,
        blank=True,
        help_text="Caminho relativo em static, ex: img/hero-1.jpg",
    )
    texto_botao = models.CharField(max_length=60, blank=True, default="Saiba mais")
    link = models.CharField(max_length=255, blank=True)
    ordem = models.PositiveIntegerField(default=0)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["ordem", "id"]
        verbose_name = "Slide do hero"
        verbose_name_plural = "Slides do hero"

    def __str__(self):
        return self.titulo

    @property
    def imagem_url(self):
        if self.imagem:
            return self.imagem.url
        if self.imagem_estatica:
            return f"/static/{self.imagem_estatica.lstrip('/')}"
        return "/static/img/hero-1.jpg"
