"""
LLM Client — Capa de abstracción multi-proveedor
=================================================

Soporta:
  - Anthropic        (claude-opus-4-6, claude-sonnet-4-6, etc.)
  - GitHub Copilot   (gpt-4o, gpt-4.1, o3-mini via GitHub Copilot API)
  - GitHub Models    (gpt-4o, Meta-Llama, Mistral, Phi via marketplace)
  - Gemini           (gemini-2.0-flash, gemini-1.5-pro via endpoint OpenAI-compat)
  - OpenAI           (gpt-4o, gpt-4-turbo, etc.)
  - Ollama           (modelos locales: llama3, mistral, qwen, etc.)
  - Groq             (llama3, mixtral — tier gratuito disponible)
  - Azure OpenAI
  - LM Studio / cualquier API compatible con OpenAI

Configuración via variables de entorno:
  LLM_PROVIDER        = anthropic | github-copilot | github-models | gemini |
                        openai | ollama | groq | azure | custom
  LLM_MODEL           = nombre del modelo
  ANTHROPIC_API_KEY   = clave Anthropic
  GITHUB_TOKEN        = token GitHub (para github-copilot y github-models)
  GEMINI_API_KEY      = clave Google AI Studio (para gemini)
  OPENAI_API_KEY      = clave OpenAI / Groq / etc.
  LLM_BASE_URL        = URL base custom (sobreescribe el default del proveedor)
  LLM_API_KEY         = clave genérica alternativa

─── Ejemplos de configuración ──────────────────────────────────────────────────

  # GitHub Copilot — GPT-4o
  export LLM_PROVIDER=github-copilot
  export LLM_MODEL=gpt-4o
  export GITHUB_TOKEN=ghp_...         # token con scope copilot

  # GitHub Copilot — GPT-4.1
  export LLM_PROVIDER=github-copilot
  export LLM_MODEL=gpt-4.1
  export GITHUB_TOKEN=ghp_...

  # GitHub Models — GPT-4o (marketplace gratuito con límites)
  export LLM_PROVIDER=github-models
  export LLM_MODEL=gpt-4o
  export GITHUB_TOKEN=ghp_...         # token clásico de GitHub (sin scope especial)

  # Google Gemini — gemini-2.0-flash
  export LLM_PROVIDER=gemini
  export LLM_MODEL=gemini-2.0-flash
  export GEMINI_API_KEY=AIza...       # desde aistudio.google.com/apikey

  # Google Gemini — gemini-1.5-pro
  export LLM_PROVIDER=gemini
  export LLM_MODEL=gemini-1.5-pro
  export GEMINI_API_KEY=AIza...

  # OpenAI
  export LLM_PROVIDER=openai
  export LLM_MODEL=gpt-4o
  export OPENAI_API_KEY=sk-...

  # Anthropic (default)
  export LLM_PROVIDER=anthropic
  export LLM_MODEL=claude-opus-4-6
  export ANTHROPIC_API_KEY=sk-ant-...

  # Ollama (local, sin API key)
  export LLM_PROVIDER=ollama
  export LLM_MODEL=llama3.2

  # Groq (tier gratuito)
  export LLM_PROVIDER=groq
  export LLM_MODEL=llama-3.3-70b-versatile
  export OPENAI_API_KEY=gsk_...
"""

import json
import os
from enum import Enum


class Provider(str, Enum):
    ANTHROPIC      = "anthropic"
    GITHUB_COPILOT = "github-copilot"
    GITHUB_MODELS  = "github-models"
    GEMINI         = "gemini"
    OPENAI         = "openai"
    OLLAMA         = "ollama"
    GROQ           = "groq"
    AZURE          = "azure"
    CUSTOM         = "custom"


# ─── URLs base por proveedor ───────────────────────────────────────────────────
_BASE_URLS = {
    Provider.GITHUB_COPILOT: "https://api.githubcopilot.com",
    Provider.GITHUB_MODELS:  "https://models.inference.ai.azure.com",
    Provider.GEMINI:         "https://generativelanguage.googleapis.com/v1beta/openai/",
    Provider.GROQ:           "https://api.groq.com/openai/v1",
    Provider.OLLAMA:         "http://localhost:11434/v1",
}

# ─── Modelos default por proveedor ────────────────────────────────────────────
_DEFAULT_MODELS = {
    Provider.ANTHROPIC:      "claude-opus-4-6",
    Provider.GITHUB_COPILOT: "gpt-4o",
    Provider.GITHUB_MODELS:  "gpt-4o",
    Provider.GEMINI:         "gemini-2.0-flash",
    Provider.OPENAI:         "gpt-4o",
    Provider.OLLAMA:         "llama3.2",
    Provider.GROQ:           "llama-3.3-70b-versatile",
    Provider.AZURE:          "gpt-4o",
    Provider.CUSTOM:         "default",
}


# ─── Helpers de configuración ─────────────────────────────────────────────────
def get_provider() -> Provider:
    raw = os.getenv("LLM_PROVIDER", "anthropic").lower()
    try:
        return Provider(raw)
    except ValueError:
        known = [p.value for p in Provider]
        print(f"  [LLM] Proveedor '{raw}' no reconocido. Opciones: {known}")
        print(f"  [LLM] Usando 'anthropic' por defecto.")
        return Provider.ANTHROPIC


