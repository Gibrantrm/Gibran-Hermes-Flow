import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))
from dotnet_seguro import ESPERA_AGOTADA, compactar, main, partir_run, ruta_candado

SALE_CON = [sys.executable, "-c", "import sys; sys.exit(int(sys.argv[-1]))"]  # "dotnet" falso: sale con el último argumento


def tomar_candado(ruta, segundos):
    """Proceso aparte que toma el candado y lo retiene; devuelve el Popen ya con el candado."""
    codigo = (
        "import sys, time; sys.path.insert(0, sys.argv[1]);"
        "from dotnet_seguro import con_candado;"
        "from pathlib import Path;"
        "cm = con_candado(Path(sys.argv[2]), espera_max=5);"
        "cm.__enter__(); print('tomado', flush=True); time.sleep(float(sys.argv[3]))"
    )
    p = subprocess.Popen([sys.executable, "-c", codigo, str(RAIZ / "scripts"), str(ruta), str(segundos)],
                         stdout=subprocess.PIPE, text=True)
    assert p.stdout.readline().strip() == "tomado"
    return p


class TestDotnetSeguro(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.candado = self.dir / "gibran-build.lock"

    def tearDown(self):
        self.tmp.cleanup()

    def test_candado_vive_en_el_git_dir_del_worktree(self):
        subprocess.run(["git", "init", "-q", str(self.dir)], check=True)
        ruta = ruta_candado(self.dir)
        self.assertEqual(ruta.name, "gibran-build.lock")
        self.assertEqual(ruta.parent.resolve(), (self.dir / ".git").resolve())

    def test_fuera_de_git_usa_la_carpeta_actual(self):
        self.assertEqual(ruta_candado(self.dir).parent.resolve(), self.dir.resolve())

    def test_propaga_el_codigo_de_salida(self):
        self.assertEqual(main(["build", "7"], dotnet=SALE_CON, candado=self.candado), 7)
        self.assertEqual(main(["build", "0"], dotnet=SALE_CON, candado=self.candado), 0)

    def test_espera_a_que_otro_suelte_el_candado(self):
        p = tomar_candado(self.candado, 1.5)
        inicio = time.monotonic()
        codigo = main(["build", "0"], dotnet=SALE_CON, candado=self.candado, espera_max=10, intervalo=0.2)
        self.assertEqual(codigo, 0)
        self.assertGreaterEqual(time.monotonic() - inicio, 1.0)
        p.wait()

    def test_espera_agotada_falla_con_codigo_propio(self):
        p = tomar_candado(self.candado, 5)
        try:
            codigo = main(["build", "0"], dotnet=SALE_CON, candado=self.candado, espera_max=1, intervalo=0.2)
            self.assertEqual(codigo, ESPERA_AGOTADA)
        finally:
            p.kill()
            p.wait()

    def test_proceso_muerto_libera_el_candado(self):
        p = tomar_candado(self.candado, 30)
        p.kill()
        p.wait()
        inicio = time.monotonic()
        # Si el candado quedara tomado, devolvería ESPERA_AGOTADA tras 5 s.
        self.assertEqual(main(["build", "0"], dotnet=SALE_CON, candado=self.candado,
                              espera_max=5, intervalo=0.2), 0)
        self.assertLess(time.monotonic() - inicio, 3)

    def test_comandos_que_no_compilan_no_esperan_el_candado(self):
        p = tomar_candado(self.candado, 5)
        try:
            inicio = time.monotonic()
            self.assertEqual(main(["--list-sdks"], dotnet=[sys.executable, "-c", "pass"],
                                  candado=self.candado, espera_max=10), 0)
            self.assertLess(time.monotonic() - inicio, 2)
        finally:
            p.kill()
            p.wait()

    def test_compactar_quita_repetidos_y_rutas_de_salida(self):
        aviso = rb"C:\x\A.cs(3,5): warning CS8632: anotacion [C:\x\A.csproj]"
        error = rb"C:\x\B.cs(9,1): error CS0103: no existe 'y' [C:\x\A.csproj]"
        salida = b"\r\n".join([aviso, rb"  Ejemplo.Api -> C:\x\bin\Debug\net5.0\Ejemplo.Api.dll",
                               aviso, error, b"    1 Advertencia(s)"])
        self.assertEqual(compactar(salida).splitlines(), [aviso, error, b"    1 Advertencia(s)"])

    def test_compactar_mismo_aviso_en_otro_proyecto_cuenta_como_repetido(self):
        salida = b"\n".join([rb"x.targets(4,5): warning : no soporta net5 [C:\a\A.csproj]",
                             rb"x.targets(4,5): warning : no soporta net5 [C:\a\B.csproj]"])
        self.assertEqual(len(compactar(salida).splitlines()), 1)

    def test_compila_imprime_compactado_y_propaga_codigo(self):
        repite = [sys.executable, "-c", "import sys; print('w'); print('w'); print('fin'); sys.exit(3)"]
        r = subprocess.run(
            [sys.executable, "-c",
             "import sys; sys.path.insert(0, sys.argv[1]); from dotnet_seguro import main;"
             "sys.exit(main(['build'], dotnet=sys.argv[3:], candado=sys.argv[2]))",
             str(RAIZ / "scripts"), str(self.candado), *repite],
            capture_output=True)
        self.assertEqual(r.returncode, 3)
        self.assertEqual(r.stdout.split(), [b"w", b"fin"])


    def test_partir_run(self):
        self.assertEqual(partir_run(["run"]), (["build"], ["run", "--no-build"]))
        build, run = partir_run(["run", "--project", "App/App.csproj", "-c", "Release", "--no-launch-profile",
                                 "--", "--updateDatabase", "--forceUpdate"])
        self.assertEqual(build, ["build", "App/App.csproj", "-c", "Release"])
        self.assertEqual(run, ["run", "--project", "App/App.csproj", "-c", "Release", "--no-launch-profile",
                               "--no-build", "--", "--updateDatabase", "--forceUpdate"])

    def test_run_suelta_el_candado_mientras_corre_la_app(self):
        # "dotnet" falso: el build sale al instante; el run (la app) imprime y espera 2 s.
        falso = [sys.executable, "-c",
                 "import sys, time; print(sys.argv[1], flush=True); time.sleep(2 if sys.argv[1] == 'run' else 0)"]
        codigo = ("import sys; sys.path.insert(0, sys.argv[1]); from dotnet_seguro import main;"
                  "sys.exit(main(['run'], dotnet=sys.argv[3:], candado=sys.argv[2]))")
        app = subprocess.Popen([sys.executable, "-c", codigo, str(RAIZ / "scripts"), str(self.candado), *falso],
                               stdout=subprocess.PIPE, text=True)
        self.assertEqual(app.stdout.readline().strip(), "build")
        self.assertEqual(app.stdout.readline().strip(), "run")
        inicio = time.monotonic()  # con la app viva, otro build toma el candado sin esperar
        self.assertEqual(main(["build", "0"], dotnet=SALE_CON, candado=self.candado, espera_max=1, intervalo=0.1), 0)
        self.assertLess(time.monotonic() - inicio, 1.0)
        app.wait()

    def test_run_con_build_fallido_no_lanza_la_app(self):
        marca = self.dir / "app-lanzada"
        falso = [sys.executable, "-c",
                 "import sys; from pathlib import Path;"
                 "sys.exit(5) if sys.argv[2] == 'build' else Path(sys.argv[1]).touch()", str(marca)]
        self.assertEqual(main(["run"], dotnet=falso, candado=self.candado), 5)
        self.assertFalse(marca.exists())


class TestAlcanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name).resolve()
        self.worktree = self.dir / "worktree"
        self.worktree.mkdir()
        self.proyecto = self.worktree / "Tests.csproj"
        self.proyecto.write_text("<Project />")
        self.estado = self.dir / "local" / "hermes" / "gibran-tests"
        self.env = patch.dict(os.environ, {
            "LOCALAPPDATA": str(self.dir / "local"),
            "HERMES_HOME": str(self.dir / "local" / "hermes"),
            "HERMES_KANBAN_TASK": "",
        })
        self.env.start()
        self.addCleanup(self.env.stop)
        cwd = Path.cwd()
        os.chdir(self.worktree)
        self.addCleanup(os.chdir, cwd)
        self.marca = self.dir / "lanzado.json"
        self.falso = [sys.executable, "-c",
                      "import sys,json; from pathlib import Path;"
                      "Path(sys.argv[1]).write_text(json.dumps(sys.argv[2:]));"
                      "sys.stdout.buffer.write(b'warning\\r\\nwarning\\r\\n'); sys.stdout.flush();"
                      "sys.stderr.buffer.write(b'fallo completo\\r\\n');"
                      "sys.exit(7)", str(self.marca)]
        self.args = ["Tests.csproj", "--filter", "FullyQualifiedName~Permitida", "--nologo"]

    def ejecutar(self, args, dotnet=None):
        return main(args, dotnet=self.falso if dotnet is None else dotnet,
                    candado=self.dir / "build.lock")

    def autorizar(self, args=None, tarea="t_uno"):
        return self.ejecutar(["autorizar-test", "--tarea", tarea,
                             "--worktree", str(self.worktree), "--",
                             *(self.args if args is None else args)])

    def test_sin_autorizacion_no_lanza_dotnet(self):
        codigo = self.ejecutar(["test", "--tarea", "t_uno", *self.args])
        self.assertFalse(self.marca.exists(), "Se ejecutaron tests sin autorización")
        self.assertNotEqual(codigo, 0)

    def test_autorizacion_no_ejecuta_tests_y_retiene_salida_completa_y_codigo(self):
        self.assertEqual(self.autorizar(), 0)
        self.assertFalse(self.marca.exists())
        self.assertEqual(self.ejecutar(["test", "--tarea", "t_uno", *self.args]), 7)
        argv = json.loads(self.marca.read_text())
        self.assertEqual(argv, ["test", str(self.proyecto), *self.args[1:]])
        [registro] = list((self.estado / "ejecuciones").glob("*.json"))
        datos = json.loads(registro.read_text(encoding="utf-8"))
        self.assertEqual(datos["tarea"], "t_uno")
        self.assertEqual(datos["worktree"], str(self.worktree))
        self.assertEqual(datos["comando"], [*self.falso, *argv])
        self.assertEqual(datos["codigo"], 7)
        self.assertEqual(registro.with_suffix(".log").read_bytes(),
                         b"warning\r\nwarning\r\nfallo completo\r\n")
        self.assertEqual(self.ejecutar(["test", "--tarea", "t_uno", *self.args]), 7)
        self.assertEqual(len(list((self.estado / "ejecuciones").glob("*.json"))), 2)

    def test_no_puede_ampliar_seleccion_ni_cambiar_identidad(self):
        self.assertEqual(self.autorizar(), 0)
        casos = [
            ["Tests.csproj"],
            ["Tests.csproj", "--filter", ""],
            ["Otra.csproj", *self.args[1:]],
            ["Tests.csproj", "--filter", "Category=E2E", "--nologo"],
            [*self.args, "--filter", "Category=E2E"],
            [*self.args, "--", "TestCaseFilter=Category=E2E"],
            [*self.args, "-p:VSTestTestCaseFilter=Category=E2E"],
            [*self.args, "@extra.rsp"],
            [*self.args, "--settings", "otra.runsettings"],
            [*self.args, "--no-build"],
        ]
        for args in casos:
            with self.subTest(args=args):
                self.assertNotEqual(self.ejecutar(["test", "--tarea", "t_uno", *args]), 0)
                self.assertFalse(self.marca.exists())
        for prefijo in (["test"], ["test", "--tarea", "t_otro"],
                        ["test", "--tarea", "..\\t_uno"],
                        ["test", "--tarea", "t_uno", "--tarea", "t_uno"]):
            with self.subTest(prefijo=prefijo):
                self.assertNotEqual(self.ejecutar([*prefijo, *self.args]), 0)
                self.assertFalse(self.marca.exists())
        with patch.dict(os.environ, {"HERMES_KANBAN_TASK": "t_otro"}):
            self.assertNotEqual(self.ejecutar(["test", "--tarea", "t_uno", *self.args]), 0)
        otro = self.dir / "otro"
        otro.mkdir()
        os.chdir(otro)
        self.assertNotEqual(self.ejecutar(["test", "--tarea", "t_uno", *self.args]), 0)
        self.assertFalse(self.marca.exists())

    def test_worker_no_se_autoriza_y_politica_no_se_amplia_sola(self):
        for perfil in ("implementador", "revisor"):
            with self.subTest(perfil=perfil), patch.dict(os.environ, {
                "HERMES_HOME": str(self.dir / "local" / "hermes" / "profiles" / perfil)
            }):
                self.assertNotEqual(self.autorizar(), 0)
                self.assertFalse(self.estado.exists())
                self.assertFalse(self.marca.exists())
        with patch.dict(os.environ, {"HERMES_KANBAN_TASK": "t_uno"}):
            self.assertNotEqual(self.autorizar(), 0)
        self.assertEqual(self.autorizar(), 0)
        with patch.dict(os.environ, {"HERMES_KANBAN_TASK": "t_uno"}):
            self.assertEqual(self.ejecutar(["test", *self.args]), 7)

    def test_autorizacion_rechaza_comandos_ambiguos_y_proyecto_externo(self):
        for args in (["Tests.csproj"], [*self.args, "--filter", "Otra"],
                     [*self.args, "--", "TestCaseFilter=Otra"],
                     ["..\\Fuera.csproj", *self.args[1:]],
                     ["Pruebas.sln", *self.args[1:]]):
            with self.subTest(args=args):
                self.assertNotEqual(self.autorizar(args), 0)
                self.assertFalse(self.marca.exists())

    def test_autorizaciones_adicionales_solo_por_orquestador_y_estado_invalido_bloquea(self):
        self.assertEqual(self.autorizar(), 0)
        otra = ["Tests.csproj", "--filter", "FullyQualifiedName~Segunda", "--no-build"]
        self.assertEqual(self.autorizar(otra), 0)
        for args in (self.args, otra):
            self.assertEqual(self.ejecutar(["test", "--tarea", "t_uno", *args]), 7)
        self.marca.unlink()
        [politica] = list((self.estado / "autorizaciones").glob("*.json"))
        for contenido in ("{", "null", "[]", '{"version": 1}'):
            politica.write_text(contenido)
            self.assertNotEqual(self.ejecutar(["test", "--tarea", "t_uno", *self.args]), 0)
            self.assertFalse(self.marca.exists())

    def test_sin_log_no_ejecuta_y_error_de_lanzamiento_no_se_oculta(self):
        self.assertEqual(self.autorizar(), 0)
        logs = self.estado / "ejecuciones"
        logs.write_text("No es un directorio")
        self.assertNotEqual(self.ejecutar(["test", "--tarea", "t_uno", *self.args]), 0)
        self.assertFalse(self.marca.exists())
        logs.unlink()
        self.assertNotEqual(self.ejecutar(["test", "--tarea", "t_uno", *self.args],
                                         dotnet=[str(self.dir / "no-existe.exe")]), 0)
        [registro] = list(logs.glob("*.json"))
        datos = json.loads(registro.read_text(encoding="utf-8"))
        self.assertIsNone(datos["codigo"])
        self.assertIn("error", datos)


if __name__ == "__main__":
    unittest.main()
