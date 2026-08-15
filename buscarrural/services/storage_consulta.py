import json
import logging
import shutil
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)


def pasta_consulta(consulta_id):
    pasta = Path(settings.MEDIA_ROOT) / "buscarrural" / "consultas" / str(consulta_id)
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta


def salvar_resultado_consulta(consulta):
    pasta = pasta_consulta(consulta.pk)
    meta = {
        "consulta_id": consulta.pk,
        "numero_car": consulta.numero_car,
        "usuario_id": consulta.usuario_id,
        "atualizado_em_site": consulta.atualizado_em_site,
        "criado_em": consulta.criado_em.isoformat() if consulta.criado_em else "",
    }

    (pasta / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (pasta / "dados.json").write_text(
        json.dumps(consulta.dados or {}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    if consulta.parecer_diagnostico:
        (pasta / "diagnostico.json").write_text(
            json.dumps(consulta.parecer_diagnostico, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    if consulta.parecer:
        (pasta / "parecer.txt").write_text(consulta.parecer, encoding="utf-8")
    if consulta.alertas_criticos:
        (pasta / "alertas_criticos.txt").write_text(
            consulta.alertas_criticos,
            encoding="utf-8",
        )

    if consulta.imagem_terreno:
        try:
            origem = Path(consulta.imagem_terreno.path)
            if origem.exists():
                shutil.copy2(origem, pasta / "terreno.png")
        except (ValueError, OSError) as exc:
            logger.warning("Não foi possível copiar mapa terreno: %s", exc)

    if consulta.pdf:
        try:
            origem_pdf = Path(consulta.pdf.path)
            if origem_pdf.exists():
                shutil.copy2(origem_pdf, pasta / "diagnostico.pdf")
        except (ValueError, OSError) as exc:
            logger.warning("Não foi possível copiar PDF: %s", exc)

    return pasta


def anexar_pdf_consulta(consulta, caminho_pdf):
    caminho = Path(caminho_pdf)
    if not caminho.exists():
        return consulta
    nome = f"diagnostico_{consulta.pk}_{consulta.numero_car[:20]}.pdf".replace("/", "-")
    with caminho.open("rb") as arquivo:
        consulta.pdf.save(nome, ContentFile(arquivo.read()), save=True)
    return consulta
