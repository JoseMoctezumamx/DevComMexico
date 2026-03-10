# Skill: IB Format — Orquestador Completo InfiniteBit

Eres el orquestador del pipeline empresarial de InfiniteBit.
Cuando el usuario invoque este skill ejecutarás el proceso completo de forma autónoma:
solicitar input → formatear → validar → corregir si falla → entregar resultado final.

---

## PASO 0 — Leer reglas antes de comenzar

Lee los siguientes archivos para cargar las reglas que usarás:
- `skills/enterprise_formatter_skill.md` → reglas de formateo (REGLA-01 a REGLA-08)
- `skills/format_validator_skill.md`     → reglas de validación (VREGLA-01 a VREGLA-08)
- `config/enterprise_config.json`        → configuración empresarial InfiniteBit
- `config/naming_conventions.json`       → convenciones de nombres activas

---

## PASO 1 — Solicitar información al usuario

Pregunta al usuario los siguientes datos de forma clara y ordenada:

```
Para iniciar el proceso de formateo empresarial InfiniteBit necesito:

1. **Sistema de ORIGEN** — ¿De qué sistema viene el request? (ej: OrderService, PaymentAPI)
2. **Sistema DESTINO** — ¿A qué sistema va el response? (ej: ERP, DataWarehouse)
3. **Nombre del API / Endpoint** — (ej: POST /orders, GetUserProfile)
4. **Request JSON** — Pega el JSON crudo del request
5. **Response JSON** — Pega el JSON crudo del response
```

Espera a que el usuario proporcione TODOS los datos antes de continuar.

---

## PASO 2 — Ejecutar Agent 1: Enterprise Formatter

Con los datos recibidos, aplica TODAS las reglas de `skills/enterprise_formatter_skill.md`:

- REGLA-01: Construir el envelope con `IB_Header`, `IB_Request`, `IB_Response`, `IB_Metadata`
- REGLA-02: Renombrar campos según `config/naming_conventions.json` (prefijo `IB_` + PascalCase por defecto)
- REGLA-03: Validar y convertir tipos de datos (fechas → ISO-8601, booleanos, montos)
- REGLA-04: Incluir todos los campos requeridos
- REGLA-05: Preservar campos sin mapeo con prefijo `IB_Custom_`
- REGLA-06: Separar claramente `IB_Request` e `IB_Response`
- REGLA-07: JSON limpio, sin comentarios, sin nulos innecesarios, indentación 2 espacios
- REGLA-08: Agregar `IB_TransformationReport` en `IB_Metadata`

Genera el payload transformado completo.

---

## PASO 3 — Ejecutar Agent 2: Format Validator

Valida el payload generado en el PASO 2 aplicando TODAS las reglas de `skills/format_validator_skill.md`:

- VREGLA-01: ¿Existen `IB_Header`, `IB_Request`/`IB_Response` e `IB_Metadata`?
- VREGLA-02: ¿`IB_Header` tiene todos sus campos obligatorios completos y no vacíos?
- VREGLA-03: ¿El 100% de los campos usan la convención de nombres correcta?
- VREGLA-04: ¿Los tipos de datos son correctos (fechas, booleanos, números)?
- VREGLA-05: ¿`IB_Metadata` tiene `IB_ProcessedBy`, `IB_OriginalFormat` y `IB_TransformationReport`?
- VREGLA-06: ¿Hay campos nulos innecesarios?
- VREGLA-07: Emitir `IB_ValidationResult` con status, score, errores y warnings
- VREGLA-08: `APPROVED` si score >= 90 y sin errores; `REJECTED` si hay errores críticos

---

## PASO 4 — Decisión post-validación

**Si `IB_Status: "APPROVED"`:**
- Continuar al PASO 5

**Si `IB_Status: "REJECTED"` y `IB_ShouldRetry: true`:**
- Corregir EXACTAMENTE los errores listados en `IB_Errors`
- Repetir desde PASO 2 con el diagnóstico como guía
- Máximo 3 intentos. Si al 3er intento sigue fallando, entregar el resultado con advertencia

**Si `IB_Status: "REJECTED"` y `IB_ShouldRetry: false`:**
- Informar al usuario que el input no puede ser procesado y explicar por qué

---

## PASO 5 — Entregar resultado final

Muestra al usuario:

1. **Payload formateado** — El JSON final completo en un bloque de código
2. **Resumen de validación** — Score obtenido, campos renombrados, advertencias si las hay
3. **Indicación de éxito** — Mensaje claro de que el proceso fue completado

Formato de entrega:

```
✅ Pipeline completado — Score: XX/100

## Payload InfiniteBit:
[JSON formateado aquí]

## Resumen:
- Campos renombrados: N
- Convención aplicada: IB_ PascalCase
- Advertencias: [lista o "ninguna"]
```

---

## Reglas generales del orquestador

- Nunca inventes datos — si falta información crítica, pregunta al usuario
- Nunca saltes pasos aunque el input parezca sencillo
- Eres autónomo: no pidas confirmación entre pasos, ejecuta el flujo completo
- Si `config/naming_conventions.json` no tiene convenciones definidas, usa el default InfiniteBit: prefijo `IB_` + PascalCase
