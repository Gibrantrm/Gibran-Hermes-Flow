import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "hooks"))
from guardia_rutas import HERMES_FLOW, evaluar

SKILL = HERMES_FLOW / "skills" / "gibran-flow" / "stack-dotnet" / "SKILL.md"


def llamada(nombre, args):
    return {"tool_name": nombre, "tool_input": args}


def bloquea(payload, solo_lectura=False):
    return evaluar(payload, solo_lectura).get("action") == "block"


class TestGuardiaRutas(unittest.TestCase):
    def test_autorizaciones_solo_mediante_el_registrador(self):
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ, {"LOCALAPPDATA": d}):
            politica = Path(d) / "hermes" / "gibran-tests" / "autorizaciones" / "t_uno.json"
            for payload in (
                llamada("write_file", {"path": str(politica), "content": "{}"}),
                llamada("patch", {"patch": f"*** Add File: {politica}\n+{{}}"}),
                llamada("patch", {"patch": f"*** Update File: {Path(d) / 'otro.json'}\n"
                                          f"*** Move to: {politica}\n@@\n-a\n+b"}),
                llamada("tool_call", {"calls": [{"name": "write_file",
                                                "arguments": {"path": str(politica)}}]}),
            ):
                self.assertTrue(bloquea(payload))
            log = politica.parent.parent / "ejecuciones" / "log.json"
            self.assertTrue(bloquea(llamada("write_file", {"path": str(log)})))

    def test_nadie_escribe_en_hermes_flow(self):
        self.assertTrue(bloquea(llamada("write_file", {"path": str(SKILL), "content": "x"})))
        self.assertTrue(bloquea(llamada("patch", {"path": str(SKILL), "old_string": "a", "new_string": "b"})))
        v4a = f"*** Begin Patch\n*** Update File: {SKILL}\n@@\n-a\n+b\n*** End Patch"
        self.assertTrue(bloquea(llamada("patch", {"mode": "patch", "patch": v4a})))

    def test_skill_manage_sobre_skill_del_flujo(self):
        self.assertTrue(bloquea(llamada("skill_manage", {"action": "patch", "name": "stack-dotnet"})))
        self.assertTrue(bloquea(llamada("skill_manage", {"operations": [
            {"action": "patch", "name": "stack-dotnet", "old_string": "a", "new_string": "b"}]})))
        self.assertFalse(bloquea(llamada("skill_manage", {"action": "create", "name": "mi-skill-personal"})))

    def test_envoltorio_tool_call(self):
        self.assertTrue(bloquea(llamada("tool_call", {"calls": [
            {"name": "skill_manage", "arguments": {"action": "patch", "name": "stack-dotnet"}}]})))
        self.assertTrue(bloquea(llamada("tool_call", {"calls": [
            {"name": "write_file", "arguments": '{"path": "%s", "content": "x"}' % SKILL.as_posix()}]})))
        self.assertFalse(bloquea(llamada("tool_call", {"calls": [
            {"name": "mcp__dbhub__search_objects_fundacion_dev", "arguments": {}}]})))

    def test_propuestas_de_mejora_es_el_canal_permitido(self):
        propuestas = HERMES_FLOW / "propuestas-de-mejora.md"
        self.assertFalse(bloquea(llamada("patch", {"path": str(propuestas), "old_string": "a", "new_string": "b"})))
        self.assertFalse(bloquea(llamada("write_file", {"path": str(propuestas), "content": "x"})))
        self.assertTrue(bloquea(llamada("write_file", {"path": str(HERMES_FLOW / "README.md"), "content": "x"})))
        for m in ("correcciones.md", "tareas.md"):
            self.assertFalse(bloquea(llamada("patch", {"path": str(HERMES_FLOW / "metricas" / m),
                                                       "old_string": "a", "new_string": "b"})))

    def test_fuera_de_hermes_flow_pasa(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertFalse(bloquea(llamada("write_file", {"path": f"{d}/a.cs", "content": "x"})))

    def test_revisor_no_escribe_en_un_repo(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / ".git").write_text("gitdir: x")  # un worktree tiene .git como archivo
            dentro = llamada("patch", {"path": f"{d}/src/a.cs", "old_string": "a", "new_string": "b"})
            self.assertTrue(bloquea(dentro, solo_lectura=True))
            self.assertFalse(bloquea(dentro))
        with tempfile.TemporaryDirectory() as d:
            self.assertFalse(bloquea(llamada("write_file", {"path": f"{d}/sonda.txt", "content": "x"}),
                                     solo_lectura=True))

    def test_otras_herramientas_pasan(self):
        self.assertFalse(bloquea(llamada("read_file", {"path": str(SKILL)})))
        self.assertFalse(bloquea({}))


if __name__ == "__main__":
    unittest.main()
