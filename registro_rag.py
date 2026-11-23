"""B28: medir latencia por etapa y tokens reales de una consulta RAG.

Etapas: embed_query (red) -> busqueda_vectorial (local) -> generacion (red).
El modelo de generacion es el mismo del resto del proyecto (cadena_tres_pasos.MODELO).
"""
import json
import os
import time
from contextlib import contextmanager
from datetime import datetime, timezone

from dotenv import load_dotenv

from recuperacion import PROMPT_TEMPLATE, formatear_contexto

ARCHIVO_REGISTROS = "registros_latencia_costo.jsonl"


@contextmanager
def medir(tiempos, etapa):
    """Mide una etapa con perf_counter (el reloj correcto para duraciones cortas)."""
    inicio = time.perf_counter()
    yield
    tiempos[etapa] = time.perf_counter() - inicio


def calcular_costo(tokens, tarifa_entrada_x1000, tarifa_salida_x1000):
    """Costo = entrada*tarifa + salida*tarifa. Las tarifas se pasan de afuera:
    NO se hardcodean (cambian; consultar la documentacion oficial vigente)."""
    if not tokens:
        return None
    return round(
        tokens["input_tokens"] / 1000 * tarifa_entrada_x1000
        + tokens["output_tokens"] / 1000 * tarifa_salida_x1000,
        8,
    )


def registrar_consulta(pregunta, vectorstore, embeddings, modelo, k=3,
                       tarifa_entrada_x1000=None, tarifa_salida_x1000=None):
    """Corre UNA consulta RAG y devuelve el registro con tiempos y tokens reales."""
    tiempos = {}

    with medir(tiempos, "embed_query"):
        vector = embeddings.embed_query(pregunta)

    with medir(tiempos, "busqueda_vectorial"):
        chunks = vectorstore.similarity_search_by_vector(vector, k=k)

    contexto, _citas = formatear_contexto(chunks)
    prompt = PROMPT_TEMPLATE.format(contexto=contexto, pregunta=pregunta)

    with medir(tiempos, "generacion"):
        respuesta = modelo.invoke(prompt)

    tokens = dict(respuesta.usage_metadata) if respuesta.usage_metadata else None
    registro = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pregunta": pregunta,
        "k": k,
        "tiempos_ms": {e: round(s * 1000, 2) for e, s in tiempos.items()},
        "tiempo_total_ms": round(sum(tiempos.values()) * 1000, 2),
        "tokens": tokens,
    }
    if tarifa_entrada_x1000 is not None and tarifa_salida_x1000 is not None:
        registro["costo"] = calcular_costo(tokens, tarifa_entrada_x1000, tarifa_salida_x1000)
    return registro


def guardar_registro(registro, archivo=ARCHIVO_REGISTROS):
    """Una corrida por linea (JSON Lines). Solo corridas reales."""
    with open(archivo, "a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")


if __name__ == "__main__":
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
    modelo = ChatGoogleGenerativeAI(model=MODELO, temperature=0.0)

    preguntas = [
        "¿Qué pasa si falla la cadena de emergencia?",
        "¿Qué acciones necesitan aprobación humana?",
        "¿Las pruebas gastan tokens de la API?",
    ]
    for pregunta in preguntas:
        try:
            registro = registrar_consulta(pregunta, tienda, embeddings, modelo, k=3)
        except Exception as error:
            print(f"No se pudo registrar '{pregunta}': {type(error).__name__}")
            continue
        print(json.dumps(registro, indent=2, ensure_ascii=False))
        guardar_registro(registro)

    # Misma pregunta con k=6: deberian subir los tokens de entrada
    try:
        registro = registrar_consulta(preguntas[0], tienda, embeddings, modelo, k=6)
        print(json.dumps(registro, indent=2, ensure_ascii=False))
        guardar_registro(registro)
    except Exception as error:
        print(f"No se pudo registrar k=6: {type(error).__name__}")
