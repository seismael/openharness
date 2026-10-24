#!/usr/bin/env python3
"""Unit tests for ast_slice.py."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ast_slice import slice_symbol


class TestAstSlice(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_extract_python_function(self):
        py_file = self.dir / "example.py"
        py_file.write_text(
            "import os\n\n"
            "def target_func(a: int) -> int:\n"
            '    """Docstring."""\n'
            "    return a * 2\n\n"
            "def other_func():\n"
            "    pass\n",
            encoding="utf-8",
        )

        res = slice_symbol(py_file, "target_func")
        self.assertNotIn("error", res)
        self.assertEqual(res["symbol"], "target_func")
        self.assertEqual(res["kind"], "function")
        self.assertEqual(res["start_line"], 3)
        self.assertEqual(res["end_line"], 5)
        self.assertIn("return a * 2", res["code"])

    def test_extract_python_class(self):
        py_file = self.dir / "example_class.py"
        py_file.write_text(
            "class MyService:\n    def __init__(self):\n        self.val = 1\n",
            encoding="utf-8",
        )

        res = slice_symbol(py_file, "MyService")
        self.assertNotIn("error", res)
        self.assertEqual(res["symbol"], "MyService")
        self.assertEqual(res["kind"], "class")
        self.assertIn("self.val = 1", res["code"])

    def test_list_python_symbols(self):
        py_file = self.dir / "symbols.py"
        py_file.write_text(
            "class A: pass\n\ndef b(): pass\n",
            encoding="utf-8",
        )

        res = slice_symbol(py_file, list_symbols=True)
        self.assertNotIn("error", res)
        symbols = [s["symbol"] for s in res["symbols"]]
        self.assertIn("A", symbols)
        self.assertIn("b", symbols)

    def test_polyglot_fallback(self):
        js_file = self.dir / "service.js"
        js_file.write_text(
            "const x = 1;\n\n"
            "function computeTotal(items) {\n"
            "  return items.reduce((a, b) => a + b, 0);\n"
            "}\n",
            encoding="utf-8",
        )

        res = slice_symbol(js_file, "computeTotal")
        self.assertNotIn("error", res)
        self.assertEqual(res["symbol"], "computeTotal")
        self.assertIn("reduce", res["code"])


if __name__ == "__main__":
    unittest.main()
