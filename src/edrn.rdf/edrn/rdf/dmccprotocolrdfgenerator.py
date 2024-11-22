# encoding: utf-8
# Copyright 2012–2021 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

'''DMCC Protocol RDF Generator. An RDF generator that describes EDRN protocols using the DMCC's web services.
'''

from edrn.rdf import _

from .rdfgenerator import IRDFGenerator
from .utils import get_suds_client
from .utils import parseTokens, validateAccessibleURL, DEFAULT_VERIFICATION_NUM, splitDMCCRows
from rdflib.term import URIRef, Literal
from zope import schema
import rdflib, logging


_logger = logging.getLogger(__name__)

_siteRoles = {
    '1':                  'Funding Source',
    '2':                  'Discovery',
    '3':                  'Reference',
    '4':                  'Coordinating Site',
    '5':                  'Specimen Contributing Site',
    '6':                  'Specimen Storage',
    '7':                  'Analysis Lab',
    '8':                  'Statistical Services',
    '9':                  'Consultant',
    '97':                 'Other',
}

_reportingStages = {
    '1':                   'Development Stage',
    '2':                   'Funding Stage',
    '3':                   'Protocol Development Stage',
    '4':                   'Procedure Development Stage',
    '5':                   'Retrospective Sample Identification Stage',
    '6':                   'Recruitment Stage',
    '7':                   'Lab Processing Stage',
    '8':                   'Blinding Stage',
    '9':                   'Lab Analysis Stage',
    '10':                  'Publication Stage',
    '11':                  'Statistical Analysis Stage',
    '12':                  'Completed',
    '97':                  'Other',
}

_fieldsOfResearch = {
    '1': 'Genomics',
    '2': 'Epigenomics',
    '3': 'Proteomics',
    '4': 'Glycomics',
    '5': 'Nanotechnology',
    '6': 'Metabolomics',
    '7': 'Hypermethylation',
    '9': 'Other',
}


