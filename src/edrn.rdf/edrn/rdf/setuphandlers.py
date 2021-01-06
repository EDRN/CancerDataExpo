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
_edrnlabcasURL = 'https://edrn-labcas.jpl.nasa.gov/solr/collections'
_edrnlabcasprefixURL = 'https://edrn-labcas.jpl.nasa.gov/ui/c/'


def addDCTitle(context, key):
    createContentInContainer(
        context,
        'edrn.rdf.literalpredicatehandler',
        id='dc-title',
        title=key,
        description='''Maps from DMCC's "Title" key to the Dublin Core title term.''',
        predicateURI='http://purl.org/dc/terms/title'
    )


def addDCDescription(context, key):
    createContentInContainer(
        context,
        'edrn.rdf.literalpredicatehandler',
        title=key,
        description='''Maps from DMCC's "Description" key to the Dublin Core description term.''',
        predicateURI='http://purl.org/dc/terms/description'
    )


def createBodySystemsGenerator(context):
    generator = createContentInContainer(
        context,
        'edrn.rdf.simpledmccrdfgenerator',
        title='Body Systems Generator',
        description='Generates graphs describing organs and other body systems.',
        webServiceURL=_dmccURL,
        operationName='Body_System',
        uriPrefix='http://edrn.nci.nih.gov/data/body-systems/',
        identifyingKey='Identifier',
        typeURI='http://edrn.nci.nih.gov/rdf/types.rdf#BodySystem'
    )
    addDCTitle(generator, 'item_Title')
    addDCDescription(generator, 'Description')
    return generator

def createDiseaseGenerator(context):
    generator = createContentInContainer(
        context,
        'edrn.rdf.simpledmccrdfgenerator',
        title='Diseases Generator',
        description='Generates graphs describing diseases that affect body systems.',
        webServiceURL=_dmccURL,
        operationName='Disease',
        uriPrefix='http://edrn.nci.nih.gov/data/diseases/',
        identifyingKey='Identifier',
        typeURI='http://edrn.nci.nih.gov/rdf/types.rdf#Disease'
    )
    addDCTitle(generator, 'item_Title')
    addDCDescription(generator, 'description')
    createContentInContainer(
        generator,
        'edrn.rdf.literalpredicatehandler',
        title='icd9',
        description='''Maps from DMCC's "icd9" key to our EDRN-specific predicate for ICD9 code.''',
        predicateURI='http://edrn.nci.nih.gov/xml/rdf/edrn.rdf#icd9'
    )
    createContentInContainer(
        generator,
        'edrn.rdf.literalpredicatehandler',
        title='icd10',
        description='''Maps from DMCC's "icd10" key to our EDRN-specific predicate for ICD10 code.''',
        predicateURI='http://edrn.nci.nih.gov/xml/rdf/edrn.rdf#icd10'
    )
    createContentInContainer(
        generator,
        'edrn.rdf.referencepredicatehandler',
        title='body_system',
        description='''Maps DMCC's "body_system" to a reference to a body system.''',
        predicateURI='http://edrn.nci.nih.gov/xml/rdf/edrn.rdf#bodySystemsAffected',
        uriPrefix='http://edrn.nci.nih.gov/data/body-systems/'
    )
    return generator

