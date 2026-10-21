"""Dependency-free structural checks for the Fractal Portal v2 web explorer.

These are source-integrity tests, NOT substitutes for actual browser tests.
"""
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest

SOURCE = Path(__file__).with_name('index.html')


class Markup(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.external_scripts = []
        self.controls = set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            self.ids.append(a['id'])
        if tag == 'script' and 'src' in a:
            self.external_scripts.append(a['src'])
        if tag in {'button', 'select', 'input'} and 'id' in a:
            self.controls.add(a['id'])


class WebExplorerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = SOURCE.read_text(encoding='utf-8')
        cls.parser = Markup()
        cls.parser.feed(cls.html)

    def test_all_referenced_dom_ids_exist(self):
        ids = set(self.parser.ids)
        self.assertEqual(len(ids), len(self.parser.ids), 'Duplicate element ID')
        js_references = set(re.findall(r"getElementById\(['\"]([^'\"]+)['\"]\)", self.html))
        self.assertFalse(js_references - ids, f'Missing DOM elements: {js_references - ids}')

    def test_no_external_code_or_uploaded_artwork(self):
        self.assertEqual(self.parser.external_scripts, [])
        self.assertNotIn('<img ', self.html.lower())
        self.assertNotIn('http://', self.html)
        self.assertIn('getContext(\'webgl2\'', self.html)
        self.assertIn('getContext(\'2d\'', self.html)

    def test_important_controls_are_present(self):
        self.assertTrue({'real','imag','zoom','iterations','glow','palette',
                         'save','share','reset','morph'} <= self.parser.controls)

    def test_math_and_export_are_implemented(self):
        self.assertIn('z=cmul(z,z)+u_c', self.html)
        self.assertIn('zr*zr-zi*zi+cr', self.html)
        self.assertIn('canvas.toBlob(', self.html)
        self.assertIn('URLSearchParams', self.html)
        self.assertIn('navigator.clipboard.writeText', self.html)
        self.assertIn('pointermove', self.html)
        self.assertIn('prefers-reduced-motion', self.html)

    def test_mobile_layout_exists(self):
        self.assertIn('@media(max-width:800px)', self.html)
        self.assertIn('@media(max-width:520px)', self.html)


if __name__ == '__main__':
    unittest.main(verbosity=2)
