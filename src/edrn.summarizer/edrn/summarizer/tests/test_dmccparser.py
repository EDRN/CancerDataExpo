# encoding: utf-8
# Copyright 2012 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

'''EDRN Summarizer Service — DMCC parser tests'''

import unittest
from edrn.summarizer.utils import parseTokens


class TokenizerTest(unittest.TestCase):
    '''Unit test of the tokenizing parser'''
    def testNonString(self):
        '''See if token parsing fails appropriately on non-strings'''
        generator = parseTokens(None)
        with self.assertRaises(TypeError):
            next(generator)
        generator = parseTokens(3)
        with self.assertRaises(TypeError):
            next(generator)
        generator = parseTokens(object())
        with self.assertRaises(TypeError):
            next(generator)
    def testEmptyString(self):
        '''Ensure we get no key-value tokens from an empty string'''
        generator = parseTokens('')
        with self.assertRaises(StopIteration):
            next(generator)
    def testGarbageString(self):
        '''Check that we get no key-value tokens from a garbage string'''
        generator = parseTokens('No angle brackets')
        with self.assertRaises(ValueError):
            next(generator)
    def testSingleElement(self):
        '''Test if we get a single key-value token from a DMCC-formatted string'''
        key, value = next(parseTokens('<Temperature>Spicy</Temperature>'))
        self.assertEquals('Temperature', key)
        self.assertEquals('Spicy', value)
    def testMultipleElements(self):
        '''Verify that we get multiple key-value tokens from a DMCC-formatted string'''
        keys, values = [], []
        for k, v in parseTokens('<Temperature>Spicy</Temperature><Protein>Shrimp</Protein><Sauce>Poblano</Sauce>'):
            keys.append(k)
            values.append(v)
        self.assertEquals(['Temperature', 'Protein', 'Sauce'], keys)
        self.assertEquals(['Spicy', 'Shrimp', 'Poblano'], values)
    def testExtraSpace(self):
        '''See to it that extra white space is stripped between tokens'''
        key, value = next(parseTokens('    <Temperature>Spicy</Temperature>'))
        self.assertEquals(('Temperature', 'Spicy'), (key, value))
        key, value = next(parseTokens('<Temperature>Spicy</Temperature>   '))
        self.assertEquals(('Temperature', 'Spicy'), (key, value))
        key, value = next(parseTokens('   <Temperature>Spicy</Temperature>   '))
        self.assertEquals(('Temperature', 'Spicy'), (key, value))
        keys, values = [], []
        for k, v in parseTokens('  <Temperature>Spicy</Temperature>  <Protein>Shrimp</Protein>  <Sauce>Poblano</Sauce>'):
            keys.append(k)
            values.append(v)
        self.assertEquals(['Temperature', 'Protein', 'Sauce'], keys)
        self.assertEquals(['Spicy', 'Shrimp', 'Poblano'], values)
    def testEmptyValues(self):
        '''Check if we can parse tokens with no values in them'''
        key, value = next(parseTokens('<EmptyKey></EmptyKey>'))
        self.assertEquals(('EmptyKey', ''), (key, value))
    def testUnterminatedElements(self):
        '''Confirm we can handle badly formatted DMCC strings'''
        generator = parseTokens('<Unterminated>Value')
        with self.assertRaises(ValueError):
            next(generator)
    def testMultilineValues(self):
        '''Assure we handle values with embedded newlines properly'''
        k, v = next(parseTokens('<msg>Hello,\nworld.</msg>'))
        self.assertEquals('msg', k)
        self.assertEquals('Hello,\nworld.', v)


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
        
