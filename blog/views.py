from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render

from blog.models import Post


def lista_posts(request):
    qs = Post.objects.filter(publicado=True)
    paginator = Paginator(qs, 9)
    page = request.GET.get("page")
    posts = paginator.get_page(page)
    return render(request, "blog/lista.html", {"posts": posts})


def detalhe_post(request, slug):
    post = get_object_or_404(Post, slug=slug, publicado=True)
    recentes = Post.objects.filter(publicado=True).exclude(pk=post.pk)[:3]
    return render(request, "blog/detalhe.html", {"post": post, "recentes": recentes})
