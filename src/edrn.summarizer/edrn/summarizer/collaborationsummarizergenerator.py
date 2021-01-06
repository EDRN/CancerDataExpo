# encoding: utf-8
# Copyright 2012 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

'''Collaboration Json Generator. An Json generator that describes EDRN collaboration mutation statistics using collaboration webservices.
'''

from Acquisition import aq_inner
from edrn.summarizer import _

from .summarizergenerator import ISummarizerGenerator
from rdflib.term import URIRef, Literal
from rdflib.parser import URLInputSource
from rdflib import ConjunctiveGraph
from .utils import validateAccessibleURL
from zope import schema
from zope.component import queryUtility
from plone.i18n.normalizer.interfaces import IIDNormalizer
from .exceptions import MissingParameterError
import jsonlib

COLLABORATIVE_GROUP_BMDB_IDS_TO_NAMES = {
    Literal('Breast and Gynecologic'):          Literal('Breast and Gynecologic Cancers Research Group'),
    Literal('G.I. and Other Associated'):       Literal('G.I. and Other Associated Cancers Research Group'),
    Literal('Lung and Upper Aerodigestive'):    Literal('Lung and Upper Aerodigestive Cancers Research Group'),
    Literal('Prostate and Urologic'):           Literal('Prostate and Urologic Cancers Research Group'),
}

COLLABORATIVE_GROUP_ECAS_IDS_TO_NAMES = {
    Literal('Breast/GYN'):                      Literal('Breast and Gynecologic Cancers Research Group'),
    Literal('GI and Other Associated'):         Literal('G.I. and Other Associated Cancers Research Group'),
    Literal('Lung and Upper Aerodigestive'):    Literal('Lung and Upper Aerodigestive Cancers Research Group'),
    Literal('Prostate and Urologic'):           Literal('Prostate and Urologic Cancers Research Group'),
}

INV_COLLABORATIVE_GROUP_BMDB_IDS_TO_NAMES = {v: k for k, v in COLLABORATIVE_GROUP_BMDB_IDS_TO_NAMES.items()}

_typeURI                                 = URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type')
_biomarkerPredicateURI                   = URIRef('http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#Biomarker')
_isPanelPredicateURI                     = URIRef('http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#IsPanel')
_bmTitlePredicateURI                     = URIRef('http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#Title')
_hgncPredicateURI                        = URIRef('http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#HgncName')
_groupPredicateURI                       = URIRef('http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#AccessGrantedTo')
_typePredicateURI                        = URIRef('http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#Type')

_collaborativeGroupDataURI               = URIRef('urn:edrn:CollaborativeGroup')
_collaborativeGroupProURI                = URIRef('http://edrn.nci.nih.gov/rdf/schema.rdf#collaborativeGroupText')

_protocolNameURI                         = URIRef('http://edrn.nci.nih.gov/rdf/schema.rdf#abbreviatedName')
_datasetIdURI                            = URIRef('urn:edrn:DatasetId')

_memberPredicateURI                      = URIRef('http://edrn.nci.nih.gov/xml/rdf/edrn.rdf#member')
_titlePredicateURI                      = URIRef('http://purl.org/dc/terms/title')

MAX_NON_UNIQUE_BIOMARKER_IDS = 100


class ICollaborationSummarizerGenerator(ISummarizerGenerator):
    '''DMCC Committee RDF Generator.'''
    biomarkerURL = schema.TextLine(
        title=_('Collaboration Web Service URL'),
        description=_('The Uniform Resource Locator to the BMDB SOAP biomarker web service.'),
        required=True,
        constraint=validateAccessibleURL,
    )
    dataURL = schema.TextLine(
        title=_('Dataset Web Service URL'),
        description=_('The Uniform Resource Locator to the BMDB SOAP dataset web service..'),
        required=True,
        constraint=validateAccessibleURL,
    )
    protocolURL = schema.TextLine(
        title=_('Protocol Web Service URL'),
        description=_('The Uniform Resource Locator to the BMDB SOAP protocol web service..'),
        required=True,
        constraint=validateAccessibleURL,
    )
    memberURL = schema.TextLine(
        title=_('Members Web Service URL'),
        description=_('The Uniform Resource Locator to the BMDB SOAP member web service..'),
        required=True,
        constraint=validateAccessibleURL,
    )


