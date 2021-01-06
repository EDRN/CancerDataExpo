# encoding: utf-8
# Copyright 2012 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

from plone.dexterity.utils import createContentInContainer
from Products.CMFCore.interfaces import IFolderish
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.WorkflowCore import WorkflowException
from z3c.relationfield import RelationValue
from ZODB.DemoStorage import DemoStorage
from zope.app.intid.interfaces import IIntIds
from zope.component import getUtility

_dmccURL = 'https://www.compass.fhcrc.org/edrn_ws/ws_newcompass.asmx?WSDL'
_biomutaURL = 'https://hive.biochemistry.gwu.edu/prd/biomuta/content/BioMuta_stat.csv'
_biomarkerURL = 'https://bmdb.jpl.nasa.gov/rdf/biomarkers?all=yeah'
_organURL = 'https://bmdb.jpl.nasa.gov/rdf/biomarker-organs?all=yeah'
_dmccpublicationURL = 'https://edrn.jpl.nasa.gov/cancerdataexpo/rdf-data/publications/@@rdf'
_bmdbpublicationURL = 'https://bmdb.jpl.nasa.gov/rdf/publications?all=yeah'
_fmproddatasetURL  = 'http://edrn.jpl.nasa.gov/fmprodp3/rdf/dataset?type=ALL&baseUrl=http://edrn.jpl.nasa.gov/ecas/data/dataset'
_ernequeryURL  = 'http://ginger.fhcrc.org/edrn/erneQuery'
_dmccprotocolURL = 'https://edrn.jpl.nasa.gov/cancerdataexpo/rdf-data/protocols/@@rdf'
_dmcccommitteeURL = 'https://edrn.jpl.nasa.gov/cancerdataexpo/rdf-data/committees/@@rdf'

def addDCTitle(context, key):
    createContentInContainer(
        context,
        'edrn.summarizer.literalpredicatehandler',
        id='dc-title',
        title=key,
        description='''Maps from DMCC's "Title" key to the Dublin Core title term.''',
        predicateURI='http://purl.org/dc/terms/title'
    )

def addDCDescription(context, key):
    createContentInContainer(
        context,
        'edrn.summarizer.literalpredicatehandler',
        title=key,
        description='''Maps from DMCC's "Description" key to the Dublin Core description term.''',
        predicateURI='http://purl.org/dc/terms/description'
    )

def createBiomutaGenerator(context):
    return createContentInContainer(
        context,
        'edrn.summarizer.biomutasummarizergenerator',
        title='Biomuta Generator',
        description='Generates graphs describing the EDRN\'s biomaker mutation statistics.',
        webServiceURL=_biomutaURL,
        typeURI='http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#Biomarker',
        uriPrefix='http://edrn.nci.nih.gov/data/biomuta/',
        geneNamePredicateURI='http://edrn.nci.nih.gov/xml/rdf/edrn.summarizer#geneName',
        uniProtACPredicateURI='http://edrn.nci.nih.gov/xml/rdf/edrn.summarizer#uniprotAccession',
        mutCountPredicateURI='http://edrn.nci.nih.gov/xml/rdf/edrn.summarizer#mutationCount',
        pmidCountPredicateURI='http://edrn.nci.nih.gov/xml/rdf/edrn.summarizer#pubmedIDCount',
        cancerDOCountPredicateURI='http://edrn.nci.nih.gov/xml/rdf/edrn.summarizer#cancerDOCount',
        affProtFuncSiteCountPredicateURI='http://edrn.nci.nih.gov/xml/rdf/edrn.summarizer#affectedProtFuncSiteCount',
        datatype = 'rdf'
    )

def createPublicationGenerator(context):
    return createContentInContainer(
        context,
        'edrn.summarizer.publicationsummarizergenerator',
        title='Publication Generator',
        description='Generates json describing the EDRN\'s publication statistics.',
        rdfDataSource=_dmccpublicationURL,
        additionalDataSources=_bmdbpublicationURL,
        datatype = 'json'
    )

def createDatasetGenerator(context):
    return createContentInContainer(
        context,
        'edrn.summarizer.datasetsummarizergenerator',
        title='Dataset Generator',
        description='Generates json describing the EDRN\'s dataset statistics.',
        rdfDataSource=_fmproddatasetURL,
        datatype = 'json'
    )


def createSpecimenGenerator(context):
    # ERNE doesn't exist anymore, so don't do anything
    # return createContentInContainer(
    #     context,
    #     'edrn.summarizer.specimensummarizergenerator',
    #     title='Specimen Generator',
    #     description='Generates json describing the EDRN\'s specimen statistics.',
    #     queryDataSource=_ernequeryURL,
    #     datatype = 'json'
    # )
    return


