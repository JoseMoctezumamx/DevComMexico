"""
Orchestrator — InfiniteBit Multi-Agent Pipeline
================================================

Flujo:
  1. Solicita información al usuario (sistema origen, destino, payload)
  2. Agent 1 (Enterprise Formatter) transforma el payload
  3. Agent 2 (Format Validator) valida el resultado
  4. Si REJECTED y ShouldRetry → regresa al Agent 1 con diagnóstico (hasta MAX_RETRIES)
  5. Si APPROVED → guarda y muestra el resultado final

Uso:
  python orchestrator.py
  python orchestrator.py --json-input input.json   (para CI/testing)
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Asegurar que el directorio raíz esté en el path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from agents import enterprise_formatter_agent, format_validator_agent

MAX_RETRIES = 3
OUTPUT_DIR = ROOT / "output"


# ─── Colores de terminal ───────────────────────────────────────────────────────
class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    BLUE = "\033[94m"
    GRAY = "\033[90m"


def _print_banner():
    print(f"""
{C.CYAN}{C.BOLD}╔══════════════════════════════════════════════════════════╗
║     InfiniteBit — Enterprise API Formatter Pipeline     ║
║          Multi-Agent Orchestration System v1.0          ║
╚══════════════════════════════════════════════════════════╝{C.RESET}
""")


def _print_section(title: str):
    print(f"\n{C.BLUE}{C.BOLD}{'─' * 60}{C.RESET}")
    print(f"{C.BLUE}{C.BOLD}  {title}{C.RESET}")
    print(f"{C.BLUE}{C.BOLD}{'─' * 60}{C.RESET}\n")


def _collect_user_input() -> dict:
    """Solicita interactivamente toda la información necesaria al usuario."""
    _print_section("Recopilación de información")

    print(f"{C.BOLD}Por favor proporciona los siguientes datos:{C.RESET}\n")

    # Sistema origen
    source_system = input(f"{C.CYAN}1. Nombre del sistema de ORIGEN{C.RESET} (ej: OrderService, PaymentAPI): ").strip()
    if not source_system:
        source_system = "SourceSystem"

    # Sistema destino
    target_system = input(f"{C.CYAN}2. Nombre del sistema DESTINO{C.RESET} (ej: ERP, DataWarehouse): ").strip()
    if not target_system:
        target_system = "TargetSystem"

    # Nombre del API/endpoint
    api_name = input(f"{C.CYAN}3. Nombre del API o Endpoint{C.RESET} (ej: POST /orders, GetUserProfile): ").strip()
    if not api_name:
        api_name = "GenericAPI"

    # Request JSON
    print(f"\n{C.CYAN}4. Request JSON crudo{C.RESET}")
    print(f"{C.GRAY}   Pega el JSON del request (una sola línea o multilínea).")
    print(f"   Cuando termines, escribe 'END' en una línea nueva y presiona Enter:{C.RESET}")
    raw_request = _read_multiline_json("Request")

    # Response JSON
    print(f"\n{C.CYAN}5. Response JSON crudo{C.RESET}")
    print(f"{C.GRAY}   Pega el JSON del response.")
    print(f"   Cuando termines, escribe 'END' en una línea nueva y presiona Enter:{C.RESET}")
    raw_response = _read_multiline_json("Response")

    return {
        "source_system": source_system,
        "target_system": target_system,
        "api_name": api_name,
        "raw_request": raw_request,
        "raw_response": raw_response,
    }


def _read_multiline_json(label: str) -> dict:
    """Lee JSON multilínea desde stdin hasta la línea 'END'."""
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip().upper() == "END":
            break
        lines.append(line)

    raw = "\n".join(lines).strip()

    if not raw:
        print(f"{C.YELLOW}  Sin input para {label}, usando objeto vacío.{C.RESET}")
        return {}

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"{C.RED}  Error parseando {label} JSON: {exc}{C.RESET}")
        print(f"{C.YELLOW}  Usando objeto vacío para {label}.{C.RESET}")
        return {}


def _load_json_input(path: str) -> dict:
    """Carga input desde archivo JSON (modo CI/testing)."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    required = {"source_system", "target_system", "api_name", "raw_request", "raw_response"}
    missing = required - data.keys()
    if missing:
        print(f"{C.RED}El archivo de input le faltan campos: {missing}{C.RESET}")
        sys.exit(1)
    return data


