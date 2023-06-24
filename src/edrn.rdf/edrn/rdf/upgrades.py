# encoding: utf-8
# Copyright 2013–2017 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

from .setuphandlers import publish
from edrn.rdf import DEFAULT_PROFILE, PACKAGE_NAME
from edrn.rdf.labcascollectionrdfgenerator import ILabCASCollectionRDFGenerator
from plone.dexterity.utils import createContentInContainer
from z3c.relationfield import RelationValue
from zope.app.intid.interfaces import IIntIds
from zope.component import getUtility
import plone.api, logging


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


def upgrade6to7(setup_tool):
    setup_tool.runImportStepFromProfile(DEFAULT_PROFILE, 'typeinfo')
    portal = plone.api.portal.get()
    if 'rdf-generators' in list(portal.keys()):
        rdf_generators = portal['rdf-generators']
        generators = list(rdf_generators.keys())
        if 'member-group-generator' not in generators:
            generator = createContentInContainer(
                rdf_generators,
                'edrn.rdf.membergrouprdfgenerator',
                title='Member Group Generator',
                description='Generates descriptions of groups of members',
                web_service_url='https://www.compass.fhcrc.org/edrn_ws/ws_newcompass.asmx?WSDL'
            )
            publish(generator, plone.api.portal.get_tool('portal_workflow'))
            if 'rdf-data' in list(portal.keys()):
                rdf_sources = portal['rdf-data']
                sources = list(rdf_sources.keys())
                if 'member-groups' not in sources:
                    source = createContentInContainer(
                        rdf_sources,
                        'edrn.rdf.rdfsource',
                        title='Member Groups',
                        description='RDF data for groups of EDRN member sites',
                        generator=RelationValue(getUtility(IIntIds).getId(generator)),
                        active=True
                    )
                publish(source, plone.api.portal.get_tool('portal_workflow'))


def upgrade7to8(setup_tool):
    setup_tool.runImportStepFromProfile(DEFAULT_PROFILE, 'typeinfo')
    portal = plone.api.portal.get()
    try:
        generator = portal.unrestrictedTraverse('rdf-generators/person-generator')
        try:
            generator.manage_delObject('email')
        except AttributeError:
            # no email handler found, so no worries
            pass
        handler = createContentInContainer(
            generator,
            'edrn.rdf.emailpredicatehandler',
            title='Email',
            description='Email predicate handler',
            predicateURI='http://xmlns.com/foaf/0.1/mbox'
        )
        publish(handler, plone.api.portal.get_tool('portal_workflow'))
    except KeyError:
        # no person handler found, so nothing to do
        pass


def upgrade8to9(setup_tool, logger=None):
    if logger is None:
        logger = logging.getLogger(PACKAGE_NAME)
    setup_tool.runImportStepFromProfile(DEFAULT_PROFILE, 'plone.app.registry')
    logging.info('Loaded registry')
