"""Gate 2: servicio RAG integrado.

Une, en un solo flujo, lo construido en el Modulo 2:
  indice persistido (B24-B25) -> embed + busqueda (B26) -> logging y filtro de
  inyeccion (B31) -> prompt con roles y contexto delimitado (B31) -> modelo ->
  verificacion de citas (B26) -> latencia/costo (B28) -> punto de supervision
  humana para respuestas marcadas (B32).

Reglas que cumple (criterios no compensables del Gate 2):
  1. No se cae: los errores del proveedor se reintentan y, si persisten, se
     devuelven como estado "error" sin Traceback.
  2. Toda respuesta entregada trae su fuente verificada contra el contexto.
  3. Ningun log lleva la pregunta ni el texto de los documentos.
  4. Si hubo inyeccion o citas no verificables, la respuesta NO se entrega sola:
     queda pausada (interrupt) hasta que una persona decide.
"""
import logging
import os
import sys
import time
import uuid

import grafo_supervision as gs
import logging_rag as lr
from logging_rag import evento, registrar_consumo
from recuperacion import verificar_citas
from registro_prompts import huella_prompt
from registro_rag import calcular_costo, medir, resumen_error
from seguridad_prompt import PLANTILLA_USUARIO, PROMPT_SISTEMA, construir_mensajes

SIN_CONTEXTO = "No tengo informacion suficiente y verificada para responder esto."
PREGUNTA_VACIA = "Escribe una pregunta para poder buscar en la documentacion."
ERROR_SERVICIO = "No pude responder en este momento. Intenta de nuevo mas tarde."
EN_REVISION = "La respuesta quedo en revision humana antes de entregarse."
RETENIDA = "La respuesta fue retenida por la revision humana."

# Misma huella que registro_prompts.registrar_prompts_del_proyecto (version activa)
HUELLA_PROMPT_ACTIVO = huella_prompt(PROMPT_SISTEMA + "\n---\n" + PLANTILLA_USUARIO)
ERRORES_REINTENTABLES = ("429", "503", "RESOURCE_EXHAUSTED", "UNAVAILABLE")
ARCHIVO_LOG = os.path.join("logs", "servicio_rag.log")


def con_reintentos(operacion, etapa, max_intentos=3, espera_inicial=2, dormir=time.sleep):
    """Repite SOLO ante saturacion/limite (503, 429). Espera 2, 4... s.
    Si se agotan los intentos (o es otro error) lo vuelve a lanzar."""
    espera = espera_inicial
    for intento in range(1, max_intentos + 1):
        try:
            return operacion()
        except Exception as error:
            reintentable = any(c in str(error) for c in ERRORES_REINTENTABLES)
            if not reintentable or intento == max_intentos:
                raise
            evento("reintento_proveedor", logging.WARNING,
                   etapa=etapa, intento=intento, error=resumen_error(error))
            dormir(espera)
            espera *= 2


def _texto(contenido):
    """El contenido del modelo puede ser texto o una lista de bloques."""
    if isinstance(contenido, str):
        return contenido
    partes = []
    for bloque in contenido or []:
        if isinstance(bloque, str):
            partes.append(bloque)
        elif isinstance(bloque, dict) and isinstance(bloque.get("text"), str):
            partes.append(bloque["text"])
    return "".join(partes)