def createPublicationGenerator(context):
    generator = createContentInContainer(
        context,
        'edrn.rdf.simpledmccrdfgenerator',
        title='Publications Generator',
        description='Generates graphs describing articles published by EDRN.',
        webServiceURL=_dmccURL,
        operationName='Publication',
        uriPrefix='http://edrn.nci.nih.gov/data/pubs/',
        identifyingKey='Identifier',
        typeURI='http://edrn.nci.nih.gov/rdf/types.rdf#Publication'
    )
    addDCTitle(generator, 'item_Title')
    addDCDescription(generator, 'Description')
    createContentInContainer(
        generator,
        'edrn.rdf.multiliteralpredicatehandler',
        title='Author',
        description='''Maps from DMCC's "Author" key to zero-or-more Dublin Core "creator" terms.''',
        predicateURI='http://purl.org/dc/terms/author'
    )
    createContentInContainer(
        generator,
        'edrn.rdf.literalpredicatehandler',
        title='Issue',
        description='''Maps from DMCC's "Issue" key to our EDRN-specific predicate for an issue of a periodical.''',
        predicateURI='http://edrn.nci.nih.gov/rdf/schema.rdf#issue'
    )
    createContentInContainer(
        generator,
        'edrn.rdf.literalpredicatehandler',
        title='Journal',
        description='''Maps from DMCC's "Journal" key to our EDRN-specific predicate for the title of a periodical.''',
        predicateURI='http://edrn.nci.nih.gov/rdf/schema.rdf#journal'
    )
    createContentInContainer(
        generator,
        'edrn.rdf.literalpredicatehandler',
        title='PMID',
        description='''Maps from DMCC's "PMID" key to our EDRN-specific predicate for the PubMed identification of an article.''',
        predicateURI='http://edrn.nci.nih.gov/rdf/schema.rdf#pmid'
    )
    createContentInContainer(
        generator,
        'edrn.rdf.referencepredicatehandler',
        title='Publication_URL',
        description='''Maps from DMCC's "Publication_URL" key to a URL to the article.''',
        predicateURI='http://edrn.nci.nih.gov/rdf/schema.rdf#pubURL',
        uriPrefix='',
    )
    createContentInContainer(
        generator,
        'edrn.rdf.literalpredicatehandler',
        title='Volume',
        description='''Maps from DMCC's "Volume" key to our EDRN-specific predicate for the volume number of a periodical.''',
        predicateURI='http://edrn.nci.nih.gov/rdf/schema.rdf#volume'
    )
    createContentInContainer(
        generator,
        'edrn.rdf.literalpredicatehandler',
        title='Year',
        description='''Maps from DMCC's "Year" key to our EDRN-specific predicate for the publication year of a periodical.''',
        predicateURI='http://edrn.nci.nih.gov/rdf/schema.rdf#year'
    )
    createContentInContainer(
        generator,
        'edrn.rdf.referencepredicatehandler',
        title='SiteID',
        description='''Maps from the DMCC's SiteID to the EDRN-specific predicate for site ID.''',
        predicateURI='http://edrn.nci.nih.gov/rdf/schema.rdf#site',
        uriPrefix='http://edrn.nci.nih.gov/data/sites/'
    )
    return generator


