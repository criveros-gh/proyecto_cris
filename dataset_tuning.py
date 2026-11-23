"""B29: dataset propio y validado para personalizar un modelo con PEFT.

Tarea (de COMPORTAMIENTO, no de informacion): clasificar el mensaje de un usuario
de la app de gatos en un JSON de formato fijo {"categoria", "prioridad"}.
El modelo ya sabe que es un gato herido; lo que falta es que SIEMPRE responda
con el mismo formato y las mismas categorias que usa enrutamiento.py.

Este script NO envia ningun trabajo de tuning (cuesta y exige cuenta habilitada):
solo construye, balancea y valida el dataset, todo local y sin API.
"""
import json
from collections import Counter

from google.genai import types

CATEGORIAS_VALIDAS = {"emergencia", "adopcion", "consulta"}   # las de enrutamiento.py
PRIORIDADES_VALIDAS = {"alta", "media", "baja"}
CLAVES_ESPERADAS = ("categoria", "prioridad")

# (mensaje del usuario, salida EXACTA que el modelo debe aprender a producir)
EJEMPLOS_RAW = [
    # --- emergencia ---
    ("Encontre un gatito en la calle que no se mueve y tiene sangre en una pata.",
     {"categoria": "emergencia", "prioridad": "alta"}),
    ("Mi gata se comio una planta y esta vomitando sin parar.",
     {"categoria": "emergencia", "prioridad": "alta"}),
    ("Hay un gato atropellado frente a mi casa, respira muy despacio.",
     {"categoria": "emergencia", "prioridad": "alta"}),
    ("El gatito que rescate esta temblando y no quiere comer desde ayer.",
     {"categoria": "emergencia", "prioridad": "media"}),
    # --- adopcion ---
    ("Quiero adoptar un gato adulto, vivo en un departamento chico.",
     {"categoria": "adopcion", "prioridad": "baja"}),
    ("Que requisitos piden para adoptar a Michi y cuando puedo conocerlo?",
     {"categoria": "adopcion", "prioridad": "baja"}),
    ("Necesito dar en adopcion a una camada de cuatro gatitos esta semana.",
     {"categoria": "adopcion", "prioridad": "media"}),
    ("Puedo adoptar dos gatos hermanos para que no se separen?",
     {"categoria": "adopcion", "prioridad": "baja"}),
    # --- consulta ---
    ("Cuanto cuesta esterilizar a una gata en Santiago?",
     {"categoria": "consulta", "prioridad": "baja"}),
    ("Que alimento le doy a un gatito de dos meses?",
     {"categoria": "consulta", "prioridad": "baja"}),
    ("Cada cuanto debo desparasitar a mi gato?",
     {"categoria": "consulta", "prioridad": "media"}),
    ("Como armo un presupuesto mensual para cuidar tres gatos?",
     {"categoria": "consulta", "prioridad": "baja"}),
]


def construir_examples(ejemplos_raw=EJEMPLOS_RAW):
    """Convierte los pares (texto, dict) al formato real de la API de tuning."""
    return [
        types.TuningExample(text_input=texto, output=json.dumps(salida, ensure_ascii=False))
        for texto, salida in ejemplos_raw
    ]


def chequear_balance(ejemplos_raw, clave="categoria"):
    """Cuenta ejemplos por categoria: un formato perfecto pero desbalanceado
    entrena un modelo sesgado hacia lo mas frecuente."""
    return Counter(salida[clave] for _, salida in ejemplos_raw)


def razon_max_min(balance):
    return max(balance.values()) / min(balance.values())


def validar_dataset(examples, claves_esperadas=CLAVES_ESPERADAS):
    """Devuelve la lista de problemas (vacia si el dataset esta listo)."""
    problemas = []
    vistos = set()
    for i, ej in enumerate(examples):
        if not ej.text_input or not ej.text_input.strip():
            problemas.append(f"ejemplo {i}: text_input vacio")
        if not ej.output or not ej.output.strip():
            problemas.append(f"ejemplo {i}: output vacio")
            continue
        if ej.text_input in vistos:
            problemas.append(f"ejemplo {i}: text_input duplicado")
        vistos.add(ej.text_input)
        try:
            salida = json.loads(ej.output)
        except json.JSONDecodeError:
            problemas.append(f"ejemplo {i}: output no es JSON valido")
            continue
        for clave in claves_esperadas:
            if clave not in salida:
                problemas.append(f'ejemplo {i}: output no tiene la clave "{clave}"')
        # Extra propio: valores dentro del vocabulario permitido
        if salida.get("categoria") not in CATEGORIAS_VALIDAS and "categoria" in salida:
            problemas.append(f'ejemplo {i}: categoria "{salida["categoria"]}" no permitida')
        if salida.get("prioridad") not in PRIORIDADES_VALIDAS and "prioridad" in salida:
            problemas.append(f'ejemplo {i}: prioridad "{salida["prioridad"]}" no permitida')
    return problemas


if __name__ == "__main__":
    examples = construir_examples()
    print(len(examples), "ejemplos construidos")
    print(examples[0])

    print("\nBalance por categoria:")
    balance = chequear_balance(EJEMPLOS_RAW)
    for categoria, cuenta in balance.most_common():
        print(f"  {categoria}: {cuenta}")
    print(f"  razon max/min: {razon_max_min(balance):.1f}x")

    problemas = validar_dataset(examples)
    print(f"\n{len(examples)} ejemplos, {len(problemas)} problemas encontrados")
    for p in problemas:
        print(" -", p)