class ServicioRAG:
    def __init__(self, vectorstore, embeddings, llm, k=3, tarifas=None,
                 max_intentos=3, espera_inicial=2, dormir=time.sleep):
        """tarifas = (entrada_por_1000_tokens, salida_por_1000_tokens) o None.
        Las tarifas NO se hardcodean: se toman de la documentacion oficial vigente."""
        self.vectorstore = vectorstore
        self.embeddings = embeddings
        self.llm = llm
        self.k = k
        self.tarifas = tarifas
        self.max_intentos = max_intentos
        self.espera_inicial = espera_inicial
        self.dormir = dormir
        self.app_revision = gs.construir_grafo_revision()

    # ---------- API publica
    def consultar(self, pregunta):
        if not isinstance(pregunta, str) or not pregunta.strip():
            return self._resultado("pregunta_vacia", PREGUNTA_VACIA)
        token = lr.trace_id_var.set("trace-" + uuid.uuid4().hex[:8])
        etapa = {"actual": "inicio"}
        try:
            return self._consultar(pregunta, etapa)
        except Exception as error:   # el servicio no se cae: falla visible y auditable
            evento("error_servicio", logging.ERROR,
                   etapa=etapa["actual"], error=resumen_error(error))
            return self._resultado("error", ERROR_SERVICIO, error=resumen_error(error))
        finally:
            lr.trace_id_var.reset(token)

    def resolver_revision(self, resultado, aprobar):
        """La persona decide sobre una respuesta pendiente. aprobar debe ser bool."""
        if resultado.get("estado") != "pendiente_revision":
            raise ValueError("este resultado no esta pendiente de revision")
        token = lr.trace_id_var.set(resultado["trace_id"])   # misma traza que la consulta
        try:
            final = gs.resolver(self.app_revision, resultado["revision"], aprobar)
            evento("revision_humana_resuelta", aprobado=aprobar)
        finally:
            lr.trace_id_var.reset(token)
        if final["resultado"] == "entregada":
            return self._resultado("entregada", resultado["propuesta"],
                                   trace_id=resultado["trace_id"], fuentes=resultado["fuentes"],
                                   motivos_revision=resultado["motivos_revision"])
        return self._resultado("retenida", RETENIDA, trace_id=resultado["trace_id"],
                               motivos_revision=resultado["motivos_revision"])

    # ---------- Internos
    @staticmethod
    def _resultado(estado, respuesta, **campos):
        base = {
            "trace_id": lr.trace_id_var.get(), "estado": estado, "respuesta": respuesta,
            "fuentes": [], "motivos_revision": [], "n_descartados": 0,
            "tiempos_ms": {}, "tokens": None, "costo": None,
            "prompt_huella": HUELLA_PROMPT_ACTIVO,
        }
        base.update(campos)
        return base

    def _consultar(self, pregunta, etapa):
        tiempos = {}
        lr.registrar_consulta_recibida(pregunta)
        evento("prompt_activo", prompt_huella=HUELLA_PROMPT_ACTIVO,
               modelo=str(getattr(self.llm, "model", None) or getattr(self.llm, "model_name", None)))

        def reintentar(operacion, nombre):
            return con_reintentos(operacion, nombre, self.max_intentos,
                                  self.espera_inicial, self.dormir)

        etapa["actual"] = "embed_query"
        with medir(tiempos, "embed_query"):
            vector = reintentar(lambda: self.embeddings.embed_query(pregunta), "embed_query")

        etapa["actual"] = "busqueda_vectorial"
        with medir(tiempos, "busqueda_vectorial"):
            documentos = self.vectorstore.similarity_search_by_vector(vector, k=self.k)

        etapa["actual"] = "filtro_inyeccion"
        limpios = lr.filtrar_y_registrar(documentos)
        n_descartados = len(documentos) - len(limpios)

        if not limpios:   # nada confiable que citar: no se le pide al modelo "hacer lo que pueda"
            evento("sin_contexto_confiable", logging.WARNING,
                   n_recuperados=len(documentos), n_descartados=n_descartados)
            return self._resultado("sin_contexto", SIN_CONTEXTO, n_descartados=n_descartados,
                                   tiempos_ms=self._ms(tiempos))

        mensajes, citas = construir_mensajes(pregunta, limpios)

        etapa["actual"] = "generacion"
        with medir(tiempos, "generacion"):
            salida = reintentar(lambda: self.llm.invoke(mensajes), "generacion")
        registrar_consumo(salida)   # dentro de la traza: lleva su trace_id
        tokens = dict(salida.usage_metadata) if salida.usage_metadata else None
        costo = calcular_costo(tokens, *self.tarifas) if (tokens and self.tarifas) else None

        etapa["actual"] = "verificacion_citas"
        texto = _texto(salida.content)
        validas, invalidas = verificar_citas(texto, citas)
        fuentes = sorted(set(validas.values()))
        evento("citas_verificadas", n_validas=len(validas), n_invalidas=len(invalidas))

        tiempos_ms = self._ms(tiempos)
        evento("latencia_costo", tiempos_ms=tiempos_ms, costo=costo,
               total_ms=round(sum(tiempos_ms.values()), 2))

        motivos = []
        if n_descartados:
            motivos.append("inyeccion_detectada")
        if not validas:
            motivos.append("sin_citas_validas")
        if invalidas:
            motivos.append("citas_invalidas")

        pie = "\n\nFuentes:\n" + "\n".join(f"[{n}] {f}" for n, f in sorted(validas.items()))
        propuesta = texto + (pie if validas else "")
        comunes = dict(fuentes=fuentes, n_descartados=n_descartados, tiempos_ms=tiempos_ms,
                       tokens=tokens, costo=costo, motivos_revision=motivos)

        if motivos:   # punto de supervision humana: pausa de verdad hasta que alguien decide
            etapa["actual"] = "revision_humana"
            config = gs.solicitar_revision(self.app_revision, motivos, propuesta, fuentes)
            evento("revision_humana_solicitada", logging.WARNING, motivos=motivos)
            return self._resultado("pendiente_revision", EN_REVISION, propuesta=propuesta,
                                   revision=config, **comunes)
        return self._resultado("ok", propuesta, **comunes)

    @staticmethod
    def _ms(tiempos):
        return {e: round(s * 1000, 2) for e, s in tiempos.items()}


