"""
Agent 2: Format Validator — InfiniteBit
Skill: skills/format_validator_skill.md

Valida que el payload generado por el Enterprise Formatter cumple con todos
los estándares empresariales InfiniteBit. Emite APPROVED o REJECTED con
diagnóstico detallado para reintento.

Soporta cualquier proveedor LLM configurado en llm_client.py
"""

import json
from pathlib import Path

from llm_client import LLMClient, extract_json

# ─── Rutas ────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
SKILL_PATH = ROOT / "skills" / "format_validator_skill.md"
CONFIG_PATH = ROOT / "config" / "enterprise_config.json"
CONVENTIONS_PATH = ROOT / "config" / "naming_conventions.json"


def _load_skill() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


def _load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def _load_conventions() -> dict:
    return json.loads(CONVENTIONS_PATH.read_text(encoding="utf-8"))


def _build_system_prompt(skill: str, config: dict, conventions: dict) -> str:
    return f"""Eres el Format Validator Agent de InfiniteBit.
Tu única responsabilidad es validar que un payload ya formateado cumple con
los estándares empresariales InfiniteBit, siguiendo estrictamente las reglas de tu skill.

## Tu Skill (reglas de validación que DEBES aplicar):
{skill}

## Configuración empresarial activa:
{json.dumps(config, ensure_ascii=False, indent=2)}

## Convenciones de nombres que deben respetarse:
{json.dumps(conventions, ensure_ascii=False, indent=2)}

## Instrucciones adicionales:
- Responde ÚNICAMENTE con el JSON de validación en formato IB_ValidationResult.
- Sin texto adicional ni markdown alrededor del JSON.
- Sé exhaustivo: revisa cada campo y cada regla del skill.
- IB_Score debe ser numérico 0-100.
- Si IB_Score >= 90 y no hay errores → IB_Status: "APPROVED".
- Si hay cualquier error de VREGLA-01 a VREGLA-05 → IB_Status: "REJECTED".
"""


def run(formatted_payload: dict, attempt: int = 1) -> dict:
    """
    Ejecuta el Format Validator Agent.

    Args:
        formatted_payload: El payload producido por el Enterprise Formatter Agent.
        attempt: Número de intento de validación.

    Returns:
        dict con el resultado de validación (IB_ValidationResult).
        Claves importantes:
          - result["IB_ValidationResult"]["IB_Status"]: "APPROVED" | "REJECTED"
          - result["IB_ValidationResult"]["IB_Errors"]: lista de errores
          - result["IB_ValidationResult"]["IB_ShouldRetry"]: bool
    """
    skill = _load_skill()
    config = _load_config()
    conventions = _load_conventions()

    system_prompt = _build_system_prompt(skill, config, conventions)

    user_content = f"""Valida el siguiente payload formateado por el Enterprise Formatter Agent.

## Intento de validación número: {attempt}

## Payload a validar:
```json
{json.dumps(formatted_payload, ensure_ascii=False, indent=2)}
```

Aplica TODAS las reglas de tu skill (VREGLA-01 a VREGLA-08) y genera el resultado
de validación en formato IB_ValidationResult ahora:
"""

    print(f"  [Agent 2] Validando (intento {attempt})...")

    client = LLMClient()
    response_text = client.complete(system=system_prompt, user=user_content, max_tokens=4096)

    try:
        validation_result = extract_json(response_text)
    except ValueError as exc:
        return {
            "IB_ValidationResult": {
                "IB_Status": "REJECTED",
                "IB_Score": 0,
                "IB_Errors": [
                    {
                        "IB_Code": "ERR_VALIDATOR_PARSE",
                        "IB_Field": "N/A",
                        "IB_Message": f"El validador no pudo parsear su propia respuesta: {exc}",
                        "IB_Suggestion": "Error interno del validator. Reintentando.",
                    }
                ],
                "IB_Warnings": [],
                "IB_ValidatedBy": "InfiniteBit-FormatValidator-Agent",
                "IB_ValidationTimestamp": "",
                "IB_ShouldRetry": True,
            }
        }

    status = validation_result.get("IB_ValidationResult", {}).get("IB_Status", "REJECTED")
    score = validation_result.get("IB_ValidationResult", {}).get("IB_Score", 0)
    print(f"  [Agent 2] Validación completada → {status} (score: {score}/100)")

    return validation_result
