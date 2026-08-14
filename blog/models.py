from ckeditor.fields import RichTextField
from django.db import models
from django.utils.text import slugify


class Categoria(models.Model):
    nome = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=90, unique=True, blank=True)

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        ordering = ["nome"]

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome) or "categoria"
        super().save(*args, **kwargs)


class Post(models.Model):
    titulo = models.CharField(max_length=200)
    slug = models.SlugField(max_length=210, unique=True, blank=True)
    categoria = models.ForeignKey(
        Categoria, on_delete=models.SET_NULL, null=True, blank=True, related_name="posts"
    )
    autor = models.CharField(max_length=100, default="Rural Pro Amazônia")
    resumo = models.TextField(max_length=500)
    conteudo = RichTextField()
    imagem = models.ImageField(upload_to="blog/", blank=True, null=True)
    imagem_estatica = models.CharField(max_length=120, blank=True)
    link_externo = models.URLField("Link externo", blank=True)
    destaque = models.BooleanField(default=False)
    publicado = models.BooleanField(default=True)
    publicado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-publicado_em"]
        verbose_name = "Post"
        verbose_name_plural = "Posts"

    def __str__(self):
        return self.titulo

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.titulo) or "post"
            slug = base
            n = 1
            while Post.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def imagem_url(self):
        if self.imagem:
            return self.imagem.url
        if self.imagem_estatica:
            return f"/static/{self.imagem_estatica.lstrip('/')}"
        return "/static/img/blog-1.jpg"
