"""B24: indexar un corpus propio (chunking + embeddings + Chroma en disco).

Se indexa UNA vez; las consultas posteriores solo se reconectan al indice
(Chroma(persist_directory=...)) sin recalcular embeddings.
"""
import os
import sys

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

DIRECTORIO_INDICE = "vectorstore/"
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
    """Parte cada documento en chunks conservando su fuente como metadato."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    textos = [d["texto"] for d in corpus]
    metadatos = [{"fuente": d["fuente"]} for d in corpus]
    return splitter.create_documents(textos, metadatas=metadatos)


def indexar(chunks, embeddings, directorio=DIRECTORIO_INDICE):
    """Calcula el embedding de cada chunk y lo guarda en Chroma (en disco)."""
    return Chroma.from_documents(
        documents=chunks, embedding=embeddings, persist_directory=directorio
    )


def contar_indexados(embeddings, directorio=DIRECTORIO_INDICE):
    """Se reconecta al indice existente SIN recalcular nada y cuenta los chunks."""
    recargado = Chroma(persist_directory=directorio, embedding_function=embeddings)
    return recargado._collection.count()


def main():
    load_dotenv(".env")
    if not os.environ.get("GEMINI_API_KEY"):
        raise SystemExit('Falta GEMINI_API_KEY. Defínela en tu archivo ".env".')

    chunks = construir_chunks(CORPUS)
    for i, c in enumerate(chunks):
        print(f"chunk {i} ({len(c.page_content)} caracteres) <- {c.metadata['fuente']}")

    embeddings = GoogleGenerativeAIEmbeddings(model=MODELO_EMBEDDINGS)
    try:  # solo se protege la parte que depende de la red
        indexar(chunks, embeddings)
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