def _save_output(payload: dict, validation: dict, user_input: dict) -> Path:
    """Guarda el resultado final en un archivo JSON."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = f"IB_{user_input['api_name'].replace('/', '_').replace(' ', '_')}_{timestamp}.json"
    output_path = OUTPUT_DIR / filename

    final_output = {
        "IB_PipelineResult": {
            "IB_Status": "SUCCESS",
            "IB_GeneratedAt": datetime.now(timezone.utc).isoformat(),
            "IB_ApiName": user_input["api_name"],
            "IB_SourceSystem": user_input["source_system"],
            "IB_TargetSystem": user_input["target_system"],
        },
        "IB_FormattedPayload": payload,
        "IB_ValidationSummary": validation.get("IB_ValidationResult", {}),
    }

    output_path.write_text(
        json.dumps(final_output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output_path


def run_pipeline(user_input: dict) -> dict:
    """
    Ejecuta el pipeline de orquestación multi-agente.

    Flujo:
      Agent1 → Agent2 → [REJECTED → Agent1 con errores → Agent2] × MAX_RETRIES
    """
    source_system = user_input["source_system"]
    target_system = user_input["target_system"]
    api_name = user_input["api_name"]
    raw_request = user_input["raw_request"]
    raw_response = user_input["raw_response"]

    validation_errors = None
    formatted_payload = None
    validation_result = None

    for attempt in range(1, MAX_RETRIES + 1):
        _print_section(f"Intento {attempt}/{MAX_RETRIES}")

        # ── Agent 1: Enterprise Formatter ────────────────────────────────────
        print(f"{C.BOLD}Agent 1 · Enterprise Formatter{C.RESET}")
        try:
            formatted_payload = enterprise_formatter_agent.run(
                source_system=source_system,
                target_system=target_system,
                api_name=api_name,
                raw_request=raw_request,
                raw_response=raw_response,
                validation_errors=validation_errors,
                attempt=attempt,
            )
        except ValueError as exc:
            print(f"{C.RED}  Error en Agent 1: {exc}{C.RESET}")
            if attempt < MAX_RETRIES:
                print(f"{C.YELLOW}  Reintentando...{C.RESET}")
                continue
            else:
                print(f"{C.RED}  Se agotaron los reintentos. Pipeline fallido.{C.RESET}")
                sys.exit(1)

        # ── Agent 2: Format Validator ─────────────────────────────────────────
        print(f"\n{C.BOLD}Agent 2 · Format Validator{C.RESET}")
        validation_result = format_validator_agent.run(
            formatted_payload=formatted_payload,
            attempt=attempt,
        )

        vr = validation_result.get("IB_ValidationResult", {})
        status = vr.get("IB_Status", "REJECTED")
        score = vr.get("IB_Score", 0)
        errors = vr.get("IB_Errors", [])
        warnings = vr.get("IB_Warnings", [])
        should_retry = vr.get("IB_ShouldRetry", False)

        # Mostrar resultado de validación
        if status == "APPROVED":
            print(f"\n  {C.GREEN}{C.BOLD}✓ APROBADO{C.RESET} — Score: {score}/100")
            if warnings:
                print(f"\n  {C.YELLOW}Advertencias:{C.RESET}")
                for w in warnings:
                    print(f"    {C.YELLOW}⚠ [{w.get('IB_Code')}]{C.RESET} {w.get('IB_Message')}")
            break

        else:
            print(f"\n  {C.RED}{C.BOLD}✗ RECHAZADO{C.RESET} — Score: {score}/100")
            print(f"\n  {C.RED}Errores encontrados:{C.RESET}")
            for err in errors:
                print(f"    {C.RED}● [{err.get('IB_Code')}]{C.RESET} Campo: {err.get('IB_Field')}")
                print(f"      Problema: {err.get('IB_Message')}")
                print(f"      {C.CYAN}Sugerencia: {err.get('IB_Suggestion')}{C.RESET}")

            if not should_retry or attempt >= MAX_RETRIES:
                print(f"\n{C.RED}Pipeline finalizado con REJECTED.{C.RESET}")
                if not should_retry:
                    print(f"{C.RED}El validador indica que el input no es corregible.{C.RESET}")
                else:
                    print(f"{C.RED}Se agotaron los {MAX_RETRIES} reintentos.{C.RESET}")
                return {
                    "status": "FAILED",
                    "formatted_payload": formatted_payload,
                    "validation_result": validation_result,
                }

            # Preparar errores para el siguiente intento del Agent 1
            validation_errors = errors
            print(f"\n  {C.YELLOW}Reiniciando pipeline con diagnóstico de errores...{C.RESET}")

    return {
        "status": "SUCCESS",
        "formatted_payload": formatted_payload,
        "validation_result": validation_result,
    }


def main():
    parser = argparse.ArgumentParser(
        description="InfiniteBit Enterprise API Formatter — Multi-Agent Orchestrator"
    )
    parser.add_argument(
        "--json-input",
        metavar="FILE",
        help="Ruta a un archivo JSON con los campos de input (modo CI/testing)",
    )
    args = parser.parse_args()

    _print_banner()

    # ── Recopilar input ───────────────────────────────────────────────────────
    if args.json_input:
        print(f"{C.GRAY}Cargando input desde: {args.json_input}{C.RESET}")
        user_input = _load_json_input(args.json_input)
    else:
        user_input = _collect_user_input()

    # Confirmar input
    _print_section("Resumen del input")
    print(f"  Sistema origen  : {C.BOLD}{user_input['source_system']}{C.RESET}")
    print(f"  Sistema destino : {C.BOLD}{user_input['target_system']}{C.RESET}")
    print(f"  API / Endpoint  : {C.BOLD}{user_input['api_name']}{C.RESET}")
    print(f"  Request campos  : {len(user_input['raw_request'])} campo(s)")
    print(f"  Response campos : {len(user_input['raw_response'])} campo(s)")

    confirm = input(f"\n{C.CYAN}¿Iniciar pipeline? [S/n]: {C.RESET}").strip().lower()
    if confirm in ("n", "no"):
        print(f"{C.YELLOW}Pipeline cancelado por el usuario.{C.RESET}")
        sys.exit(0)

    # ── Ejecutar pipeline ─────────────────────────────────────────────────────
    result = run_pipeline(user_input)

    # ── Mostrar y guardar resultado ───────────────────────────────────────────
    _print_section("Resultado Final")

    if result["status"] == "SUCCESS":
        output_path = _save_output(
            payload=result["formatted_payload"],
            validation=result["validation_result"],
            user_input=user_input,
        )

        print(f"{C.GREEN}{C.BOLD}Pipeline completado exitosamente.{C.RESET}")
        print(f"\n{C.BOLD}Payload formateado:{C.RESET}")
        print(json.dumps(result["formatted_payload"], ensure_ascii=False, indent=2))
        print(f"\n{C.GREEN}Archivo guardado en: {output_path}{C.RESET}")
    else:
        print(f"{C.RED}{C.BOLD}Pipeline finalizado con errores.{C.RESET}")
        print(f"\n{C.BOLD}Último payload generado (no validado):{C.RESET}")
        print(json.dumps(result["formatted_payload"], ensure_ascii=False, indent=2))
        print(f"\n{C.BOLD}Resultado de validación:{C.RESET}")
        print(json.dumps(result["validation_result"], ensure_ascii=False, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
