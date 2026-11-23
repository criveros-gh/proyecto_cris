"""Pruebas offline de B24: embeddings falsos, Chroma real en una carpeta temporal."""
from langchain_core.embeddings import DeterministicFakeEmbedding

import indexar_corpus as ic

EMB = DeterministicFakeEmbedding(size=16)


def test_corpus_tiene_al_menos_cinco_documentos():
    assert len(ic.CORPUS) >= 5


def test_chunks_conservan_la_fuente():
    chunks = ic.construir_chunks(ic.CORPUS)
    assert all("fuente" in c.metadata for c in chunks)


def test_chunks_respetan_el_tamano():
    chunks = ic.construir_chunks(ic.CORPUS, chunk_size=200, chunk_overlap=30)
    assert all(0 < len(c.page_content) <= 200 for c in chunks)


def test_documento_largo_se_divide_en_varios_chunks():
    largo = [{"fuente": "x", "texto": "Una idea completa. " * 40}]
    assert len(ic.construir_chunks(largo, 200, 30)) > 1


def test_indexa_y_persiste_en_disco(tmp_path):
    carpeta = str(tmp_path / "idx")
    chunks = ic.construir_chunks(ic.CORPUS)
    ic.indexar(chunks, EMB, carpeta)
    assert (tmp_path / "idx").exists() and any((tmp_path / "idx").iterdir())
    # reconexion sin recalcular: mismo conteo
    assert ic.contar_indexados(EMB, carpeta) == len(chunks)


def test_busqueda_devuelve_la_fuente(tmp_path):
    carpeta = str(tmp_path / "idx")
    ic.indexar(ic.construir_chunks(ic.CORPUS), EMB, carpeta)
    from langchain_chroma import Chroma
    tienda = Chroma(persist_directory=carpeta, embedding_function=EMB)
    res = tienda.similarity_search("aprobacion humana", k=1)
    assert res and "fuente" in res[0].metadata