def construir_servicio_real(k=3):
    """Servicio con Gemini real: reutiliza el modelo y el indice ya definidos en el proyecto."""
    from dotenv import load_dotenv
    from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

    from cadena_tres_pasos import MODELO
    from indexar_corpus import DIRECTORIO_INDICE, MODELO_EMBEDDINGS, cargar_vectorstore

    load_dotenv(".env")
    if not os.environ.get("GEMINI_API_KEY"):
        raise SystemExit('Falta GEMINI_API_KEY. Defínela en tu archivo ".env".')
    embeddings = GoogleGenerativeAIEmbeddings(model=MODELO_EMBEDDINGS)
    tienda = cargar_vectorstore(embeddings, DIRECTORIO_INDICE)
    if tienda._collection.count() == 0:
        raise SystemExit("El índice está vacío. Corre primero: python indexar_corpus.py")
    llm = ChatGoogleGenerativeAI(model=MODELO, temperature=0.0)
    return ServicioRAG(tienda, embeddings, llm, k=k)


def main(argv):
    lr.agregar_archivo_de_log(ARCHIVO_LOG)
    servicio = construir_servicio_real()
    pregunta = " ".join(argv).strip() or "¿Qué acciones necesitan aprobación humana?"
    resultado = servicio.consultar(pregunta)

    if resultado["estado"] == "pendiente_revision":
        from agente_supervision import esperar_aprobacion   # misma pausa humana del B23

        print("\n--- RESPUESTA RETENIDA PARA REVISION HUMANA ---")
        print("motivos:", ", ".join(resultado["motivos_revision"]))
        print("propuesta:\n" + resultado["propuesta"])
        aprobada = esperar_aprobacion("¿Entregar esta respuesta? (s/n): ", 300)
        resultado = servicio.resolver_revision(resultado, aprobada)

    print("\nrespuesta final:", resultado["respuesta"])
    print("estado:", resultado["estado"], "| trace_id:", resultado["trace_id"])
    if resultado["tiempos_ms"]:
        print("tiempos_ms:", resultado["tiempos_ms"], "| tokens:", resultado["tokens"])
    if resultado["estado"] == "error":
        print("El servicio no pudo completar la consulta (", resultado.get("error"), ").")
        return 1
    print("Proceso terminado sin errores.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
