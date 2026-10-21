"""Fast, standard-library tests for Fractal Portal (no pytest required)."""
from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess
import sys
import unittest

from PIL import Image, ImageChops


SCRIPT = Path(__file__).resolve().with_name("fractal_portal.py")


def invoke(destination: Path, *arguments: str) -> Image.Image:
    subprocess.run(
        [sys.executable, str(SCRIPT), "--width", "320", "--height", "200",
         "--iterations", "120", "--output", str(destination), *arguments],
        check=True, capture_output=True, text=True,
    )
    with Image.open(destination) as image:
        assert image.format == "PNG"
        image.load()
        return image.copy()


class FractalPortalTests(unittest.TestCase):
    def test_png_is_not_blank(self):
        with TemporaryDirectory() as td:
            pic = invoke(Path(td) / "aurora.png", "--preset", "aurora")
            self.assertEqual(pic.size, (320, 200))
            self.assertEqual(pic.mode, "RGB")
            limits = pic.getextrema()
            self.assertGreater(max(hi - lo for lo, hi in limits), 80)

    def test_deterministic(self):
        with TemporaryDirectory() as td:
            a = invoke(Path(td) / "one.png", "--preset", "ember")
            b = invoke(Path(td) / "two.png", "--preset", "ember")
            self.assertIsNone(ImageChops.difference(a, b).getbbox())

    def test_custom_equation_changes_art(self):
        with TemporaryDirectory() as td:
            a = invoke(Path(td) / "default.png", "--preset", "aurora")
            b = invoke(Path(td) / "custom.png", "--preset", "aurora",
                       "--real", "-0.70176", "--imag", "-0.3842")
            self.assertIsNotNone(ImageChops.difference(a, b).getbbox())


if __name__ == "__main__":
    unittest.main()
