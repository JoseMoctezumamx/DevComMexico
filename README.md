# InfiniteBit — Enterprise API Formatter Pipeline
## Sistema de Orquestación Multi-Agente con Claude

Transforma cualquier request/response JSON al formato empresarial **InfiniteBit**,
validando que cumpla con los estándares corporativos antes de entregar el resultado.

---

## Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│                     ORCHESTRATOR                        │
│                    orchestrator.py                      │
│                                                         │
│  1. Solicita información al usuario                     │
│  2. Inicia el pipeline de agentes                       │
│  3. Coordina reintentos si la validación falla          │
└──────────────┬──────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────┐
│  AGENT 1: Enterprise        │  Skill: skills/enterprise_formatter_skill.md
│  Formatter                  │  ─────────────────────────────────────────
│  agents/enterprise_         │  Reglas:
│  formatter_agent.py         │  · REGLA-01: Envelope corporativo IB_
│                             │  · REGLA-02: Convención de nombres
│  Transforma el JSON crudo   │  · REGLA-03: Tipos de datos
│  al formato InfiniteBit     │  · REGLA-04: Campos requeridos
│  aplicando todas las reglas │  · REGLA-05: Preservación de datos
│  de su skill                │  · REGLA-06: Separación Request/Response
└──────────────┬──────────────┘  · REGLA-07: Salida limpia
               │                 · REGLA-08: Reporte de transformación
               │ formatted_payload
               ▼
┌─────────────────────────────┐
│  AGENT 2: Format Validator  │  Skill: skills/format_validator_skill.md
│  agents/format_validator_   │  ─────────────────────────────────────────
│  agent.py                   │  Reglas:
│                             │  · VREGLA-01: Validar envelope completo
│  Valida que el payload      │  · VREGLA-02: Validar IB_Header
│  cumple todos los           │  · VREGLA-03: Validar convención de nombres
│  estándares InfiniteBit     │  · VREGLA-04: Validar tipos de datos
└──────────────┬──────────────┘  · VREGLA-05: Validar IB_Metadata
               │                 · VREGLA-06: Validar sin nulos innecesarios
               │                 · VREGLA-07: Emitir veredicto IB_ValidationResult
               │                 · VREGLA-08: Criterio de aprobación (score >= 90)
               ▼
        APPROVED ───────────────────────────────────── output/IB_*.json
        REJECTED + ShouldRetry ──► Agent 1 (con diagnóstico) → max 3 reintentos
        REJECTED + !ShouldRetry ─► Pipeline fallido
```

---

## Estructura del Proyecto

```
DevComMexico/
└── orchestrators/
    └── enterprise-api-formatter/      # <- Este orquestador
        ├── orchestrator.py            # Punto de entrada principal
        ├── requirements.txt
        │
        ├── agents/
        │   ├── enterprise_formatter_agent.py  # Sub-agente 1: Formateador
        │   └── format_validator_agent.py      # Sub-agente 2: Validador
        │
        ├── skills/
        │   ├── enterprise_formatter_skill.md  # Reglas del Agent 1
        │   └── format_validator_skill.md      # Reglas del Agent 2
        │
        ├── .claude/
        │   └── commands/
        │       ├── enterprise-formatter.md    # Slash command /enterprise-formatter
        │       └── format-validator.md        # Slash command /format-validator
        │
        ├── config/
        │   ├── enterprise_config.json         # Configuracion InfiniteBit
        │   └── naming_conventions.json        # <- CONFIGURA AQUI tus convenciones
        │
        ├── examples/
        │   └── input_example.json             # Ejemplo de input para testing
        │
        └── output/                            # Resultados generados (auto-creado)
            └── IB_*.json