class CollaborationJsonGenerator(object):
    '''A Json generator that produces statements about EDRN's collaboration frequencies using the BMDB's web service.'''
    def __init__(self, context):
        self.context = context

    def updateCollaborativeGroup(self, objects, groups, allObj, collabFreq):
        for groupID in groups:
            groupID = Literal(groupID.strip())
            groupName = ""
            if groupID in COLLABORATIVE_GROUP_ECAS_IDS_TO_NAMES:
                groupName = COLLABORATIVE_GROUP_ECAS_IDS_TO_NAMES[groupID]
            elif groupID in COLLABORATIVE_GROUP_BMDB_IDS_TO_NAMES:
                groupName = COLLABORATIVE_GROUP_BMDB_IDS_TO_NAMES[groupID]
            elif groupID in INV_COLLABORATIVE_GROUP_BMDB_IDS_TO_NAMES:
                groupName = groupID
            else:
                continue
            for obj in objects:
                #if obj not in allObj:
                #    allObj[obj]=1

                if groupName in collabFreq:
                    collabFreq[groupName] += 1
                else:
                    collabFreq[groupName] = 1
        return collabFreq

    def updateCollaboratorFreq(self, biomarker, predicates, allBiomarkers, collabBmFreq):
        for accessGroup in predicates[_groupPredicateURI]:
            collabGroup = COLLABORATIVE_GROUP_BMDB_IDS_TO_NAMES.get(accessGroup)
            if not collabGroup: continue
            if biomarker not in allBiomarkers:
                if collabGroup in collabBmFreq:
                    collabBmFreq[collabGroup] += 1
                else:
                    collabBmFreq[collabGroup] = 1
        return collabBmFreq

    def _parseRDF(self, graph):
        '''Parse the statements in graph into a mapping {u→{p→o}} where u is a
        resource URI, p is a predicate URI, and o is a list of objects which
        may be literals or URI references.'''
        statements = {}
        for s, p, o in graph:
            if s not in statements:
                statements[s] = {}
            predicates = statements[s]
            if p not in predicates:
                predicates[p] = []
            predicates[p].append(o)
        return statements

    def generateJson(self):
        collabBmFreq    = {}
        collabPnFreq    = {}
        collabDataFreq  = {}
        collabProtoFreq = {}
        collabMemFreq   = {}

        context = aq_inner(self.context)
        bmDataSource, dataDataSource, protocolDataSource, memberDataSource = context.biomarkerURL, context.dataURL, context.protocolURL, context.memberURL
        if not bmDataSource or not dataDataSource or not protocolDataSource or not memberDataSource:
            raise MissingParameterError(_('This generator folder lacks one or both of its RDF source URLs.'))
        normalizerFunction = queryUtility(IIDNormalizer).normalize
        graph = ConjunctiveGraph()
        graph.parse(URLInputSource(bmDataSource))
        statements = self._parseRDF(graph)

        allBiomarkers = {}
        allDatasets   = {}
        allProtocols  = {}
        allMembers    = {}

        for uri, predicates in statements.items():
            try:
                typeURI = predicates[_typeURI][0]
                if typeURI != _biomarkerPredicateURI:
                    continue
                isPanel = bool(int(predicates[_isPanelPredicateURI][0]))
                title = str(predicates[_bmTitlePredicateURI][0])
                hgnc = predicates[_hgncPredicateURI][0] if _hgncPredicateURI in predicates else None

                if hgnc is not None:
                    hgnc = hgnc.strip()
                objID = hgnc if hgnc else normalizerFunction(title)
                if URIRef(uri) in allBiomarkers:
                    continue
                #Add frequencies for collaboration associated with frequencies in contribution
                if isPanel:
                    collabPnFreq = self.updateCollaboratorFreq(objID, predicates, allBiomarkers, collabPnFreq)
                else:
                    collabBmFreq = self.updateCollaboratorFreq(objID, predicates, allBiomarkers, collabBmFreq)
                allBiomarkers[URIRef(uri)] = objID
            except KeyError:
                pass

        graph = ConjunctiveGraph()
        graph.parse(URLInputSource(dataDataSource))
        statements = self._parseRDF(graph)
        for uri, predicates in statements.items():
            if _collaborativeGroupDataURI in predicates:
                collabDataFreq = self.updateCollaborativeGroup(predicates[_datasetIdURI], predicates[_collaborativeGroupDataURI], allDatasets, collabDataFreq)

        graph = ConjunctiveGraph()
        graph.parse(URLInputSource(protocolDataSource))
        statements = self._parseRDF(graph)
        for uri, predicates in statements.items():
            if _collaborativeGroupProURI in predicates:
                collabProtoFreq = self.updateCollaborativeGroup(predicates[_protocolNameURI], predicates[_collaborativeGroupProURI], allProtocols, collabProtoFreq)

        graph = ConjunctiveGraph()
        graph.parse(URLInputSource(memberDataSource))
        statements = self._parseRDF(graph)
        for uri, predicates in statements.items():
            if _memberPredicateURI in predicates:
                collabMemFreq = self.updateCollaborativeGroup(predicates[_memberPredicateURI], predicates[_titlePredicateURI], allMembers, collabMemFreq)
        
        # Coalate all dictionaries into one
        
        jsondata = {"biomarker" : collabBmFreq, "panel" : collabPnFreq, "data" : collabDataFreq, "protocol" : collabProtoFreq, "member" : collabMemFreq}

        # C'est tout.
        return jsonlib.write(jsondata)
