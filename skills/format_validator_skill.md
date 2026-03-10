# Skill: Format Validator — InfiniteBit
## Descripción
Especialista en validar que el output del Enterprise Formatter cumple al 100%
con los estándares empresariales InfiniteBit. Emite veredicto de aprobación o rechazo
con diagnóstico detallado para reprocesamiento.

---

## Reglas de Validación

### VREGLA-01 · Validar Envelope Completo
Verificar que existan TODOS estos campos de primer nivel:
- `IB_Header` ✓
- `IB_Request` ✓  ← si aplica
- `IB_Response` ✓ ← si aplica
- `IB_Metadata` ✓

**Fallo:** Si falta cualquiera → `REJECTED` con código `ERR_MISSING_ENVELOPE`.

### VREGLA-02 · Validar IB_Header
Campos obligatorios dentro de `IB_Header`:
- `IB_TransactionId` → debe ser string no vacío
- `IB_Timestamp` → debe ser ISO-8601 válido
- `IB_Version` → debe existir
- `IB_SourceSystem` → debe ser string no vacío
- `IB_TargetSystem` → debe ser string no vacío

**Fallo:** Cualquier campo ausente o vacío → `REJECTED` con código `ERR_INVALID_HEADER`.

### VREGLA-03 · Validar Convención de Nombres
El 100% de los campos en `IB_Request` e `IB_Response` deben:
- Tener el prefijo correcto definido en `config/naming_conventions.json`
- Si no hay convención definida, usar prefijo `IB_`
- No contener caracteres especiales excepto `_`

**Fallo:** Cualquier campo sin prefijo correcto → `REJECTED` con código `ERR_NAMING_CONVENTION`
indicando los campos que no cumplen.

### VREGLA-04 · Validar Tipos de Datos
- Fechas deben ser strings ISO-8601
- Booleanos deben ser `true`/`false` (no strings `"true"`)
- Números no deben ser strings

**Fallo:** Tipo de dato incorrecto → `REJECTED` con código `ERR_DATA_TYPE`.

### VREGLA-05 · Validar IB_Metadata
Campos obligatorios:
- `IB_ProcessedBy` → debe ser string que contenga "InfiniteBit"
- `IB_OriginalFormat` → debe existir
- `IB_TransformationReport` → debe existir con `IB_FieldsRenamed` y `IB_ConventionApplied`

**Fallo:** Metadata incompleto → `REJECTED` con código `ERR_METADATA_INCOMPLETE`.

### VREGLA-06 · Validar Sin Campos Nulos Innecesarios
No debe haber campos con valor `null` a menos que estén listados como requeridos.

**Advertencia:** Campos nulos → `WARNING` código `WARN_NULL_FIELDS` (no rechaza, solo advierte).

### VREGLA-07 · Emitir Veredicto
El validator SIEMPRE debe responder en este formato JSON:
```json
{
  "IB_ValidationResult": {
    "IB_Status": "APPROVED" | "REJECTED",
    "IB_Score": <0-100>,
    "IB_Errors": [
      {
        "IB_Code": "<código de error>",
        "IB_Field": "<campo afectado>",
        "IB_Message": "<descripción del problema>",
        "IB_Suggestion": "<cómo corregirlo>"
      }
    ],
    "IB_Warnings": [
      {
        "IB_Code": "<código de advertencia>",
        "IB_Field": "<campo>",
        "IB_Message": "<descripción>"
      }
    ],
    "IB_ValidatedBy": "InfiniteBit-FormatValidator-Agent",
    "IB_ValidationTimestamp": "<ISO-8601>",
    "IB_ShouldRetry": true | false
  }
}
```

### VREGLA-08 · Criterio de Aprobación
- `APPROVED` si `IB_Score` >= 90 y `IB_Errors` está vacío
- `REJECTED` si hay cualquier error de las reglas VREGLA-01 a VREGLA-05
- `IB_ShouldRetry` = `true` cuando el rechazo puede corregirse con un nuevo formateo
- `IB_ShouldRetry` = `false` cuando el input original es inválido o irreparable
