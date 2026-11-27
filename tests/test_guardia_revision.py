import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "hooks"))
import guardia_revision
from guardia_revision import evaluar


class TestRevisionConSnapshots(unittest.TestCase):
    """Ejercita la decisión y persistencia sin commits ni escrituras en BD."""

    def setUp(self):
        temporal = tempfile.TemporaryDirectory()
        self.addCleanup(temporal.cleanup)
        self.fotos = Path(temporal.name)
        self.actual = {"a.cs": "entregado"}
        for parche in (
            patch.object(guardia_revision, "carpeta_fotos", return_value=self.fotos),
            patch.object(guardia_revision, "foto", side_effect=lambda _: dict(self.actual)),
            patch.object(guardia_revision, "paralelas", return_value=["t_par"]),
        ):
            parche.start()
            self.addCleanup(parche.stop)
        self.llamar("read_file")

    def llamar(self, herramienta, sid="revision", envuelta=False):
        payload = {"tool_name": herramienta, "tool_input": {}, "session_id": sid, "cwd": "repo"}
        if envuelta:
            payload.update(tool_name="tool_call", tool_input={
                "calls": [{"name": herramienta, "arguments": {}}]})
        return evaluar(payload)

    def test_paralela_no_exime_rutas_fuera_de_la_foto(self):
        for ruta, contenido in (
            ("nuevo.cs", "nuevo"),
            ("permisos.cs", "modificado"),
            ("eliminado.cs", "borrado"),
        ):
            self.actual = {"a.cs": "entregado", ruta: contenido}
            for herramienta in ("kanban_complete", "kanban_request_changes"):
                for envuelta in (False, True):
                    with self.subTest(ruta=ruta, herramienta=herramienta, envuelta=envuelta):
                        r = self.llamar(herramienta, envuelta=envuelta)
                        self.assertEqual(r.get("action"), "block")
                        self.assertIn(ruta, r["message"])
                        self.assertIn("t_par", r["message"])

    def test_paralela_sin_cambios_no_impide_cerrar(self):
        for herramienta in ("kanban_complete", "kanban_request_changes"):
            self.assertEqual(self.llamar(herramienta), {})

    def test_bloqueo_no_reemplaza_foto_y_otra_ronda_toma_estado_nuevo(self):
        foto_inicial = next(self.fotos.iterdir()).read_bytes()
        self.actual["permisos.cs"] = "modificado"
        self.assertEqual(self.llamar("kanban_complete").get("action"), "block")
        self.assertEqual(self.llamar("kanban_block"), {})
        self.assertEqual(next(self.fotos.iterdir()).read_bytes(), foto_inicial)
        self.assertEqual(self.llamar("kanban_complete").get("action"), "block")
        self.assertEqual(self.llamar("read_file", sid="otra-ronda"), {})
        self.assertEqual(self.llamar("kanban_complete", sid="otra-ronda"), {})


if __name__ == "__main__":
    unittest.main()
