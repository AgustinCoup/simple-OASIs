# simple-OASIs

Versión sencilla de OASIs: dado un programa y una aserción (oráculo), consulta a un LLM para generar
**feedback** que ayude al usuario a refinar la aserción. La herramienta nunca modifica la aserción: la
decisión final es del usuario. **No se ejecuta código**: el LLM razona leyéndolo.

## Uso

```
python -m pip install -r requirements.txt
$env:OPENROUTER_API_KEY="sk-or-..."      # PowerShell
python -m oasis examples/clamp.py "result > lo"
```

Solo dos argumentos: el archivo del programa y la aserción. Siempre se hacen las dos consultas:

| Problema de la aserción | Qué pide la herramienta al LLM |
|---|---|
| Demasiado **fuerte** (falso positivo) | **Tests** que violen la aserción, con traza y si el culpable es el programa o la aserción |
| Demasiado **débil** (falso negativo) | **Mutantes** del programa que la aserción **no mata**, con una entrada donde difieren del original |

La respuesta del LLM se imprime tal cual, seguida de una nota recordando que nada fue ejecutado.

## Casos de estudio

Aplicación a contratos de Daikon del proyecto 2048 (Java), con verificación ejecutada y resultados: [`docs/casos_de_estudio.md`](docs/casos_de_estudio.md).

## Configuración (variables de entorno)

- `OPENROUTER_API_KEY`: obligatoria.
- `OASIS_MODEL`: opcional. Por defecto `nvidia/nemotron-3-ultra-550b-a55b:free` (Nemotron 3 Ultra,
  variante gratuita de OpenRouter). La versión de pago es el mismo id sin `:free`.

## Estructura

- `oasis/cli.py`: lee los argumentos, hace las dos consultas e imprime.
- `oasis/prompts.py`: los dos prompts (aserción muy fuerte / muy débil).
- `oasis/llm.py`: cliente OpenAI-compatible apuntando a OpenRouter.

## Limitaciones

- Como nada se ejecuta, las trazas y resultados del LLM pueden ser incorrectos: hay que verificarlos.
- La variante gratuita puede devolver error 429 por límite de uso.

## Tests

```
python -m unittest discover -s tests -t . -v
```
(usan un LLM falso; no necesitan red ni API key).
