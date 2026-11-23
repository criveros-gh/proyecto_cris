"""Pruebas offline de B27: metricas y evaluador (retriever falso / embeddings falsos)."""
from types import SimpleNamespace

import pytest
from langchain_core.embeddings import DeterministicFakeEmbedding

import evaluacion_recuperacion as ev
import indexar_corpus as ic
import metricas_recuperacion as m


def test_precision_y_recall_del_ejemplo_de_la_clase():
    rec, rel = ["doc2", "doc0", "doc4"], {"doc0"}
    assert m.precision_at_k(rec, rel) == pytest.approx(1 / 3)
    assert m.recall_at_k(rec, rel) == 1.0


def test_casos_borde_sin_error():
    assert m.precision_at_k([], {"a"}) == 0.0
    assert m.recall_at_k(["a"], set()) is None


def test_f1_maximo_en_k3_del_ejemplo():
    ranked, rel = ["doc2", "doc4", "doc0", "doc1", "doc3"], {"doc0"}
    f = [m.f1(m.precision_at_k(ranked[:k], rel), m.recall_at_k(ranked[:k], rel))
         for k in range(1, 6)]
    assert f.index(max(f)) == 2 and f[2] == pytest.approx(0.5)


def test_promediar_ignora_none():
    assert m.promediar([1.0, None, 0.0]) == 0.5
    assert m.promediar([None]) == 0.0


def test_conjunto_de_evaluacion_cumple_el_minimo_y_tiene_un_caso_sin_respuesta():
    assert 8 <= len(ev.CASOS_EVALUACION) <= 15
    assert any(not c["ids_relevantes"] for c in ev.CASOS_EVALUACION)


def test_etiquetas_apuntan_a_ids_que_existen_en_el_indice():
    ids = set(ic.generar_ids(ic.construir_chunks(ic.CORPUS)))
    for caso in ev.CASOS_EVALUACION:
        assert caso["ids_relevantes"] <= ids


class _RetrieverFijo:
    def __init__(self, ids):
        self.ids = ids

    def invoke(self, pregunta):
        return [SimpleNamespace(id=i) for i in self.ids]


def test_evaluador_con_retriever_falso():
    casos = [{"pregunta": "a", "ids_relevantes": {"x"}},
             {"pregunta": "b", "ids_relevantes": set()}]
    res, p, r = ev.evaluar_recuperacion(_RetrieverFijo(["x", "y", "z"]), casos, k=3)
    assert res[0]["recall"] == 1.0 and res[1]["recall"] is None
    assert r == 1.0                      # el caso sin respuesta no entra al promedio
    assert 0.0 <= p <= 1.0


def test_evaluador_con_indice_real_y_embeddings_falsos(tmp_path):
    carpeta = str(tmp_path / "idx")
    ic.indexar(ic.construir_chunks(ic.CORPUS), DeterministicFakeEmbedding(size=16), carpeta)
    tienda = ic.cargar_vectorstore(DeterministicFakeEmbedding(size=16), carpeta)
    res, p, r = ev.evaluar_recuperacion(tienda.as_retriever(search_kwargs={"k": 3}),
                                        ev.CASOS_EVALUACION, 3)
    assert len(res) == len(ev.CASOS_EVALUACION)
    assert all(0.0 <= x["precision"] <= 1.0 for x in res)
    assert all(len(x["recuperados"]) == 3 for x in res)


def test_corrida_repetida_es_determinista(tmp_path):
    carpeta = str(tmp_path / "idx")
    emb = DeterministicFakeEmbedding(size=16)
    ic.indexar(ic.construir_chunks(ic.CORPUS), emb, carpeta)
    ret = ic.cargar_vectorstore(emb, carpeta).as_retriever(search_kwargs={"k": 3})
    a = ev.evaluar_recuperacion(ret, ev.CASOS_EVALUACION, 3)
    b = ev.evaluar_recuperacion(ret, ev.CASOS_EVALUACION, 3)
    assert a == b


def test_guardar_no_sobrescribe(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    n1 = ev.guardar_resultados("uno", 3)
    n2 = ev.guardar_resultados("dos", 3)
    assert n1 != n2
    assert open(n1, encoding="utf-8").read() == "uno"


def test_informe_tiene_fecha_configuracion_y_promedio():
    res = [{"pregunta": "q", "precision": 0.5, "recall": None, "recuperados": []}]
    texto = ev.formatear_resultados(res, 0.5, 0.0, 3)
    assert texto.startswith("Fecha:") and "Configuracion: k=3" in texto
    assert "n/a" in texto and "promedio -> precision: 0.500" in texto
