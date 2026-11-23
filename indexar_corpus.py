"""B24: indexar un corpus propio (chunking + embeddings + Chroma en disco).

Se indexa UNA vez; las consultas posteriores solo se reconectan al indice
(Chroma(persist_directory=...)) sin recalcular embeddings.
"""
import os
import sys
import time

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

DIRECTORIO_INDICE = os.path.abspath("vectorstore")
NOMBRE_COLECCION = "corpus_michis"  # explicito: evita "colecciones fantasma"
MODELO_EMBEDDINGS = "models/gemini-embedding-001"

# Corpus propio: documentacion de este mismo proyecto (cada texto con su fuente,
# que luego servira para citar de donde salio cada respuesta).
CORPUS = [
    {"fuente": "enrutamiento.py",
     "texto": "El enrutamiento clasifica el mensaje del usuario como emergencia, "
              "adopcion o consulta y lo manda a la cadena correspondiente."},
    {"fuente": "enrutamiento.py (B20)",
     "texto": "Si falla la cadena de emergencia, se usa una respuesta generica "
              "con pasos seguros, como llamar a una veterinaria. Los errores se "
              "registran con logger.exception y el usuario recibe un mensaje claro."},
    {"fuente": "agente_con_herramientas.py",
     "texto": "El agente decide por si mismo que herramienta usar segun su "
              "descripcion: buscar_guia_cuidado para guias y calcular_presupuesto "
              "para costos de cuidado de gatos."},
    {"fuente": "agente_con_memoria.py",
     "texto": "La memoria del agente se guarda por session_id. Cada sesion tiene "
              "su propio historial y las sesiones no deben mezclarse entre usuarios. "
              "Mas historial significa mas costo por turno."},
    {"fuente": "agente_supervision.py",
     "texto": "Las herramientas de riesgo alto, como generar_reembolso, requieren "
              "aprobacion humana. Si nadie responde a tiempo, el resultado por "
              "defecto es no aprobado, y cada decision queda registrada."},
    {"fuente": "tests",
     "texto": "Las pruebas del proyecto son offline: usan modelos y ejecutores "
              "falsos, de modo que corren en menos de un segundo y sin gastar "
              "tokens ni depender de la API."},
]


def construir_chunks(corpus, chunk_size=200, chunk_overlap=30):
    """Parte cada documento en chunks conservando su fuente y un doc_id."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    textos = [d["texto"] for d in corpus]
    metadatos = [{"fuente": d["fuente"], "doc_id": f"doc_{i}"}
                 for i, d in enumerate(corpus)]
    return splitter.create_documents(textos, metadatas=metadatos)


def generar_ids(chunks):
    """Un id predecible por chunk (doc_0_chunk_0, ...). Permite agregar,
    reemplazar o borrar chunks puntuales sin reindexar todo."""
    contadores = {}
    ids = []
    for c in chunks:
        doc = c.metadata["doc_id"]
        n = contadores.get(doc, 0)
        ids.append(f"{doc}_chunk_{n}")
        contadores[doc] = n + 1
    return ids


def con_reintentos(operacion, max_intentos=4, espera_inicial=5):
    """Repite la operacion SOLO ante error de limite (429); espera 5, 10, 20 s.
    Si se agotan los intentos (o es otro error) lo vuelve a lanzar: no se oculta."""
    espera = espera_inicial
    for intento in range(1, max_intentos + 1):
        try:
            return operacion()
        except Exception as error:
            mensaje = str(error)
            es_limite = "429" in mensaje or "RESOURCE_EXHAUSTED" in mensaje
            if not es_limite or intento == max_intentos:
                raise
            print(f"Límite de peticiones alcanzado. Reintento {intento} de "
                  f"{max_intentos - 1} en {espera} s...")
            time.sleep(espera)
            espera *= 2


def indexar(chunks, embeddings, directorio=DIRECTORIO_INDICE):
    """Calcula el embedding de cada chunk y lo guarda en Chroma (en disco)."""
    return Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        ids=generar_ids(chunks),
        collection_name=NOMBRE_COLECCION,
        persist_directory=directorio,
    )


def cargar_vectorstore(embeddings, directorio=DIRECTORIO_INDICE):
    """Reconecta a un indice ya indexado, SIN recalcular nada."""
    return Chroma(
        collection_name=NOMBRE_COLECCION,
        persist_directory=directorio,
        embedding_function=embeddings,
    )


def contar_indexados(embeddings, directorio=DIRECTORIO_INDICE):
    return cargar_vectorstore(embeddings, directorio)._collection.count()


def agregar_documento(vectorstore, documento, doc_id):
    """Agrega UN documento nuevo; solo calcula embeddings de sus chunks."""
    chunks = construir_chunks([documento])
    for c in chunks:
        c.metadata["doc_id"] = doc_id
    vectorstore.add_documents(chunks, ids=generar_ids(chunks))
    return len(chunks)


def borrar_documento(vectorstore, doc_id):
    """Borra todos los chunks de un documento por su doc_id."""
    vectorstore.delete(where={"doc_id": doc_id})


def main():
    load_dotenv(".env")
    if not os.environ.get("GEMINI_API_KEY"):
        raise SystemExit('Falta GEMINI_API_KEY. Defínela en tu archivo ".env".')

    chunks = construir_chunks(CORPUS)
    for i, c in enumerate(chunks):
        print(f"chunk {i} ({len(c.page_content)} caracteres) <- {c.metadata['fuente']}")

    embeddings = GoogleGenerativeAIEmbeddings(model=MODELO_EMBEDDINGS)
    try:  # solo se protege la parte que depende de la red
        con_reintentos(lambda: indexar(chunks, embeddings))
    except Exception as error:
        mensaje = str(error)
        if "429" in mensaje or "RESOURCE_EXHAUSTED" in mensaje:
            print("Límite de peticiones alcanzado. Espera un minuto y vuelve a ejecutar.")
        elif "API key" in mensaje or "401" in mensaje or "403" in mensaje:
            print('La API rechazó tu clave. Revisa GEMINI_API_KEY en tu ".env".')
        else:
            print("No se pudo indexar:", type(error).__name__)
        sys.exit(1)

    print(f"Indexados {len(chunks)} chunks en {DIRECTORIO_INDICE}")
    print("Chunks persistidos al reconectar:", contar_indexados(embeddings))


if __name__ == "__main__":
    main()
