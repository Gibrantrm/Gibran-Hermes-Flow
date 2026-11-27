import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "hooks"))
from guardia_build import PY, SCRIPT, evaluar


def p(comando, herramienta="terminal", clave="command"):
    return {"tool_name": herramienta, "tool_input": {clave: comando}}


class TestGuardiaBuild(unittest.TestCase):
    def test_worker_no_registra_su_propio_alcance(self):
        for comando in ('python dotnet_seguro.py autorizar-test --tarea t_uno',
                        "subprocess.run(['python', 'dotnet_seguro.py', 'autorizar-test'])"):
            self.assertEqual(evaluar(p(comando)).get("action"), "block")

    def test_reescribe_dotnet_que_compila_en_terminal(self):
        # El worker escribe dotnet normal; la guardia lo pasa por el candado sin gastar una llamada.
        for c, esperado in [
            ("dotnet build src/Api/Api.csproj", "build src/Api/Api.csproj"),
            ("dotnet test tests/X.Tests.csproj --filter Foo", "test tests/X.Tests.csproj --filter Foo"),
            ("dotnet.exe publish -c Release", "publish -c Release"),
            ("DOTNET build", "build"),
        ]:
            r = evaluar(p(c))
            self.assertEqual(r.get("action"), "modify", c)
            self.assertEqual(r["args"], {"command": f'"{PY}" "{SCRIPT}" {esperado}'}, c)

    def test_reescribe_cada_aparicion_y_conserva_el_resto(self):
        r = evaluar(p("cd src && dotnet build A.csproj && dotnet run"))
        self.assertEqual(r["args"]["command"],
                         f'cd src && "{PY}" "{SCRIPT}" build A.csproj && "{PY}" "{SCRIPT}" run')

    def test_en_execute_code_bloquea_y_dice_que_usar(self):
        r = evaluar(p("subprocess.run(['dotnet', 'test'])", "execute_code", "code"))
        self.assertEqual(r.get("action"), "block")
        self.assertIn("dotnet_seguro.py", r["message"])

    def test_permite_dotnet_seguro_y_lo_que_no_compila(self):
        for c in [
            '"python" "hermes-flow/scripts/dotnet_seguro.py" build X.csproj',
            "dotnet --list-sdks",
            "dotnet restore",
            "dotnet format --verify-no-changes",
            "dotnet ef migrations list",
            "git status",
        ]:
            self.assertEqual(evaluar(p(c)), {}, c)

    def test_payload_raro(self):
        self.assertEqual(evaluar({}), {})
        self.assertEqual(evaluar({"tool_input": None}), {})


if __name__ == "__main__":
    unittest.main()
