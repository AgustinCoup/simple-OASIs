"""Cliente LLM mínimo para APIs compatibles con OpenAI (por defecto, Nemotron 3 Ultra en OpenRouter)."""
import os
import sys
import time
from typing import Protocol

BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "nvidia/nemotron-3-ultra-550b-a55b:free"  # la versión de pago es sin ":free"
MAX_TOKENS = 16384
TIMEOUT_S = 240  # por lectura de stream; los reintentos los maneja complete()


class LLM(Protocol):
    def complete(self, system: str, prompt: str) -> str: ...


class OpenRouterLLM:
    def __init__(self):
        from openai import OpenAI  # import perezoso: los tests no lo necesitan

        key = os.environ.get("OPENROUTER_API_KEY")
        if not key:
            raise SystemExit("Falta la variable de entorno OPENROUTER_API_KEY.")
        self.client = OpenAI(api_key=key, base_url=BASE_URL, timeout=TIMEOUT_S, max_retries=0)
        self.model = os.environ.get("OASIS_MODEL", DEFAULT_MODEL)
        self.last_info = ""
        self.last_finish = None
        self.reasoning = {"effort": "low"}

    def complete(self, system: str, prompt: str, attempts: int = 3) -> str:
        for i in range(attempts):
            print(f"[oasis] consultando a {self.model} (intento {i + 1}/{attempts})...", file=sys.stderr, flush=True)
            try:
                text = self._call(system, prompt)
                if text.strip():
                    return text
                reason = f"respuesta vacía ({self.last_info})"
                if self.last_finish == "length":  # el razonamiento se comió todo el presupuesto de tokens
                    self.reasoning = {"enabled": False}
                    reason += "; el próximo intento va sin razonamiento"
            except Exception as e:  # timeout, 429, error del proveedor: se reintenta
                reason = f"{type(e).__name__}: {e}"
            print(f"[oasis] falló: {reason}", file=sys.stderr, flush=True)
            if i < attempts - 1:
                time.sleep(5 * (i + 1))
        raise RuntimeError(f"El modelo {self.model} no devolvió contenido tras {attempts} intentos: {reason}")

    def _call(self, system: str, prompt: str) -> str:
        # Streaming: la conexión no queda muda mientras el modelo razona (evita los 504 del proveedor).
        # Esfuerzo de razonamiento bajo: respuestas mucho más rápidas, suficiente para esta tarea.
        stream = self.client.chat.completions.create(
            model=self.model, max_tokens=MAX_TOKENS, temperature=0.2, stream=True,
            extra_body={"reasoning": self.reasoning},
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        )
        parts, finish, reasoning_chars = [], None, 0
        for chunk in stream:
            err = getattr(chunk, "error", None)  # OpenRouter reporta errores a mitad de stream así
            if err:
                raise RuntimeError(err)
            if chunk.choices:
                ch = chunk.choices[0]
                finish = ch.finish_reason or finish
                if ch.delta.content:
                    parts.append(ch.delta.content)
                # los modelos que razonan mandan su razonamiento en un campo aparte
                reasoning_chars += len(getattr(ch.delta, "reasoning", None) or getattr(ch.delta, "reasoning_content", None) or "")
        self.last_finish = finish
        self.last_info = f"finish_reason={finish}, caracteres de razonamiento={reasoning_chars}"
        return "".join(parts)
