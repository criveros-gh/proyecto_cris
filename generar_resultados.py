import json

from cliente import consultar_modelo
from metricas import calcular_metricas, resumir_metricas
from pipeline_texto import CASOS


def generar_resultados(
    casos: list[dict], ruta: str = "resultados_metricas.json"
) -> list[dict]:
    """Genera una respuesta por caso, calcula sus métricas y las guarda en un JSON."""
    resultados = []
    for caso in casos:
        respuesta = consultar_modelo(caso["consulta"])
        metricas = calcular_metricas(caso["referencia"], respuesta)
        resultados.append(
            {
                "consulta": caso["consulta"],
                "referencia": caso["referencia"],
                "respuesta": respuesta,
                **metricas,
            }
        )
        with open(ruta, "w", encoding="utf-8") as archivo:
            json.dump(resultados, archivo, indent=2, ensure_ascii=False)
    return resultados


if __name__ == "__main__":
    resultados = generar_resultados(CASOS)
    print(resumir_metricas(resultados))

    peores_casos = sorted(resultados, key=lambda r: r["f1"])
    for caso in peores_casos[:3]:
        print(caso["consulta"], round(caso["f1"], 2))