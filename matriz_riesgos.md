# Matriz de riesgos del servicio RAG

Puntaje = probabilidad x impacto. Cortes: CRITICO >= 15, ALTO >= 9, MEDIO >= 4, BAJO < 4.
`al limite` = mover un punto la probabilidad o el impacto cambia la categoria (la estimacion es una opinion: conviene que otra persona la revise).

| Categoria | Puntaje | Riesgo | P | I | Mitigacion | Estado | Supervision | Al limite |
|---|---|---|---|---|---|---|---|---|
| CRITICO | 16 | Inyeccion de prompt via documento recuperado | 4 | 4 | Roles separados, contexto delimitado y filtro de patrones en seguridad_prompt.py (Bloque 31); lo descartado queda en el log | parcial | Si el filtro descarta un documento, revision humana antes de entregar la respuesta (se conecta en servicio_rag.py, Gate 2) | si |
| CRITICO | 15 | Contenido crudo o datos personales en los logs | 3 | 5 | logging_rag.py registra huellas y largos, nunca la pregunta ni los documentos; test que lo verifica (Bloque 31) | construida | Acceso a los logs restringido y aprobado por una persona (control organizacional, fuera del codigo) | si |
| ALTO | 12 | Respuesta con cita inventada o sin respaldo en las fuentes | 3 | 4 | Prompt que exige [n] y admitir contexto insuficiente, mas verificar_citas en recuperacion.py (Bloque 26) | parcial | Una respuesta con citas invalidas se marca para revision y no se entrega como definitiva (Gate 2) | si |
| ALTO | 12 | Proveedor del modelo con errores intermitentes (503) o rate limit | 4 | 3 | Reintentos con backoff en cliente.py (Unidad 2.1) y errores resumidos sin romper el flujo en registro_rag.py (Bloque 28) | parcial | Si fallan todos los reintentos el servicio avisa y no inventa respuesta; un operador decide reintentar o escalar | si |
| ALTO | 12 | Cambio de prompt sin trazabilidad o desplegado sin revision | 3 | 4 | registro_prompts.py con huella y diff, y grafo_supervision.py con aprobacion obligatoria (Bloque 32) | construida | interrupt() en grafo_supervision.py: nadie activa una version sin Command(resume=True) | si |
| ALTO | 10 | Accion irreversible del agente (reembolso) sin aprobacion humana | 2 | 5 | esperar_aprobacion con timeout y por defecto 'no aprobado' en agente_supervision.py (Bloque 23); la herramienta aun no esta conectada al agente (ver limites_autonomia_agente.md) | parcial | Aprobacion humana explicita antes de generar_reembolso | si |
| ALTO | 9 | Recuperacion deficiente: el chunk relevante no llega al contexto | 3 | 3 | precision@k y recall@k sobre 12 casos con k=1/3/5 (evaluacion_recuperacion.py, Bloque 27) | construida | Revision humana periodica de los casos con recall bajo al cambiar corpus, chunk_size o modelo de embeddings | si |
| MEDIO | 6 | Costo o latencia por consulta fuera de lo esperado | 3 | 2 | Medicion por etapa y costo real con usage_metadata en registro_rag.py (Bloque 28) | construida | - | si |
