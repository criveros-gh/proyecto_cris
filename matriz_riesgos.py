"""B32: matriz de riesgos del servicio RAG.

puntaje = probabilidad (1-5) x impacto (1-5). Los cortes (15, 9, 4) son una
convencion del programa: se fijan antes y se aplican igual a todos los riesgos.
Cada mitigacion apunta a algo que existe en el repo (con su bloque) y declara
su estado real: construida / parcial / pendiente.
"""

CAMPOS = ("riesgo", "probabilidad", "impacto", "mitigacion", "estado", "supervision")
ESTADOS_VALIDOS = ("construida", "parcial", "pendiente")


def puntaje_riesgo(probabilidad, impacto):
    return probabilidad * impacto


def categoria_riesgo(puntaje):
    if puntaje >= 15:
        return "CRITICO"
    if puntaje >= 9:
        return "ALTO"
    if puntaje >= 4:
        return "MEDIO"
    return "BAJO"


def esta_en_el_limite(probabilidad, impacto):
    """True si mover probabilidad o impacto en 1 punto cambia la categoria
    (la estimacion es una opinion, no una medicion)."""
    actual = categoria_riesgo(puntaje_riesgo(probabilidad, impacto))
    vecinos = [
        (probabilidad + 1, impacto), (probabilidad - 1, impacto),
        (probabilidad, impacto + 1), (probabilidad, impacto - 1),
    ]
    for p2, i2 in vecinos:
        if not (1 <= p2 <= 5 and 1 <= i2 <= 5):
            continue
        if categoria_riesgo(puntaje_riesgo(p2, i2)) != actual:
            return True
    return False


def _entero_1_a_5(valor):
    # bool es subclase de int: True no vale como "1"
    return isinstance(valor, int) and not isinstance(valor, bool) and 1 <= valor <= 5


def validar_riesgo(r):
    """Devuelve una lista de problemas de una fila (vacia si esta bien)."""
    problemas = []
    for campo in CAMPOS:
        if campo not in r:
            problemas.append(f"falta el campo '{campo}'")
    if problemas:
        return problemas
    if not str(r["riesgo"]).strip():
        problemas.append("el riesgo esta vacio")
    for campo in ("probabilidad", "impacto"):
        if not _entero_1_a_5(r[campo]):
            problemas.append(f"'{campo}' debe ser un entero de 1 a 5")
    if r["estado"] not in ESTADOS_VALIDOS:
        problemas.append(f"'estado' debe ser uno de {ESTADOS_VALIDOS}")
    return problemas


def evaluar_matriz(riesgos):
    """Devuelve copias de las filas con puntaje, categoria y al_limite,
    ordenadas de mayor a menor puntaje. No modifica la lista original."""
    for r in riesgos:
        problemas = validar_riesgo(r)
        if problemas:
            raise ValueError(f"fila invalida '{r.get('riesgo', '?')}': {'; '.join(problemas)}")
    filas = []
    for r in riesgos:
        fila = dict(r)
        fila["puntaje"] = puntaje_riesgo(r["probabilidad"], r["impacto"])
        fila["categoria"] = categoria_riesgo(fila["puntaje"])
        fila["al_limite"] = esta_en_el_limite(r["probabilidad"], r["impacto"])
        filas.append(fila)
    return sorted(filas, key=lambda x: -x["puntaje"])


def verificar_matriz(filas):
    """Reglas de la actividad. Devuelve la lista de incumplimientos."""
    fallas = []
    if len(filas) < 5:
        fallas.append("hay menos de 5 riesgos")
    if not any(f["categoria"] in ("ALTO", "CRITICO") for f in filas):
        fallas.append("ningun riesgo ALTO o CRITICO: revisar si se subestima")
    if len({f["categoria"] for f in filas}) < 2:
        fallas.append("todos los riesgos caen en la misma categoria")
    for f in filas:
        if f["categoria"] in ("ALTO", "CRITICO") and not f["supervision"].strip():
            fallas.append(f"'{f['riesgo']}' es {f['categoria']} y no tiene punto de supervision")
    con_bloque = [f for f in filas if "Bloque" in f["mitigacion"] and f["estado"] != "pendiente"]
    if len(con_bloque) < 2:
        fallas.append("menos de 2 mitigaciones apuntan a algo construido con su bloque")
    return fallas


