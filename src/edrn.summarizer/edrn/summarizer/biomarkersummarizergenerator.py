# encoding: utf-8
# Copyright 2012 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

'''Biomarker Json Generator. An Json generator that describes EDRN biomarker organ statistics using Biomarker webservices.
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
import jsonlib

_typeURI                                 = URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type')
_bmOrganDataTypeURI                      = URIRef('http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#BiomarkerOrganData')
_biomarkerPredicateURI                   = URIRef('http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#Biomarker')
_organPredicateURI                       = URIRef('http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#Organ')
_isPanelPredicateURI                     = URIRef('http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#IsPanel')
_bmTitlePredicateURI                     = URIRef('http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#Title')
_hgncPredicateURI                        = URIRef('http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#HgncName')
_typePredicateURI                        = URIRef('http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#Type')

MAX_NON_UNIQUE_BIOMARKER_IDS = 100


class IBiomarkerSummarizerGenerator(ISummarizerGenerator):
    '''DMCC Committee RDF Generator.'''
    biomarkerURL = schema.TextLine(
        title=_('Biomarker Web Service URL'),
        description=_('The Uniform Resource Locator to the BMDB SOAP biomarker web service.'),
        required=True,
        constraint=validateAccessibleURL,
    )
    organURL = schema.TextLine(
        title=_('Organ Web Service URL'),
        description=_('The Uniform Resource Locator to the BMDB SOAP organ web service..'),
        required=True,
        constraint=validateAccessibleURL,
    )

class BiomarkerJsonGenerator(object):
    '''A Json generator that produces statements about EDRN's biomarker and organ statistics using the BMDB's web service.'''
    def __init__(self, context):
        self.context = context

    def addOrganSpecificInformation(self, biomarkers, statements, biomarkerOrganFreq):
        '''Populate JSON with body system (aka "organ") biomarker assocation statistics.'''
        for uri, predicates in statements.items():
            try:
                if predicates[_typeURI][0] != _bmOrganDataTypeURI:
                    continue
            except KeyError:
                continue

            #Add Organ biomarker associations for statistical visualizations
            for objID in predicates[_biomarkerPredicateURI]:
                bmID = biomarkers[objID]
                for bmorgan in predicates[_organPredicateURI]:
                    if bmID in biomarkerOrganFreq:
                        biomarkerOrganFreq[bmID] += [bmorgan]
                    else:
                        biomarkerOrganFreq[bmID] = [bmorgan]

    def generateOrganTypeStats(self, biomarkerTypeFreq, biomarkerOrganFreq):
        organByType = {}
        for bmID in biomarkerTypeFreq:
            for bmtype in biomarkerTypeFreq[bmID]:
                if bmID not in biomarkerOrganFreq:
                    biomarkerOrganFreq[bmID] = [Literal('Other')]
                for bmorgan in biomarkerOrganFreq[bmID]:
                    if bmorgan in organByType:
                        if bmtype in organByType[bmorgan]:
                            organByType[bmorgan][bmtype] += 1
                        else:
                            organByType[bmorgan][bmtype] = 1
                    else:
                        organByType[bmorgan] = {}
                        organByType[bmorgan][bmtype] = 1

        return organByType

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
        #graph = rdflib.Graph()
        context = aq_inner(self.context)
        rdfDataSource, bmoDataSource = context.biomarkerURL, context.organURL
        if not rdfDataSource or not bmoDataSource:
            raise RDFIngestException(_('This generator folder lacks one or both of its RDF source URLs.'))
        normalizerFunction = queryUtility(IIDNormalizer).normalize
        graph = ConjunctiveGraph()
        graph.parse(URLInputSource(rdfDataSource))
        statements = self._parseRDF(graph)

        biomarkerTypeFreq = {}
        biomarkerOrganFreq = {}
        allBiomarkers = {}

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

                if not isPanel:
                    #Add frequencies for biomarker associated with biomarker type (Gene, Protein, etc...)
                    for bmtype in predicates[_typePredicateURI]:
                        if objID in biomarkerTypeFreq:
                            biomarkerTypeFreq[objID] += [bmtype]
                        else:
                            biomarkerTypeFreq[objID] = [bmtype]
                allBiomarkers[URIRef(uri)] = objID
            except KeyError:
                pass

        # Add organ-specific information
        graph = ConjunctiveGraph()
        graph.parse(URLInputSource(bmoDataSource))
        organStatements = self._parseRDF(graph)
        self.addOrganSpecificInformation(allBiomarkers, organStatements, biomarkerOrganFreq)

        jsondata = self.generateOrganTypeStats(biomarkerTypeFreq,biomarkerOrganFreq)

        # C'est tout.
        return jsonlib.write(jsondata)
