from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from config.admin import admin_site

urlpatterns = [
    path("admin/", admin_site.urls),
    path("accounts/", include("allauth.urls")),
    path("", include("core.urls")),
    path("servicos/", include("servicos.urls")),
    path("blog/", include("blog.urls")),
    path("contato/", include("contato.urls")),
    path("clientes/", include("clientes.urls")),
    path("buscarrural/", include("buscarrural.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
