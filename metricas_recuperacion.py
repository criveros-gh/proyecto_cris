"""B27: metricas de recuperacion (python puro, sin API)."""


def precision_at_k(ids_recuperados, ids_relevantes):
    """De lo recuperado, que fraccion es relevante. 0.0 si no se recupero nada."""
    if not ids_recuperados:
        return 0.0
    acertados = [i for i in ids_recuperados if i in ids_relevantes]
    return len(acertados) / len(ids_recuperados)


def recall_at_k(ids_recuperados, ids_relevantes):
    """De lo relevante, que fraccion se recupero. None si el caso no tiene
    ningun relevante (pregunta que el corpus no puede responder)."""
    if not ids_relevantes:
        return None
    acertados = [i for i in ids_recuperados if i in ids_relevantes]
    return len(acertados) / len(ids_relevantes)


def f1(precision, recall):
    """Media armonica: un solo numero para comparar configuraciones."""
    if precision is None or recall is None or precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def promediar(valores):
    """Promedio que ignora los None y evita dividir por cero."""
    validos = [v for v in valores if v is not None]
    return sum(validos) / len(validos) if validos else 0.0
