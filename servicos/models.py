from ckeditor.fields import RichTextField
from django.db import models
from django.utils.text import slugify


class Servico(models.Model):
    titulo = models.CharField(max_length=150)
    slug = models.SlugField(max_length=160, unique=True, blank=True)
    resumo = models.TextField(max_length=400)
    link = models.CharField(
        "Link externo",
        max_length=300,
        blank=True,
        help_text="Ex.: https://buscarural.com.br",
    )
    descricao = RichTextField()
    imagem = models.ImageField(upload_to="servicos/", blank=True, null=True)
    imagem_estatica = models.CharField(max_length=120, blank=True)
    destaque = models.BooleanField(default=False)
    ativo = models.BooleanField(default=True)
    ordem = models.PositiveIntegerField(default=0)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["ordem", "titulo"]
        verbose_name = "Serviço"
        verbose_name_plural = "Serviços"

    def __str__(self):
        return self.titulo

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.titulo) or "servico"
            slug = base
            n = 1
            while Servico.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def link_rotulo(self):
        if not self.link:
            return ""
        return self.link.replace("https://", "").replace("http://", "").strip("/")

    @property
    def link_url(self):
        if not self.link:
            return ""
        link = self.link.strip()
        if link.startswith(("http://", "https://")):
            return link
        return f"https://{link.lstrip('/')}"

    @property
    def imagem_url(self):
        if self.imagem:
            return self.imagem.url
        if self.imagem_estatica:
            return f"/static/{self.imagem_estatica.lstrip('/')}"
        return "/static/img/servico-1.jpg"
