"""Pruebas offline de B26 (embeddings falsos: validan la mecanica, no el significado)."""
from langchain_core.documents import Document
from langchain_core.embeddings import DeterministicFakeEmbedding

import indexar_corpus as ic
import recuperacion as rc

EMB = DeterministicFakeEmbedding(size=16)


def _tienda(tmp_path):
    carpeta = str(tmp_path / "idx")
    ic.indexar(ic.construir_chunks(ic.CORPUS), EMB, carpeta)
    return ic.cargar_vectorstore(EMB, carpeta)


def test_contexto_numerado_desde_1_y_mapa_de_citas():
    docs = [Document(page_content="A", metadata={"fuente": "a.md"}),
            Document(page_content="B", metadata={"fuente": "b.md"})]
    contexto, citas = rc.formatear_contexto(docs)
    assert contexto.startswith("[1] A") and "[2] B" in contexto
    assert citas == {1: "a.md", 2: "b.md"}


def test_chunk_sin_fuente_se_marca_desconocida():
    _, citas = rc.formatear_contexto([Document(page_content="x", metadata={})])
    assert citas[1] == "desconocida"


def test_prompt_trae_pregunta_exacta_y_k_citas(tmp_path):
    pregunta = "¿Qué pasa si falla la cadena de emergencia?"
    prompt, citas = rc.construir_prompt(pregunta, _tienda(tmp_path), k=3)
    assert f"Pregunta: {pregunta}" in prompt
    assert list(citas) == [1, 2, 3]
    assert prompt.count("[1]") >= 1 and "[3]" in prompt


def test_todas_las_citas_son_archivos_reales_del_proyecto(tmp_path):
    _, citas = rc.construir_prompt("aprobacion", _tienda(tmp_path), k=3)
    fuentes_validas = {d["fuente"] for d in ic.CORPUS}
    assert set(citas.values()) <= fuentes_validas
    assert "desconocida" not in citas.values()


def test_prompt_exige_citar_y_admitir_falta_de_contexto(tmp_path):
    prompt, _ = rc.construir_prompt("x", _tienda(tmp_path), k=2)
    assert "SOLO el contexto" in prompt
    assert "dilo explicitamente" in prompt


def test_k_mayor_que_los_chunks_devuelve_todos(tmp_path):
    tienda = _tienda(tmp_path)
    _, citas = rc.construir_prompt("x", tienda, k=50)
    assert len(citas) == tienda._collection.count()


def test_verificar_citas_detecta_la_inventada():
    citas = {1: "a.md", 2: "b.md"}
    validas, invalidas = rc.verificar_citas("Dato [1] y otro [2], mas uno [99].", citas)
    assert validas == {1: "a.md", 2: "b.md"}
    assert invalidas == [99]


def test_respuesta_sin_citas_no_revienta():
    assert rc.verificar_citas("Sin citas.", {1: "a.md"}) == ({}, [])
