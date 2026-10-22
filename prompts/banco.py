# Banco de prompts de la app de michis (Bloque 10 · Actividad Core)
# Cada prompt tiene: nombre, prompt de sistema, ejemplo de entrada,
# claves esperadas y el esquema JSON que debe cumplir la respuesta.

BANCO_DE_PROMPTS = [
    {
        "nombre": "crear_carta",
        "system_instruction": (
            "Eres un creador de cartas de colección de gatos callejeros. "
            "Responde únicamente con un objeto JSON válido, sin texto adicional "
            "y sin usar bloques de markdown. El JSON debe tener exactamente estas "
            "claves: 'nombre' (string, un nombre inventado para el gato) y "
            "'poder' (string, un poder especial en una frase corta)."
        ),
        "ejemplo_usuario": "Un gato negro de ojos amarillos que vive en una plaza.",
        "claves_esperadas": ["nombre", "poder"],
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "nombre": {"type": "STRING"},
                "poder": {"type": "STRING"}
            },
            "required": ["nombre", "poder"]
        },
    },
    {
        "nombre": "describir_apariencia",
        "system_instruction": (
            "Eres un experto en gatos. A partir de la descripción de un gato, "
            "responde únicamente con un objeto JSON válido, sin texto adicional "
            "y sin usar bloques de markdown. El JSON debe tener exactamente estas "
            "claves: 'color_principal' (string), 'patron' (string, por ejemplo "
            "'atigrado', 'tricolor', 'liso' o 'bicolor') y 'descripcion' "
            "(string, una sola frase)."
        ),
        "ejemplo_usuario": "Un gato naranjo atigrado con una mancha blanca en el pecho.",
        "claves_esperadas": ["color_principal", "patron", "descripcion"],
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "color_principal": {"type": "STRING"},
                "patron": {"type": "STRING"},
                "descripcion": {"type": "STRING"}
            },
            "required": ["color_principal", "patron", "descripcion"]
        },
    },
    {
        "nombre": "clasificar_rareza",
        "system_instruction": (
            "Eres el clasificador de rareza de un álbum de gatos callejeros. "
            "Responde únicamente con un objeto JSON válido, sin texto adicional "
            "y sin usar bloques de markdown. El JSON debe tener exactamente estas "
            "claves: 'rareza' (string: 'comun', 'rara' o 'legendaria') y "
            "'confianza' (número entre 0 y 1)."
        ),
        "ejemplo_usuario": "Un gato tricolor (blanco, negro y naranjo) con un ojo de cada color.",
        "claves_esperadas": ["rareza", "confianza"],
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "rareza": {"type": "STRING"},
                "confianza": {"type": "NUMBER"}
            },
            "required": ["rareza", "confianza"]
        },
    },
]