RIESGOS = [
    {"riesgo": "Inyeccion de prompt via documento recuperado",
     "probabilidad": 4, "impacto": 4,
     "mitigacion": "Roles separados, contexto delimitado y filtro de patrones en "
                   "seguridad_prompt.py (Bloque 31); lo descartado queda en el log; "
                   "si todo el contexto es sospechoso no se llama al modelo (servicio_rag.py)",
     "estado": "construida",
     "supervision": "Si el filtro descarta un documento, la respuesta queda pausada con "
                    "interrupt() hasta que una persona decide (servicio_rag.py + "
                    "grafo_supervision.py, Bloque 32)"},
    {"riesgo": "Contenido crudo o datos personales en los logs",
     "probabilidad": 3, "impacto": 5,
     "mitigacion": "logging_rag.py registra huellas y largos, nunca la pregunta ni "
                   "los documentos; test que lo verifica (Bloque 31)",
     "estado": "construida",
     "supervision": "Acceso a los logs restringido y aprobado por una persona "
                    "(control organizacional, fuera del codigo)"},
    {"riesgo": "Respuesta con cita inventada o sin respaldo en las fuentes",
     "probabilidad": 3, "impacto": 4,
     "mitigacion": "Prompt que exige [n] y admitir contexto insuficiente, mas "
                   "verificar_citas en recuperacion.py (Bloque 26); el servicio solo "
                   "entrega fuentes verificadas contra el contexto",
     "estado": "construida",
     "supervision": "Sin citas validas o con citas inventadas la respuesta queda pausada "
                    "para revision humana (servicio_rag.py + grafo_supervision.py)"},
    {"riesgo": "Recuperacion deficiente: el chunk relevante no llega al contexto",
     "probabilidad": 3, "impacto": 3,
     "mitigacion": "precision@k y recall@k sobre 12 casos con k=1/3/5 "
                   "(evaluacion_recuperacion.py, Bloque 27)",
     "estado": "construida",
     "supervision": "Revision humana periodica de los casos con recall bajo al cambiar "
                    "corpus, chunk_size o modelo de embeddings"},
    {"riesgo": "Proveedor del modelo con errores intermitentes (503) o rate limit",
     "probabilidad": 4, "impacto": 3,
     "mitigacion": "Reintentos con backoff en cliente.py (Unidad 2.1) y en "
                   "servicio_rag.py (probado con fallas simuladas, no contra una caida "
                   "real); si persiste devuelve estado 'error' sin Traceback",
     "estado": "construida",
     "supervision": "Si fallan todos los reintentos el servicio avisa y no inventa "
                    "respuesta; un operador decide reintentar o escalar"},
    {"riesgo": "Costo o latencia por consulta fuera de lo esperado",
     "probabilidad": 3, "impacto": 2,
     "mitigacion": "Medicion por etapa y costo real con usage_metadata en "
                   "registro_rag.py (Bloque 28)",
     "estado": "construida",
     "supervision": ""},
    {"riesgo": "Cambio de prompt sin trazabilidad o desplegado sin revision",
     "probabilidad": 3, "impacto": 4,
     "mitigacion": "registro_prompts.py con huella y diff, y grafo_supervision.py "
                   "con aprobacion obligatoria (Bloque 32)",
     "estado": "construida",
     "supervision": "interrupt() en grafo_supervision.py: nadie activa una version sin "
                    "Command(resume=True)"},
    {"riesgo": "Accion irreversible del agente (reembolso) sin aprobacion humana",
     "probabilidad": 2, "impacto": 5,
     "mitigacion": "esperar_aprobacion con timeout y por defecto 'no aprobado' en "
                   "agente_supervision.py (Bloque 23); la herramienta aun no esta "
                   "conectada al agente (ver limites_autonomia_agente.md)",
     "estado": "parcial",
     "supervision": "Aprobacion humana explicita antes de generar_reembolso"},
]


def a_markdown(filas):
    lineas = [
        "# Matriz de riesgos del servicio RAG",
        "",
        "Puntaje = probabilidad x impacto. Cortes: CRITICO >= 15, ALTO >= 9, MEDIO >= 4, BAJO < 4.",
        "`al limite` = mover un punto la probabilidad o el impacto cambia la categoria "
        "(la estimacion es una opinion: conviene que otra persona la revise).",
        "",
        "| Categoria | Puntaje | Riesgo | P | I | Mitigacion | Estado | Supervision | Al limite |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for f in filas:
        lineas.append(
            f"| {f['categoria']} | {f['puntaje']} | {f['riesgo']} | {f['probabilidad']} | "
            f"{f['impacto']} | {f['mitigacion']} | {f['estado']} | "
            f"{f['supervision'] or '-'} | {'si' if f['al_limite'] else 'no'} |"
        )
    return "\n".join(lineas) + "\n"


if __name__ == "__main__":
    filas = evaluar_matriz(RIESGOS)
    for f in filas:
        marca = "[AL LIMITE]" if f["al_limite"] else ""
        print(f"{f['categoria']:8} ({f['puntaje']:2}) - {f['riesgo']} {marca}")
    fallas = verificar_matriz(filas)
    print("\nverificacion:", "OK" if not fallas else fallas)
    with open("matriz_riesgos.md", "w", encoding="utf-8") as archivo:
        archivo.write(a_markdown(filas))
    print("guardado en matriz_riesgos.md")