def createSiteGenerator(context):
    generator = createContentInContainer(
        context,
        'edrn.rdf.simpledmccrdfgenerator',
        title='Sites Generator',
        description='Generates graphs describing the member sites of EDRN.',
        webServiceURL=_dmccURL,
        operationName='Site',
        uriPrefix='http://edrn.nci.nih.gov/data/sites/',
        identifyingKey='Identifier',
        typeURI='http://edrn.nci.nih.gov/rdf/types.rdf#Site'
    )
    addDCTitle(generator, 'item_Title')
    createContentInContainer(
        generator,
        'edrn.rdf.literalpredicatehandler',
        title='Institution_Name_Abbrev',
        description='''Maps from DMCC's Institution_Name_Abbrev to EDRN-specific predicate for abbreviated name.''',
        predicateURI='http://edrn.nci.nih.gov/rdf/schema.rdf#abbrevName',
    )
    createContentInContainer(
        generator,
        'edrn.rdf.referencepredicatehandler',
        title='Associate_Members_Sponsor',
        description='''Maps from DMCC's Associate_Members_Sponsor to EDRN-specific predicate for sponsoring site.''',
        predicateURI='http://edrn.nci.nih.gov/rdf/schema.rdf#sponsor',
        uriPrefix='http://edrn.nci.nih.gov/data/sites/'
    )
    createContentInContainer(
        generator,
        'edrn.rdf.literalpredicatehandler',
        title='EDRN_Funding_Date_Start',
        description='''Maps from DMCC's EDRN_Funding_Date_Start to EDRN-specific predicate for starting date of funding.''',
        predicateURI='http://edrn.nci.nih.gov/rdf/schema.rdf#fundStart',
    )
    createContentInContainer(
        generator,
        'edrn.rdf.literalpredicatehandler',
        title='EDRN_Funding_Date_Finish',
        description='''Maps from DMCC's EDRN_Funding_Date_Finish to EDRN-specific predicate for ending date of funding.''',
        predicateURI='http://edrn.nci.nih.gov/rdf/schema.rdf#fundEnd',
    )
    createContentInContainer(
        generator,
        'edrn.rdf.literalpredicatehandler',
        title='FWA_Number',
        description='''Maps from DMCC's FWA_Number to EDRN-specific predicate for the so-called "FWA" number. Fwa!''',
        predicateURI='http://edrn.nci.nih.gov/rdf/schema.rdf#fwa',
    )
    createContentInContainer(
        generator,
        'edrn.rdf.referencepredicatehandler',
        title='ID_for_Principal_Investigator',
        description='''Maps from DMCC's ID_for_Principal_Investigator to EDRN-specific predicate for the PI.''',
        predicateURI='http://edrn.nci.nih.gov/rdf/schema.rdf#pi',
        uriPrefix='http://edrn.nci.nih.gov/data/registered-person/'
    )
    createContentInContainer(
        generator,
        'edrn.rdf.referencepredicatehandler',
        title='IDs_for_CoPrincipalInvestigators',
        description='''Maps from DMCC's IDs_for_CoPrincipalInvestigators to EDRN-specific predicate for co-PIs.''',
        predicateURI='http://edrn.nci.nih.gov/rdf/schema.rdf#copi',
        uriPrefix='http://edrn.nci.nih.gov/data/registered-person/'
    )
    createContentInContainer(
        generator,
        'edrn.rdf.referencepredicatehandler',
        title='IDs_for_CoInvestigators',
        description='''Maps from DMCC's IDs_for_CoInvestigators to EDRN-specific predicate for co-investigators.''',
        predicateURI='http://edrn.nci.nih.gov/rdf/schema.rdf#coi',
        uriPrefix='http://edrn.nci.nih.gov/data/registered-person/'
    )
    createContentInContainer(
        generator,
        'edrn.rdf.referencepredicatehandler',
        title='IDs_for_Investigators',
        description='''Maps from DMCC's IDs_for_Investigators to EDRN-specific predicate for investigators.''',
        predicateURI='http://edrn.nci.nih.gov/rdf/schema.rdf#investigator',
        uriPrefix='http://edrn.nci.nih.gov/data/registered-person/'
    )
    createContentInContainer(
        generator,
        'edrn.rdf.referencepredicatehandler',
        title='IDs_for_Staff',
        description='''Maps from DMCC's IDs_for_Staff to EDRN-specific predicate for peons.''',
        predicateURI='http://edrn.nci.nih.gov/rdf/schema.rdf#staff',
        uriPrefix='http://edrn.nci.nih.gov/data/registered-person/'
    )
    createContentInContainer(
        generator,
        'edrn.rdf.literalpredicatehandler',
        title='Site_Program_Description',
        description='''Maps from DMCC's Site_Program_Description to EDRN-specific predicate for the site's program.''',
        predicateURI='http://edrn.nci.nih.gov/rdf/schema.rdf#program'
    )
    createContentInContainer(
        generator,
        'edrn.rdf.referencepredicatehandler',
        title='Institution_URL',
        description='''Maps from DMCC's Institution_URL to EDRN-specific predicate for the site's home page.''',
        predicateURI='http://edrn.nci.nih.gov/rdf/schema.rdf#url',
        uriPrefix=''
    )
    createContentInContainer(
        generator,
        'edrn.rdf.literalpredicatehandler',
        title='Member_Type',
        description='''Maps from DMCC's Member_Type to EDRN-specific predicate for the kind of site.''',
        predicateURI='http://edrn.nci.nih.gov/rdf/schema.rdf#memberType'
    )
    createContentInContainer(
        generator,
        'edrn.rdf.literalpredicatehandler',
        title='Member_Type_Historical_Notes',
        description='''Maps from DMCC's Member_Type_Historical_Notes to EDRN-specific predicate for various notes.''',
        predicateURI='http://edrn.nci.nih.gov/rdf/schema.rdf#historicalNotes'
    )
    return generator


