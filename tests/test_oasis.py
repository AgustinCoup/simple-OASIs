import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from oasis.cli import NOTE, main

CLAMP = str(Path(__file__).parent.parent / "examples" / "clamp.py")


class FakeLLM:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.prompts = []

    def complete(self, system, prompt):
        self.prompts.append(prompt)
        return self.responses.pop(0)


class CliTest(unittest.TestCase):
    def run_cli(self, llm, assertion="result > lo"):
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(main([CLAMP, assertion], llm=llm), 0)
        return buf.getvalue()

    def test_runs_both_analyses_and_prints_raw_responses(self):
        llm = FakeLLM("RESPUESTA-FP", "RESPUESTA-FN")
        out = self.run_cli(llm)
        self.assertEqual(len(llm.prompts), 2)
        self.assertIn("demasiado fuerte", llm.prompts[0])
        self.assertIn("demasiado débil", llm.prompts[1])
        for p in llm.prompts:  # cada consulta lleva programa y aserción
            self.assertIn("def clamp", p)
            self.assertIn("result > lo", p)
        self.assertLess(out.index("RESPUESTA-FP"), out.index("RESPUESTA-FN"))
        self.assertTrue(out.rstrip().endswith(NOTE))

    def test_prompts_contienen_las_reglas_de_calidad(self):
        from oasis import prompts
        fp = prompts.fp_prompt("prog", "aserto")
        fn = prompts.fn_prompt("prog", "aserto")
        self.assertIn("no uses assertFalse", fp)          # estilo único de test
        self.assertIn("retornos normales", fp)            # excepción != violación de postcondición
        self.assertIn("SOLO el método", fn)               # alcance de los mutantes
        self.assertIn("No propongas mutantes de otros métodos", fn)
        self.assertIn("No debe ser equivalente", fn)      # mutantes no equivalentes
        self.assertIn("constructor o método exacto", fn)  # testigos que ejercitan el cambio

    def test_only_two_arguments(self):
        with self.assertRaises(SystemExit):
            main([CLAMP], llm=FakeLLM())
        with self.assertRaises(SystemExit):
            main([CLAMP, "True", "--mode", "fp"], llm=FakeLLM())

    def test_no_code_execution_in_package(self):
        src = "".join(p.read_text(encoding="utf-8") for p in Path(CLAMP).parent.parent.glob("oasis/*.py"))
        for banned in ("subprocess", "exec(", "eval(", "os.system"):
            self.assertNotIn(banned, src)


if __name__ == "__main__":
    unittest.main()
