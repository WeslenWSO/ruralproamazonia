from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from blog.models import Categoria, Post
from contato.models import ContatoAlertaClima
from core.models import ConfiguracaoSite, HistoriaEmpresa, SlideHero
from servicos.models import Servico


class Command(BaseCommand):
    help = "Popula dados de demonstracao do site Rural Pro Amazonia"

    def handle(self, *args, **options):
        config = ConfiguracaoSite.load()
        config.nome_site = "Rural Pro Amazônia"
        config.slogan = "Soluções sustentáveis para o agronegócio na Amazônia"
        config.telefone = "(68) 99901-2015"
        config.whatsapp = "5568999012015"
        config.email = "contato@ruralproamazonia.com.br"
        config.endereco = "Av. Example, 1000 — Adrianópolis"
        config.cidade = "Manaus"
        config.estado = "AM"
        config.pilar_1_titulo = "Sustentabilidade"
        config.pilar_1_texto = "Práticas responsáveis que preservam a floresta e geram valor."
        config.pilar_2_titulo = "Inovação"
        config.pilar_2_texto = "Tecnologia e conhecimento aplicados ao campo amazônico."
        config.pilar_3_titulo = "Comunidade"
        config.pilar_3_texto = "Parcerias com produtores e cooperativas em toda a região."
        config.texto_rodape = "© Rural Pro Amazônia. Todos os direitos reservados."
        config.meta_description = "Consultoria e serviços para o agronegócio sustentável na Amazônia."
        config.save()

        historia = HistoriaEmpresa.load()
        historia.titulo = "Nossa história na Amazônia"
        historia.conteudo = (
            "<p>A <strong>Rural Pro Amazônia</strong> nasceu da união entre experiência técnica "
            "e compromisso com o desenvolvimento sustentável da região.</p>"
            "<p>Atuamos apoiando produtores rurais, cooperativas e empresas com consultoria, "
            "capacitação e soluções integradas para o campo.</p>"
        )
        historia.save()

        SlideHero.objects.all().delete()
        slides = [
            ("Agronegócio sustentável", "Tecnologia e respeito à floresta", "img/hero-1.png", "/servicos/", 1),
            ("Consultoria especializada", "Do planejamento à execução", "img/hero-2.png", "/contato/", 2),
            ("Fortalecendo comunidades", "Parcerias que transformam", "img/hero-3.png", "/blog/", 3),
            (
                "Medida de terra por drone",
                "Topografia de precisão para sua propriedade",
                "img/hero-drone-topografia.jpg",
                "/servicos/topografia/",
                4,
            ),
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
            ("Consultoria agrícola", "Planejamento de safra e manejo sustentável.", "servico-1.png", True, 1, None),
            ("Gestão ambiental", "Regularização e boas práticas ambientais.", "servico-2.png", True, 2, None),
            ("Capacitação rural", "Treinamentos presenciais e online.", "servico-3.png", True, 3, None),
            (
                "BuscarRural",
                "Consultas de CAR e CCIR para propriedades rurais.",
                "servico-2.png",
                True,
                4,
                (
                    "<p>O <strong>BuscarRural</strong> reúne consultas "
                    "essenciais para regularização e gestão de imóveis rurais na Amazônia.</p>"
                    "<h3>Selo Verde Acre</h3>"
                    "<p>Consulta socioambiental automática pelo código CAR no portal "
                    "oficial da SEMA/AC, com download do relatório em PDF e histórico salvo.</p>"
                    "<h3>Buscar Car</h3>"
                    "<p>Consulta e acompanhamento do Cadastro Ambiental Rural (CAR).</p>"
                    "<h3>Buscar CCIR</h3>"
                    "<p>Emissão e validação do Certificado de Cadastro de Imóvel Rural (CCIR).</p>"
                ),
            ),
            (
                "Topografia",
                "Medição de áreas e levantamento topográfico com drone.",
                "servico-topografia.jpg",
                True,
                5,
                (
                    "<p>Serviço de <strong>topografia</strong> com tecnologia de "
                    "<strong>drone</strong> para medição precisa de terras rurais.</p>"
                    "<h3>Medição de terra por drone</h3>"
                    "<p>Levantamento de perímetros, áreas cultiváveis e divisas com "
                    "agilidade e precisão centimétrica.</p>"
                    "<h3>Entregáveis</h3>"
                    "<p>Plantas topográficas, memoriais descritivos e dados georreferenciados "
                    "para regularização, financiamento e planejamento da propriedade.</p>"
                ),
            ),
        ]
        links = {"BuscarRural": "https://buscarural.com.br"}
        for titulo, resumo, img, destaque, ordem, descricao_extra in servicos_data:
            descricao = descricao_extra or (
                f"<p>{resumo}</p><p>Entre em contato para um diagnóstico personalizado.</p>"
            )
            Servico.objects.create(
                titulo=titulo,
                resumo=resumo,
                link=links.get(titulo, ""),
                descricao=descricao,
                imagem_estatica=f"img/{img}",
                destaque=destaque,
                ativo=True,
                ordem=ordem,
            )

        cat, _ = Categoria.objects.get_or_create(slug="noticias", defaults={"nome": "Notícias"})
        Post.objects.all().delete()
        posts_data = [
            ("Novidades do setor na Amazônia", "Panorama das tendências para o agronegócio regional.", "blog-1.png"),
            ("Evento de capacitação rural", "Inscrições abertas para workshop gratuito.", "blog-2.png"),
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

        for telefone, nome in (("68999073217", "Contato 1"), ("68992824636", "Contato 2")):
            ContatoAlertaClima.objects.update_or_create(
                telefone=telefone,
                defaults={"nome": nome, "ativo": True},
            )

        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@ruralproamazonia.com.br", "admin123")

        self.stdout.write(self.style.SUCCESS("Dados de demonstracao criados com sucesso."))
