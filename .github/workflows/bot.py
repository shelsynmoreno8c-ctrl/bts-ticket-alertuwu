import os
import hashlib
import json
import requests
from bs4 import BeautifulSoup

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

URL = "https://www.ticketmaster.co/event/bts-world-tour-venta-general-sabado-3-octubre"

ZONAS = ["norte", "sur", "oriental"]

STATE_FILE = "ticket_state.json"


def enviar_telegram(mensaje):
    telegram_url = (
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    )

    requests.post(
        telegram_url,
        data={
            "chat_id": CHAT_ID,
            "text": mensaje,
            "disable_web_page_preview": False
        },
        timeout=20
    )


def obtener_pagina():
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(
        URL,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    texto = soup.get_text(" ", strip=True).lower()

    return texto


def cargar_estado():
    if not os.path.exists(STATE_FILE):
        return None

    with open(STATE_FILE, "r", encoding="utf-8") as archivo:
        return json.load(archivo)


def guardar_estado(datos):
    with open(STATE_FILE, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo)


def revisar():
    texto = obtener_pagina()

    zonas_detectadas = [
        zona.upper()
        for zona in ZONAS
        if zona in texto
    ]

    agotado = "agotado" in texto

    informacion = {
        "hash": hashlib.sha256(
            texto.encode("utf-8")
        ).hexdigest(),
        "zonas": zonas_detectadas,
        "agotado": agotado
    }

    estado_anterior = cargar_estado()

    # Primera ejecución: guarda el estado inicial
    if estado_anterior is None:
        guardar_estado(informacion)

        print("Estado inicial guardado.")
        print(informacion)

        return

    cambio = (
        informacion["hash"] != estado_anterior["hash"]
    )

    disponibilidad_posible = (
        estado_anterior.get("agotado", True)
        and not agotado
    )

    if disponibilidad_posible:
        mensaje = (
            "🚨🚨 ALERTA BTS 🚨🚨\n\n"
            "¡La página del 3 de octubre cambió y ya no "
            "muestra el estado AGOTADO!\n\n"
            f"📍 Zonas detectadas: {', '.join(zonas_detectadas) or 'Revisar página'}\n\n"
            "🎟️ ENTRA AHORA A TICKETMASTER:\n"
            f"{URL}"
        )

        enviar_telegram(mensaje)

    elif cambio:
        mensaje = (
            "🔔 BTS Ticket Alert\n\n"
            "Detecté un cambio en la página del evento "
            "del 3 de octubre.\n\n"
            "Esto no garantiza disponibilidad, pero puede "
            "valer la pena revisar:\n\n"
            f"{URL}"
        )

        enviar_telegram(mensaje)

    guardar_estado(informacion)

    print("Revisión terminada.")
    print(informacion)


if __name__ == "__main__":
    revisar()