class IDMCCProtocolRDFGenerator(IRDFGenerator):
    '''DMCC Protocol RDF Generator.'''
    webServiceURL = schema.TextLine(
        title=_('Web Service URL'),
        description=_('The Uniform Resource Locator to the DMCC SOAP web service.'),
        required=True,
        constraint=validateAccessibleURL,
    )
    protocolOrStudyOperation = schema.TextLine(
        title=_('Protocol-Or-Study Operation Name'),
        description=_('Name of the SOAP operation to invoke in order to retrieve protocol-or-study information.'),
        required=True,
    )
    edrnProtocolOperation = schema.TextLine(
        title=_('EDRN Protocol Operation Name'),
        description=_('Name of the SOAP operation to invoke in order to retrieve information about EDRN protocols.'),
        required=True,
    )
    protoSiteSpecificsOperation = schema.TextLine(
        title=_('Protocol Site-Specifics Operation Name'),
        description=_('Name of the SOAP operation to invoke in order to retrieve site-specific information about protocols.'),
        required=True,
    )
    protoProtoRelationshipOperation = schema.TextLine(
        title=_('Protocol-Protocol Relationship Operation Name'),
        description=_('Name of the SOAP operation to invoke in order to get information regarding protocol interrelationships.'),
        required=True,
    )
    verificationNum = schema.TextLine(
        title=_('Verification Number String'),
        description=_('Feeble and jejune parameter to pass to the operation. A default will be used if unset.'),
        required=False,
    )
    typeURI = schema.TextLine(
        title=_('Type URI'),
        description=_('Uniform Resource Identifier naming the type of protocol objects described by this generator.'),
        required=True,
    )
    siteSpecificTypeURI = schema.TextLine(
        title=_('Site-Specific Type URI'),
        description=_('Uniform Resource Identifier naming the type of protocol/site-specific objects described.'),
        required=True,
    )
    uriPrefix = schema.TextLine(
        title=_('URI Prefix'),
        description=_('The Uniform Resource Identifier prepended to all protocols described by this generator.'),
        required=True,
    )
    siteSpecURIPrefix = schema.TextLine(
        title=_('Site-Specific URI Prefix'),
        description=_('Prefix string to prepend to identifiers to generate complete URIs to site-specific information.'),
        required=True,
    )
    publicationURIPrefix = schema.TextLine(
        title=_('Publication URI Prefix'),
        description=_('Prefix string to prepend to identifiers to generate complete URIs to publications.'),
        required=True,
    )
    siteURIPrefix = schema.TextLine(
        title=_('Site URI Prefix'),
        description=_('Prefix string to prepend to identifiers to generate complete URIs to sites.'),
        required=True,
    )
    titleURI = schema.TextLine(
        title=_('Title URI'),
        description=_('Uniform Resource Identifier for the title predicate.'),
        required=True,
    )
    abstractURI = schema.TextLine(
        title=_('Abstract URI'),
        description=_('Uniform Resource Identifier for the abstract predicate.'),
        required=True,
    )
    involvedInvestigatorSiteURI = schema.TextLine(
        title=_('Involved Investigator Site URI'),
        description=_('Uniform Resource Identifier for the involved investigator site predicate.'),
        required=True,
    )
    bmNameURI = schema.TextLine(
        title=_('BM Name URI'),
        description=_('Uniform Resource Identifier for the BM name predicate.'),
        required=True,
    )
    coordinateInvestigatorSiteURI = schema.TextLine(
        title=_('Coordinating Investigator Site URI'),
        description=_('Uniform Resource Identifier for the coordinating site predicate.'),
        required=True,
    )
    leadInvestigatorSiteURI = schema.TextLine(
        title=_('Lead Investigator Site URI'),
        description=_('Uniform Resource Identifier for the lead investigator site predicate.'),
        required=True,
    )
    collaborativeGroupTextURI = schema.TextLine(
        title=_('Collaborative Group Text URI'),
        description=_('Uniform Resource Identifier for the collaborative group text predicate.'),
        required=True,
    )
    phasedStatusURI = schema.TextLine(
        title=_('Phased Status URI'),
        description=_('Uniform Resource Identifier for the phased status predicate.'),
        required=True,
    )
    aimsURI = schema.TextLine(
        title=_('Aims URI'),
        description=_('Uniform Resource Identifier for the aims predicate.'),
        required=True,
    )
    analyticMethodURI = schema.TextLine(
        title=_('Analytic Method URI'),
        description=_('Uniform Resource Identifier for the analytic method predicate.'),
        required=True,
    )
    blindingURI = schema.TextLine(
        title=_('Blinding URI'),
        description=_('Uniform Resource Identifier for the blinding predicate.'),
        required=True,
    )
    cancerTypeURI = schema.TextLine(
        title=_('Cancer Type URI'),
        description=_('Uniform Resource Identifier for the cancer type predicate.'),
        required=True,
    )
    cancerTypeURIPrefix = schema.TextLine(
        title=_('Disease URI Prefix'),
        description=_('URI prefix to identity Disease objects for the cancer type studied by a protocol.'),
        required=True,
        default='http://edrn.nci.nih.gov/data/diseases/'
    )
    commentsURI = schema.TextLine(
        title=_('Comments URI'),
        description=_('Uniform Resource Identifier for the comments predicate.'),
        required=True,
    )
    dataSharingPlanURI = schema.TextLine(
        title=_('Data Sharing Plan URI'),
        description=_('Uniform Resource Identifier for the data sharing plan predicate.'),
        required=True,
    )
    inSituDataSharingPlanURI = schema.TextLine(
        title=_('In-Situ Data Sharing Plan URI'),
        description=_('Uniform Resource Identifier for the in-situ data sharing plan predicate.'),
        required=True,
    )
    finishDateURI = schema.TextLine(
        title=_('Finish Date URI'),
        description=_('Uniform Resource Identifier for the finish date predicate.'),
        required=True,
    )
    estimatedFinishDateURI = schema.TextLine(
        title=_('Estimated Finish Date URI'),
        description=_('Uniform Resource Identifier for the estimated finish date predicate.'),
        required=True,
    )
    startDateURI = schema.TextLine(
        title=_('Start Date URI'),
        description=_('Uniform Resource Identifier for the start date predicate.'),
        required=True,
    )
    designURI = schema.TextLine(
        title=_('Design URI'),
        description=_('Uniform Resource Identifier for the design predicate.'),
        required=True,
    )
    fieldOfResearchURI = schema.TextLine(
        title=_('Field of Research URI'),
        description=_('Uniform Resource Identifier for the field of research predicate.'),
        required=True,
    )
    abbreviatedNameURI = schema.TextLine(
        title=_('Abbreviated Name URI'),
        description=_('Uniform Resource Identifier for the abbreviated name predicate.'),
        required=True,
    )
    objectiveURI = schema.TextLine(
        title=_('Objective URI'),
        description=_('Uniform Resource Identifier for the objective predicate.'),
        required=True,
    )
    projectFlagURI = schema.TextLine(
        title=_('Project Flag URI'),
        description=_('Uniform Resource Identifier for the project flag predicate.'),
        required=True,
    )
    protocolTypeURI = schema.TextLine(
        title=_('Protocol Type URI'),
        description=_('Uniform Resource Identifier for the protocol type predicate.'),
        required=True,
    )
    publicationsURI = schema.TextLine(
        title=_('Publications URI'),
        description=_('Uniform Resource Identifier for the publications predicate.'),
        required=True,
    )
    outcomeURI = schema.TextLine(
        title=_('Outcome URI'),
        description=_('Uniform Resource Identifier for the outcome predicate.'),
        required=True,
    )
    secureOutcomeURI = schema.TextLine(
        title=_('Secure Outcome URI'),
        description=_('Uniform Resource Identifier for the secure outcome predicate.'),
        required=True,
    )
    finalSampleSizeURI = schema.TextLine(
        title=_('Final Sample Size URI'),
        description=_('Uniform Resource Identifier for the final sample size predicate.'),
        required=True,
    )
    plannedSampleSizeURI = schema.TextLine(
        title=_('Planend Sample Size URI'),
        description=_('Uniform Resource Identifier for the planned sample size predicate.'),
        required=True,
    )
    isAPilotForURI = schema.TextLine(
        title=_('Is A Pilot URI'),
        description=_('Uniform Resource Identifier for the "is a pilot" predicate.'),
        required=True,
    )
    obtainsDataFromURI = schema.TextLine(
        title=_('Obtains Data From URI'),
        description=_('Uniform Resource Identifier for the "obtains data from" predicate.'),
        required=True,
    )
    providesDataToURI = schema.TextLine(
        title=_('Provides Data To URI'),
        description=_('Uniform Resource Identifier for the "provides data to" predicate.'),
        required=True,
    )
    contributesSpecimensURI = schema.TextLine(
        title=_('Contributes Sepcimens URI'),
        description=_('Uniform Resource Identifier for the "contributes specimens" predicate.'),
        required=True,
    )
    obtainsSpecimensFromURI = schema.TextLine(
        title=_('Obtains Specimens From URI'),
        description=_('Uniform Resource Identifier for the "obtains specimens from" predicate.'),
        required=True,
    )
    hasOtherRelationshipURI = schema.TextLine(
        title=_('Has Other Relationship URI'),
        description=_('Uniform Resource Identifier for the "has other relationship" predicate.'),
        required=True,
    )
    animalSubjectTrainingReceivedURI = schema.TextLine(
        title=_('Animal Subject Training Received URI'),
        description=_('Uniform Resource Identifier for the predicate that indicates if animal subject training as been received.'),
        required=True,
    )
    humanSubjectTrainingReceivedURI = schema.TextLine(
        title=_('Human Subject Training Received URI'),
        description=_('Uniform Resource Identifier for the predicate that indicates if human subject training as been received.'),
        required=True,
    )
    irbApprovalNeededURI = schema.TextLine(
        title=_('IRB Approval Needed URI'),
        description=_('Uniform Resource Identifier for the predicate that indicates if IRB approval is still needed.'),
        required=True,
    )
    currentIRBApprovalDateURI = schema.TextLine(
        title=_('Current IRB Approval Date URI'),
        description=_('Uniform Resource Identifier for the predicate that tells the current IRB approval date.'),
        required=True,
    )
    originalIRBApprovalDateURI = schema.TextLine(
        title=_('Original IRB Approval Date URI'),
        description=_('Uniform Resource Identifier for the predicate that tells of the original date of IRB approval.'),
        required=True,
    )
    irbExpirationDateURI = schema.TextLine(
        title=_('IRB Expiration Date URI'),
        description=_('Uniform Resource Identifier for the predicate that tells when the IRB will expire.'),
        required=True,
    )
    generalIRBNotesURI = schema.TextLine(
        title=_('General IRB Notes URI'),
        description=_('Uniform Resource Identifier for the predicate that lists general notes about the IRB.'),
        required=True,
    )
    irbNumberURI = schema.TextLine(
        title=_('IRB Number URI'),
        description=_('Uniform Resource Identifier for the predicate that identifies the IRB number.'),
        required=True,
    )
    siteRoleURI = schema.TextLine(
        title=_('Site Role URI'),
        description=_('Uniform Resource Identifier for the predicate that lists the roles the site participates in.'),
        required=True,
    )
    reportingStageURI = schema.TextLine(
        title=_('Report Stage URI'),
        description=_('Uniform Resource Identifier for the predicate that names the stages of reporting.'),
        required=True,
    )
    eligibilityCriteriaURI = schema.TextLine(
        title=_('Eligibility Criteria URI'),
        description=_('Uniform Resource Identifier for the predicate that identifies the eligibility criteria.'),
        required=True,
    )


