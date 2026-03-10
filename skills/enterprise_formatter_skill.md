# Skill: Enterprise Formatter — InfiniteBit
## Descripción
Especialista en transformar requests y responses a formato empresarial InfiniteBit.
Aplica convenciones de nombres, estructura de envelope y metadatos corporativos.

---

## Reglas Obligatorias

### REGLA-01 · Envelope de Respuesta
Toda respuesta transformada DEBE contener el envelope empresarial:
```json
{
  "IB_Header": {
    "IB_TransactionId": "<uuid-v4>",
    "IB_Timestamp": "<ISO-8601>",
    "IB_Version": "1.0",
    "IB_SourceSystem": "<nombre del sistema de origen>",
    "IB_TargetSystem": "<nombre del sistema destino>",
    "IB_CorrelationId": "<id de correlación>"
  },
  "IB_Payload": { ... },
  "IB_Metadata": {
    "IB_ProcessedBy": "InfiniteBit-EnterpriseFormatter-Agent",
    "IB_OriginalFormat": "<formato origen>",
    "IB_ConventionVersion": "<versión de convención aplicada>"
  }
}
```

### REGLA-02 · Convención de Nombres
Aplicar la convención cargada desde `config/naming_conventions.json`.
Si el archivo no tiene convención definida, usar el **default InfiniteBit**:
- Prefijo: `IB_`
- Estilo: `PascalCase` después del prefijo
- Ejemplo: `IB_UserId`, `IB_CreatedAt`, `IB_OrderStatus`

### REGLA-03 · Tipos de Datos
- Fechas → ISO-8601 (`2026-03-10T00:00:00Z`)
- Booleanos → `true` / `false` (minúsculas JSON)
- Identificadores → string con prefijo de contexto (ej: `ORD-001`, `USR-042`)
- Montos → number con 2 decimales máximos

### REGLA-04 · Campos Requeridos
Cada campo transformado debe tener:
- Nombre renombrado con la convención activa
- Tipo de dato validado
- Descripción corta en `IB_Metadata.IB_FieldDescriptions` (opcional pero recomendado)

### REGLA-05 · Preservación de Datos
NUNCA eliminar campos del payload original.
Si un campo no tiene equivalente en la convención, mantenerlo con prefijo `IB_Custom_`.

### REGLA-06 · Separación Request / Response
El output DEBE distinguir claramente:
```json
{
  "IB_Header": { ... },
  "IB_Request": { ... },
  "IB_Response": { ... },
  "IB_Metadata": { ... }
}
```

### REGLA-07 · Salida Limpia
- Sin comentarios en el JSON final
- Sin campos `null` a menos que sean explícitamente requeridos
- Indentación de 2 espacios

### REGLA-08 · Reporte de Transformación
Al finalizar, incluir en `IB_Metadata` un resumen:
```json
"IB_TransformationReport": {
  "IB_FieldsRenamed": <número>,
  "IB_FieldsAdded": <número>,
  "IB_ConventionApplied": "<nombre de convención>",
  "IB_Warnings": []
}
```
