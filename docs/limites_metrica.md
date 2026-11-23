# Límites de la métrica de evaluación

## Qué mide

El F1 compara las palabras de la respuesta del modelo con las de una referencia que escribí yo, después de limpiarlas y separarlas en tokens, y cuenta cuántas comparten (con repeticiones). Mide coincidencia de palabras, no si la respuesta es verdadera ni si dice lo mismo con otras palabras.

## Modos de falla conocidos

- Una respuesta correcta pero más larga y detallada que la referencia saca un F1 bajo. Ejemplo: "¿Qué comen los gatos callejeros?", f1=0.17, la respuesta es correcta y más completa que la referencia.
- Los sinónimos y las paráfrasis se castigan aunque el sentido sea el mismo. Ejemplo: "¿Cómo sé si un gato callejero está herido?", f1=0.24, la respuesta habla de "apático" y "evita comer" y la referencia de "no comer" y "maullar de dolor".
- Las cifras distintas pasan con un F1 medio o alto si el resto de la frase coincide. Ejemplo: "¿Cuántas crías puede tener una gata por camada?", f1=0.56, tres a cinco contra cuatro a seis; y "¿Cuánto dura la gestación de una gata?", f1=0.74, hasta 65 días contra hasta 67.
- Un F1 muy bajo a veces sí marca un desacuerdo real, pero no dice quién tiene razón. Ejemplo: "¿Cada cuánto se debe desparasitar a un gato?", f1=0.07, cada tres meses contra cada mes.

## Muestra revisada

Revisé a mano 10 de las 20 respuestas, repartidas desde el F1 más bajo (0.07) hasta uno alto (0.74), con la rúbrica de tres preguntas (corrección factual, completitud, contradicción) y una nota por caso. Está en `revision_manual.py`. 8 de las 10 eran correctas aunque varias tuvieran F1 bajo; 2 tenían un dato distinto al de la referencia (desparasitación y número de crías), y solo una de ellas tenía el F1 más bajo de todos.

## Recomendación de uso

En este pipeline el F1 sirve para ordenar qué revisar primero, no para decir si una respuesta está bien. No hay que confiar en el número solo cuando la pregunta tiene cifras, plazos o dosis (desparasitación, edad de esterilización, gestación): ahí hay que comparar los números a mano, incluso con F1 alto. Tampoco hay que descartar una respuesta solo porque el F1 salió bajo: primero revisar si dice lo mismo con otras palabras o con más detalle.
