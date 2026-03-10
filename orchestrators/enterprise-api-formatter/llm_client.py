"""
LLM Client — Capa de abstracción multi-proveedor
=================================================

Soporta:
  - Anthropic   (claude-opus-4-6, claude-sonnet-4-6, etc.)
  - OpenAI      (gpt-4o, gpt-4-turbo, etc.)
  - Compatible OpenAI:
      · Ollama   (modelos locales: llama3, mistral, qwen, etc.)
      · Groq     (llama3, mixtral, etc.)
      · Azure OpenAI
      · LM Studio
      · Together AI
      · Cualquier proveedor con API compatible a OpenAI

Configuración via variables de entorno:
  LLM_PROVIDER        = anthropic | openai | ollama | groq | azure | custom
  LLM_MODEL           = nombre del modelo (ej: gpt-4o, llama3, claude-opus-4-6)
  ANTHROPIC_API_KEY   = tu clave Anthropic
  OPENAI_API_KEY      = tu clave OpenAI / Groq / Together / etc.
  LLM_BASE_URL        = URL base para APIs compatibles (Ollama, LM Studio, custom)
  LLM_API_KEY         = clave genérica para proveedores custom (alternativa a OPENAI_API_KEY)

Ejemplos:
  # Anthropic (default)
  export LLM_PROVIDER=anthropic
  export LLM_MODEL=claude-opus-4-6
  export ANTHROPIC_API_KEY=sk-ant-...

  # OpenAI
  export LLM_PROVIDER=openai
  export LLM_MODEL=gpt-4o
  export OPENAI_API_KEY=sk-...

  # Ollama (local, sin API key)
  export LLM_PROVIDER=ollama
  export LLM_MODEL=llama3.2
  export LLM_BASE_URL=http://localhost:11434/v1

  # Groq
  export LLM_PROVIDER=groq
  export LLM_MODEL=llama-3.3-70b-versatile
  export OPENAI_API_KEY=gsk_...
  export LLM_BASE_URL=https://api.groq.com/openai/v1

  # LM Studio (local)
  export LLM_PROVIDER=custom
  export LLM_MODEL=local-model
  export LLM_BASE_URL=http://localhost:1234/v1
  export LLM_API_KEY=lm-studio
"""

import json
import os
from enum import Enum


class Provider(str, Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    OLLAMA = "ollama"
    GROQ = "groq"
    AZURE = "azure"
    CUSTOM = "custom"


# ─── Configuración desde entorno ──────────────────────────────────────────────
def get_provider() -> Provider:
    raw = os.getenv("LLM_PROVIDER", "anthropic").lower()
    try:
        return Provider(raw)
    except ValueError:
        print(f"  [LLM] Proveedor '{raw}' no reconocido, usando 'anthropic'.")
        return Provider.ANTHROPIC


def get_model(provider: Provider) -> str:
    defaults = {
        Provider.ANTHROPIC: "claude-opus-4-6",
        Provider.OPENAI: "gpt-4o",
        Provider.OLLAMA: "llama3.2",
        Provider.GROQ: "llama-3.3-70b-versatile",
        Provider.AZURE: "gpt-4o",
        Provider.CUSTOM: "default",
    }
    return os.getenv("LLM_MODEL", defaults[provider])


def get_base_url(provider: Provider) -> str | None:
    env_url = os.getenv("LLM_BASE_URL")
    if env_url:
        return env_url
    if provider == Provider.OLLAMA:
        return "http://localhost:11434/v1"
    if provider == Provider.GROQ:
        return "https://api.groq.com/openai/v1"
    return None


def get_api_key(provider: Provider) -> str:
    if provider == Provider.ANTHROPIC:
        key = os.getenv("ANTHROPIC_API_KEY", "")
        if not key:
            raise EnvironmentError(
                "ANTHROPIC_API_KEY no está configurada.\n"
                "Ejecuta: export ANTHROPIC_API_KEY=sk-ant-..."
            )
        return key

    if provider == Provider.OLLAMA:
        return os.getenv("LLM_API_KEY", "ollama")  # Ollama no requiere key real

    # OpenAI y compatibles
    key = (
        os.getenv("OPENAI_API_KEY")
        or os.getenv("LLM_API_KEY")
        or ""
    )
    if not key and provider not in (Provider.OLLAMA, Provider.CUSTOM):
        raise EnvironmentError(
            f"API key no encontrada para proveedor '{provider}'.\n"
            "Configura OPENAI_API_KEY o LLM_API_KEY."
        )
    return key or "no-key"


# ─── Cliente unificado ─────────────────────────────────────────────────────────
class LLMClient:
    """
    Cliente LLM agnóstico al proveedor.
    Expone un único método `complete(system, user, max_tokens)` que devuelve str.
    """

    def __init__(self):
        self.provider = get_provider()
        self.model = get_model(self.provider)
        self.base_url = get_base_url(self.provider)
        self.api_key = get_api_key(self.provider)

        print(
            f"  [LLM] Proveedor: {self.provider.value} | "
            f"Modelo: {self.model}"
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
            Texto de respuesta del modelo.
        """
        if self.provider == Provider.ANTHROPIC:
            return self._complete_anthropic(system, user, max_tokens)
        else:
            return self._complete_openai_compatible(system, user, max_tokens)

    # ── Anthropic ──────────────────────────────────────────────────────────────
    def _complete_anthropic(self, system: str, user: str, max_tokens: int) -> str:
        try:
            import anthropic as anthropic_sdk
        except ImportError:
            raise ImportError("Instala el SDK: pip install anthropic")

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

    # ── OpenAI y compatibles (Ollama, Groq, Azure, LM Studio, etc.) ───────────
    def _complete_openai_compatible(self, system: str, user: str, max_tokens: int) -> str:
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "Instala el SDK de OpenAI: pip install openai\n"
                "Es compatible con Ollama, Groq, LM Studio y otros."
            )

        kwargs = {"api_key": self.api_key}
        if self.base_url:
            kwargs["base_url"] = self.base_url

        client = OpenAI(**kwargs)

        response = client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
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
        # Eliminar primera línea (```json o ```) y última (```)
        start = 1
        end = len(lines) - 1 if lines[-1].strip() == "```" else len(lines)
        cleaned = "\n".join(lines[start:end]).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Respuesta no es JSON válido: {exc}\nRespuesta recibida:\n{cleaned}"
        ) from exc
