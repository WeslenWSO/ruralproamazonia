from pathlib import Path
content = r'''from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from blog.models import Categoria, Post
from core.models import ConfiguracaoSite, HistoriaEmpresa, SlideHero
from servicos.models import Servico


class Command(BaseCommand):
    help = "Popula dados de demonstracao do site Rural Pro Amazonia"

    def handle(self, *args, **options):
        config = ConfiguracaoSite.load()
        config.nome_site = "Rural Pro Amaz\u00f4nia"
        config.slogan = "Solu\u00e7\u00f5es sustent\u00e1veis para o agroneg\u00f3cio na Amaz\u00f4nia"
        config.telefone = "(92) 3000-0000"
        config.whatsapp = "5592300000000"
        config.email = "contato@ruralproamazonia.com.br"
        config.endereco = "Av. Example, 1000 \u2014 Adrian\u00f3polis"
        config.cidade = "Manaus"
        config.estado = "AM"
        config.pilar_1_titulo = "Sustentabilidade"
        config.pilar_1_texto = "Pr\u00e1ticas respons\u00e1veis que preservam a floresta e geram valor."
        config.pilar_2_titulo = "Inova\u00e7\u00e3o"
        config.pilar_2_texto = "Tecnologia e conhecimento aplicados ao campo amaz\u00f4nico."
        config.pilar_3_titulo = "Comunidade"
        config.pilar_3_texto = "Parcerias com produtores e cooperativas em toda a regi\u00e3o."
        config.texto_rodape = "\u00a9 Rural Pro Amaz\u00f4nia. Todos os direitos reservados."
        config.meta_description = "Consultoria e servi\u00e7os para o agroneg\u00f3cio sustent\u00e1vel na Amaz\u00f4nia."
        config.save()

        historia = HistoriaEmpresa.load()
        historia.titulo = "Nossa hist\u00f3ria na Amaz\u00f4nia"
        historia.conteudo = (
            "<p>A <strong>Rural Pro Amaz\u00f4nia</strong> nasceu da uni\u00e3o entre experi\u00eancia t\u00e9cnica "
            "e compromisso com o desenvolvimento sustent\u00e1vel da regi\u00e3o.</p>"
            "<p>Atuamos apoiando produtores rurais, cooperativas e empresas com consultoria, "
            "capacita\u00e7\u00e3o e solu\u00e7\u00f5es integradas para o campo.</p>"
        )
        historia.save()

        SlideHero.objects.all().delete()
        slides = [
            ("Agroneg\u00f3cio sustent\u00e1vel", "Tecnologia e respeito \u00e0 floresta", "img/hero-1.png", "/servicos/", 1),
            ("Consultoria especializada", "Do planejamento \u00e0 execu\u00e7\u00e3o", "img/hero-2.png", "/contato/", 2),
            ("Fortalecendo comunidades", "Parcerias que transformam", "img/hero-3.png", "/blog/", 3),
        ]
        for titulo, subtitulo, img, link, ordem in slides:
            SlideHero.objects.create(
                titulo=titulo,
                subtitulo=subtitulo,
                imagem_estatica=img,
                link=link,
                ordem=ordem,
                ativo=True,
            )

        Servico.objects.all().delete()
        servicos_data = [
            ("Consultoria agr\u00edcola", "Planejamento de safra e manejo sustent\u00e1vel.", "servico-1.png", True, 1),
            ("Gest\u00e3o ambiental", "Regulariza\u00e7\u00e3o e boas pr\u00e1ticas ambientais.", "servico-2.png", True, 2),
            ("Capacita\u00e7\u00e3o rural", "Treinamentos presenciais e online.", "servico-3.png", True, 3),
        ]
        for titulo, resumo, img, destaque, ordem in servicos_data:
            Servico.objects.create(
                titulo=titulo,
                resumo=resumo,
                descricao=f"<p>{resumo}</p><p>Entre em contato para um diagn\u00f3stico personalizado.</p>",
                imagem_estatica=f"img/{img}",
                destaque=destaque,
                ativo=True,
                ordem=ordem,
            )

        cat, _ = Categoria.objects.get_or_create(slug="noticias", defaults={"nome": "Not\u00edcias"})
        Post.objects.all().delete()
        posts_data = [
            ("Novidades do setor na Amaz\u00f4nia", "Panorama das tend\u00eancias para o agroneg\u00f3cio regional.", "blog-1.png"),
            ("Evento de capacita\u00e7\u00e3o rural", "Inscri\u00e7\u00f5es abertas para workshop gratuito.", "blog-2.png"),
            ("Parceria com cooperativas", "Ampliamos atendimento a produtores associados.", "blog-3.png"),
        ]
        for titulo, resumo, img in posts_data:
            Post.objects.create(
                titulo=titulo,
                resumo=resumo,
                conteudo=f"<p>{resumo}</p>",
                categoria=cat,
                imagem_estatica=f"img/{img}",
                destaque=True,
                publicado=True,
            )

        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@ruralproamazonia.com.br", "admin123")

        self.stdout.write(self.style.SUCCESS("Dados de demonstracao criados com sucesso."))
'''
Path('core/management/commands/seed_demo.py').write_text(content.encode('utf-8').decode('unicode_escape'), encoding='utf-8')
print('written')