class _Identified(object):
    def __init__(self, identifier):
        self.identifier = identifier
    def __lt__(self, other):
        return self.identifier < other.identifier
    def __le__(self, other):
        return self.identifier <= other.identifier
    def __eq__(self, other):
        return self.identifier == other.identifier
    def __ne__(self, other):
        return self.identifier != other.identifier
    def __gt__(self, other):
        return self.identifier > other.identifier
    def __ge__(self, other):
        return self.identifier >= other.identifier
    def __repr__(self):
        return '%s(identifier=%s,attributes=%r)' % (self.__class__.__name__, self.identifier, self.attributes)
    def __hash__(self):
        return hash(self.identifier)
    def addToGraph(self, graph, context):
        raise NotImplementedError('Subclasses must implement %s.addToGraph' % self.__class__.__name__)


class _Slotted(_Identified):
    def __init__(self, identifier):
        super(_Slotted, self).__init__(identifier)
        self.slots = {}


class Study(_Slotted):
    def __init__(self, identifier):
        super(Study, self).__init__(identifier)
    def addToGraph(self, graph, context):
        subjectURI = URIRef(context.uriPrefix + self.identifier)
        for slotName, attrName in (
            ('Eligibility_criteria', 'eligibilityCriteriaURI'),
            ('Protocol_Abstract', 'abstractURI'),
            ('Title', 'titleURI')
        ):
            value = self.slots.get(slotName, None)
            if not value: continue
            predicateURI = URIRef(getattr(context, attrName))
            graph.add((subjectURI, predicateURI, Literal(value)))


