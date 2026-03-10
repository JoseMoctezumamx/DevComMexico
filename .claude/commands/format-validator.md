# /format-validator
Activa el modo Format Validator de InfiniteBit.

Valida que el JSON formateado cumple con todos los estándares empresariales.
Aplica las reglas de `skills/format_validator_skill.md` y emite un veredicto
APPROVED / REJECTED con diagnóstico detallado.

**Uso:** Proporciona el JSON ya formateado por el Enterprise Formatter.
El agente analizará cada campo y regla, devolviendo el resultado de validación
en formato IB_ValidationResult.

Si el resultado es REJECTED, el orquestador reiniciará el proceso desde el
Enterprise Formatter con el diagnóstico de errores adjunto.
