import argparse
import sys
from pathlib import Path

from . import prompts
from .llm import OpenRouterLLM

NOTE = ("Nota: el LLM razona sobre el código sin ejecutarlo; verificá estos resultados antes de "
        "decidir. La decisión de refinar la aserción es tuya.")


def analyze(llm, program: str, assertion: str) -> str:
    """Hace las dos consultas (aserción muy fuerte / muy débil) y devuelve el texto a imprimir."""
    fp = llm.complete(prompts.SYSTEM, prompts.fp_prompt(program, assertion))
    fn = llm.complete(prompts.SYSTEM, prompts.fn_prompt(program, assertion))
    return (f"Aserción: {assertion}\n\n"
            f"== Posible aserción demasiado FUERTE (tests que la violan) ==\n{fp.strip()}\n\n"
            f"== Posible aserción demasiado DÉBIL (mutantes que no mata) ==\n{fn.strip()}\n\n{NOTE}")


def main(argv=None, llm=None):
    ap = argparse.ArgumentParser(prog="oasis", description="Feedback LLM para refinar una aserción.")
    ap.add_argument("program", help="archivo con el programa")
    ap.add_argument("assertion", help="la aserción a analizar")
    a = ap.parse_args(argv)
    program = Path(a.program).read_text(encoding="utf-8")
    print(analyze(llm or OpenRouterLLM(), program, a.assertion))
    return 0


if __name__ == "__main__":
    sys.exit(main())
