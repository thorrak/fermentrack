import unittest
import BrewPiUtil as util
# import simplejson as json
import json

class BrewPiUtilsTestCase(unittest.TestCase):
    # test that characters from extended ascii are removed (except degree symbol)
    def test_ascii_to_unicode_extended_ascii_is_discarded(self):
        s = 'test\xff'
        s = util.asciiToUnicode(s)
        self.assertEqual(s, u'test')

    # test that degree symbol is replaced by &deg
    def test_ascii_to_unicode_degree_sign(self):
        s = 'temp: 18\xB0C'
        s = util.asciiToUnicode(s)
        self.assertEqual(s, u'temp: 18&degC')

    def testAsciiToUnicodeCanBeJsonSerialized(self):
        s = '{"test": "18\xB0C"}'
        # without next line, error will be:
        # UnicodeDecodeError: 'utf8' codec can't decode byte 0xb0 in position 2: invalid start byte
        s = util.asciiToUnicode(s)
        json.loads(s)
