"""B27: evaluar la recuperacion del RAG con un conjunto de preguntas etiquetadas.

Las etiquetas (ids_relevantes) se escribieron LEYENDO EL CORPUS (indexar_corpus.py),
antes de ver lo que devuelve el retriever. No se ajustan para que "den bien".
"""
import os
import sys
from datetime import date

from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from indexar_corpus import DIRECTORIO_INDICE, MODELO_EMBEDDINGS, cargar_vectorstore
from metricas_recuperacion import f1, precision_at_k, promediar, recall_at_k

K = 3
CHUNK_SIZE = 200      # deben coincidir con construir_chunks() en indexar_corpus.py
CHUNK_OVERLAP = 30

# ids: doc_N_chunk_0 (un chunk por documento del corpus).
CASOS_EVALUACION = [
    {"pregunta": "¿Cómo clasifica el sistema el mensaje del usuario?",
     "ids_relevantes": {"doc_0_chunk_0"}},
    {"pregunta": "¿Qué respuesta se da si falla la cadena de emergencia?",
     "ids_relevantes": {"doc_1_chunk_0"}},
    {"pregunta": "¿Qué se hace con los errores del sistema?",
     "ids_relevantes": {"doc_1_chunk_0"}},
    {"pregunta": "¿Cómo decide el agente qué herramienta usar?",
     "ids_relevantes": {"doc_2_chunk_0"}},
    {"pregunta": "¿Qué herramientas tiene el agente para cuidar gatos?",
     "ids_relevantes": {"doc_2_chunk_0"}},
    {"pregunta": "¿Cómo se guarda la memoria del agente?",
     "ids_relevantes": {"doc_3_chunk_0"}},
    {"pregunta": "¿Por qué no deben mezclarse las sesiones de distintos usuarios?",
     "ids_relevantes": {"doc_3_chunk_0"}},
    {"pregunta": "¿Qué acciones necesitan aprobación humana?",
     "ids_relevantes": {"doc_4_chunk_0"}},
    {"pregunta": "¿Qué pasa si nadie responde a una solicitud de aprobación?",
     "ids_relevantes": {"doc_4_chunk_0"}},
    {"pregunta": "¿Cómo son las pruebas automáticas del proyecto?",
     "ids_relevantes": {"doc_5_chunk_0"}},
    {"pregunta": "¿Las pruebas gastan tokens de la API?",
     "ids_relevantes": {"doc_5_chunk_0"}},
    # Pregunta que el corpus NO puede responder (recall = n/a, no entra al promedio)
    {"pregunta": "¿Cuánto cuesta arrendar una oficina en Santiago?",
     "ids_relevantes": set()},
]


def evaluar_recuperacion(retriever, casos, k=K):
    """Corre cada caso contra el retriever y devuelve (resultados, p_prom, r_prom)."""
    resultados = []
    for caso in casos:
        chunks = retriever.invoke(caso["pregunta"])
        ids_recuperados = [c.id for c in chunks][:k]
        p = precision_at_k(ids_recuperados, caso["ids_relevantes"])
        r = recall_at_k(ids_recuperados, caso["ids_relevantes"])
        resultados.append({
            "pregunta": caso["pregunta"],
            "recuperados": ids_recuperados,
            "precision": p,
            "recall": r,
        })
    p_prom = promediar(x["precision"] for x in resultados)
    r_prom = promediar(x["recall"] for x in resultados)
    return resultados, p_prom, r_prom


def formatear_resultados(resultados, p_prom, r_prom, k=K):
    """Texto del informe (fecha, configuracion, una linea por pregunta, promedios)."""
    lineas = [f"Fecha: {date.today()}",
              f"Configuracion: k={k}, chunk_size={CHUNK_SIZE}, chunk_overlap={CHUNK_OVERLAP}",
              ""]
    for r in resultados:
        recall_txt = "n/a" if r["recall"] is None else f"{r['recall']:.2f}"
        lineas.append(f"{r['precision']:.2f} {recall_txt} {r['pregunta']}")
    lineas += ["", f"promedio -> precision: {p_prom:.3f} recall: {r_prom:.3f} "
                   f"F1: {f1(p_prom, r_prom):.3f}"]
    return "\n".join(lineas) + "\n"


def guardar_resultados(texto, k=K):
    """Guarda en un archivo con fecha y k SIN sobrescribir uno anterior."""
    base = f"resultados_evaluacion_{date.today()}_k{k}"
    nombre, n = f"{base}.txt", 2
    while os.path.exists(nombre):
        nombre, n = f"{base}_v{n}.txt", n + 1
    with open(nombre, "w", encoding="utf-8") as f:
        f.write(texto)
    return nombre


if __name__ == "__main__":
    load_dotenv(".env")
    if not os.environ.get("GEMINI_API_KEY"):
        raise SystemExit('Falta GEMINI_API_KEY. Defínela en tu archivo ".env".')
    embeddings = GoogleGenerativeAIEmbeddings(model=MODELO_EMBEDDINGS)
    tienda = cargar_vectorstore(embeddings, DIRECTORIO_INDICE)
    if tienda._collection.count() == 0:
        raise SystemExit("El índice está vacío. Corre primero: python indexar_corpus.py")
    # k opcional por consola: python evaluacion_recuperacion.py 1
    k = int(sys.argv[1]) if len(sys.argv) > 1 else K
    retriever = tienda.as_retriever(search_kwargs={"k": k})
    resultados, p_prom, r_prom = evaluar_recuperacion(retriever, CASOS_EVALUACION, k)
    texto = formatear_resultados(resultados, p_prom, r_prom, k)
    print(texto)
    print("Guardado en", guardar_resultados(texto, k))
