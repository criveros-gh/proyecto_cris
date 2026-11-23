"""Pruebas offline de B28: modelo y embeddings falsos, Chroma real en carpeta temporal."""
import json

from langchain_core.embeddings import DeterministicFakeEmbedding
from langchain_core.messages import AIMessage

import indexar_corpus as ic
import preflight as pf
import registro_rag as rr

EMB = DeterministicFakeEmbedding(size=16)


class ModeloFalso:
    """Devuelve usage_metadata proporcional al largo del prompt (como una API real)."""
    def __init__(self, con_uso=True):
        self.con_uso = con_uso

    def invoke(self, prompt):
        entrada = len(prompt) // 4
        uso = {"input_tokens": entrada, "output_tokens": 40,
               "total_tokens": entrada + 40} if self.con_uso else None
        return AIMessage(content="ok [1]", usage_metadata=uso)


def _tienda(tmp_path):
    carpeta = str(tmp_path / "idx")
    ic.indexar(ic.construir_chunks(ic.CORPUS), EMB, carpeta)
    return ic.cargar_vectorstore(EMB, carpeta)


def test_registro_tiene_la_estructura_pedida(tmp_path):
    r = rr.registrar_consulta("¿aprobación?", _tienda(tmp_path), EMB, ModeloFalso(), k=3)
    assert set(r) >= {"timestamp", "pregunta", "k", "tiempos_ms", "tiempo_total_ms", "tokens"}
    assert set(r["tiempos_ms"]) == {"embed_query", "busqueda_vectorial", "generacion"}


def test_total_es_la_suma_de_las_etapas(tmp_path):
    r = rr.registrar_consulta("x", _tienda(tmp_path), EMB, ModeloFalso(), k=3)
    assert abs(r["tiempo_total_ms"] - sum(r["tiempos_ms"].values())) < 0.1


def test_subir_k_sube_los_tokens_de_entrada(tmp_path):
    tienda = _tienda(tmp_path)
    r3 = rr.registrar_consulta("x", tienda, EMB, ModeloFalso(), k=1)
    r6 = rr.registrar_consulta("x", tienda, EMB, ModeloFalso(), k=6)
    assert r6["tokens"]["input_tokens"] > r3["tokens"]["input_tokens"]


def test_sin_usage_metadata_guarda_null_sin_fallar(tmp_path):
    r = rr.registrar_consulta("x", _tienda(tmp_path), EMB, ModeloFalso(con_uso=False), k=3)
    assert r["tokens"] is None


def test_costo_usa_entrada_y_salida_con_tarifas_recibidas():
    tokens = {"input_tokens": 1000, "output_tokens": 1000}
    assert rr.calcular_costo(tokens, 0.5, 2.0) == 2.5
    assert rr.calcular_costo(None, 0.5, 2.0) is None


def test_el_costo_solo_aparece_si_se_dan_tarifas(tmp_path):
    tienda = _tienda(tmp_path)
    assert "costo" not in rr.registrar_consulta("x", tienda, EMB, ModeloFalso(), k=3)
    r = rr.registrar_consulta("x", tienda, EMB, ModeloFalso(), k=3, tarifa_entrada_x1000=1, tarifa_salida_x1000=1)
    assert r["costo"] > 0


def test_jsonl_una_linea_por_corrida(tmp_path):
    archivo = str(tmp_path / "r.jsonl")
    tienda = _tienda(tmp_path)
    for _ in range(3):
        rr.guardar_registro(rr.registrar_consulta("x", tienda, EMB, ModeloFalso(), k=3), archivo)
    lineas = open(archivo, encoding="utf-8").read().splitlines()
    assert len(lineas) == 3 and all(json.loads(l)["k"] == 3 for l in lineas)


def test_preflight_ok_y_con_problemas(tmp_path):
    (tmp_path / "vectorstore").mkdir()
    gi = tmp_path / ".gitignore"
    gi.write_text("vectorstore/\n")
    assert pf.preflight_check(str(tmp_path / "vectorstore"), str(gi)) == []
    gi.write_text(".env\n")
    assert any("no esta en" in p for p in pf.preflight_check(str(tmp_path / "vectorstore"), str(gi)))
    assert any("no existe" in p for p in pf.preflight_check(str(tmp_path / "nada"), str(tmp_path / "x")))
