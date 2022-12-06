# encoding: utf-8
# Copyright 2012 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

'''Publicatoin Json Generator. An Json generator that describes EDRN publication statistics using publication webservices.
'''

from Acquisition import aq_inner
from edrn.summarizer import _, ENTREZ_TOOL, ENTREZ_EMAIL

from .summarizergenerator import ISummarizerGenerator
from rdflib.term import URIRef
from rdflib.parser import URLInputSource
from rdflib import ConjunctiveGraph
from .utils import validateAccessibleURL
from zope import schema
from zope.component import getUtility
from plone.i18n.normalizer.interfaces import IIDNormalizer
import contextlib
import json
from Bio import Entrez

# Constants
FETCH_GROUP_SIZE = 100  # Fetch this many publications in Entrez.fetch, pausing to construct objects between each
START_YEAR = 2000

_publicationTypeURI = URIRef('http://edrn.nci.nih.gov/rdf/types.rdf#Publication')
_typeURI            = URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type')
_pmidURI            = URIRef('http://edrn.nci.nih.gov/rdf/schema.rdf#pmid')
_yearURI            = URIRef('http://edrn.nci.nih.gov/rdf/schema.rdf#year')

Entrez.tool = ENTREZ_TOOL
Entrez.email = ENTREZ_EMAIL

class IPublicationSummarizerGenerator(ISummarizerGenerator):
    '''Publication JSON Statistics Generator.'''
    rdfDataSource = schema.TextLine(
        title=_('Publications Web Service URL'),
        description=_('The Uniform Resource Locator to the DMCC Publications web service.'),
        required=True,
        constraint=validateAccessibleURL,
    )
    additionalDataSources = schema.TextLine(
        title=_('Publicatoins additional Web Service URL'),
        description=_('The Uniform Resource Locator to the BMDB SOAP additional Publications web service..'),
        required=True,
        constraint=validateAccessibleURL,
    )

class PublicationJsonGenerator(object):
    '''A Json generator that produces statements about EDRN's publication statistics using the DMCC and BMDB web service.'''
    def __init__(self, context):
        self.context = context

    def addGraphToStatements(self, graph, statements):
        '''Add the statements in the RDF ``graph`` to the ``statements`` dict.'''
        for s, p, o in graph:
            if s not in statements:
                statements[s] = {}
            predicates = statements[s]
            if p not in predicates:
                predicates[p] = []
            predicates[p].append(o)

    def getRDFStatements(self):
        '''Parse the main and additional RDF data sources and return a dict {uri → {predicate → [objects]}}'''
        context = aq_inner(self.context)
        urls = [context.rdfDataSource]
        urls = urls + [context.additionalDataSources]
        statements = {}
        for url in urls:
            graph = ConjunctiveGraph()
            graph.parse(URLInputSource(url))
            self.addGraphToStatements(graph, statements)
        return statements

    def getIdentifiersForPubMedID(self, statements, pubMedYears):
        '''Given statements in the form of a dict {uri → {predicate → [objects]}}, yield a new dict
        {uri → PubMedID} including only those uris that are EDRN publication objects and only including
        those that have PubMedIDs.  In addition, don't duplicate PubMedIDs.'''
        identifiers, pubMedIDs= {}, set()
        for uri, predicates in statements.items():
            uri = str(uri)
            typeURI = predicates[_typeURI][0]
            if typeURI != _publicationTypeURI: continue
            if _pmidURI not in predicates: continue
            pmID = predicates[_pmidURI][0]
            pmID = str(pmID).strip()
            if _yearURI in predicates:
                year = predicates[_yearURI][0]
            if not pmID: continue
            if pmID == 'N/A': continue
            if pmID in pubMedIDs:
                #_logger.warning('PubMedID %s duplicated in %s, ignoring that URI', pmID, uri)
                continue
            pubMedIDs.add(pmID)
            if _yearURI in predicates:
                year = str(predicates[_yearURI][0])
                if int(year) < START_YEAR:
                    continue
                #Get pubmed year frequencies
                if year in pubMedYears:
                    pubMedYears[year] += 1
                else:
                    pubMedYears[year] = 1
            else:
                identifiers[uri] = pmID

        return identifiers, pubMedYears
    def divvy(self, identifiers):
        identifiers = list(identifiers.items())
        while len(identifiers) > 0:
            group = identifiers[:FETCH_GROUP_SIZE]
            identifiers = identifiers[FETCH_GROUP_SIZE:]
            yield group
    def queryPubmedYear(self, identifiers, allPublications, pubMedYears):
        '''Given a dict {uri → PubMedID}, create Publications using data from PubMed.  Return a sequence
        of CreatedObjects.'''
        context = aq_inner(self.context)
        normalize = getUtility(IIDNormalizer).normalize
        for group in self.divvy(identifiers):
            identifiers, pubMedIDs = [i[0] for i in group], [i[1] for i in group]
            with contextlib.closing(Entrez.efetch(db='pubmed',retmode='xml',rettype='medline',id=pubMedIDs)) as handle:
                records = Entrez.read(handle)
                if 'PubmedArticle' in records:
                    records = records['PubmedArticle']
                for i in zip(identifiers, records):
                    identifier, medline = str(i[0]), i[1]
                    pubMedID = str(medline['MedlineCitation']['PMID'])
                    year = medline['MedlineCitation']['Article']['Journal']['JournalIssue']['PubDate'].get(
                        'Year', None
                    )
                    if not year or year is None : continue
                    year = str(year)
                    if int(year) < START_YEAR:
                        continue
                    if pubMedID not in allPublications:
                        allPublications[pubMedID] = 1
                        #Get pubmed year frequencies
                        if year in pubMedYears:
                            pubMedYears[year] += 1
                        else:
                            pubMedYears[year] = 1
        return pubMedYears

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
        pubMedYears = {}
        allPublications = {}
        statements = self.getRDFStatements()
        allPubmedIds, pubMedYears = self.getIdentifiersForPubMedID(statements, pubMedYears)
        pubMedYears = self.queryPubmedYear(allPubmedIds, allPublications, pubMedYears)

        # C'est tout.
        return json.dumps(pubMedYears)
