# encoding: utf-8
# Copyright 2013–2017 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

from .setuphandlers import publish
from edrn.rdf import DEFAULT_PROFILE
from plone.dexterity.utils import createContentInContainer
from edrn.rdf.labcascollectionrdfgenerator import ILabCASCollectionRDFGenerator
import plone.api


def nullUpgradeStep(setupTool):
    '''A null step when a profile upgrade requires no custom activity.'''


def upgrade3to4(setupTool):
    setupTool.runImportStepFromProfile(DEFAULT_PROFILE, 'typeinfo')


def upgrade4to5(setupTool):
    # Note that I (kelly) went ahead and added these through the web to the
    # running https://edrn.jpl.nasa.gov/cancerdataexpo/ so we could take
    # immediate advantage of the new data without cutting a new release.
    # This is provided just in case there is a disaster and we need to
    # re-release.
    portal = setupTool.getSite()
    if 'rdf-generators' in list(portal.keys()):
        rdfGenerators = portal['rdf-generators']
        if 'person-generator' in list(rdfGenerators.keys()):
            personGenerator = rdfGenerators['person-generator']
            if 'staff_status' not in list(personGenerator.keys()):
                predicate = createContentInContainer(
                    personGenerator,
                    'edrn.rdf.literalpredicatehandler',
                    title='Staff_Status',
                    description='''Maps from DMCC's Staff_Status to the EDRN-specific predicate for employmentActive.''',
                    predicateURI='http://edrn.nci.nih.gov/rdf/schema.rdf#employmentActive'
                )
                publish(predicate, plone.api.portal.get_tool('portal_workflow'))
        if 'publications-generator' in list(rdfGenerators.keys()):
            publicationsGenerator = rdfGenerators['publications-generator']
            if 'siteid' not in list(publicationsGenerator.keys()):
                predicate = createContentInContainer(
                    publicationsGenerator,
                    'edrn.rdf.referencepredicatehandler',
                    title='SiteID',
                    description='''Maps from the DMCC's SiteID to the EDRN-specific predicate for site ID.''',
                    predicateURI='http://edrn.nci.nih.gov/rdf/schema.rdf#site',
                    uriPrefix='http://edrn.nci.nih.gov/data/sites/'
                )
                publish(predicate, plone.api.portal.get_tool('portal_workflow'))


def upgrade5to6(setupTool):
    catalog = plone.api.portal.get_tool('portal_catalog')
    for brain in catalog(object_provides=ILabCASCollectionRDFGenerator.__identifier__):
        obj = brain.getObject()
        obj.labcasSolrURL = 'https://edrn-labcas.jpl.nasa.gov/data-access-api'
