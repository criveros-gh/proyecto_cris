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
    tienda = ic.cargar_vectorstore(EMB, carpeta)
    res = tienda.similarity_search("aprobacion humana", k=1)
    assert res and "fuente" in res[0].metadata


# ---- B25: ids explicitos, reintentos, coleccion con nombre, actualizacion ----
import pytest


def test_ids_son_unicos_y_predecibles():
    ids = ic.generar_ids(ic.construir_chunks(ic.CORPUS))
    assert len(ids) == len(set(ids))
    assert ids[0] == "doc_0_chunk_0"


def test_reindexar_no_duplica_chunks(tmp_path):
    carpeta = str(tmp_path / "idx")
    chunks = ic.construir_chunks(ic.CORPUS)
    ic.indexar(chunks, EMB, carpeta)
    ic.indexar(chunks, EMB, carpeta)  # mismos ids -> reemplaza, no duplica
    assert ic.contar_indexados(EMB, carpeta) == len(chunks)


def test_agregar_y_borrar_un_documento(tmp_path):
    carpeta = str(tmp_path / "idx")
    chunks = ic.construir_chunks(ic.CORPUS)
    tienda = ic.indexar(chunks, EMB, carpeta)
    n = ic.agregar_documento(tienda, {"fuente": "nuevo.md", "texto": "Un dato nuevo."}, "doc_nuevo")
    assert ic.contar_indexados(EMB, carpeta) == len(chunks) + n
    ic.borrar_documento(tienda, "doc_nuevo")
    assert ic.contar_indexados(EMB, carpeta) == len(chunks)


def test_reintenta_ante_429_y_luego_funciona(monkeypatch):
    monkeypatch.setattr(ic.time, "sleep", lambda s: None)
    llamadas = {"n": 0}

    def operacion():
        llamadas["n"] += 1
        if llamadas["n"] < 3:
            raise RuntimeError("429 RESOURCE_EXHAUSTED")
        return "ok"

    assert ic.con_reintentos(operacion) == "ok"
    assert llamadas["n"] == 3


def test_no_reintenta_otros_errores(monkeypatch):
    monkeypatch.setattr(ic.time, "sleep", lambda s: None)
    llamadas = {"n": 0}

    def operacion():
        llamadas["n"] += 1
        raise ValueError("API key not valid")

    with pytest.raises(ValueError):
        ic.con_reintentos(operacion)
    assert llamadas["n"] == 1


def test_agota_reintentos_y_relanza(monkeypatch):
    monkeypatch.setattr(ic.time, "sleep", lambda s: None)
    with pytest.raises(RuntimeError):
        ic.con_reintentos(lambda: (_ for _ in ()).throw(RuntimeError("429")), max_intentos=2)