def createPersonGenerator(context):
    generator = createContentInContainer(
        context,
        'edrn.rdf.simpledmccrdfgenerator',
        title='Person Generator',
        description='Generates graphs describing the people of EDRN.',
        webServiceURL=_dmccURL,
        operationName='Registered_Person',
        uriPrefix='http://edrn.nci.nih.gov/data/registered-person/',
        identifyingKey='Identifier',
        typeURI='http://edrn.nci.nih.gov/rdf/types.rdf#Person'
    )
    createContentInContainer(
        generator,
        'edrn.rdf.literalpredicatehandler',
        title='Name_First',
        description='''Maps from DMCC's Name_First to the FOAF predicate for given name.''',
        predicateURI='http://xmlns.com/foaf/0.1/givenname'
    )
    createContentInContainer(
        generator,
        'edrn.rdf.literalpredicatehandler',
        title='Name_Middle',
        description='''Maps from DMCC's Name_Middle to EDRN-specific predicate for middle name.''',
        predicateURI='http://edrn.nci.nih.gov/rdf/schema.rdf#middleName'
    )
    createContentInContainer(
        generator,
        'edrn.rdf.literalpredicatehandler',
        title='Name_Last',
        description='''Maps from DMCC's Name_Last to the FOAF predicate for surname.''',
        predicateURI='http://xmlns.com/foaf/0.1/surname'
    )
    createContentInContainer(
        generator,
        'edrn.rdf.literalpredicatehandler',
        title='Phone',
        description='''Maps from DMCC's Phone to the FOAF predicate for phone.''',
        predicateURI='http://xmlns.com/foaf/0.1/phone'
    )
    createContentInContainer(
        generator,
        'edrn.rdf.referencepredicatehandler',
        title='Email',
        description='''Maps from DMCC's Email to the FOAF predicate for "mbox".''',
        predicateURI='http://xmlns.com/foaf/0.1/mbox',
        uriPrefix='mailto:'
    )
    createContentInContainer(
        generator,
        'edrn.rdf.literalpredicatehandler',
        title='Fax',
        description='''Maps from DMCC's Fax to the VCARD predicate for "fax".''',
        predicateURI='http://www.w3.org/2001/vcard-rdf/3.0#fax'
    )
    createContentInContainer(
        generator,
        'edrn.rdf.literalpredicatehandler',
        title='Specialty',
        description='''Maps from DMCC's Specialty to EDRN-specific predicate for specialty.''',
        predicateURI='http://edrn.nci.nih.gov/rdf/schema.rdf#specialty'
    )
    createContentInContainer(
        generator,
        'edrn.rdf.referencepredicatehandler',
        title='Photo_file_name',
        description='''Maps from DMCC's Photo_file_name to the FOAF predicate for photograph.''',
        predicateURI='http://xmlns.com/foaf/0.1/img',
        uriPrefix='http://edrn.jpl.nasa.gov/dmcc/staff-photographs/'
    )
    createContentInContainer(
        generator,
        'edrn.rdf.literalpredicatehandler',
        title='EDRN_Title',
        description='''Maps from DMCC's EDRN_Title to EDRN-specific predicate for EDRN job title.''',
        predicateURI='http://edrn.nci.nih.gov/rdf/schema.rdf#edrnTitle'
    )
    createContentInContainer(
        generator,
        'edrn.rdf.literalpredicatehandler',
        title='userID',
        description='''Maps from DMCC's userID to the FOAF predicate for account name.''',
        predicateURI='http://xmlns.com/foaf/0.1/accountName'
    )
    createContentInContainer(
        generator,
        'edrn.rdf.literalpredicatehandler',
        title='Role_Secure_Site',
        description='''Maps from DMCC's Role_Secure_Site to the EDRN predicate for secure site role.''',
        predicateURI='http://edrn.nci.nih.gov/rdf/schema.rdf#secureSiteRole'
    )
    createContentInContainer(
        generator,
        'edrn.rdf.literalpredicatehandler',
        title='Salutation',
        description='''Maps from DMCC's salutation to the FOAF predicate for account name.''',
        predicateURI='http://xmlns.com/foaf/0.1/salutation'
    )
    createContentInContainer(
        generator,
        'edrn.rdf.referencepredicatehandler',
        title='Site_id',
        description='''Maps from DMCC's Site_id to EDRN-specific predicate for the member's site.''',
        predicateURI='http://edrn.nci.nih.gov/rdf/schema.rdf#site',
        uriPrefix='http://edrn.nci.nih.gov/data/sites/'
    )
    for kind in ('mailing', 'physical', 'shipping'):
        prefix = kind[0].upper() + kind[1:]
        createContentInContainer(
            generator,
            'edrn.rdf.literalpredicatehandler',
            title=prefix + '_Address1',
            description='Maps from DMCC\'s {}_Address1 to EDRN-specific predicate of {} address.'.format(
                prefix, kind
            ),
            predicateURI='http://edrn.nci.nih.gov/rdf/schema.rdf#{}Address'.format(kind)
        )
        # Why, DMCC? Why?
        createContentInContainer(
            generator,
            'edrn.rdf.literalpredicatehandler',
            title=prefix + '_Other_StateOrProvince',
            description='Maps DMCC\'s {}_Other_StateOrProvince to EDRN-specific predicate for {} other address'.format(
                prefix, kind
            ),
            predicateURI='http://edrn.nci.nih.gov/rdf/schema.rdf#{}OtherStateOrProvince'.format(kind)
        )
        # Why, DMCC? Why?
        createContentInContainer(
            generator,
            'edrn.rdf.literalpredicatehandler',
            title=prefix + 'Mailing_Other_State_Province',
            description='Maps DMCC\'s {}Mailing_Other_State_Province to predicate for {} state/prov address'.format(
                prefix, kind
            ),
            predicateURI='http://edrn.nci.nih.gov/rdf/schema.rdf#{}OtherStateAndProvince'.format(kind)
        )
        createContentInContainer(
            generator,
            'edrn.rdf.literalpredicatehandler',
            title=prefix + '_City',
            description='Maps from DMCC\'s {}_City to EDRN-specific predicate for {} city.'.format(prefix, kind),
            predicateURI='http://edrn.nci.nih.gov/rdf/schema.rdf#{}City'.format(kind)
        )
        createContentInContainer(
            generator,
            'edrn.rdf.literalpredicatehandler',
            title=prefix + '_State',
            description='Maps from DMCC\'s {}_State to EDRN-specific predicate for {} state.'.format(prefix, kind),
            predicateURI='http://edrn.nci.nih.gov/rdf/schema.rdf#{}State'.format(kind)
        )
        createContentInContainer(
            generator,
            'edrn.rdf.literalpredicatehandler',
            title=prefix + '_Zip',
            description='Maps from DMCC\'s {}_Zip to EDRN-specific predicate for {} postal code.'.format(prefix, kind),
            predicateURI='http://edrn.nci.nih.gov/rdf/schema.rdf#{}PostalCode'.format(kind)
        )
        createContentInContainer(
            generator,
            'edrn.rdf.literalpredicatehandler',
            title=prefix + '_Country',
            description='Maps from DMCC\'s {}_Country to EDRN-specific predicate for {} country.'.format(prefix, kind),
            predicateURI='http://edrn.nci.nih.gov/rdf/schema.rdf#{}Country'.format(kind)
        )
    # Special case (thanks DMCC):
    createContentInContainer(
        generator,
        'edrn.rdf.literalpredicatehandler',
        title='Shipping_Address2',
        description='Maps from DMCC\'s Shipping_Address2 to EDRN-specific predicate for shipping address line 2.',
        predicateURI='http://edrn.nci.nih.gov/rdf/schema.rdf#shippingAddress2'
    )
    for degree in range(1, 4):
        createContentInContainer(
            generator,
            'edrn.rdf.literalpredicatehandler',
            title='Degree{}'.format(degree),
            description='Maps from DMCC\'s Degree{} to EDRN-specific predicate for degree #{}'.format(degree, degree),
            predicateURI='http://edrn.nci.nih.gov/rdf/schema.rdf#degree{}'.format(degree)
        )
    createContentInContainer(
        generator,
        'edrn.rdf.literalpredicatehandler',
        title='Staff_Status',
        description='''Maps from DMCC's Staff_Status to the EDRN-specific predicate for employmentActive.''',
        predicateURI='http://edrn.nci.nih.gov/rdf/schema.rdf#employmentActive'
    )
    return generator


