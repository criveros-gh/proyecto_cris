"""B30: metodo de decision de estrategia de personalizacion (RAG / FT completo / PEFT).

Cada respuesta lleva la EVIDENCIA que la sustenta. Se corre el metodo sobre dos
casos del propio proyecto y el resultado alimenta decision_personalizacion.md.
Solo Python estandar: no llama a ninguna API.
"""

TECNICAS = ("RAG", "Fine-tuning completo", "PEFT")


def recomendar_estrategia(respuestas):
    """Devuelve (puntos, ganadoras). Reporta EMPATES: no esconde cual quedo primero."""
    for clave, valor in respuestas.items():
        if not isinstance(valor, bool):          # un "si" (texto) contaria como True
            raise TypeError(f"{clave} debe ser True o False, no {valor!r}")

    puntos = {t: 0 for t in TECNICAS}
    if respuestas["informacion_cambia_seguido"]:
        puntos["RAG"] += 3
    if respuestas["problema_de_formato_o_tono"]:
        puntos["PEFT"] += 2
        puntos["Fine-tuning completo"] += 1
    if respuestas["dataset_grande_y_de_calidad"]:
        puntos["Fine-tuning completo"] += 2
        puntos["PEFT"] += 1
    if respuestas["presupuesto_limitado_o_iterar_rapido"]:
        puntos["RAG"] += 2
        puntos["PEFT"] += 1
    if respuestas["necesita_multiples_variantes"]:
        puntos["PEFT"] += 2

    maximo = max(puntos.values())
    return puntos, [t for t, p in puntos.items() if p == maximo]


def estimar_costo_de_etiquetar(num_ejemplos, minutos_por_ejemplo, costo_por_hora=None):
    horas = num_ejemplos * minutos_por_ejemplo / 60
    return horas, (None if costo_por_hora is None else horas * costo_por_hora)


# --- Caso 1: el servicio RAG del proyecto (responder con informacion propia) ---
CASO_SERVICIO = {
    "problema": "El servicio debe responder preguntas sobre la documentacion del propio "
                "proyecto, citando la fuente.",
    "respuestas": {
        "informacion_cambia_seguido": True,
        "problema_de_formato_o_tono": False,
        "dataset_grande_y_de_calidad": False,
        "presupuesto_limitado_o_iterar_rapido": True,
        "necesita_multiples_variantes": False,
    },
    "evidencia": {
        "informacion_cambia_seguido": "El repositorio tiene 49 commits con actividad en octubre y "
            "noviembre de 2026 (2 de 2 meses); las fuentes del corpus se siguen editando.",
        "problema_de_formato_o_tono": "No hay muestra de 20 respuestas con fallos de formato. El prompt "
            "ya exige citar y 1 de 1 corrida real respondio. Sin evidencia de incumplimiento: False.",
        "dataset_grande_y_de_calidad": "Hay 12 ejemplos etiquetados (dataset_tuning.py); el umbral "
            "es 200. Con menos de 200 la respuesta es False.",
        "presupuesto_limitado_o_iterar_rapido": "La entrega del Gate 2 vence el mismo dia (23:59): "
            "hay que ver el efecto de un cambio en menos de un dia.",
        "necesita_multiples_variantes": "Un solo servicio para un solo tipo de usuario: 1 version.",
    },
}

# --- Caso 2: el clasificador de mensajes a JSON (el candidato a PEFT del B29) ---
CASO_CLASIFICADOR = {
    "problema": "Clasificar el mensaje de un usuario en un JSON fijo {categoria, prioridad}.",
    "respuestas": {
        "informacion_cambia_seguido": False,
        "problema_de_formato_o_tono": False,
        "dataset_grande_y_de_calidad": False,
        "presupuesto_limitado_o_iterar_rapido": True,
        "necesita_multiples_variantes": False,
    },
    "evidencia": {
        "informacion_cambia_seguido": "Las 3 categorias son fijas (emergencia, adopcion, consulta) y "
            "enrutamiento.py no las ha cambiado desde que se definieron.",
        "problema_de_formato_o_tono": "No se midio. enrutamiento.py ya normaliza la salida con "
            "strip().lower() y se probo offline; no hay 3 de 20 fallos documentados: False.",
        "dataset_grande_y_de_calidad": "12 ejemplos, de 200 necesarios.",
        "presupuesto_limitado_o_iterar_rapido": "Mismo plazo de un dia.",
        "necesita_multiples_variantes": "Un solo clasificador: 1 version.",
    },
}

if __name__ == "__main__":
    for nombre, caso in (("servicio", CASO_SERVICIO), ("clasificador", CASO_CLASIFICADOR)):
        puntos, ganadoras = recomendar_estrategia(caso["respuestas"])
        print(f"caso {nombre}: {puntos} -> {ganadoras}")
    horas, _ = estimar_costo_de_etiquetar(200 - 12, 5)
    print(f"etiquetar los 188 ejemplos que faltan: {horas:.1f} horas")
