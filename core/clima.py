import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from django.core.cache import cache
from django.utils import timezone

MESES_PT = [
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
]
DIAS_PT = [
    "segunda-feira", "terça-feira", "quarta-feira", "quinta-feira",
    "sexta-feira", "sábado", "domingo",
]

MUNICIPIOS_CLIMA = [
    {"id": "rio-branco", "nome": "Rio Branco", "uf": "AC", "lat": -9.975, "lon": -67.824},
    {"id": "capixaba", "nome": "Capixaba", "uf": "AC", "lat": -9.581, "lon": -67.532},
    {"id": "placido-de-castro", "nome": "Plácido de Castro", "uf": "AC", "lat": -8.814, "lon": -67.186},
    {"id": "acrelandia", "nome": "Acrelândia", "uf": "AC", "lat": -9.826, "lon": -66.897},
    {"id": "cruzeiro-do-sul", "nome": "Cruzeiro do Sul", "uf": "AC", "lat": -7.628, "lon": -72.676},
    {"id": "senador-guiomard", "nome": "Senador Guiomard", "uf": "AC", "lat": -10.149, "lon": -67.740},
    {"id": "sena-madureira", "nome": "Sena Madureira", "uf": "AC", "lat": -9.066, "lon": -68.657},
    {"id": "feijo", "nome": "Feijó", "uf": "AC", "lat": -8.165, "lon": -70.355},
    {"id": "tarauaca", "nome": "Tarauacá", "uf": "AC", "lat": -8.161, "lon": -70.766},
    {"id": "brasileia", "nome": "Brasiléia", "uf": "AC", "lat": -10.995, "lon": -68.750},
    {"id": "assis-brasil", "nome": "Assis Brasil", "uf": "AC", "lat": -10.936, "lon": -69.568},
    {"id": "extrema", "nome": "Extrema", "uf": "RO", "lat": -11.690, "lon": -61.020},
    {"id": "vista-alegre-do-abuna", "nome": "Vista Alegre do Abunã", "uf": "RO", "lat": -8.733, "lon": -72.967},
    {"id": "nova-california", "nome": "Nova Califórnia", "uf": "RO", "lat": -8.467, "lon": -63.417},
]

DESCRICAO_CLIMA = {
    0: "Céu limpo",
    1: "Predominantemente limpo",
    2: "Parcialmente nublado",
    3: "Nublado",
    45: "Neblina",
    48: "Neblina com gelo",
    51: "Garoa leve",
    53: "Garoa moderada",
    55: "Garoa forte",
    61: "Chuva fraca",
    63: "Chuva moderada",
    65: "Chuva forte",
    71: "Neve fraca",
    73: "Neve moderada",
    75: "Neve forte",
    80: "Pancadas de chuva",
    81: "Pancadas fortes",
    82: "Pancadas violentas",
    95: "Tempestade",
    96: "Tempestade com granizo",
    99: "Tempestade forte com granizo",
}

ICONE_CLIMA = {
    0: "☀️",
    1: "🌤️",
    2: "⛅",
    3: "☁️",
    45: "🌫️",
    48: "🌫️",
    51: "🌦️",
    53: "🌦️",
    55: "🌧️",
    61: "🌧️",
    63: "🌧️",
    65: "🌧️",
    80: "🌧️",
    81: "🌧️",
    82: "⛈️",
    95: "⛈️",
    96: "⛈️",
    99: "⛈️",
}

CACHE_TTL = 60 * 30
CACHE_ERRO_TTL = 60
OPEN_METEO_HEADERS = {
    "User-Agent": "RuralProAmazonia/1.0 (previsao-clima; +https://ruralproamazonia.com.br)",
    "Accept": "application/json",
}


def _descricao_clima(codigo):
    if codigo in DESCRICAO_CLIMA:
        return DESCRICAO_CLIMA[codigo]
    if codigo in (56, 57):
        return "Garoa congelante"
    if codigo in (66, 67):
        return "Chuva congelante"
    if codigo in (71, 73, 75, 77):
        return "Neve"
    if codigo in (80, 81, 82):
        return "Pancadas de chuva"
    return "Condição variável"