_specificsPredicates = {
    'animalTraining': 'animalSubjectTrainingReceivedURI',
    'humanTraining': 'humanSubjectTrainingReceivedURI',
    'irbApprovalNeeded': 'irbApprovalNeededURI',
    'irbCurrentApprovalDate': 'currentIRBApprovalDateURI',
    'irbOriginalApprovalDate': 'originalIRBApprovalDateURI',
    'irbExpirationDate': 'irbExpirationDateURI',
    'irbNotes': 'generalIRBNotesURI',
    'irbNumber': 'irbNumberURI',
}

_miscSlots = {
    'BiomarkerName':                        'bmNameURI',
    'Eligibility_criteria':                 'eligibilityCriteriaURI',
    'Protocol_5_Phase_Status':              'phasedStatusURI',
    'Protocol_Aims':                        'aimsURI',
    'Protocol_Analytic_Method':             'analyticMethodURI',
    'Protocol_Blinding':                    'blindingURI',
    'Protocol_Collaborative_Group':         'collaborativeGroupTextURI',
    'Protocol_Comments':                    'commentsURI',
    'Protocol_Data_Sharing_Plan':           'dataSharingPlanURI',
    'Protocol_Data_Sharing_Plan_In_Place':  'inSituDataSharingPlanURI',
    'Protocol_Date_Finish':                 'finishDateURI',
    'Protocol_Date_Finish_Estimate':        'estimatedFinishDateURI',
    'Protocol_Date_Start':                  'startDateURI',
    'Protocol_Design':                      'designURI',
    'Protocol_Name_Abbrev':                 'abbreviatedNameURI',
    'Protocol_Objective':                   'objectiveURI',
    'Protocol_or_Project_Flag':             'projectFlagURI',
    'Protocol_Results_Outcome':             'outcomeURI',
    'Protocol_Results_Outcome_Secure_Site': 'secureOutcomeURI',
    'Sample_Size_Final':                    'finalSampleSizeURI',
    'Sample_Size_Planned':                  'plannedSampleSizeURI',
}