def get_model(provider: Provider) -> str:
    return os.getenv("LLM_MODEL", _DEFAULT_MODELS[provider])


def get_base_url(provider: Provider) -> str | None:
    # Variable de entorno tiene prioridad
    env_url = os.getenv("LLM_BASE_URL")
    if env_url:
        return env_url
    return _BASE_URLS.get(provider)


def get_api_key(provider: Provider) -> str:
    # Anthropic usa su propia variable
    if provider == Provider.ANTHROPIC:
        key = os.getenv("ANTHROPIC_API_KEY", "")
        if not key:
            raise EnvironmentError(
                "ANTHROPIC_API_KEY no está configurada.\n"
                "Ejecuta: export ANTHROPIC_API_KEY=sk-ant-..."
            )
        return key

    # GitHub Copilot y GitHub Models usan GITHUB_TOKEN
    if provider in (Provider.GITHUB_COPILOT, Provider.GITHUB_MODELS):
        key = os.getenv("GITHUB_TOKEN", "")
        if not key:
            raise EnvironmentError(
                "GITHUB_TOKEN no está configurado.\n"
                "Ejecuta: export GITHUB_TOKEN=ghp_...\n"
                "Obtén tu token en: https://github.com/settings/tokens"
            )
        return key

    # Gemini usa GEMINI_API_KEY (o OPENAI_API_KEY como alternativa)
    if provider == Provider.GEMINI:
        key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")
        if not key:
            raise EnvironmentError(
                "GEMINI_API_KEY no está configurada.\n"
                "Ejecuta: export GEMINI_API_KEY=AIza...\n"
                "Obtén tu clave en: https://aistudio.google.com/apikey"
            )
        return key

    # Ollama no requiere key real
    if provider == Provider.OLLAMA:
        return os.getenv("LLM_API_KEY", "ollama")

    # OpenAI, Groq, Azure, Custom
    key = (
        os.getenv("OPENAI_API_KEY")
        or os.getenv("LLM_API_KEY")
        or ""
    )
    if not key and provider not in (Provider.CUSTOM,):
        raise EnvironmentError(
            f"API key no encontrada para proveedor '{provider.value}'.\n"
            "Configura OPENAI_API_KEY o LLM_API_KEY."
        )
    return key or "no-key"


# ─── Cliente unificado ─────────────────────────────────────────────────────────
class LLMClient:
    """
    Cliente LLM agnóstico al proveedor.
    Expone un único método `complete(system, user, max_tokens)` → str.
    """

    def __init__(self):
        self.provider = get_provider()
        self.model    = get_model(self.provider)
        self.base_url = get_base_url(self.provider)
        self.api_key  = get_api_key(self.provider)

        print(
            f"  [LLM] Proveedor: {self.provider.value} | Modelo: {self.model}"
            + (f" | URL: {self.base_url}" if self.base_url else "")
        )

    def complete(self, system: str, user: str, max_tokens: int = 8192) -> str:
        """
        Genera una respuesta del LLM.

        Args:
            system: System prompt / instrucciones del agente.
            user: Mensaje del usuario / payload a procesar.
            max_tokens: Máximo de tokens en la respuesta.

        Returns:
            Texto de respuesta del modelo (str).
        """
        if self.provider == Provider.ANTHROPIC:
            return self._complete_anthropic(system, user, max_tokens)
        else:
            return self._complete_openai_compatible(system, user, max_tokens)

    # ── Anthropic (SDK nativo con thinking adaptativo) ─────────────────────────
    def _complete_anthropic(self, system: str, user: str, max_tokens: int) -> str:
        try:
            import anthropic as anthropic_sdk
        except ImportError:
            raise ImportError("Ejecuta: pip install anthropic")

        client = anthropic_sdk.Anthropic(api_key=self.api_key)

        with client.messages.stream(
            model=self.model,
            max_tokens=max_tokens,
            thinking={"type": "adaptive"},
            system=system,
            messages=[{"role": "user", "content": user}],
        ) as stream:
            final = stream.get_final_message()

        for block in final.content:
            if block.type == "text":
                return block.text.strip()
        return ""

    # ── OpenAI-compatible (GitHub Copilot, GitHub Models, Gemini, OpenAI, etc.) ─
    def _complete_openai_compatible(self, system: str, user: str, max_tokens: int) -> str:
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("Ejecuta: pip install openai")

        client = OpenAI(api_key=self.api_key, base_url=self.base_url)

        response = client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
        )

        return response.choices[0].message.content.strip()


# ─── Limpieza de respuesta JSON ────────────────────────────────────────────────
def extract_json(text: str) -> dict:
    """
    Extrae y parsea JSON de la respuesta del LLM.
    Maneja bloques de código markdown (```json ... ```) automáticamente.
    """
    cleaned = text.strip()

    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        start = 1
        end = len(lines) - 1 if lines[-1].strip() == "```" else len(lines)
        cleaned = "\n".join(lines[start:end]).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Respuesta no es JSON válido: {exc}\nRespuesta recibida:\n{cleaned}"
        ) from exc