def createBiomutaGenerator(context):
    return createContentInContainer(
        context,
        'edrn.rdf.biomutardfgenerator',
        title='Biomuta Generator',
        description='Generates graphs describing the EDRN\'s biomaker mutation statistics.',
        webServiceURL=_biomutaURL,
        typeURI='http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#Biomarker',
        uriPrefix='http://edrn.nci.nih.gov/data/biomuta/',
        geneNamePredicateURI='http://edrn.nci.nih.gov/xml/rdf/edrn.rdf#geneName',
        uniProtACPredicateURI='http://edrn.nci.nih.gov/xml/rdf/edrn.rdf#uniprotAccession',
        mutCountPredicateURI='http://edrn.nci.nih.gov/xml/rdf/edrn.rdf#mutationCount',
        pmidCountPredicateURI='http://edrn.nci.nih.gov/xml/rdf/edrn.rdf#pubmedIDCount',
        cancerDOCountPredicateURI='http://edrn.nci.nih.gov/xml/rdf/edrn.rdf#cancerDOCount',
        affProtFuncSiteCountPredicateURI='http://edrn.nci.nih.gov/xml/rdf/edrn.rdf#affectedProtFuncSiteCount'
    )

def createCommitteeGenerator(context):
    return createContentInContainer(
        context,
        'edrn.rdf.dmcccommitteerdfgenerator',
        title='Committees Generator',
        description='Generates graphs describing the EDRN\'s committees.',
        webServiceURL=_dmccURL,
        committeeOperation='Committees',
        membershipOperation='Committee_Membership',
        typeURI='http://edrn.nci.nih.gov/rdf/types.rdf#Committee',
        uriPrefix='http://edrn.nci.nih.gov/data/committees/',
        personPrefix='http://edrn.nci.nih.gov/data/registered-person/',
        titlePredicateURI='http://purl.org/dc/terms/title',
        abbrevNamePredicateURI='http://edrn.nci.nih.gov/xml/rdf/edrn.rdf#abbreviatedName',
        committeeTypePredicateURI='http://edrn.nci.nih.gov/xml/rdf/edrn.rdf#committeeType',
        chairPredicateURI='http://edrn.nci.nih.gov/xml/rdf/edrn.rdf#chair',
        coChairPredicateURI='http://edrn.nci.nih.gov/xml/rdf/edrn.rdf#coChair',
        consultantPredicateURI='http://edrn.nci.nih.gov/xml/rdf/edrn.rdf#consultant',
        memberPredicateURI='http://edrn.nci.nih.gov/xml/rdf/edrn.rdf#member'
    )