class Protocol(_Slotted):
    def __init__(self, identifier):
        super(Protocol, self).__init__(identifier)
    def getSubjectURI(self, context):
        return URIRef(context.uriPrefix + self.identifier)
    def _addInvolvedInvestigatorSites(self, graph, specifics, context):
        for involvedInvestigatorSiteID in self.slots.get('Involved_Investigator_Site_ID', '').split(', '):
            key = (self.identifier, involvedInvestigatorSiteID)
            if key not in specifics: continue
            specific = specifics[key]
            subject = URIRef(context.siteSpecURIPrefix + self.identifier + '-' + involvedInvestigatorSiteID)
            graph.add((subject, rdflib.RDF.type, URIRef(context.siteSpecificTypeURI)))
            for fieldName, predicateFieldName in _specificsPredicates.items():
                fieldValue = getattr(specific, fieldName, None)
                if not fieldValue: continue
                predicateURI = URIRef(getattr(context, predicateFieldName))
                graph.add((subject, predicateURI, Literal(fieldValue)))
            if specific.siteRoles:
                predicateURI = URIRef(context.siteRoleURI)
                for roleID in specific.siteRoles.split(', '):
                    graph.add((subject, predicateURI, Literal(_siteRoles.get(roleID, 'UNKNOWN'))))
            if specific.reportingStages:
                predicateURI = URIRef(context.reportingStageURI)
                for reportingStageID in specific.reportingStages.split(', '):
                    graph.add((subject, predicateURI, Literal(_reportingStages.get(reportingStageID, 'UNKNOWN'))))
    def _addOtherSites(self, graph, context):
        subjectURI = self.getSubjectURI(context)
        for slotName, predicateFieldName in (
            ('Coordinating_Investigator_Site_ID', 'coordinateInvestigatorSiteURI'),
            ('Lead_Investigator_Site_ID', 'leadInvestigatorSiteURI'),
        ):
            siteIDs = self.slots.get(slotName, '')
            predicateURI = URIRef(getattr(context, predicateFieldName))
            for siteID in siteIDs.split(', '):
                graph.add((subjectURI, predicateURI, URIRef(context.siteURIPrefix + siteID)))
    def _addPublications(self, graph, context):
        subjectURI, predicateURI = self.getSubjectURI(context), URIRef(context.publicationsURI)
        for pubID in self.slots.get('Protocol_Publications', '').split(', '):
            pubID = pubID.strip()
            if not pubID: continue
            graph.add((subjectURI, predicateURI, URIRef(context.publicationURIPrefix + pubID)))
    def _addFieldsOfResearch(self, graph, context):
        subjectURI, predicateURI = self.getSubjectURI(context), URIRef(context.fieldOfResearchURI)
        for fieldOfResearchID in self.slots.get('Protocol_Field_of_Research', '').split(', '):
            graph.add((subjectURI, predicateURI, Literal(_fieldsOfResearch.get(fieldOfResearchID, 'UNKNOWN'))))
    def _addMiscFields(self, graph, context):
        subjectURI = self.getSubjectURI(context)
        for slotName, predicateFieldName in _miscSlots.items():
            obj = self.slots.get(slotName, None)
            if not obj: continue
            predicateURI = URIRef(getattr(context, predicateFieldName))
            graph.add((subjectURI, predicateURI, Literal(obj)))
    def _addCancerTypes(self, graph, context):
        subjectURI, predicateURI = self.getSubjectURI(context), URIRef(context.cancerTypeURI)
        values = self.slots.get('Protocol_Cancer_Type', '')
        for value in values.strip().split(', '):
            value = value.strip()
            if value:
                graph.add((subjectURI, predicateURI, URIRef(context.cancerTypeURIPrefix + value)))
    def _addProtocolType(self, graph, context):
        subjectURI = self.getSubjectURI(context)
        kind = self.slots.get('Protocol_Type')
        if not kind: return
        kind = 'Other' if kind == 'Other specify' else kind
        graph.add((subjectURI, URIRef(context.protocolTypeURI), Literal(kind)))
    def addToGraph(self, graph, specifics, context):
        self._addProtocolType(graph, context)
        self._addInvolvedInvestigatorSites(graph, specifics, context)
        self._addOtherSites(graph, context)
        self._addPublications(graph, context)
        self._addFieldsOfResearch(graph, context)
        self._addCancerTypes(graph, context)
        self._addMiscFields(graph, context)


_specificsMap = {
    'Animal_Subject_Training_Received': 'animalTraining',
    'Human_Subject_Training_Recieved':  'humanTraining',
    'IRB_Approval_Needed':              'irbApprovalNeeded',
    'IRB_Date_Current_Approval_Date':   'irbCurrentApprovalDate',
    'IRB_Date_Original_Approval_Date':  'irbOriginalApprovalDate',
    'IRB_Expiration_Date':              'irbExpirationDate',
    'IRB_General_Notes':                'irbNotes',
    'IRB_Number':                       'irbNumber',
    'Protocol_ID':                      'protocolID',
    'Protocol_Site_Roles':              'siteRoles',
    'Reporting_Stages':                 'reportingStages',
    'Site_ID':                          'siteID',
}


