import contextlib
import io
import os
import socket
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import app_local  # noqa: E402
from app_local import apps_de, escuchando, main, vivo  # noqa: E402

SERVIDOR = "import sys, http.server as h; h.HTTPServer(('127.0.0.1', int(sys.argv[1])), h.BaseHTTPRequestHandler).serve_forever()"


def puerto_libre():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class TestAppLocal(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name
        # Registro y rango propios: los tests nunca ven ni matan apps reales de los agentes.
        self.antes = app_local.DIR, app_local.RANGO
        app_local.DIR = Path(self.dir) / "_registro"
        p = puerto_libre()
        app_local.RANGO = range(p, p + 1)
        os.environ.pop("HERMES_KANBAN_TASK", None)

    def tearDown(self):
        os.environ.pop("HERMES_KANBAN_TASK", None)
        main(["detener"], cwd=self.dir)
        app_local.DIR, app_local.RANGO = self.antes
        self.tmp.cleanup()

    def lanzar(self, *extra, tarea=None):
        if tarea:
            os.environ["HERMES_KANBAN_TASK"] = tarea
        r = main(["iniciar", *extra, "--espera", "30", "--", sys.executable, "-c", SERVIDOR, "{puerto}"], cwd=self.dir)
        os.environ.pop("HERMES_KANBAN_TASK", None)
        return r

    def test_iniciar_y_detener_mata_el_arbol(self):
        puerto = app_local.RANGO.start
        # Un "dotnet run" falso: un padre que lanza a un hijo que es el que escucha (como dotnet → app).
        hijo = f"import http.server as h; h.HTTPServer(('127.0.0.1', {puerto}), h.BaseHTTPRequestHandler).serve_forever()"
        padre = f"import subprocess, sys; subprocess.run([sys.executable, '-c', {hijo!r}])"
        self.assertEqual(main(["iniciar", "--puerto", str(puerto), "--espera", "30", "--",
                               sys.executable, "-c", padre], cwd=self.dir), 0)
        self.assertTrue(escuchando(puerto))
        pid = apps_de(self.dir)[0]["pid"]
        self.assertEqual(main(["detener"], cwd=self.dir), 0)
        self.assertFalse(escuchando(puerto))
        self.assertFalse(vivo(pid))
        self.assertEqual(apps_de(self.dir), [])

    def test_app_que_termina_antes_de_escuchar(self):
        r = main(["iniciar", "--puerto", "auto", "--espera", "20", "--",
                  sys.executable, "-c", "import sys; sys.exit(3)"], cwd=self.dir)
        self.assertEqual(r, 1)

    def test_puerto_ocupado_no_lanza(self):
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            s.listen()
            puerto = s.getsockname()[1]
            self.assertEqual(main(["iniciar", "--puerto", str(puerto), "--", sys.executable, "-c", "pass"],
                                  cwd=self.dir), 2)

    def test_puerto_auto_copia_y_variables(self):
        bin_ = Path(self.dir) / "bin"
        bin_.mkdir()
        # La "app" vive en la carpeta copiada, lee una variable y escucha en el puerto sustituido.
        (bin_ / "app.py").write_text(
            "import os, sys, http.server as h" + chr(10) +
            "assert os.environ['MODO'] == 'prueba'" + chr(10) +
            "h.HTTPServer(('127.0.0.1', int(sys.argv[1])), h.BaseHTTPRequestHandler).serve_forever()" + chr(10),
            encoding="utf-8")
        self.assertEqual(main(["iniciar", "--puerto", "auto", "--copia", "bin", "--env", "MODO=prueba", "--espera", "30",
                               "--", sys.executable, "{copia}/app.py", "{puerto}"], cwd=self.dir), 0)
        app = apps_de(self.dir)[0]
        self.assertIn(app["puerto"], app_local.RANGO)
        self.assertTrue(escuchando(app["puerto"]))
        self.assertTrue(Path(app["copia"], "app.py").exists())
        self.assertNotEqual(Path(app["copia"]).parent, Path(self.dir))  # corre fuera del worktree
        self.assertEqual(main(["detener"], cwd=self.dir), 0)
        self.assertFalse(Path(app["copia"]).exists())

    def test_reservar_es_atomico(self):
        # Dos tarjetas en paralelo eligiendo puerto: solo una se queda con él (antes se pisaban el registro).
        n = app_local.RANGO.start
        self.assertTrue(app_local.reservar(n))
        self.assertFalse(app_local.reservar(n))

    def test_detener_no_mata_la_app_de_otra_tarjeta_activa(self):
        self.assertEqual(self.lanzar("--puerto", "auto", tarea="t_otra"), 0)
        puerto = apps_de(self.dir)[0]["puerto"]
        os.environ["HERMES_KANBAN_TASK"] = "t_mia"
        original = app_local.estado_tarjeta
        app_local.estado_tarjeta = lambda t: "running"
        try:
            self.assertEqual(main(["detener"], cwd=self.dir), 0)
            self.assertTrue(escuchando(puerto))  # la de t_otra sigue
            app_local.estado_tarjeta = lambda t: "done"
            self.assertEqual(main(["detener"], cwd=self.dir), 0)
            self.assertFalse(escuchando(puerto))  # terminada: ya se limpia
        finally:
            app_local.estado_tarjeta = original

    def test_sin_tarjeta_se_protege_si_hay_otra_activa(self):
        # Worker sin HERMES_KANBAN_TASK (registro con tarea None): con otra tarjeta activa en el
        # worktree no se mata; sin tarjetas activas, sí.
        self.assertEqual(self.lanzar("--puerto", "auto"), 0)  # sin tarea
        puerto = apps_de(self.dir)[0]["puerto"]
        original = app_local.otra_activa_en
        app_local.otra_activa_en = lambda w, m: True
        try:
            self.assertEqual(main(["detener"], cwd=self.dir), 0)
            self.assertTrue(escuchando(puerto))  # protegida: dueño desconocido + otra activa
            app_local.otra_activa_en = lambda w, m: False
            self.assertEqual(main(["detener"], cwd=self.dir), 0)
            self.assertFalse(escuchando(puerto))
        finally:
            app_local.otra_activa_en = original

    def test_tarea_por_parametro_sin_env(self):
        # La shell del worker no trae HERMES_KANBAN_TASK: --tarea registra el dueño y permite
        # que su propio detener la mate aunque su tarjeta siga activa.
        self.assertEqual(main(["iniciar", "--puerto", "auto", "--tarea", "t_e2", "--espera", "30",
                               "--", sys.executable, "-c", SERVIDOR, "{puerto}"], cwd=self.dir), 0)
        self.assertEqual(apps_de(self.dir)[0]["tarea"], "t_e2")
        original = app_local.otra_activa_en
        app_local.otra_activa_en = lambda w, m: True  # ella misma sigue activa en el kanban
        try:
            puerto = apps_de(self.dir)[0]["puerto"]
            estado_original = app_local.estado_tarjeta
            app_local.estado_tarjeta = lambda t: "running"
            try:
                self.assertEqual(main(["detener", "--tarea", "t_e2"], cwd=self.dir), 0)
            finally:
                app_local.estado_tarjeta = estado_original
            self.assertFalse(escuchando(puerto))  # es suya: la mata aunque esté activa
        finally:
            app_local.otra_activa_en = original

    def test_detener_reporta_sin_tocar_proceso_ni_copia_sin_registro(self):
        if os.name != "nt":
            self.skipTest("huérfanas solo en Windows")
        puerto = app_local.RANGO.start
        copia = Path(self.dir) / f"app-{puerto}"
        copia.mkdir()
        archivo = copia / "conservar.txt"
        archivo.write_text("ajeno", encoding="utf-8")
        servidor = (
            "import os, sys, http.server as h;"
            "s = h.HTTPServer(('127.0.0.1', int(sys.argv[1])), h.BaseHTTPRequestHandler);"
            "print(os.getpid(), flush=True); s.serve_forever()"
        )
        p = subprocess.Popen([sys.executable, "-c", servidor, str(puerto)], stdout=subprocess.PIPE, text=True)
        try:
            pid_servidor = int(p.stdout.readline().strip())
            for _ in range(50):
                if escuchando(puerto):
                    break
                __import__("time").sleep(0.2)
            self.assertTrue(escuchando(puerto), "el servidor de prueba no arrancó")
            salida = io.StringIO()
            with patch("app_local.tempfile.gettempdir", return_value=self.dir), contextlib.redirect_stdout(salida):
                self.assertEqual(main(["detener"], cwd=self.dir), 0)
            self.assertIsNone(p.poll(), "detener cerró un proceso sin atribución")
            self.assertTrue(escuchando(puerto))
            self.assertEqual(archivo.read_text(encoding="utf-8"), "ajeno")
            self.assertIn("sin registro", salida.getvalue())
            self.assertIn(str(pid_servidor), salida.getvalue())
            self.assertIn(str(puerto), salida.getvalue())
        finally:
            if p.poll() is None:
                app_local.matar_arbol(p.pid)
            p.wait(timeout=10)
            p.stdout.close()

    def test_puerto_invalido(self):
        with self.assertRaises(SystemExit):
            main(["iniciar", "--puerto", "abc", "--", sys.executable, "-c", "pass"], cwd=self.dir)

    def test_vivo_con_utf8_forzado(self):
        # Windows en español + PYTHONUTF8=1: tasklist no viene en UTF-8 (bug visto en una prueba real).
        codigo = ("import sys, os; sys.path.insert(0, sys.argv[1]); from app_local import vivo;"
                  "print(vivo(999999), vivo(os.getpid()))")
        r = subprocess.run([sys.executable, "-c", codigo, str(Path(__file__).resolve().parents[1] / "scripts")],
                           capture_output=True, text=True, env={**os.environ, "PYTHONUTF8": "1"})
        self.assertEqual(r.stdout.split(), ["False", "True"], r.stderr)

    def test_detener_sin_apps(self):
        self.assertEqual(main(["detener"], cwd=self.dir), 0)


if __name__ == "__main__":
    unittest.main()
