# encoding: utf-8
# Copyright 2012 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

'''Biomuta RDF Generator. An RDF generator that describes EDRN biomarker mutation statistics using Biomuta webservices.
'''

from .rdfgenerator import IRDFGenerator
from .utils import validateAccessibleURL
from Acquisition import aq_inner
from edrn.rdf import _
from rdflib.term import URIRef, Literal
from urllib.request import urlopen
from zope import schema
import rdflib, csv, codecs

_biomutaPredicates = {
    'GeneName': 'geneNamePredicateURI',
    'UniProtAC': 'uniProtACPredicateURI',
    '#mutated_site': 'mutCountPredicateURI',
    '#PMID': 'pmidCountPredicateURI',
    '#CancerDO': 'cancerDOCountPredicateURI',
    '#AffectedProtFunSite': 'affProtFuncSiteCountPredicateURI'
}


class IBiomutaRDFGenerator(IRDFGenerator):
    '''DMCC Committee RDF Generator.'''
    webServiceURL = schema.TextLine(
        title=_('Web Service URL'),
        description=_('The Uniform Resource Locator to the DMCC SOAP web service.'),
        required=True,
        constraint=validateAccessibleURL,
    )
    typeURI = schema.TextLine(
        title=_('Type URI'),
        description=_('Uniform Resource Identifier naming the type of biomuta objects described by this generator.'),
        required=True,
    )
    uriPrefix = schema.TextLine(
        title=_('URI Prefix'),
        description=_('The Uniform Resource Identifier prepended to all biomuta described by this generator.'),
        required=True,
    )
    geneNamePredicateURI = schema.TextLine(
        title=_('Gene Symbol/Name Predicate URI'),
        description=_('The Uniform Resource Identifier of the predicate that indicates gene symbol or name.'),
        required=True,
    )
    uniProtACPredicateURI = schema.TextLine(
        title=_('Uniprot Accession Predicate URI'),
        description=_('The Uniform Resource Identifier of the predicate that indicates the associated uniprot accession.'),
        required=True,
    )
    mutCountPredicateURI = schema.TextLine(
        title=_('Number of Mutation Sites Predicate URI'),
        description=_('The Uniform Resource Identifier of the predicate that indicates the number of mutation sites.'),
        required=True,
    )
    pmidCountPredicateURI = schema.TextLine(
        title=_('Pubmed ID Count Predicate URI'),
        description=_('The Uniform Resource Identifier of the predicate that indicates the number of associated pubmed ids.'),
        required=True,
    )
    cancerDOCountPredicateURI = schema.TextLine(
        title=_('CancerDO Predicate URI'),
        description=_('The Uniform Resource Identifier of the predicate that indicates the CancerDO.'),
        required=True,
    )
    affProtFuncSiteCountPredicateURI = schema.TextLine(
        title=_('Affected Protein Function Site Count Predicate URI'),
        description=_('The Uniform Resource Identifier of the predicate that indicates the number of affected protein function sites.'),
        required=True,
    )


class BiomutaGraphGenerator(object):
    # @yuliujpl: this doesn't talk to the DMCC's web service, though; so why is this doc-comment here?
    '''A graph generator that produces statements about EDRN's committees using the DMCC's fatuous web service.'''
    def __init__(self, context):
        self.context = context
    def generateGraph(self):
        graph = rdflib.Graph()
        context = aq_inner(self.context)
        with urlopen(context.webServiceURL) as f:
            reader = csv.reader(codecs.iterdecode(f, 'utf-8'))
            inputPredicates = None
            for row in reader:
                if inputPredicates is None:
                    inputPredicates = row
                else:
                    geneName = row[0].strip()
                    subjectURI = URIRef(context.uriPrefix + geneName)
                    graph.add((subjectURI, rdflib.RDF.type, URIRef(context.typeURI)))
                    for idx in range(0, len(inputPredicates)):
                        key = inputPredicates[idx]
                        predicateURI = URIRef(getattr(context, _biomutaPredicates[key]))
                        graph.add((subjectURI, predicateURI, Literal(row[idx].strip())))
                        # Seriously @yuliujpl? This *hides* errors. Exceptions should be thrown, not printed 🤢
                        # Also the indentation is incorrect.
                        # try:
                        #   graph.add((subjectURI, predicateURI, Literal(row[idx].strip())))
                        # except Exception as e:
                        #   print str(e)

        # C'est tout.
        return graph
