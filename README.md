# App de michis — miniaplicación del Módulo 1 (Gate 1)

Miniaplicación del programa *Especialización en Desarrollo con IA Generativa* (Skillnest / Accenture).

A partir de la descripción de un gato callejero, la app le pide a **Gemini 3.1 Flash-Lite** que cree una carta de colección con un **nombre** y un **poder**, en JSON validado, y muestra el costo de la petición. Es la base de una futura app móvil para "capturar" y coleccionar gatos callejeros de Chile.

## Requisitos

- Python 3.10 o superior
- Git
- Una API key de Google Gemini (gratis en https://aistudio.google.com/apikey)

## Instalación

### macOS / Linux / WSL

```bash
git clone https://github.com/criveros-gh/proyecto_cris.git
cd proyecto_cris
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### Windows (PowerShell)

```powershell
git clone https://github.com/criveros-gh/proyecto_cris.git
cd proyecto_cris
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

### Configurar la API key

Abre el archivo `.env` que acabas de crear y reemplaza `tu_llave_aqui` por tu llave real:

```
GEMINI_API_KEY=tu_llave_real
```

El `.env` está excluido en `.gitignore` y nunca se sube al repositorio.

## Ejecución

Con el entorno virtual activado, desde la carpeta del proyecto:

```bash
python3 main.py
```

(en Windows, `python main.py`). También puedes pasarle tu propia descripción:

```bash
python3 main.py "Un gato blanco con una oreja negra que duerme sobre un auto"
```

Salida esperada (el nombre y el poder cambian en cada ejecución):

```
Gato: Un gato negro de ojos amarillos que vive en una plaza.
Nombre: ...
Poder: ...
Costo de la petición: 0.00000xxx USD
Proceso terminado sin errores.
```

### Otros scripts

| Comando | Qué hace |
|---|---|
| `python3 prompts/test_consistencia.py` | Corre cada prompt del banco 3 veces y guarda cuántas respuestas fueron JSON válido en `prompts/registro_resultados.json` (Bloque 10) |
| `python3 src/comparar_modelos.py` | Mide latencia, costo y calidad del modelo (Bloque 9). Tarda unos 2–3 minutos por las pausas para no chocar con el límite de uso |

## Estructura

```
main.py                    punto de entrada de la miniaplicación
src/consumir_gemini.py     módulo de consumo de la API: armar_peticion, enviar_peticion,
                           extraer_texto, parsear_respuesta_json, calcular_costo, crear_carta
src/comparar_modelos.py    comparación de modelos (Bloque 9)
prompts/banco.py           banco de prompts con salida JSON (Bloque 10)
prompts/test_consistencia.py  validación de consistencia del banco
prompts/registro_resultados.json  resultado de la última validación
docs/diagrama_arquitectura_gamecat.png  diagrama de arquitectura (Bloque 8)
docs/decision-arquitectura.md  decisión de modelo con tabla comparativa (Bloque 9)
docs/evidencia_peticion_autenticada.md  primera petición autenticada (Bloque 4)
tests/                     pruebas (Módulo 2)
```

## Manejo de errores

El módulo no se cae con un `Traceback` ante los errores esperables; muestra un mensaje claro cuando:

- la pregunta viene vacía,
- falta la API key en `.env`,
- no hay conexión a internet o el servicio tarda más de 60 segundos,
- Gemini responde con un error (401 llave inválida, 429 límite de uso, 503 alta demanda),
- la respuesta no es JSON o no trae las claves esperadas.

## Banco de prompts: resultado de la validación

| Prompt | Respuestas JSON válidas |
|---|---|
| `crear_carta` | 3 de 3 |
| `describir_apariencia` | 3 de 3 |
| `clasificar_rareza` | 2 de 3 |

## Documentación

- Diagrama de arquitectura: [docs/diagrama_arquitectura_gamecat.png](docs/diagrama_arquitectura_gamecat.png)
- Decisión de modelo: [docs/decision-arquitectura.md](docs/decision-arquitectura.md)

## Registro del ensayo de instalación limpia

- Fecha: 2026-10-26
- Encontrado: sin hallazgos en el repositorio. El proyecto se instaló solo con requirements.txt y .env.example, siguiendo este README.
- Corregido: nada.
- Resultado: clonado en una carpeta nueva con un entorno virtual nuevo, `python3 main.py` corrió sin errores contra la API real.