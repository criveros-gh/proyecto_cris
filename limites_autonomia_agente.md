# Límites de autonomía: agente de cuidado de gatos

Documento que describe el código que existe hoy en este repositorio
(`agente_con_herramientas.py`, `agente_con_memoria.py`, `agente_supervision.py`, `trazas_agente.py`).

## Herramientas y nivel de riesgo
- `buscar_guia_cuidado`: bajo (solo lee una guía fija; no modifica nada).
- `calcular_presupuesto`: bajo (solo calcula; no ejecuta ninguna acción externa).
- `consultar_estado_gato_con_historial`: bajo (solo lee datos; peor caso, una respuesta equivocada).
- `generar_reembolso`: alto (mueve dinero de forma irreversible). Existe en `agente_supervision.py`
  como herramienta de demostración con aprobación humana; **todavía no está conectada al agente**
  (no está en su lista `HERRAMIENTAS`). Hoy el agente no puede mover dinero.

No hay herramientas de riesgo medio (escritura reversible) en este agente.

## Herramientas que requieren aprobación humana
- `generar_reembolso`: es irreversible y tiene impacto económico. Llama a `esperar_aprobacion`
  (espera hasta 300 s). Si no hay respuesta a tiempo, el resultado por defecto es **no aprobado**.
  Cada decisión (aprobada o no) se guarda en `registro_aprobaciones` con herramienta, argumentos y momento.
- Las tres herramientas de riesgo bajo **no** piden aprobación: si todo pidiera permiso, quien aprueba
  terminaría diciendo que sí por costumbre. Se revisan después con la traza.

Limitación conocida: `registro_aprobaciones` vive en memoria y se pierde al cerrar el programa;
en un caso real iría a una base de datos. `select` sobre `stdin` no funciona en Windows.

## Revisión de trazas
- Qué se guarda: `registrar_traza` escribe una línea JSON por interacción en `trazas_agente.jsonl`
  (entrada, herramientas con argumentos, observaciones, respuesta final).
- Frecuencia: una muestra pequeña por semana, más **todas** las trazas donde se use una herramienta de riesgo alto.
- Qué se busca:
  1. La misma herramienta repetida seguidas (`marcar_repeticiones_sospechosas` hace la primera pasada;
     solo compara nombres, así que puede dar falsos positivos).
  2. Una herramienta de riesgo alto sin registro de aprobación o rechazo.
  3. Una respuesta final que afirma algo que ninguna observación respalda (posible invención).
- Estado actual: las funciones están probadas con pruebas automáticas (`test_supervision.py`), pero
  `registrar_traza` aún no está conectada al `__main__` del agente, y no hay un `trazas_agente.jsonl`
  real de una corrida en vivo.

## Qué hacer ante un comportamiento inesperado
1. Sacar la herramienta sospechosa de `HERRAMIENTAS` (el agente deja de poder usarla de inmediato).
2. Revisar en `trazas_agente.jsonl` qué argumentos y qué orden usó el agente.
3. Leer la descripción (docstring) de la herramienta: si es ambigua, el modelo la elige mal; reescribirla.
4. Ajustar el prompt del agente si el problema es de criterio, no de la herramienta.
5. Agregar una prueba offline que reproduzca el caso, y recién entonces volver a activar la herramienta.
6. Si hubo una acción de riesgo alto, revisar `registro_aprobaciones` para saber quién la autorizó.
