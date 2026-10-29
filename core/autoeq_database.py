"""
AutoEq Calibration Database & Acoustic Compensation Engine — HeadsetPlus Studio
Autor: Matheus Veras
Licença: Source-Available Proprietary (Ver LICENSE.md)

Base de dados de calibração acústica profissional inspirada no projeto AutoEq (Jaakkopasanen).
Mapeia curvas de compensação Harman Target 2019 / Neutral para DSP de 6 bandas (Clear Bass + 5 bandas paramétricas).
"""

from typing import Any, Dict, List, Optional

# Banco de dados curado com calibrações acústicas Harman Target / Oratory1990 / Crinacle
AUTOEQ_DATABASE: List[Dict[str, Any]] = [
    # ==================== SONY ====================
    {
        "id": "sony-wf-1000xm3-harman",
        "name": "Sony WF-1000XM3 (Harman Neutral)",
        "brand": "Sony",
        "type": "TWS In-Ear",
        "target": "Harman Target In-Ear",
        "clear_bass": 2,
        "bands": [-1, 2, 4, 3, 2],
        "desc": "Ajuste de referência Harman: corrige o recuo dos médios-altos (2.5kHz) e dá clareza vocal sem sibilância.",
    },
    {
        "id": "sony-wf-1000xm4-harman",
        "name": "Sony WF-1000XM4 (Harman Neutral)",
        "brand": "Sony",
        "type": "TWS In-Ear",
        "target": "Harman Target In-Ear",
        "clear_bass": -1,
        "bands": [0, 1, 3, 4, 3],
        "desc": "Compensa o calor excessivo nos graves e traz os agudos e a clareza aos padrões Harman.",
    },
    {
        "id": "sony-wf-1000xm5-harman",
        "name": "Sony WF-1000XM5 (Harman Neutral)",
        "brand": "Sony",
        "type": "TWS In-Ear",
        "target": "Harman Target In-Ear",
        "clear_bass": 0,
        "bands": [-1, 1, 2, 3, 1],
        "desc": "Equilíbrio tonal perfeito com resposta plana de estúdio.",
    },
    {
        "id": "sony-wh-1000xm4-harman",
        "name": "Sony WH-1000XM4 (Over-Ear Harman)",
        "brand": "Sony",
        "type": "Over-Ear ANC",
        "target": "Harman Over-Ear",
        "clear_bass": -2,
        "bands": [-2, 1, 3, 4, 1],
        "desc": "Reduz o 'muddy bass' de fábrica e abre o palco sonoro e os harmônicos de cordas.",
    },
    {
        "id": "sony-wh-1000xm5-harman",
        "name": "Sony WH-1000XM5 (Over-Ear Harman)",
        "brand": "Sony",
        "type": "Over-Ear ANC",
        "target": "Harman Over-Ear",
        "clear_bass": -1,
        "bands": [-1, 0, 2, 3, 2],
        "desc": "Neutralidade acústica de estúdio para masterização e audição crítica.",
    },
    {
        "id": "sony-linkbuds-s-harman",
        "name": "Sony LinkBuds S (Harman Neutral)",
        "brand": "Sony",
        "type": "TWS In-Ear",
        "target": "Harman Target In-Ear",
        "clear_bass": 1,
        "bands": [0, 1, 2, 2, 1],
        "desc": "Linearização de resposta para vocais cristalinos.",
    },
    {
        "id": "sony-wf-c500-harman",
        "name": "Sony WF-C500 (Harman Neutral)",
        "brand": "Sony",
        "type": "TWS In-Ear",
        "target": "Harman Target In-Ear",
        "clear_bass": 3,
        "bands": [1, 2, 3, 1, 0],
        "desc": "Enriquece a resposta de frequências de entrada dando corpo audiófilo.",
    },

    # ==================== APPLE ====================
    {
        "id": "apple-airpods-pro-harman",
        "name": "Apple AirPods Pro (1ª Geração)",
        "brand": "Apple",
        "type": "TWS In-Ear",
        "target": "Harman Target In-Ear",
        "clear_bass": 2,
        "bands": [0, 1, 1, 3, 2],
        "desc": "Adiciona subgraves envolventes e amplia a extensão dos agudos além de 10kHz.",
    },
    {
        "id": "apple-airpods-pro-2-harman",
        "name": "Apple AirPods Pro 2 (USB-C / Lightning)",
        "brand": "Apple",
        "type": "TWS In-Ear",
        "target": "Harman Target In-Ear",
        "clear_bass": 1,
        "bands": [0, 0, 1, 2, 2],
        "desc": "Pequeno realce nos agudos superiores mantendo a excelente assinatura quase Harman original.",
    },
    {
        "id": "apple-airpods-max-harman",
        "name": "Apple AirPods Max (Over-Ear)",
        "brand": "Apple",
        "type": "Over-Ear ANC",
        "target": "Harman Over-Ear",
        "clear_bass": 0,
        "bands": [-1, 1, 2, 3, 1],
        "desc": "Compensa o leve vale em 4kHz trazendo brilho extra para pratos e ar de bateria.",
    },
    {
        "id": "apple-airpods-3-harman",
        "name": "Apple AirPods 3 (Open-Fit)",
        "brand": "Apple",
        "type": "Open Earbuds",
        "target": "Diffuse Field / Harman",
        "clear_bass": 5,
        "bands": [2, 1, 0, 2, 3],
        "desc": "Compensa o vazamento acústico natural do design semi-aberto com reforço de graves e agudos dinâmicos.",
    },

    # ==================== SAMSUNG ====================
    {
        "id": "samsung-galaxy-buds-2-pro",
        "name": "Samsung Galaxy Buds 2 Pro",
        "brand": "Samsung",
        "type": "TWS In-Ear",
        "target": "Harman Target In-Ear",
        "clear_bass": 0,
        "bands": [0, 0, 0, 1, 1],
        "desc": "Já segue muito de perto a curva Harman da AKG; leve refinamento nos agudos finos.",
    },
    {
        "id": "samsung-galaxy-buds-fe",
        "name": "Samsung Galaxy Buds FE",
        "brand": "Samsung",
        "type": "TWS In-Ear",
        "target": "Harman Target In-Ear",
        "clear_bass": 1,
        "bands": [-1, 1, 2, 2, 2],
        "desc": "Abre o palco e equilibra a transição de médios para vocais femininos.",
    },
    {
        "id": "samsung-galaxy-buds-pro",
        "name": "Samsung Galaxy Buds Pro (1ª Geração)",
        "brand": "Samsung",
        "type": "TWS In-Ear",
        "target": "Harman Target In-Ear",
        "clear_bass": -1,
        "bands": [-1, 0, 1, 3, 2],
        "desc": "Contém os picos de 6kHz mantendo o punch dinâmico.",
    },

    # ==================== REALME ====================
    {
        "id": "realme-buds-air-5-pro",
        "name": "realme Buds Air 5 Pro (Dual Driver Coaxial)",
        "brand": "Realme",
        "type": "TWS In-Ear",
        "target": "Harman Target In-Ear",
        "clear_bass": 1,
        "bands": [-2, 0, 3, 2, 1],
        "desc": "Domina o subgrave agressivo de fábrica e extrai a máxima resolução do planar tweeter integrado.",
    },
    {
        "id": "realme-buds-air-3",
        "name": "realme Buds Air 3",
        "brand": "Realme",
        "type": "TWS In-Ear",
        "target": "Harman Target In-Ear",
        "clear_bass": 0,
        "bands": [-1, 1, 3, 3, 2],
        "desc": "Ajuste para clareza e separação instrumental.",
    },

    # ==================== SENNHEISER ====================
    {
        "id": "sennheiser-momentum-tw3",
        "name": "Sennheiser Momentum True Wireless 3 / 4",
        "brand": "Sennheiser",
        "type": "TWS In-Ear",
        "target": "Harman Target In-Ear",
        "clear_bass": 0,
        "bands": [-1, 1, 2, 2, 3],
        "desc": "Mantém os graves característicos da Sennheiser e abre as microfrequências dos agudos.",
    },
    {
        "id": "sennheiser-momentum-4-wireless",
        "name": "Sennheiser Momentum 4 Wireless (Over-Ear)",
        "brand": "Sennheiser",
        "type": "Over-Ear ANC",
        "target": "Harman Over-Ear",
        "clear_bass": -3,
        "bands": [-2, 1, 2, 3, 2],
        "desc": "Abaixa a ênfase excessiva em 100Hz para uma resposta equilibrada com fidelidade de estúdio.",
    },
    {
        "id": "sennheiser-hd600-reference",
        "name": "Sennheiser HD 600 / HD 650 (Audiophile Reference)",
        "brand": "Sennheiser",
        "type": "Open-Back Studio",
        "target": "Harman Neutral Target",
        "clear_bass": 4,
        "bands": [2, 0, -1, 1, 2],
        "desc": "Estende a sub-extensão que falta nos clássicos abertos e preserva os médios lendários.",
    },

    # ==================== BOSE ====================
    {
        "id": "bose-qc45-harman",
        "name": "Bose QuietComfort 45 / SE",
        "brand": "Bose",
        "type": "Over-Ear ANC",
        "target": "Harman Over-Ear",
        "clear_bass": 2,
        "bands": [0, -1, 1, -2, -1],
        "desc": "Atenua o pico incômodo em 6kHz dos QC45 para um som macio e relaxante de longa duração.",
    },
    {
        "id": "bose-qc-ultra-harman",
        "name": "Bose QuietComfort Ultra",
        "brand": "Bose",
        "type": "Over-Ear ANC",
        "target": "Harman Over-Ear",
        "clear_bass": -1,
        "bands": [0, 1, 1, 2, 1],
        "desc": "Linearização de resposta acústica com espacialização estéreo expandida.",
    },
    {
        "id": "bose-qc-earbuds-2",
        "name": "Bose QuietComfort Earbuds II",
        "brand": "Bose",
        "type": "TWS In-Ear",
        "target": "Harman Target In-Ear",
        "clear_bass": -2,
        "bands": [-1, 1, 3, 2, 1],
        "desc": "Controle de graves pesados para vocais em primeiro plano.",
    },

    # ==================== GAMING & ESPORTS ====================
    {
        "id": "logitech-g-pro-x-wireless",
        "name": "Logitech G PRO X Wireless Gaming",
        "brand": "Logitech",
        "type": "Gaming Headset",
        "target": "Harman / Competitive FPS",
        "clear_bass": -2,
        "bands": [-1, 2, 5, 4, 1],
        "desc": "Equalização competitiva otimizada para passos no CS2, Valorant e Warzone sem fadiga auricular.",
    },
    {
        "id": "hyperx-cloud-2-wireless",
        "name": "HyperX Cloud II / Cloud Alpha Wireless",
        "brand": "HyperX",
        "type": "Gaming Headset",
        "target": "Harman Over-Ear",
        "clear_bass": 1,
        "bands": [-1, 1, 2, -1, 2],
        "desc": "Remove o resíduo metálico dos agudos e estabiliza a curva para audição musical e jogos.",
    },
    {
        "id": "steelseries-arctis-nova-pro",
        "name": "SteelSeries Arctis Nova Pro",
        "brand": "SteelSeries",
        "type": "Gaming Headset",
        "target": "Sonar / Harman",
        "clear_bass": 1,
        "bands": [0, 2, 3, 4, 2],
        "desc": "Calibração estilo SteelSeries Sonar com nitidez cirúrgica de posicionamento 3D.",
    },

    # ==================== ESTÚDIO & IEMS AUDIÓFILOS ====================
    {
        "id": "audio-technica-m50x",
        "name": "Audio-Technica ATH-M50x",
        "brand": "Audio-Technica",
        "type": "Studio Monitor",
        "target": "Harman Over-Ear",
        "clear_bass": -2,
        "bands": [-2, 1, 1, -2, 1],
        "desc": "Domesticador do grave estufado e do pico em 9kHz para mixagem e masterização fiel.",
    },
    {
        "id": "moondrop-aria-harman",
        "name": "Moondrop Aria / Chu II / Blessing 3",
        "brand": "Moondrop",
        "type": "Audiophile IEM",
        "target": "VDSF / Harman Target",
        "clear_bass": 2,
        "bands": [0, 0, 1, 2, 2],
        "desc": "Refinamento da curva VDSF da Moondrop para timbragem vocal perfeita.",
    },
    {
        "id": "tangzu-wan-er-harman",
        "name": "Tangzu Wan'er S.G / 7Hz Zero",
        "brand": "Tangzu",
        "type": "Audiophile IEM",
        "target": "Harman Target In-Ear",
        "clear_bass": 1,
        "bands": [0, 1, 1, 2, 1],
        "desc": "Palco sonoro holográfico com corpo equilibrado.",
    },
]


def search_autoeq(query: str, brand_filter: Optional[str] = None, limit: int = 25) -> List[Dict[str, Any]]:
    """Busca em tempo real no banco de calibração AutoEq."""
    q = query.strip().lower()
    results: List[Dict[str, Any]] = []

    for item in AUTOEQ_DATABASE:
        if brand_filter and brand_filter.lower() != "all":
            if item["brand"].lower() != brand_filter.lower():
                continue

        if not q:
            results.append(item)
            continue

        searchable = f"{item['name']} {item['brand']} {item['type']} {item['target']} {item['desc']}".lower()
        if q in searchable:
            results.append(item)

        if len(results) >= limit:
            break

    return results


def get_brands() -> List[str]:
    """Retorna todas as marcas disponíveis no banco de dados."""
    brands = set(item["brand"] for item in AUTOEQ_DATABASE)
    return sorted(list(brands))

