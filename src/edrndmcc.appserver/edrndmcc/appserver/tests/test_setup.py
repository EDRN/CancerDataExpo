# encoding: utf-8
# Copyright 2008 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

'''Tests for the setup of the site policy.
'''

import unittest
from Products.CMFCore.utils import getToolByName
from edrndmcc.appserver.testing import EDRN_DMCC_APP_SERVER_FUNCTIONAL_TESTING


class SetupTest(unittest.TestCase):
    '''Unit tests the setup of the site policy.'''
    layer = EDRN_DMCC_APP_SERVER_FUNCTIONAL_TESTING
    def setUp(self):
        super(SetupTest, self).setUp()
        self.portal = self.layer['portal']
    def testIfEDRNRDFServiceAvailable(self):
        types = getToolByName(self.portal, 'portal_types')
        self.failUnless('edrn.rdf.rdfsource' in types.objectIds(), 'EDRN RDF Service not installed')
    def testHomePage(self):
        homePage = self.portal['front-page']
        wfTool = getToolByName(self.portal, 'portal_workflow')
        state = wfTool.getInfoFor(homePage, 'review_state')
        self.assertEquals('published', state, "Home page isn't published, should be")
        text = homePage.getText()
        self.failUnless("The Cancer Data Expo is a marketplace" in text, 'Home page text not set')


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
