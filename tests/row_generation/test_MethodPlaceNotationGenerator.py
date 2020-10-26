import unittest
from unittest import TestCase

from wheatley.row_generation import MethodPlaceNotationGenerator, generator_from_special_title, PlaceNotationGenerator, \
    PlainHuntGenerator
from wheatley.row_generation.method_place_notation_generator import MethodNotFoundError

plain_bob_minimus = """<?xml version="1.0"?>
<methods xmlns="http://methods.ringing.org/NS/method" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:db="http://methods.ringing.org/NS/database" xmlns:ns_1="http://methods.ringing.org/NS/database" version="0.1" ns_1:page="0" ns_1:pagesize="100" ns_1:rows="1">
  <method xmlns:a="http://methods.ringing.org/NS/method" id="m13199">
    <stage>4</stage>
    <title>Plain Bob Minimus</title>
    <pn>
      <symblock>-14-14</symblock>
      <symblock>12</symblock>
    </pn>
  </method>
</methods>
"""

single_oxford_triples = """<?xml version="1.0"?>
<methods xmlns="http://methods.ringing.org/NS/method" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:db="http://methods.ringing.org/NS/database" xmlns:ns_1="http://methods.ringing.org/NS/database" version="0.1" ns_1:page="0" ns_1:pagesize="100" ns_1:rows="1">
  <method xmlns:a="http://methods.ringing.org/NS/method" id="m14153">
    <stage>7</stage>
    <title>Single Oxford Bob Triples</title>
    <pn>
      <symblock>3</symblock>
      <symblock>1.5.1.7.1.7.1</symblock>
    </pn>
  </method>
</methods>
"""

scientific_triples = """<?xml version="1.0"?>
<methods xmlns="http://methods.ringing.org/NS/method" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:db="http://methods.ringing.org/NS/database" xmlns:ns_1="http://methods.ringing.org/NS/database" version="0.1" ns_1:page="0" ns_1:pagesize="100" ns_1:rows="1">
  <method xmlns:a="http://methods.ringing.org/NS/method" id="m26235">
    <stage>7</stage>
    <title>Scientific Triples</title>
    <pn>
      <block>3.1.7.1.5.1.7.1.7.5.1.7.1.7.1.7.1.7.1.5.1.5.1.7.1.7.1.7.1.7</block>
    </pn>
  </method>
</methods>
"""


class MethodPlaceNotationGeneratorTests(TestCase):
    def test_parse_symblock_even(self):
        method_pn, stage, title = MethodPlaceNotationGenerator._parse_xml(plain_bob_minimus)
        self.assertEqual("&-14-14,&12", method_pn)
        self.assertEqual(4, stage)
        self.assertEqual("Plain Bob Minimus", title)

    def test_parse_symblock_odd(self):
        method_pn, stage, title = MethodPlaceNotationGenerator._parse_xml(single_oxford_triples)
        self.assertEqual("&3,&1.5.1.7.1.7.1", method_pn)
        self.assertEqual(7, stage)
        self.assertEqual("Single Oxford Bob Triples", title)

    def test_parse_block(self):
        method_pn, stage, title = MethodPlaceNotationGenerator._parse_xml(scientific_triples)
        self.assertEqual("3.1.7.1.5.1.7.1.7.5.1.7.1.7.1.7.1.7.1.5.1.5.1.7.1.7.1.7.1.7", method_pn)
        self.assertEqual(7, stage)
        self.assertEqual("Scientific Triples", title)


class SpecialMethodNameTests(TestCase):
    def test_grandsire__all_stages_above_4(self):
        test_cases = [
            ("Grandsire Doubles", 5),
            ("GrandSire DouBles", 5),
            ("grandsire doubles", 5),
            ("GRANDSIRE DOUBLES", 5),
            ("  Grandsire   Doubles  ", 5),
            ("Grandsire 5", 5),
            ("Grandsire Triples", 7),
            ("Grandsire Caters", 9),
            ("Grandsire Cinques", 11),
            ("Grandsire Minor", 6),
            ("Grandsire Major", 8),
            ("Grandsire Royal", 10),
            ("Grandsire Maximus", 12),
        ]

        for (method_title, expected_stage) in test_cases:
            with self.subTest(method_title=method_title, expected_stage=expected_stage):
                generator = generator_from_special_title(method_title)
                self.assertIsInstance(generator, PlaceNotationGenerator)
                self.assertTrue(expected_stage, generator.stage)

    def test_grandsire__in_title__is_none(self):
        test_cases = [
            ("Reverse Grandsire Doubles"),
            ("Double Grandsire Triples"),
            ("Grandsire Five Little Bob Triples")
        ]

        for (method_title) in test_cases:
            with self.subTest(method_title=method_title):
                generator = generator_from_special_title(method_title)
                self.assertIsNone(generator)

    def test_stedman__odd_stages(self):
        test_cases = [
            ("Stedman Doubles", 5),
            ("Stedman Triples", 7),
            ("Stedman Caters", 9),
            ("Stedman Cinques", 11),
        ]

        for (method_title, expected_stage) in test_cases:
            with self.subTest(method_title=method_title, expected_stage=expected_stage):
                generator = generator_from_special_title(method_title)
                self.assertIsInstance(generator, PlaceNotationGenerator)
                self.assertTrue(expected_stage, generator.stage)

    def test_stedman__other_stages__is_none(self):
        test_cases = [
            ("Stedman Singles"),
            ("Stedman Minimus"),
            ("Stedman Minor"),
            ("Stedman Major"),
            ("Stedman Royal"),
            ("Stedman Maximus"),
        ]

        for (method_title) in test_cases:
            with self.subTest(method_title=method_title):
                generator = generator_from_special_title(method_title)
                self.assertIsNone(generator)

    def test_plain_hunt__all_stages(self):
        test_cases = [
            ("Plain Hunt Singles", 3),
            ("Plain Hunt 3", 3),
            ("Plain Hunt on 3", 3),
            ("Plain Hunt Doubles", 5),
            ("Plain Hunt Triples", 7),
            ("Plain Hunt Caters", 9),
            ("Plain Hunt Cinques", 11),
            ("Plain Hunt Minimus", 4),
            ("Plain Hunt Minor", 6),
            ("Plain Hunt Major", 8),
            ("Plain Hunt Royal", 10),
            ("Plain Hunt Maximus", 12),
        ]

        for (method_title, expected_stage) in test_cases:
            with self.subTest(method_title=method_title, expected_stage=expected_stage):
                generator = generator_from_special_title(method_title)
                self.assertIsInstance(generator, PlainHuntGenerator)
                self.assertTrue(expected_stage, generator.stage)

    def test_unknown_stages__throws_MethodNotFoundError(self):
        test_cases = [
            ("Stedman"),
            ("Stedman Not a stage"),
            ("Stedman 0"),
        ]

        for (method_title) in test_cases:
            with self.subTest(method_title=method_title):
                with self.assertRaises(MethodNotFoundError):
                    generator = generator_from_special_title(method_title)


if __name__ == '__main__':
    unittest.main()
