# encoding: utf-8
# Copyright 2008-2011 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

'''EDRN RDF Service — functional doctests.'''

import doctest
import unittest
from plone.testing import layered
from edrn.rdf.testing import EDRN_RDF_FUNCTIONAL_TESTING as LAYER

optionFlags = (doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE | doctest.REPORT_ONLY_FIRST_FAILURE)


def test_suite():
    return unittest.TestSuite([
        layered(doctest.DocFileSuite('README.rst', package='edrn.rdf', optionflags=optionFlags), LAYER),
    ])


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
