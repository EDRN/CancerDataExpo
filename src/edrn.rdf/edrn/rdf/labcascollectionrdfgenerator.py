# encoding: utf-8
# Copyright 2012–2020 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

'''LabCAS RDF Generator.
'''

from .rdfgenerator import IRDFGenerator
from .utils import validateAccessibleURL
from Acquisition import aq_inner
from edrn.rdf import _
from pysolr import Solr
from rdflib.term import URIRef, Literal
from zope import schema
import rdflib, logging

_logger = logging.getLogger(__name__)

# Predicate URIs
_titlePredicateURI = URIRef('http://purl.org/dc/terms/title')
_typeURI = URIRef('urn:edrn:types:labcas:collection')
_piPredicateURI = URIRef('urn:edrn:predicates:pi')
_organPredicateURI = URIRef('urn:edrn:predicates:organ')
_protocolPredicateURI = URIRef('urn:edrn:predicates:protocol')
_collaborativeGroupPredicateURI = URIRef('urn:edrn:predicates:collaborativeGroup')

# URI prefixes
_protocolPrefix = 'http://edrn.nci.nih.gov/data/protocols/'
_subjectPrefix = 'https://edrn-labcas.jpl.nasa.gov/labcas-ui/c/index.html?collection_id='

# Data inconsistency; thanks to @LucaCinquini and @AshishMahabal for
# https://github.com/EDRN/labcas-backend/issues/3 …
# This maps from various collaborative group names in LabCAS to the
# official names; if a mapping doesn't appear here, then it's an
# invalid collaborative group like "TBD" and we don't put it in RDF.

_inconsistentCollaborativeGroupNaming = {
    'Breast and Gynecologic Cancers Research Group': 'Breast and Gynecologic Cancers Research Group',
    'Breast and Gynecologic': 'Breast and Gynecologic Cancers Research Group',
    'Breast/GYN': 'Breast and Gynecologic Cancers Research Group',
    'G.I. and Other Associated Cancers Research Group': 'G.I. and Other Associated Cancers Research Group',
    'GI and Other Associated': 'G.I. and Other Associated Cancers Research Group',
    'Lung and Upper Aerodigestive Cancers Research Group': 'Lung and Upper Aerodigestive Cancers Research Group',
    'Lung and Upper Aerodigestive': 'Lung and Upper Aerodigestive Cancers Research Group',
    'Lung and Upper Areodigestive': 'Lung and Upper Aerodigestive Cancers Research Group',
    'Prostate and Urologic Cancers Research Group': 'Prostate and Urologic Cancers Research Group',
    'Prostate and Urologic': 'Prostate and Urologic Cancers Research Group',
}


class ILabCASCollectionRDFGenerator(IRDFGenerator):
    '''Generator for RDF using data from LabCAS.'''
    labcasSolrURL = schema.TextLine(
        title=_('LabCAS Solr URL'),
        description=_('The Uniform Resource Locator to the collections search using Solr.'),
        required=True,
        constraint=validateAccessibleURL,
        default='https://edrn-labcas.jpl.nasa.gov/data-access-api/collections'
    )
    username = schema.TextLine(
        title=_('Username'),
        description=_('Username to authenticate with; use a service account if available'),
        required=True,
        default='service'
    )
    password = schema.TextLine(
        title=_('Password'),
        description=_('Password to confirm the identity of the username; this will be visible!'),
        required=True,
    )


class LabCASCollectionGraphGenerator(object):
    '''A graph generator that produces statements about EDRN's science data collections.'''
    def __init__(self, context):
        self.context = context
    def generateGraph(self):
        context = aq_inner(self.context)
        graph = rdflib.Graph()
        solr = Solr(context.labcasSolrURL, auth=(context.username, context.password))
        results = solr.search(q='*:*', rows=999999)  # 😮 TODO This'll fail once we get to a million collections
        for i in results:
            collectionID, name, consortia = i.get('id'), i.get('CollectionName', '«unknown»'), i.get('Consortium', [])
            if not collectionID:
                _logger.warn('😮 The ``id`` is missing from a LabCAS collection named %s; skipping', name)
                continue
            if 'EDRN' not in consortia:
                _logger.warn('😌 Collection ``%s`` belongs to %r, not EDRN, so skipping it', collectionID, consortia)
                continue
            subjectURI = URIRef(_subjectPrefix + collectionID)  # ⚠️ Note that we are not URI-escaping anything here, hope that's oK!
            graph.add((subjectURI, rdflib.RDF.type, URIRef(_typeURI)))
            graph.add((subjectURI, _titlePredicateURI, Literal(name)))
            for pi in i.get('LeadPI', []):
                graph.add((subjectURI, _piPredicateURI, Literal(pi)))
            for organ in i.get('Organ', []):
                graph.add((subjectURI, _organPredicateURI, Literal(organ)))
            for protocolID in i.get('ProtocolId', []):
                try:
                    protocolID = int(protocolID)
                    graph.add((subjectURI, _protocolPredicateURI, URIRef(f'{_protocolPrefix}{protocolID}')))
                except ValueError:
                    _logger.warn('😮 The protocol ID «%s» for collection «%s» looks invalid; I will skip it', protocolID, collectionID)
            for group in i.get('CollaborativeGroup', []):
                group = _inconsistentCollaborativeGroupNaming.get(group)
                if group is not None:
                    graph.add((subjectURI, _collaborativeGroupPredicateURI, Literal(group)))
        return graph
