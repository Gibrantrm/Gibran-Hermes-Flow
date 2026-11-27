import contextlib
import datetime
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from cierre import main

WT = r"C:\x\Repo.wt-algo"


class TestCierre(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = Path(self.tmp.name)
        self.db, self.metricas, self.costos = d / "kanban.db", d / "tareas.md", d / "costos.jsonl"
        self.metricas.write_text("| fecha | repo |\n|---|---|\n", encoding="utf-8")
        entorno = patch.dict(os.environ, {"GIBRAN_COSTOS": str(self.costos)})
        entorno.start()
        self.addCleanup(entorno.stop)
        self.creada = datetime.datetime.now() - datetime.timedelta(hours=1)
        t = int(self.creada.timestamp())
        self.tareas = [
            ("t1", "done", WT, t), ("t2", "done", WT.replace("\\", "/"), t + 60),
            ("otra", "done", r"C:\x\Otro.wt-y", t)]
        self.rondas = [
            ("t1", "implementador", "review_requested"), ("t1", "revisor", "changes_requested"),
            ("t1", "implementador", "review_requested"), ("t1", "revisor", "completed"),
            ("t2", "implementador", "review_requested"), ("t2", "revisor", "completed")]

        def consultar(sql, parametros=()):
            if sql == "select id, status, workspace_path, created_at from tasks":
                return list(self.tareas)
            if sql == "select profile, outcome from task_runs where task_id = ?":
                return [(p, o) for tid, p, o in self.rondas if tid == parametros[0]]
            raise AssertionError(f"Consulta no esperada: {sql}")

        def conectar(ruta, **opciones):
            if not ruta.endswith("?mode=ro") or opciones != {"uri": True}:
                raise AssertionError("El Kanban debe abrirse solo para lectura")
            return Mock(execute=Mock(side_effect=consultar))

        for parche in (
            patch("cierre.sqlite3.connect", side_effect=conectar),
            patch("cierre.repo_principal", return_value=Path("Repo")),
            patch("cierre.apps_de", return_value=[]),
        ):
            parche.start()
            self.addCleanup(parche.stop)

    def tearDown(self):
        self.tmp.cleanup()

    def correr(self, *extra):
        salida = io.StringIO()
        with contextlib.redirect_stdout(salida):
            codigo = main(["--worktree", WT, "--rama", "feature/algo", "--modo", "feature", "--riesgo", "ALTO",
                           "--e2e", "arnés", *extra], kanban_db=self.db, metricas=self.metricas)
        return codigo, salida.getvalue()

    def marcar(self, cuando, llamadas=()):
        self.costos.with_name("costos.inicio").write_text(cuando.isoformat(timespec="seconds"), encoding="utf-8")
        self.costos.write_text("\n".join(json.dumps(x) for x in llamadas), encoding="utf-8")

    def test_cuenta_del_kanban_y_escribe_la_fila(self):
        self.marcar(self.creada - datetime.timedelta(minutes=10), [
            {"ts": datetime.datetime.now().isoformat(), "perfil": "revisor", "model": "claude-sonnet-5",
             "provider": "anthropic", "usage": {"prompt_tokens": 1_000_000, "completion_tokens": 0}}])
        codigo, out = self.correr()
        self.assertEqual(codigo, 0)
        self.assertIn("Tarjetas: 2 · revisiones del revisor: 3", out)
        fila = self.metricas.read_text(encoding="utf-8").splitlines()[-1]
        self.assertIn("| feature | ALTO | 2 | 3 | arnés | 37.30 | pendiente |", fila)  # 1M × $2 × 18.65
        self.assertIn('integrar.py" --worktree "C:\\x\\Repo.wt-algo" --rama feature/algo', out)

    def test_marca_vieja_o_ausente_no_inventa_costo(self):
        _, out = self.correr()
        self.assertIn("sin medir", self.metricas.read_text(encoding="utf-8"))
        self.assertIn("no hay marca", out)
        self.metricas.write_text("", encoding="utf-8")
        self.marcar(self.creada - datetime.timedelta(days=2))
        _, out = self.correr()
        self.assertIn("no es de esta tarea", out)

    def test_marca_con_zona_horaria_no_truena(self):
        self.marcar(self.creada - datetime.timedelta(minutes=10))
        f = self.costos.with_name("costos.inicio")
        f.write_text(datetime.datetime.fromisoformat(f.read_text()).astimezone().isoformat(timespec="seconds"),
                     encoding="utf-8")
        codigo, out = self.correr()
        self.assertEqual(codigo, 0)
        self.assertIn("desde", out)  # calculó el costo en vez de lanzar TypeError

    def test_alerta_tarjeta_sin_revisor(self):
        self.tareas.append(("t3", "done", WT, int(self.creada.timestamp())))
        self.rondas.append(("t3", "implementador", "completed"))
        codigo, out = self.correr()
        self.assertEqual(codigo, 1)
        self.assertIn("sin aprobación del revisor: t3", out)

    def test_no_duplica_la_fila(self):
        self.correr()
        self.correr()
        self.assertEqual(self.metricas.read_text(encoding="utf-8").count("| feature | ALTO |"), 1)

    def test_tareas_distintas_con_metricas_iguales_conservan_dos_filas(self):
        self.correr()
        self.tareas = [(f"nueva-{i}", s, w, t) for i, s, w, t in self.tareas]
        self.rondas = [(f"nueva-{i}", p, o) for i, p, o in self.rondas]
        self.correr()
        texto = self.metricas.read_text(encoding="utf-8")
        self.assertEqual(texto.count("| feature | ALTO |"), 2)
        self.assertNotIn(WT, texto)

    def test_repetir_cierre_actualiza_costo_sin_perder_fecha_ni_defectos(self):
        self.correr()
        texto = self.metricas.read_text(encoding="utf-8")
        texto = texto.replace(datetime.date.today().isoformat(), "2026-01-01")
        texto = texto.replace("| pendiente |", "| 2 |")
        self.metricas.write_text(texto, encoding="utf-8")
        self.marcar(self.creada - datetime.timedelta(minutes=10), [
            {"ts": datetime.datetime.now().isoformat(), "perfil": "revisor", "model": "claude-sonnet-5",
             "provider": "anthropic", "usage": {"prompt_tokens": 1_000_000, "completion_tokens": 0}}])
        self.correr()
        texto = self.metricas.read_text(encoding="utf-8")
        self.assertEqual(texto.count("| feature | ALTO |"), 1)
        self.assertIn("| 2026-01-01 | Repo |", texto)
        self.assertIn("| 37.30 | 2 |", texto)
        self.assertNotIn("sin medir", texto)

    def test_agregar_tarjetas_no_cambia_identidad_del_cierre(self):
        self.correr()
        self.tareas.append(("t3", "done", WT, int(self.creada.timestamp()) + 120))
        self.rondas.append(("t3", "revisor", "completed"))
        self.tareas = [(i, "archived", w, t) for i, _, w, t in reversed(self.tareas)]
        self.correr()
        texto = self.metricas.read_text(encoding="utf-8")
        self.assertEqual(texto.count("| feature | ALTO |"), 1)
        self.assertIn("| ALTO | 3 | 4 |", texto)

    def test_fila_historica_identica_sin_id_no_se_atribuye_a_esta_tarea(self):
        historica = (f"| {datetime.date.today().isoformat()} | Repo | feature | ALTO | 2 | "
                     "3 | arnés | sin medir | pendiente |\n")
        self.metricas.write_text(historica, encoding="utf-8")
        self.correr()
        texto = self.metricas.read_text(encoding="utf-8")
        self.assertTrue(texto.startswith(historica))
        self.assertEqual(texto.count("| feature | ALTO |"), 2)

    def test_sin_tarjetas_alerta_y_no_escribe_metrica_sin_identidad(self):
        self.tareas = []
        anterior = self.metricas.read_bytes()
        codigo, out = self.correr()
        self.assertEqual(codigo, 1)
        self.assertIn("ALERTA", out)
        self.assertEqual(self.metricas.read_bytes(), anterior)

    def test_identidad_duplicada_o_fila_danada_alerta_sin_sobrescribir(self):
        self.correr()
        original = self.metricas.read_text(encoding="utf-8")
        fila = original.splitlines(keepends=True)[-1]
        for texto in (original + fila, original.replace("| feature |", "")):
            with self.subTest(texto=texto):
                self.metricas.write_text(texto, encoding="utf-8")
                anterior = self.metricas.read_bytes()
                codigo, out = self.correr()
                self.assertEqual(codigo, 1)
                self.assertIn("ALERTA", out)
                self.assertEqual(self.metricas.read_bytes(), anterior)


if __name__ == "__main__":
    unittest.main()
