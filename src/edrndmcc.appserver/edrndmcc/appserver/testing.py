# encoding: utf-8
# Copyright 2011–2012 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

from edrn.rdf.testing import EDRN_RDF
from plone.app.testing import PloneSandboxLayer, IntegrationTesting, FunctionalTesting, PLONE_FIXTURE
from Products.CMFCore.utils import getToolByName


class EDRN_DMCC_AppServerLayer(PloneSandboxLayer):
    defaultBases = (EDRN_RDF, PLONE_FIXTURE,)
    def setUpZope(self, app, configurationContext):
        import edrndmcc.appserver, edrn.rdf, edrn.summarizer
        import yafowil.plone, plone.caching, plone.app.caching
        self.loadZCML(package=edrn.summarizer)
        self.loadZCML(package=edrn.rdf)
        self.loadZCML(package=plone.caching)
        self.loadZCML(package=plone.app.caching)
        self.loadZCML(package=edrndmcc.appserver)
    def setUpPloneSite(self, portal):
        wfTool = getToolByName(portal, 'portal_workflow')
        wfTool.setDefaultChain('plone_workflow')
        self.applyProfile(portal, 'edrndmcc.appserver:default')


EDRN_DMCC_APP_SERVER = EDRN_DMCC_AppServerLayer()
EDRN_DMCC_APP_SERVER_INTEGRATION_TESTING = IntegrationTesting(
    bases=(EDRN_DMCC_APP_SERVER,),
    name='EDRN_DMCC_APP_SERVER:Integration'
)
EDRN_DMCC_APP_SERVER_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(EDRN_DMCC_APP_SERVER,),
    name='EDRN_DMCC_APP_SERVER:Functional'
)
