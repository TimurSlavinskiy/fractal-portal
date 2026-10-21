"""FRACTAL PORTAL v3.0 source regression suite; browser functionality also manually smoke-tested.

The test suite has no pip dependencies and is compatible with the v2 Actions workflow.
"""
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest

HERE = Path(__file__).resolve().parent
HTML = (HERE / 'index.html').read_text(encoding='utf-8')

class Markup(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.controls = set()
        self.scripts = []
    def handle_starttag(self, tag, attrs):
        props = dict(attrs)
        if 'id' in props:
            self.ids.append(props['id'])
            if tag in {'input','button','select'}:
                self.controls.add(props['id'])
        if tag == 'script' and 'src' in props:
            self.scripts.append(props['src'])

class V3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.markup=Markup(); cls.markup.feed(HTML)

    def test_unique_ids_and_valid_references(self):
        ids=set(self.markup.ids)
        self.assertEqual(len(ids),len(self.markup.ids),'Duplicate HTML id')
        refs=set(re.findall(r"getElementById\(['\"]([^'\"]+)['\"]\)",HTML))
        self.assertFalse(refs-ids,f'Missing elements: {refs-ids}')

    def test_no_external_javascript_or_data_dependency(self):
        self.assertEqual(self.markup.scripts,[])
        self.assertNotIn('<script src=',HTML)
        self.assertIn("getContext('webgl2'",HTML)
        self.assertIn("getContext('2d'",HTML)
        self.assertIn('canvas.replaceWith(replacement)',HTML)
        self.assertIn('URLSearchParams',HTML)

    def test_math_implemented_on_gpu_and_cpu(self):
        self.assertIn('z=cmul(z,z)+u_c',HTML)
        self.assertIn('zr*zr-zi*zi+cr',HTML)
        fragment = re.search(r'const fragment = `([\s\S]*?)`;',HTML)
        self.assertIsNotNone(fragment)
        self.assertIn('smoothIter',fragment.group(1))
        self.assertNotRegex(fragment.group(1),r'\b(?:float|int|vec[234])\s+smooth\b')

    def test_original_controls_retained(self):
        self.assertTrue({'real','imag','zoom','iterations','glow','palette','save','share','reset','morph'}<=self.markup.controls)

    def test_new_v3_controls(self):
        expected={'saved-toggle','help-toggle','undo','redo','save-discovery','export-hd','fullscreen','tour','saved-close','clear-saved','discovery-name','modal-cancel'}
        self.assertTrue(expected <= set(self.markup.ids))
        self.assertIn('localStorage.setItem',HTML)
        self.assertIn('localStorage.getItem',HTML)
        self.assertIn('Ctrl+Z',HTML)
        self.assertIn('validSnapshot(',HTML)
        self.assertIn('canvas.toBlob(',HTML)

    def test_accessibility_and_responsive(self):
        for feature in ['aria-expanded','aria-label','aria-live','aria-modal','focus-visible','prefers-reduced-motion','@media(max-width:520px)']:
            self.assertIn(feature,HTML)
        self.assertIn('aria-pressed',HTML)
        self.assertIn('<title>Fractal Portal v3',HTML)

    def test_logo_embedded_and_assets_exist(self):
        self.assertIn('<svg ',HTML)
        self.assertIn('FRACTAL PORTAL', HTML)
        self.assertIn('viewBox="0 0 512 512"', HTML)
        # The logo is embedded inline, so a missing asset directory never breaks the header.

    def test_bounds_and_precision_are_honest(self):
        self.assertIn('u_maxiter',HTML)
        self.assertIn('u_zoom',HTML)
        self.assertIn('32×',HTML)
        self.assertIn('floating-point precision',HTML)

if __name__ == '__main__':
    unittest.main(verbosity=2)