def _icone_clima(codigo):
    if codigo in ICONE_CLIMA:
        return ICONE_CLIMA[codigo]
    if codigo in (61, 63, 65, 66, 67):
        return "🌧️"
    if codigo in (71, 73, 75, 77):
        return "❄️"
    return "🌡️"


def _buscar_previsao(lat, lon, dias=1):
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code",
        "timezone": "America/Rio_Branco",
        "forecast_days": dias,
    }
    ultimo_erro = None
    for tentativa in range(3):
        try:
            response = requests.get(
                "https://api.open-meteo.com/v1/forecast",
                params=params,
                headers=OPEN_METEO_HEADERS,
                timeout=15,
            )
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, json.JSONDecodeError, ValueError) as exc:
            ultimo_erro = exc
            if tentativa < 2:
                time.sleep(0.75 * (tentativa + 1))
    raise ultimo_erro


def obter_clima_municipio(municipio, forcar=False):
    cache_key = f"clima:{municipio['id']}"
    if not forcar:
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

    try:
        dados = _buscar_previsao(municipio["lat"], municipio["lon"], dias=3)
    except (requests.RequestException, json.JSONDecodeError, KeyError, TypeError):
        resultado = {
            "nome": municipio["nome"],
            "uf": municipio["uf"],
            "erro": True,
        }
        cache.set(cache_key, resultado, CACHE_ERRO_TTL)
        return resultado

    atual = dados["current"]
    diario = dados["daily"]
    codigo = int(atual.get("weather_code", 0))
    dias_extra = []
    for idx in range(1, min(3, len(diario["temperature_2m_max"]))):
        cod = int(diario.get("weather_code", [codigo])[idx])
        dias_extra.append(
            {
                "temp_max": round(diario["temperature_2m_max"][idx]),
                "temp_min": round(diario["temperature_2m_min"][idx]),
                "chuva": diario.get("precipitation_sum", [0])[idx],
                "codigo": cod,
                "condicao": _descricao_clima(cod),
            }
        )
    resultado = {
        "id": municipio["id"],
        "nome": municipio["nome"],
        "uf": municipio["uf"],
        "temperatura": round(atual["temperature_2m"]),
        "umidade": int(atual.get("relative_humidity_2m", 0)),
        "precipitacao": atual.get("precipitation", 0),
        "vento": round(atual.get("wind_speed_10m", 0)),
        "temp_max": round(diario["temperature_2m_max"][0]),
        "temp_min": round(diario["temperature_2m_min"][0]),
        "chuva_dia": diario.get("precipitation_sum", [0])[0],
        "condicao": _descricao_clima(codigo),
        "icone": _icone_clima(codigo),
        "codigo": codigo,
        "dias": dias_extra,
        "erro": False,
    }
    cache.set(cache_key, resultado, CACHE_TTL)
    return resultado


def obter_clima_municipios(forcar=False):
    acre = []
    rondonia = []
    por_id = {}

    with ThreadPoolExecutor(max_workers=8) as executor:
        futuros = {
            executor.submit(obter_clima_municipio, municipio, forcar): municipio
            for municipio in MUNICIPIOS_CLIMA
        }
        for futuro in as_completed(futuros):
            municipio = futuros[futuro]
            item = futuro.result()
            por_id[municipio["id"]] = item
            if municipio["uf"] == "AC":
                acre.append(item)
            else:
                rondonia.append(item)

    acre.sort(key=lambda i: i.get("nome", ""))
    rondonia.sort(key=lambda i: i.get("nome", ""))
    return {"acre": acre, "rondonia": rondonia, "por_id": por_id}


def obter_data_clima():
    agora = timezone.localtime(timezone.now())
    return {
        "iso": agora.date().isoformat(),
        "curta": agora.strftime("%d/%m/%Y"),
        "completa": (
            f"{DIAS_PT[agora.weekday()]}, {agora.day} de "
            f"{MESES_PT[agora.month - 1]} de {agora.year}"
        ),
    }
