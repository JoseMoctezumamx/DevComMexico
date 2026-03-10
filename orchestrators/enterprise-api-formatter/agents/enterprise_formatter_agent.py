"""
Agent 1: Enterprise Formatter — InfiniteBit
Skill: skills/enterprise_formatter_skill.md

Transforma requests y responses crudos al formato empresarial InfiniteBit,
aplicando convenciones de nombres y el envelope corporativo.

Soporta cualquier proveedor LLM configurado en llm_client.py
"""

import json
from pathlib import Path

from llm_client import LLMClient, extract_json

# ─── Rutas ────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
SKILL_PATH = ROOT / "skills" / "enterprise_formatter_skill.md"
CONFIG_PATH = ROOT / "config" / "enterprise_config.json"
CONVENTIONS_PATH = ROOT / "config" / "naming_conventions.json"


def _load_skill() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


def _load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def _load_conventions() -> dict:
    return json.loads(CONVENTIONS_PATH.read_text(encoding="utf-8"))


def _build_system_prompt(skill: str, config: dict, conventions: dict) -> str:
    return f"""Eres el Enterprise Formatter Agent de InfiniteBit.
Tu única responsabilidad es transformar datos crudos (request/response) al formato
empresarial InfiniteBit, siguiendo estrictamente las reglas de tu skill.

## Tu Skill (reglas que DEBES cumplir):
{skill}

## Configuración empresarial activa:
{json.dumps(config, ensure_ascii=False, indent=2)}

## Convenciones de nombres activas:
{json.dumps(conventions, ensure_ascii=False, indent=2)}

## Instrucciones adicionales:
- Responde ÚNICAMENTE con el JSON transformado, sin texto adicional ni markdown.
- Si recibes un diagnóstico de errores de validación previo, corrígelos en esta iteración.
- El JSON de salida debe ser válido y parseable.
- Usa siempre comillas dobles para strings en JSON.
"""


def run(
    source_system: str,
    target_system: str,
    api_name: str,
    raw_request: dict,
    raw_response: dict,
    validation_errors: list | None = None,
    attempt: int = 1,
) -> dict:
    """
    Ejecuta el Enterprise Formatter Agent.

    Args:
        source_system: Nombre del sistema de origen.
        target_system: Nombre del sistema destino.
        api_name: Nombre descriptivo del API/endpoint.
        raw_request: Payload crudo del request.
        raw_response: Payload crudo del response.
        validation_errors: Lista de errores del validador (si es un reintento).
        attempt: Número de intento actual.

    Returns:
        dict con el payload transformado en formato InfiniteBit.
    """
    skill = _load_skill()
    config = _load_config()
    conventions = _load_conventions()

    system_prompt = _build_system_prompt(skill, config, conventions)

    user_content = f"""Transforma los siguientes datos al formato empresarial InfiniteBit.

## Información del contexto:
- Sistema origen: {source_system}
- Sistema destino: {target_system}
- API / Endpoint: {api_name}
- Intento número: {attempt}

## Request crudo:
```json
{json.dumps(raw_request, ensure_ascii=False, indent=2)}
```

## Response crudo:
```json
{json.dumps(raw_response, ensure_ascii=False, indent=2)}
```
"""

    if validation_errors:
        errors_text = json.dumps(validation_errors, ensure_ascii=False, indent=2)
        user_content += f"""
## ERRORES DEL VALIDADOR (corrígelos en este intento):
```json
{errors_text}
```
Asegúrate de resolver TODOS los errores listados antes de generar el output.
"""

    user_content += "\nGenera el JSON transformado ahora:"

    print(f"  [Agent 1] Formateando (intento {attempt})...")

    client = LLMClient()
    response_text = client.complete(system=system_prompt, user=user_content, max_tokens=8192)

    try:
        formatted_payload = extract_json(response_text)
    except ValueError as exc:
        raise ValueError(f"Agent 1 produjo JSON inválido en intento {attempt}: {exc}") from exc

    print(f"  [Agent 1] Formateo completado (intento {attempt}).")
    return formatted_payload
