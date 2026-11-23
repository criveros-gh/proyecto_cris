revision_manual = [
    {
        "consulta": "¿Cada cuánto se debe desparasitar a un gato?",
        "f1": 0.07,
        "correccion_factual": "no",
        "completitud": "si",
        "contradiccion": "no",
        "nota": (
            "la referencia dice cada tres meses y la respuesta dice cada "
            "mes para gatos con acceso al exterior: el F1 bajo marca un "
            "desacuerdo real, pero el número no dice cuál de las dos tiene razón"
        ),
    },
    {
        "consulta": "¿Qué comen los gatos callejeros?",
        "f1": 0.17,
        "correccion_factual": "si",
        "completitud": "si",
        "contradiccion": "no",
        "nota": (
            "la respuesta es correcta y más completa que la referencia "
            "(restos, roedores, aves, puntos de alimentación); el F1 es bajo "
            "solo porque dice mucho más que la referencia"
        ),
    },
    {
        "consulta": "¿Cómo sé si un gato callejero está herido?",
        "f1": 0.24,
        "correccion_factual": "si",
        "completitud": "si",
        "contradiccion": "no",
        "nota": (
            "menciona los mismos signos con otras palabras (apático, evita "
            "comer) y agrega abscesos y secreciones; el F1 bajo es por "
            "sinónimos y detalles extra, no por error"
        ),
    },
    {
        "consulta": "¿Pueden los gatos ver en la oscuridad?",
        "f1": 0.30,
        "correccion_factual": "si",
        "completitud": "si",
        "contradiccion": "no",
        "nota": (
            "dice lo mismo que la referencia (no ven en oscuridad absoluta, "
            "ven con muy poca luz) y agrega el tapetum lucidum; F1 bajo por "
            "la explicación extra"
        ),
    },
    {
        "consulta": "¿A qué edad se puede esterilizar a un gato?",
        "f1": 0.37,
        "correccion_factual": "si",
        "completitud": "si",
        "contradiccion": "no",
        "nota": (
            "dice desde los cuatro meses, coincide con el inicio del rango "
            "de la referencia (cuatro a seis); agrega el criterio del peso"
        ),
    },
    {
        "consulta": "¿Se le puede dar leche de vaca a un gato?",
        "f1": 0.43,
        "correccion_factual": "si",
        "completitud": "si",
        "contradiccion": "no",
        "nota": (
            "mismo veredicto (no) con otra causa dicha con otras palabras "
            "(lactosa en vez de diarrea); 'problemas digestivos graves' "
            "exagera un poco, pero la idea es correcta"
        ),
    },
    {
        "consulta": "¿Cuánto vive en promedio un gato callejero?",
        "f1": 0.55,
        "correccion_factual": "si",
        "completitud": "si",
        "contradiccion": "no",
        "nota": (
            "mismo rango de 2 a 5 años que la referencia; agrega la "
            "comparación con gatos domésticos"
        ),
    },
    {
        "consulta": "¿Cuántas crías puede tener una gata por camada?",
        "f1": 0.56,
        "correccion_factual": "no",
        "completitud": "si",
        "contradiccion": "no",
        "nota": (
            "la referencia dice entre tres y cinco y la respuesta dice entre "
            "cuatro y seis: el rango es distinto y aun así el F1 sale medio, "
            "porque el resto de la frase coincide"
        ),
    },
    {
        "consulta": "¿Cuántas horas al día duerme un gato adulto?",
        "f1": 0.67,
        "correccion_factual": "si",
        "completitud": "si",
        "contradiccion": "no",
        "nota": (
            "mismo rango de 12 a 16 horas; agrega que algunos llegan a 20, "
            "un detalle extra que no contradice a la referencia"
        ),
    },
    {
        "consulta": "¿Cuánto dura la gestación de una gata?",
        "f1": 0.74,
        "correccion_factual": "si",
        "completitud": "si",
        "contradiccion": "no",
        "nota": (
            "F1 alto y respuesta correcta, pero el rango termina en 67 días "
            "y la referencia en 65: una diferencia pequeña que el F1 no "
            "alcanza a detectar"
        ),
    },
]

if __name__ == "__main__":
    import json

    with open("revision_manual.json", "w", encoding="utf-8") as archivo:
        json.dump(revision_manual, archivo, indent=2, ensure_ascii=False)
