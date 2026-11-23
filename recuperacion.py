"""B26: recuperacion semantica + prompt dinamico que obliga a citar la fuente.

Flujo: pregunta -> retriever (k chunks mas cercanos) -> contexto numerado
[1], [2]... -> prompt que exige citar -> (modelo) -> citas verificables.
"""
import os
import re

from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from indexar_corpus import DIRECTORIO_INDICE, MODELO_EMBEDDINGS, cargar_vectorstore

PROMPT_TEMPLATE = """Responde la pregunta usando SOLO el contexto de abajo. \
Cita la fuente de cada afirmacion con su numero entre corchetes, como [1]. \
Si el contexto no alcanza para responder, dilo explicitamente en vez de inventar.

Contexto:
{contexto}

Pregunta: {pregunta}

Respuesta:"""


def formatear_contexto(chunks_recuperados):
    """Contexto numerado para el prompt + mapa numero -> fuente para citar."""
    lineas = []
    citas = {}
    for i, doc in enumerate(chunks_recuperados, start=1):
        fuente = doc.metadata.get("fuente", "desconocida")
        lineas.append(f"[{i}] {doc.page_content}")
        citas[i] = fuente
    return "\n\n".join(lineas), citas


def construir_prompt(pregunta, vectorstore, k=3):
    """Recupera los k chunks mas relevantes y arma el prompt con citas.
    Recibe el vector store ya cargado: NUNCA reindexa aqui."""
    retriever = vectorstore.as_retriever(search_kwargs={"k": k})
    chunks = retriever.invoke(pregunta)
    contexto, citas = formatear_contexto(chunks)
    prompt = PROMPT_TEMPLATE.format(contexto=contexto, pregunta=pregunta)
    return prompt, citas


def verificar_citas(respuesta, citas):
    """Separa las citas [n] de la respuesta en validas (existen en el contexto)
    e invalidas (el modelo las invento, p. ej. [99]). Devuelve (validas, invalidas)."""
    numeros = [int(n) for n in re.findall(r"\[(\d+)\]", respuesta)]
    validas = {n: citas[n] for n in numeros if n in citas}
    invalidas = [n for n in numeros if n not in citas]
    return validas, invalidas


if __name__ == "__main__":
    load_dotenv(".env")
    if not os.environ.get("GEMINI_API_KEY"):
        raise SystemExit('Falta GEMINI_API_KEY. Defínela en tu archivo ".env".')
    embeddings = GoogleGenerativeAIEmbeddings(model=MODELO_EMBEDDINGS)
    tienda = cargar_vectorstore(embeddings, DIRECTORIO_INDICE)
    if tienda._collection.count() == 0:
        raise SystemExit("El índice está vacío. Corre primero: python indexar_corpus.py")

    for pregunta in [
        "¿Qué pasa si falla la cadena de emergencia?",
        "¿Cuándo hay que pedir aprobación humana?",
    ]:
        prompt, citas = construir_prompt(pregunta, tienda, k=3)
        print(prompt)
        print("citas:", citas)
        print("-" * 60)