class Specifics(_Identified):
    def __init__(self, row):
        self.identifier, self.attributes = None, {}
        for key, value in parseTokens(row):
            if key == 'Identifier':
                self.identifier = value
            else:
                self.attributes[_specificsMap[key]] = value
    def __getattr__(self, key):
        return self.attributes.get(key, None)


_relationshipsMap = {
    'contributes specimens to': 'contributesSpecimensURI',
    'is a pilot for':           'isAPilotForURI',
    'obtains data from':        'obtainsDataFromURI',
    'obtains specimens from':   'obtainsSpecimensFromURI',
    'Other':                    'hasOtherRelationshipURI',
    'provides data to':         'providesDataToURI',
}


class Relationship(_Identified):
    def __init__(self, row):
        self.identifier = None
        for key, value in parseTokens(row):
            if key == 'Identifier':
                self.identifier = value
            elif key == 'Protocol_1_Identifier':
                self.fromID = value
            elif key == 'Protocol_2_Identifier':
                self.toID = value
            elif key == 'Protocol_relationship_type':
                self.relationshipType = value
    def addToGraph(self, graph, context):
        predicateFieldName = _relationshipsMap.get(self.relationshipType, 'hasOtherRelationshipURI')
        predicateURI = URIRef(getattr(context, predicateFieldName))
        subjectURI, objURI = URIRef(context.uriPrefix + self.fromID), URIRef(context.uriPrefix + self.toID)
        graph.add((subjectURI, predicateURI, objURI))


class DMCCProtocolGraphGenerator(object):
    '''A graph generator that produces statements about EDRN's protocols using the DMCC's web service.'''
    def __init__(self, context):
        self.context = context
    @property
    def verificationNum(self):
        return self.context.verificationNum if self.context.verificationNum else DEFAULT_VERIFICATION_NUM
    @property
    def client(self):
        return get_suds_client(self.context.webServiceURL, self.context)
    def getSlottedItems(self, operation, kind):
        function = getattr(self.client.service, operation)
        # try:
        #     horribleString = function(self.verificationNum)
        # except:
        #     breakpoint()
        horribleString = function(self.verificationNum)
        objects = {}
        obj = None
        for row in splitDMCCRows(horribleString):
            lastSlot = None
            for key, value in parseTokens(row):
                if key == 'Identifier':
                    if obj is None or obj.identifier != value:
                        obj = kind(value)
                        objects[value] = obj
                elif key == 'slot':
                    lastSlot = value
                    _logger.warning('Slot = %s', lastSlot)
                elif key == 'value':
                    if lastSlot is None:
                        raise ValueError('Value with no preceding slot in row "%r"' % row)
                    obj.slots[lastSlot] = value
                    lastSlot = None
        return objects
    def getStudies(self):
        return self.getSlottedItems(self.context.protocolOrStudyOperation, Study)
    def getProtocols(self):
        return self.getSlottedItems(self.context.edrnProtocolOperation, Protocol)
    def getSpecifics(self):
        function = getattr(self.client.service, self.context.protoSiteSpecificsOperation)
        horribleString = function(self.verificationNum)
        specifics = {}
        for row in splitDMCCRows(horribleString):
            specific = Specifics(row)
            specifics[(specific.protocolID, specific.siteID)] = specific
        return specifics
    def getRelationships(self):
        function = getattr(self.client.service, self.context.protoProtoRelationshipOperation)
        horribleString = function(self.verificationNum)
        relationships = []
        for row in splitDMCCRows(horribleString):
            relationships.append(Relationship(row))
        return relationships
    def generateGraph(self):
        graph = rdflib.Graph()
        studies = self.getStudies()
        specifics = self.getSpecifics()
        relationships = self.getRelationships()
        protocols = self.getProtocols()
        for study in studies.values():
            subjectURI = URIRef(self.context.uriPrefix + study.identifier)
            graph.add((subjectURI, rdflib.RDF.type, URIRef(self.context.typeURI)))
            study.addToGraph(graph, self.context)
            if study.identifier in protocols:
                protocol = protocols[study.identifier]
                protocol.addToGraph(graph, specifics, self.context)
        for relation in relationships:
            relation.addToGraph(graph, self.context)
        for protocol in protocols.values():
            protocol.addToGraph(graph, specifics, self.context)
        # C'est tout.
        return graph
