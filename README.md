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

## Módulo 2: servicio RAG con observabilidad y supervisión (Gate 2)

Además de la miniaplicación, el repositorio contiene un **servicio RAG** que responde preguntas sobre la documentación del propio proyecto, citando la fuente de cada respuesta.

### Cómo se usa (desde cero)

Con el entorno virtual activado y el `.env` con `GEMINI_API_KEY` (ver Instalación):

```bash
pip install -r requirements.txt
python verificar_entorno.py          # revisa Python, paquetes, clave e índice (no imprime la clave)
python indexar_corpus.py             # UNA vez: crea el índice persistido en vectorstore/
python servicio_rag.py "¿Qué acciones necesitan aprobación humana?"
```

El índice se persiste en `vectorstore/` (no se sube a Git) y el servicio **nunca reindexa al consultar**: solo se reconecta. Si cambia el corpus, el tamaño de chunk o el modelo de embeddings, hay que volver a correr `python indexar_corpus.py`. Para agregar o borrar un solo documento sin reindexar todo: `agregar_documento` / `borrar_documento` (Bloque 25).

Salida esperada (cambian `trace_id`, tiempos y texto): una línea JSON por evento y al final

```
respuesta final: ... Fuentes: [1] <archivo>
estado: ok | trace_id: trace-xxxxxxxx
Proceso terminado sin errores.
```

Los mismos eventos se guardan en `logs/servicio_rag.log` (ignorado por Git).

### Qué hace `servicio_rag.py`

| Etapa | Qué pasa | Bloque |
|---|---|---|
| Recuperar | embedding de la pregunta + búsqueda en el índice persistido, con tiempo por etapa | 24-26, 28 |
| Filtrar | descarta documentos con patrones de inyección de prompt; si todo es sospechoso no llama al modelo | 31 |
| Generar | prompt con roles separados y contexto delimitado como dato; reintentos ante 503/429 | 31 |
| Citar | solo entrega fuentes verificadas contra el contexto recuperado | 26 |
| Registrar | logs JSON con `trace_id`, consumo real de tokens, latencia y costo (si se pasan tarifas) | 28, 31 |
| Supervisar | si hubo inyección o las citas no se pueden verificar, la respuesta **queda pausada** (`interrupt()`) hasta que una persona la aprueba o la rechaza | 32 |

Gobernanza de logs: **nunca** se registra la pregunta ni el texto de los documentos; solo longitudes, huellas (hash), conteos y nombres de fuente. Cada consulta lleva un `trace_id` propio y el log incluye la huella del prompt activo (`registro_prompts.py`).

### Verificación

```bash
python -m pytest test_gate2.py -v        # los 4 criterios no compensables (offline, sin API)
python -m pytest test_servicio_rag.py test_grafo_supervision.py test_logging_rag.py test_registro_prompts.py test_matriz_riesgos.py -q
```

Las pruebas usan embeddings y modelo simulados: no consumen la API. **No correr `pytest` sin argumentos**: `prompts/test_consistencia.py` hace llamadas reales.

### Piezas del módulo

| Archivo | Contenido |
|---|---|
| `indexar_corpus.py`, `recuperacion.py` | indexación persistida, recuperación y citas verificables |
| `evaluacion_recuperacion.py`, `metricas_recuperacion.py` | precisión/exhaustividad sobre 12 casos etiquetados a mano (`resultados_evaluacion_2026-11-23_k*.txt`) |
| `registro_rag.py`, `registros_latencia_costo.jsonl` | latencia por etapa y tokens reales |
| `decision.py`, `decision_personalizacion.md` | decisión RAG vs fine-tuning vs PEFT |
| `dataset_tuning.py` | dataset de ejemplo y chequeo de balance |
| `seguridad_prompt.py`, `logging_rag.py` | mitigación de inyección, logging estructurado y `trace_id` |
| `registro_prompts.py`, `registro_prompts.json` | versionado de prompts con huella y diff |
| `grafo_supervision.py` | supervisión humana con LangGraph (`interrupt` / `Command`): despliegue de prompts y revisión de respuestas |
| `matriz_riesgos.py`, `matriz_riesgos.md` | matriz de riesgos (8 filas propias) |
| `servicio_rag.py` | servicio integrado |

### Resultados medidos y límites conocidos

- **Recuperación** (12 casos, corpus propio, recall 1.00 en los tres k): precisión 0.917 con k=1, 0.306 con k=3 y 0.183 con k=5. Con k más grande llegan más fragmentos de los que hacen falta; el caso sin respuesta ("arriendo de oficina") se incluyó a propósito.
- **Latencia y costo:** hay **dos** corridas reales documentadas (`registros_latencia_costo.jsonl`). La primera: generación ≈ 17,5 s, 194 tokens de entrada y 24 de salida. La segunda, del servicio integrado: embed ≈ 1,3 s, búsqueda ≈ 5 ms y generación ≈ 185 s (299 de entrada, 21 de salida) porque Gemini respondió 503 y hubo un reintento. La generación domina la latencia y es muy variable cuando el proveedor está saturado. Las tarifas no están fijadas en el código: se pasan a `ServicioRAG(tarifas=(entrada_por_1000, salida_por_1000))` desde la documentación oficial vigente. La comparación real k=3 vs k=6 quedó pendiente porque Gemini respondió 503 de forma intermitente durante las pruebas.
- **Supervisión:** la pausa pide la decisión por consola (`s` para aprobar; sin respuesta en 5 minutos queda en "no aprobado"). El checkpointer es en memoria (`InMemorySaver`): si el proceso se reinicia con una revisión pendiente, se pierde. En producción hace falta un checkpointer durable.
- **Filtro de inyección:** es una lista de patrones; no detecta cualquier ataque (sinónimos, otros idiomas). Por eso es una capa más y no la única.
- **Agente de reembolsos:** `generar_reembolso` pide aprobación humana (Bloque 23) pero aún no está conectado al agente; detalle en `limites_autonomia_agente.md`.

## Documentación

- Diagrama de arquitectura: [docs/diagrama_arquitectura_gamecat.png](docs/diagrama_arquitectura_gamecat.png)
- Decisión de modelo: [docs/decision-arquitectura.md](docs/decision-arquitectura.md)

## Registro del ensayo de instalación limpia

- Fecha: 2026-10-26
- Encontrado: sin hallazgos en el repositorio. El proyecto se instaló solo con requirements.txt y .env.example, siguiendo este README.
- Corregido: nada.
- Resultado: clonado en una carpeta nueva con un entorno virtual nuevo, `python3 main.py` corrió sin errores contra la API real.

## Registro del ensayo de rate limit

- Fecha: 2026-11-04
- Peticiones enviadas: 40
- Primer reintento: en la petición número 1 (Respuesta 0). Las respuestas 0 a 3 agotaron los 3 intentos y fallaron definitivamente (probablemente por la cuota aún sin liberar de pruebas anteriores)
- Esperas observadas: 2.0s a 2.2s en el primer reintento y 4.1s a 4.3s en el segundo (backoff exponencial con jitter, correcto)
- Respuesta 22: falló una vez, esperó 2.1s y terminó con éxito al reintentar
- Costo total del ensayo: $0.00363 (36 peticiones exitosas; las 4 fallidas no registraron costo)
- Resultado: 36 de 40 terminaron con éxito; 4 fallaron definitivamente con RuntimeError y mensaje claro