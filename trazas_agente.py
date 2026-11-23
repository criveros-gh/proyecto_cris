"""B23: guardar y revisar la traza de decision del agente."""
import json
from datetime import datetime, timezone

ARCHIVO_TRAZAS = "trazas_agente.jsonl"


def registrar_traza(session_id: str, entrada: str, resultado: dict,
                    archivo: str = ARCHIVO_TRAZAS) -> None:
    """Guarda una interaccion como una linea JSON: que se pregunto, que
    herramientas se usaron (con argumentos) y la respuesta final.
    Sin "intermediate_steps" en el resultado, acciones queda vacia."""
    registro = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "entrada": entrada,
        "acciones": [
            {
                "herramienta": accion.tool,
                "argumentos": accion.tool_input,
                "observacion": observacion,
            }
            for accion, observacion in resultado.get("intermediate_steps", [])
        ],
        "respuesta_final": resultado["output"],
    }
    with open(archivo, "a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")


def marcar_repeticiones_sospechosas(archivo: str = ARCHIVO_TRAZAS) -> list:
    """Marca sesiones donde la misma herramienta se uso dos veces SEGUIDAS.
    Es un candidato a revision humana, no una conclusion. Devuelve los avisos."""
    try:
        with open(archivo, encoding="utf-8") as f:
            registros = [json.loads(linea) for linea in f if linea.strip()]
    except FileNotFoundError:
        print(f"No se encontro '{archivo}'. Corre registrar_traza al menos una vez.")
        return []

    avisos = []
    for registro in registros:
        herramientas = [a["herramienta"] for a in registro.get("acciones", [])]
        for i in range(1, len(herramientas)):
            if herramientas[i] == herramientas[i - 1]:
                aviso = (f"Revisar: {registro['session_id']} uso "
                         f"'{herramientas[i]}' dos veces seguidas")
                print(aviso)
                avisos.append(aviso)
                break
    return avisos
