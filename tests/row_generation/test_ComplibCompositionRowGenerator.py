import unittest
from unittest import TestCase


from wheatley.row_generation import ComplibCompositionGenerator


class CompLibGeneratorTests(TestCase):
    def test_comp_fetching(self):
        for (url, expected_title) in [
            ("complib.org/composition/62355", "5040 Plain Bob Major by Ben White-Horne"),
            ("www.complib.org/composition/62355", "5040 Plain Bob Major by Ben White-Horne"),
            ("https://www.complib.org/composition/71994", "110 2-Spliced Major"),
            ("https://complib.org/composition/71994", "110 2-Spliced Major"),
            (
                "https://complib.org/composition/70383?accessKey=cf75d5e0d213d4d3ea38f58f5bfdfd8e86b99ccf",
                "56 3-Spliced Bob Royal",
            ),
            (
                "https://complib.org/composition/51155?substitutedmethodid=27600"
                + "&accessKey=9e1fcd2b11435552cf236be93c7ff73058870995",
                "720 Moss Treble Place Minor",
            ),
        ]:
            with self.subTest(url=url, expected_title=expected_title):
                self.assertEqual(ComplibCompositionGenerator.from_arg(url).comp_title, expected_title)


if __name__ == "__main__":
    unittest.main()