```

---

## Configuración Inicial

### 1. Instalar dependencias

```bash
cd orchestrators/enterprise-api-formatter
pip install -r requirements.txt
```

### 2. Elegir proveedor de IA

El sistema soporta múltiples proveedores. Configura via variables de entorno:

#### Anthropic (Claude) — default
```bash
export LLM_PROVIDER=anthropic
export LLM_MODEL=claude-opus-4-6
export ANTHROPIC_API_KEY=sk-ant-...
```

#### OpenAI (GPT-4o, GPT-4-turbo, etc.)
```bash
export LLM_PROVIDER=openai
export LLM_MODEL=gpt-4o
export OPENAI_API_KEY=sk-...
```

#### Ollama — modelos locales (sin costo, sin internet)
```bash
# Primero instala Ollama: https://ollama.com
ollama pull llama3.2

export LLM_PROVIDER=ollama
export LLM_MODEL=llama3.2
# LLM_BASE_URL default: http://localhost:11434/v1
```

#### Groq (ultra rapido, tier gratuito disponible)
```bash
export LLM_PROVIDER=groq
export LLM_MODEL=llama-3.3-70b-versatile
export OPENAI_API_KEY=gsk_...
export LLM_BASE_URL=https://api.groq.com/openai/v1
```

#### LM Studio u otro compatible OpenAI
```bash
export LLM_PROVIDER=custom
export LLM_MODEL=nombre-del-modelo-local
export LLM_BASE_URL=http://localhost:1234/v1
export LLM_API_KEY=lm-studio
```

### 3. Configurar convenciones de nombres (importante)

Edita `config/naming_conventions.json` con tus reglas personalizadas:

```json
{
  "convention": {
    "prefix": "IB_",
    "style": "PascalCase"
  },
  "fieldMappings": {
    "user_id":    "IB_UserId",
    "created_at": "IB_CreatedAt",
    "order_id":   "IB_OrderId"
  }
}
```

---

## Uso

### Modo interactivo (recomendado)

```bash
cd orchestrators/enterprise-api-formatter
python orchestrator.py
```

El sistema solicitará:
1. Nombre del sistema de origen
2. Nombre del sistema destino
3. Nombre del API/Endpoint
4. Request JSON crudo (pegar y escribir `END`)
5. Response JSON crudo (pegar y escribir `END`)

### Modo CI / Testing (input desde archivo)

```bash
cd orchestrators/enterprise-api-formatter
python orchestrator.py --json-input examples/input_example.json
```

---

## Proveedores soportados

| Proveedor | Variable `LLM_PROVIDER` | Requiere API Key | Modelos ejemplo |
|-----------|------------------------|------------------|-----------------|
| Anthropic | `anthropic` (default) | `ANTHROPIC_API_KEY` | claude-opus-4-6, claude-sonnet-4-6 |
| OpenAI | `openai` | `OPENAI_API_KEY` | gpt-4o, gpt-4-turbo |
| Ollama (local) | `ollama` | No | llama3.2, mistral, qwen2.5 |
| Groq | `groq` | `OPENAI_API_KEY` | llama-3.3-70b-versatile |
| Azure OpenAI | `azure` | `OPENAI_API_KEY` | gpt-4o |
| LM Studio / Custom | `custom` | `LLM_API_KEY` | cualquiera |

---

## Formato de Output

El resultado se guarda en `output/IB_<api>_<timestamp>.json`:

```json
{
  "IB_PipelineResult": {
    "IB_Status": "SUCCESS",
    "IB_GeneratedAt": "2026-03-10T10:30:00Z",
    "IB_ApiName": "POST /orders/create",
    "IB_SourceSystem": "OrderService",
    "IB_TargetSystem": "ERP-InfiniteBit"
  },
  "IB_FormattedPayload": {
    "IB_Header": { },
    "IB_Request": { },
    "IB_Response": { },
    "IB_Metadata": { }
  },
  "IB_ValidationSummary": {
    "IB_Status": "APPROVED",
    "IB_Score": 98,
    "IB_Errors": [],
    "IB_Warnings": []
  }
}
```

---

## Configuracion del Pipeline

- **Max reintentos:** 3 (configurable en `orchestrator.py -> MAX_RETRIES`)
- **Score minimo de aprobacion:** 90/100 (configurable en `config/enterprise_config.json`)