def createProtocolGenerator(context):
    return createContentInContainer(
        context,
        'edrn.rdf.dmccprotocolrdfgenerator',
        title='Protocols Generator',
        description='Generates graphs describing EDRN protocols and studies.',
        webServiceURL=_dmccURL,
        protocolOrStudyOperation='Protocol_or_Study',
        edrnProtocolOperation='EDRN_Protocol',
        protoSiteSpecificsOperation='Protocol_Site_Specifics',
        protoProtoRelationshipOperation='Protocol_Protocol_Relationship',
        typeURI='http://edrn.nci.nih.gov/rdf/types.rdf#Protocol',
        siteSpecificTypeURI='http://edrn.nci.nih.gov/rdf/types.rdf#ProtocolSiteSpecific',
        uriPrefix='http://edrn.nci.nih.gov/data/protocols/',
        siteSpecURIPrefix='http://edrn.nci.nih.gov/data/protocols/site-specific/',
        publicationURIPrefix='http://edrn.nci.nih.gov/data/pubs/',
        siteURIPrefix='http://edrn.nci.nih.gov/data/sites/',
        titleURI='http://purl.org/dc/terms/title',
        abstractURI='http://purl.org/dc/terms/description',
        involvedInvestigatorSiteURI='http://edrn.nci.nih.gov/rdf/schema.rdf#involvedInvestigatorSite',
        bmNameURI='http://edrn.nci.nih.gov/rdf/schema.rdf#bmName',
        coordinateInvestigatorSiteURI='http://edrn.nci.nih.gov/rdf/schema.rdf#coordinatingInvestigatorSite',
        leadInvestigatorSiteURI='http://edrn.nci.nih.gov/rdf/schema.rdf#leadInvestigatorSite',
        collaborativeGroupTextURI='http://edrn.nci.nih.gov/rdf/schema.rdf#collaborativeGroupText',
        phasedStatusURI='http://edrn.nci.nih.gov/rdf/schema.rdf#phasedStatus',
        aimsURI='http://edrn.nci.nih.gov/rdf/schema.rdf#aims',
        analyticMethodURI='http://edrn.nci.nih.gov/rdf/schema.rdf#analyticMethod',
        blindingURI='http://edrn.nci.nih.gov/rdf/schema.rdf#blinding',
        cancerTypeURI='http://edrn.nci.nih.gov/rdf/schema.rdf#cancerType',
        commentsURI='http://edrn.nci.nih.gov/rdf/schema.rdf#comments',
        dataSharingPlanURI='http://edrn.nci.nih.gov/rdf/schema.rdf#dataSharingPlan',
        inSituDataSharingPlanURI='http://edrn.nci.nih.gov/rdf/schema.rdf#inSituDataSharingPlan',
        finishDateURI='http://edrn.nci.nih.gov/rdf/schema.rdf#finishDate',
        estimatedFinishDateURI='http://edrn.nci.nih.gov/rdf/schema.rdf#estimatedFinishDate',
        startDateURI='http://edrn.nci.nih.gov/rdf/schema.rdf#startDate',
        designURI='http://edrn.nci.nih.gov/rdf/schema.rdf#design',
        fieldOfResearchURI='http://edrn.nci.nih.gov/rdf/schema.rdf#fieldOfResearch',
        abbreviatedNameURI='http://edrn.nci.nih.gov/rdf/schema.rdf#abbreviatedName',
        objectiveURI='http://edrn.nci.nih.gov/rdf/schema.rdf#objective',
        projectFlagURI='http://edrn.nci.nih.gov/rdf/schema.rdf#projectFlag',
        protocolTypeURI='http://edrn.nci.nih.gov/rdf/schema.rdf#protocolType',
        publicationsURI='http://edrn.nci.nih.gov/rdf/schema.rdf#publications',
        outcomeURI='http://edrn.nci.nih.gov/rdf/schema.rdf#outcome',
        secureOutcomeURI='http://edrn.nci.nih.gov/rdf/schema.rdf#secureOutcome',
        finalSampleSizeURI='http://edrn.nci.nih.gov/rdf/schema.rdf#finalSampleSize',
        plannedSampleSizeURI='http://edrn.nci.nih.gov/rdf/schema.rdf#plannedSampleSize',
        isAPilotForURI='http://edrn.nci.nih.gov/rdf/schema.rdf#isAPilot',
        obtainsDataFromURI='http://edrn.nci.nih.gov/rdf/schema.rdf#obtainsDataFrom',
        providesDataToURI='http://edrn.nci.nih.gov/rdf/schema.rdf#providesDataTo',
        contributesSpecimensURI='http://edrn.nci.nih.gov/rdf/schema.rdf#contributesSpecimensTo',
        obtainsSpecimensFromURI='http://edrn.nci.nih.gov/rdf/schema.rdf#obtainsSpecimensFrom',
        hasOtherRelationshipURI='http://edrn.nci.nih.gov/rdf/schema.rdf#hasOtherRelationship',
        animalSubjectTrainingReceivedURI='http://edrn.nci.nih.gov/rdf/schema.rdf#animalSubjectTrainingReceived',
        humanSubjectTrainingReceivedURI='http://edrn.nci.nih.gov/rdf/schema.rdf#humanSubjectTrainingReceived',
        irbApprovalNeededURI='http://edrn.nci.nih.gov/rdf/schema.rdf#irbApprovalNeeded',
        currentIRBApprovalDateURI='http://edrn.nci.nih.gov/rdf/schema.rdf#currentIRBApprovalDate',
        originalIRBApprovalDateURI='http://edrn.nci.nih.gov/rdf/schema.rdf#originalIRBApprovalDate',
        irbExpirationDateURI='http://edrn.nci.nih.gov/rdf/schema.rdf#irbExpirationDate',
        generalIRBNotesURI='http://edrn.nci.nih.gov/rdf/schema.rdf#irbNotes',
        irbNumberURI='http://edrn.nci.nih.gov/rdf/schema.rdf#irbNumber',
        siteRoleURI='http://edrn.nci.nih.gov/rdf/schema.rdf#siteRole',
        reportingStageURI='http://edrn.nci.nih.gov/rdf/schema.rdf#reportingStage',
        eligibilityCriteriaURI='http://edrn.nci.nih.gov/rdf/schema.rdf#eligibilityCriteria'
    )


