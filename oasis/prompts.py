SYSTEM = ("Eres un asistente de ingeniería de software que ayuda a refinar aserciones (oráculos) de "
          "programas. No puedes ejecutar código: razona leyéndolo y traza a mano el programa y la "
          "aserción con cuidado. Responde en español, de forma escueta: sin introducciones, sin repetir el programa ni la aserción.")


def context(program: str, assertion: str) -> str:
    return f"Programa:\n```\n{program}\n```\n\nAserción:\n```\n{assertion}\n```\n"


def fp_prompt(program: str, assertion: str) -> str:
    return (context(program, assertion) +
            "\nLa aserción podría ser demasiado fuerte (falso positivo): rechazar comportamientos "
            "correctos del programa. Genera como máximo 2 TESTS EJECUTABLES para el programa (en su mismo lenguaje, con "
            "el framework habitual, por ejemplo JUnit para Java o pytest para Python) que hagan FALLAR la aserción. "
            "Reglas:\n"
            "- El test debe invocar el programa y comprobar la aserción sobre el resultado, y debe FALLAR cuando la "
            "aserción se viola (usa assertTrue/assert sobre la aserción; no uses assertFalse para invertirla).\n"
            "- Usa solo entradas válidas: respeta los invariantes del programa y usa constructores o métodos que "
            "realmente existan; indica cuál usas.\n"
            "- Una postcondición describe solo los retornos normales. Si el test falla porque el método lanza una "
            "excepción en lugar de retornar, dilo explícitamente en vez de decir sin más que la aserción es fuerte.\n"
            "Para cada test indica:\n"
            "- el código completo del test,\n"
            "- el resultado que produce el programa con esa entrada (traza breve),\n"
            "- por qué viola la aserción,\n"
            "- si parece un bug del programa o si la aserción es demasiado fuerte.\n"
            "Limita la búsqueda: si tras un análisis razonable no encuentras ninguno, responde que no encontraste y "
            "no sugieras ningún cambio. Si encontraste alguno, sugiere al final una aserción más débil.")


def fn_prompt(program: str, assertion: str) -> str:
    return (context(program, assertion) +
            "\nLa aserción podría ser demasiado débil (falso negativo): dejar pasar comportamientos "
            "incorrectos. Genera como máximo 3 mutantes que la aserción NO pueda matar. Reglas:\n"
            "- El mutante debe cambiar SOLO el método (o el código que ese método ejecuta directamente) al que se "
            "refiere la aserción. No propongas mutantes de otros métodos, aunque sean bugs reales: la aserción "
            "solo describe este método.\n"
            "- Cambio pequeño y plausible que altere la semántica. No debe ser equivalente al original: comprueba "
            "con la entrada que el resultado realmente cambia.\n"
            "- La entrada testigo debe ser válida (respeta los invariantes del programa) y debe ejercitar el cambio: "
            "indica el constructor o método exacto que usas y verifica que ese camino ejecuta la línea mutada.\n"
            "Para cada mutante indica:\n"
            "- el cambio realizado y SOLO el método o las líneas mutadas (no repitas la clase entera),\n"
            "- una entrada donde mutante y original dan resultados distintos,\n"
            "- por qué la aserción se cumple igual en ambos.\n"
            "Limita la búsqueda: si tras un análisis razonable no encuentras ninguno, responde que no encontraste y "
            "no sugieras ningún cambio. Si encontraste alguno, sugiere al final una aserción más fuerte.")
