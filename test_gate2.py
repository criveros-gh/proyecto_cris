"""Autochequeo del Gate 2: un test por cada criterio NO compensable.

Corre offline (embeddings y modelo simulados) sobre el servicio REAL del proyecto:
  python -m pytest test_gate2.py -v
"""
import io
import logging
import tempfile

import logging_rag as lr

# Dato sensible de prueba que NUNCA debe aparecer en los logs
CORREO = "ana.perez@example.com"
PREGUNTA = "Cual es la politica de aprobacion humana? Mi correo es " + CORREO

# ===== ADAPTA ESTA SECCION A TU PROYECTO =====
_SERVICIO = None


def _servicio():
    """Servicio real (servicio_rag.ServicioRAG) con indice del corpus propio en una
    carpeta temporal, embeddings deterministas y un modelo simulado que cita [1]."""
    global _SERVICIO
    if _SERVICIO is None:
        from langchain_core.embeddings import DeterministicFakeEmbedding
        from langchain_core.messages import AIMessage

        import indexar_corpus as ic
        from servicio_rag import ServicioRAG

        class ModeloSimulado:
            model = "modelo-simulado"

            def invoke(self, mensajes):
                return AIMessage(content="Segun la documentacion, se necesita aprobacion [1].",
                                 usage_metadata={"input_tokens": 200, "output_tokens": 20,
                                                 "total_tokens": 220})

        embeddings = DeterministicFakeEmbedding(size=32)
        tienda = ic.indexar(ic.construir_chunks(ic.CORPUS), embeddings,
                            directorio=tempfile.mkdtemp(prefix="gate2_idx_"))
        _SERVICIO = ServicioRAG(tienda, embeddings, ModeloSimulado(), k=3)
    return _SERVICIO


def ejecutar_servicio(pregunta):
    """Corre tu flujo completo. Devuelve (respuesta, fuentes)."""
    resultado = _servicio().consultar(pregunta)
    return resultado["respuesta"], resultado["fuentes"]


def crear_supervision():
    """Devuelve (app, entrada): el grafo de supervision humana (B32) con checkpointer."""
    import grafo_supervision as gs

    return gs.construir_grafo(), {"huella_nueva": "abc123", "aprobado": False, "resultado": ""}
# ===== FIN DE LA SECCION A ADAPTAR =====


def test_1_pipeline_sin_excepciones():
    respuesta, _ = ejecutar_servicio(PREGUNTA)
    assert respuesta.strip(), "el servicio devolvio una respuesta vacia"


def test_2_respuesta_cita_fuente():
    respuesta, fuentes = ejecutar_servicio(PREGUNTA)
    assert fuentes, "el servicio no devolvio ninguna fuente"
    assert any(f in respuesta for f in fuentes), "la respuesta no menciona su fuente"


def test_3_logs_sin_contenido_crudo(caplog):
    # El logger del proyecto tiene propagate=False (caplog no lo ve), asi que se
    # captura directo en su handler. Ademas se exige que haya logs: sin eso la
    # prueba pasaria "en vacio".
    buf = io.StringIO()
    lr.configurar_logger(buf)
    try:
        with caplog.at_level(logging.DEBUG):
            ejecutar_servicio(PREGUNTA)
    finally:
        lr.configurar_logger()
    texto_logs = buf.getvalue() + " ".join(r.getMessage() + " " + str(r.__dict__) for r in caplog.records)
    assert buf.getvalue().strip(), "no se registro ningun log: la prueba no verifica nada"
    assert CORREO not in texto_logs, "un dato sensible aparece en los logs"
    assert PREGUNTA not in texto_logs, "la consulta completa aparece en los logs"


def test_4_supervision_pausa_y_reanuda():
    from langgraph.types import Command

    app, entrada = crear_supervision()
    config = {"configurable": {"thread_id": "test-gate2"}}
    pausado = app.invoke(entrada, config=config)
    assert "__interrupt__" in pausado, "el grafo no se detuvo en el punto de supervision"
    final = app.invoke(Command(resume=True), config=config)
    assert "__interrupt__" not in final, "el grafo sigue pausado despues de reanudar"
    assert final["aprobado"] is True, "la decision no quedo registrada"