def createLabCASGenerator(context):
    return createContentInContainer(
        context,
        'edrn.rdf.labcascollectionrdfgenerator',
        title='LabCAS Generator',
        description='Generates graphs of RDF describing EDRN science data stored in the Laboratory Catalog and Archive Management System.',
        labcasSolrURL='https://edrn-labcas.jpl.nasa.gov/data-access-api/collections',
        username='service',
        password='secret'
    )


def createRDFGenerators(context):
    generators = {}
    folder = createContentInContainer(
        context,
        'Folder',
        id='rdf-generators',
        title='RDF Generators',
        description='These objects are used to generate graphs of statements.'
    )
    generators['body-systems']      = createBodySystemsGenerator(folder)
    generators['committees']        = createCommitteeGenerator(folder)
    generators['diseases']          = createDiseaseGenerator(folder)
    generators['protocols']         = createProtocolGenerator(folder)
    generators['publications']      = createPublicationGenerator(folder)
    generators['registered-person'] = createPersonGenerator(folder)
    generators['sites']             = createSiteGenerator(folder)
    generators['biomuta']           = createBiomutaGenerator(folder)
    generators['labcas']            = createLabCASGenerator(folder)

    return generators


def createRDFSources(context, generators):
    folder = createContentInContainer(
        context,
        'Folder',
        id='rdf-data',
        title='RDF Sources',
        description='Sources of RDF information for EDRN.'
    )
    for objID, title, desc in (
        ('body-systems', 'Body Systems', 'Source of RDF for body systems.'),
        ('diseases', 'Diseases', 'Source of RDF for diseases.'),
        ('publications', 'Publications', 'Source of RDF for publications.'),
        ('sites', 'Sites', 'Source of RDF for EDRN\'s member sites.'),
        ('registered-person', 'Registered Person', 'Source of RDF for EDRN\'s people.'),
        ('committees', 'Committees', 'Source of RDF for committees and working groups in EDRN.'),
        ('biomuta', 'Biomuta', 'Source of RDF for biomarker mutation statistics in EDRN.'),
        ('labcas', 'LabCAS', 'Source of RDF for LabCAS science data in EDRN.'),
        ('protocols', 'Protocols', 'Source of RDF for EDRN\'s various protocols and studies.')
    ):
        generator = RelationValue(generators[objID])
        createContentInContainer(folder, 'edrn.rdf.rdfsource', title=title, description=desc, generator=generator, active=True)


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
    if 'rdf-generators' in list(portal.keys()):
        portal.manage_delObjects('rdf-generators')
    if 'rdf-data' in list(portal.keys()):
        portal.manage_delObjects('rdf-data')
    generators = createRDFGenerators(portal)
    wfTool = getToolByName(portal, 'portal_workflow')
    publish(portal['rdf-generators'], wfTool)
    intIDs = getUtility(IIntIds)
    for key, generator in generators.items():
        intID = intIDs.getId(generator)
        generators[key] = intID
    createRDFSources(portal, generators)
    publish(portal['rdf-data'], wfTool)


def setupVarious(context):
    if context.readDataFile('edrn.rdf.marker.txt') is None: return
    portal = context.getSite()
    installInitialSources(portal)
