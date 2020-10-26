import unittest
from unittest import TestCase


from wheatley.row_generation import ComplibCompositionGenerator


class CompLibGeneratorTests(TestCase):
    def test_comp_fetching(self):
        for (url, expected_title) in [
            ("complib.org/composition/62355", "5040 Plain Bob Major Op. Cyclic #1 by Ben White-Horne"),
            ("www.complib.org/composition/62355", "5040 Plain Bob Major Op. Cyclic #1 by Ben White-Horne"),
            ("https://www.complib.org/composition/71994", "110 2-Spliced Major"),
            ("https://complib.org/composition/71994", "110 2-Spliced Major"),
            (
                "https://complib.org/composition/70383?accessKey=cf75d5e0d213d4d3ea38f58f5bfdfd8e86b99ccf",
                "56 3-Spliced Bob Royal"
            )
        ]:
            with self.subTest(url=url, expected_title=expected_title):
                self.assertEqual(ComplibCompositionGenerator.from_url(url).comp_title, expected_title)


if __name__ == '__main__':
    unittest.main()