def createBiomarkerGenerator(context):
    return createContentInContainer(
        context,
        'edrn.summarizer.biomarkersummarizergenerator',
        title='Biomarker Generator',
        description='Generates json describing the EDRN\'s biomaker statistics.',
        biomarkerURL=_biomarkerURL,
        organURL    =_organURL,
        datatype = 'json'
    )

def createExtResourceGenerator(context):
    return createContentInContainer(
        context,
        'edrn.summarizer.extresourcesummarizergenerator',
        title='External Resource Generator',
        description='Generates json describing the EDRN\'s External Resource information.',
        biomarkerURL=_biomarkerURL,
        datatype = 'json'
    )

def createCollaborationGenerator(context):
    return createContentInContainer(
        context,
        'edrn.summarizer.collaborationsummarizergenerator',
        title='Collaboration Generator',
        description='Generates json describing the EDRN\'s collaboration statistics.',
        biomarkerURL=_biomarkerURL,
        dataURL =_fmproddatasetURL,
        protocolURL =_dmccprotocolURL,
        memberURL =_dmcccommitteeURL,
        datatype = 'json'
    )


def createSummarizerGenerators(context):
    generators = {}

    folder = createContentInContainer(
        context,
        'Folder',
        id='summarizer-generators',
        title='Summarizer Generators',
        description='Copy/paste much?'
    )

    generators['biomuta']           = createBiomutaGenerator(folder)
    generators['biomarker']         = createBiomarkerGenerator(folder)
    generators['publication']       = createPublicationGenerator(folder)
    generators['dataset']           = createDatasetGenerator(folder)
    # ERNE doesn't exist anymore, so don't bother with this
    # generators['specimen']          = createSpecimenGenerator(folder)
    generators['collaboration']     = createCollaborationGenerator(folder)
    generators['extresources']      = createExtResourceGenerator(folder)

    return generators


def createSummarizerSources(context, generators):
    folder = createContentInContainer(
        context,
        'Folder',
        id='summarizer-data',
        title='Summarizer Sources',
        description='Sources of Summarizer information for EDRN.'
    )

    for objID, title, desc in (
        ('biomuta', 'Biomuta', 'Source of Summarizer for biomarker mutation statistics in EDRN.'),
        ('publication', 'Publication', 'Source of Summarizer for publication statistics in EDRN.'),
        ('dataset', 'Dataset', 'Source of Summarizer for dataset statistics in EDRN.'),
        # ERNE doesn't exist anymore, so don't bother with this
        # ('specimen', 'Specimen', 'Source of Summarizer for specimen statistics in EDRN.'),
        ('collaboration', 'Collaboration', 'Source of Summarizer for collaboration statistics in EDRN.'),
        ('biomarker', 'Biomarker', 'Source of Summarizer for biomarker statistics in EDRN.'),
        ('extresources', 'External Resources', 'Source of Summarizer for External Resource references in EDRN.')
    ):
        generator = RelationValue(generators[objID])
        createContentInContainer(folder, 'edrn.summarizer.summarizersource', title=title, description=desc, generator=generator, active=True)


def publish(item, wfTool):
    try:
        wfTool.doActionFor(item, action='publish')
        item.reindexObject()
    except WorkflowException:
        pass
    if IFolderish.providedBy(item):
        for itemID, subItem in item.contentItems():
            publish(subItem, wfTool)


def installInitialSources(portal):
    # Don't bother if we're running under test fixture
    if hasattr(portal._p_jar, 'db') and isinstance(portal._p_jar.db().storage, DemoStorage): return
    if 'summarizer-generators' in list(portal.keys()):
        portal.manage_delObjects('summarizer-generators')
    if 'summarizer-data' in list(portal.keys()):
        portal.manage_delObjects('summarizer-data')
    generators = createSummarizerGenerators(portal)
    wfTool = getToolByName(portal, 'portal_workflow')
    publish(portal['summarizer-generators'], wfTool)
    intIDs = getUtility(IIntIds)
    for key, generator in list(generators.items()):
        intID = intIDs.getId(generator)
        generators[key] = intID
    createSummarizerSources(portal, generators)
    publish(portal['summarizer-data'], wfTool)

def setupVarious(context):
    if context.readDataFile('edrn.summarizer.marker.txt') is None: return
    portal = context.getSite()
    installInitialSources(portal)
