import unittest
from unittest import TestCase

from wheatley.row_generation import MethodPlaceNotationGenerator

plain_bob_minimus = """<?xml version="1.0"?>
<methods xmlns="http://methods.ringing.org/NS/method" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:db="http://methods.ringing.org/NS/database" xmlns:ns_1="http://methods.ringing.org/NS/database" version="0.1" ns_1:page="0" ns_1:pagesize="100" ns_1:rows="1">
  <method xmlns:a="http://methods.ringing.org/NS/method" id="m13199">
    <stage>4</stage>
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
    <pn>
      <block>3.1.7.1.5.1.7.1.7.5.1.7.1.7.1.7.1.7.1.5.1.5.1.7.1.7.1.7.1.7</block>
    </pn>
  </method>
</methods>
"""


class MethodPlaceNotationGeneratorTests(TestCase):
    def test_parse_symblock_even(self):
        method_pn, stage = MethodPlaceNotationGenerator._parse_xml(plain_bob_minimus)
        self.assertEqual("&-14-14,&12", method_pn)
        self.assertEqual(4, stage)

    def test_parse_symblock_odd(self):
        method_pn, stage = MethodPlaceNotationGenerator._parse_xml(single_oxford_triples)
        self.assertEqual("&3,&1.5.1.7.1.7.1", method_pn)
        self.assertEqual(7, stage)

    def test_parse_block(self):
        method_pn, stage = MethodPlaceNotationGenerator._parse_xml(scientific_triples)
        self.assertEqual("3.1.7.1.5.1.7.1.7.5.1.7.1.7.1.7.1.7.1.5.1.5.1.7.1.7.1.7.1.7", method_pn)
        self.assertEqual(7, stage)


if __name__ == '__main__':
    unittest.main()
