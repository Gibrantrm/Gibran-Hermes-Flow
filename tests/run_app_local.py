"""Ejecuta únicamente test_app_local sin abrir una base Kanban real."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import test_app_local


def main():
    artifacts = Path(__file__).resolve().parents[1] / ".verification"
    artifacts.mkdir(exist_ok=True)
    os.environ["TEMP"] = os.environ["TMP"] = str(artifacts)
    tempfile.tempdir = str(artifacts)
    # Sin Kanban legible, la protección de producción conserva apps sin dueño.
    # Esta frontera representa un tablero vacío; los casos de concurrencia
    # fijan sus propios estados y ejercitan el resto de la implementación real.
    with patch("app_local.sqlite3.connect") as connect:
        cursor = connect.return_value.execute.return_value
        cursor.fetchall.return_value = []
        cursor.fetchone.return_value = None
        suite = unittest.defaultTestLoader.loadTestsFromModule(test_app_local)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
