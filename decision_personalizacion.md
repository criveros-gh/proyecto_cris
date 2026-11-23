# Decisión de personalización

Método: `decision.py` (cinco preguntas con evidencia, puntaje por técnica). Fecha: 2026-11-23.

## 1. El problema
**Caso principal (servicio RAG):** el servicio debe responder preguntas sobre la documentación del propio proyecto citando la fuente. Al modelo le falta información propia del proyecto; no le falta comportamiento.

**Caso secundario (clasificador):** clasificar el mensaje de un usuario en un JSON fijo `{categoria, prioridad}`. Es de comportamiento y fue el candidato a PEFT del B29.

## 2. Resultado del método de decisión

### Caso principal: servicio RAG
- RAG: 5 puntos
- PEFT: 1 puntos
- Fine-tuning completo: 0 puntos

Ganadora clara: RAG (sin empate).

| Pregunta | Respuesta | Evidencia |
|---|---|---|
| ¿La información cambia seguido? | Sí | 49 commits con actividad en octubre y noviembre de 2026 (2 de 2 meses); las fuentes del corpus se siguen editando. |
| ¿Problema de formato o tono? | No | No hay una muestra de 20 respuestas con 3 o más fallos. El prompt ya exige citar y 1 de 1 corrida real respondió. |
| ¿Dataset grande y de calidad? | No | 12 ejemplos etiquetados; el umbral es 200. |
| ¿Presupuesto limitado o iterar rápido? | Sí | La entrega del Gate 2 vence el mismo día (23:59). |
| ¿Múltiples variantes? | No | Un solo servicio: 1 versión. |

### Caso secundario: clasificador
- RAG: 2 puntos
- PEFT: 1 puntos
- Fine-tuning completo: 0 puntos

El puntaje favorece a RAG, pero **esa ventaja viene solo de la pregunta del plazo de un día**; las otras cuatro respuestas fueron "No". Además RAG no resuelve un problema de formato. El puntaje no se descarta ni se obedece sin pensar: se interpreta en la sección 3.

## 3. Técnica elegida y por qué
**Servicio: RAG.** La información es propia del proyecto y cambia: agregar un documento es indexarlo, no reentrenar (ya construido y evaluado: con `k=1` la precisión fue 0,917 y el recall 1,000 sobre 12 preguntas, resultados reales del 2026-11-23). Se descartan PEFT y fine-tuning completo porque no hay problema de comportamiento medido ni dataset suficiente.

**Clasificador: no personalizar todavía.** Ninguna técnica está justificada hoy. RAG no aplica (no falta información) y PEFT no tiene base: no se midió ningún fallo de formato, la salida ya se normaliza con `strip().lower()` y hay 12 ejemplos de los 200 necesarios. Entrenar sin haber medido el problema sería elegir la técnica antes de tener la evidencia.

## 4. Qué se necesitaría para ejecutarla
- **RAG (ya ejecutado):** el corpus indexado cubre 6 de 27 archivos fuente (22 módulos `.py` + 5 documentos `.md`); faltarían 21 por indexar si se quisiera cubrir todo el proyecto.
- **Para reconsiderar PEFT en el clasificador:**
  1. Medir primero: revisar 20 respuestas reales del clasificador; se justifica si 3 o más (15 %) incumplen el formato.
  2. Llegar a 200 ejemplos etiquetados: faltan 188; a 5 minutos cada uno son 15,7 horas.
  3. Revisar 20 ejemplos al azar y confirmar que ninguno tiene etiquetas contradictorias.

## Limitaciones de esta decisión
- Las respuestas "No" a formato dependen de que no hay medición, no de que se haya medido que no hay problema.
- Los umbrales (20 respuestas, 200 ejemplos, una vez al mes) son los orientativos del curso, no valores oficiales de la API.
- No se envió ningún trabajo de tuning: no hubo costo de cómputo ni tokens facturables que reportar.
