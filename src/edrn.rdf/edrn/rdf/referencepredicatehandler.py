# encoding: utf-8
# Copyright 2012–2020 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

from . import _
from .predicatehandler import ISimplePredicateHandler
from Acquisition import aq_inner
from rfc3986_validator import validate_rfc3986
from zope import schema
import rdflib, logging

_logger = logging.getLogger(__name__)


class IReferencePredicateHandler(ISimplePredicateHandler):
    '''A handler for DMCC web services that maps tokenized keys to URI references to other RDF subjects.'''
    uriPrefix = schema.TextLine(
        title=_('URI Prefix'),
        description=_('Uniform Resource Identifier that prefixes values mapped by this handler.'),
        required=True,
    )


class ReferenceAsserter(object):
    '''Describes subjects using predicates with complementary references to other objects.'''
    def __init__(self, context):
        self.context = context
    def characterize(self, obj):
        context = aq_inner(self.context)
        characterizations = []
        for i in obj.split(', '):
            i = i.strip()
            if not i: continue
            target = context.uriPrefix + i
            if validate_rfc3986(target):
                characterizations.append((rdflib.URIRef(context.predicateURI), rdflib.URIRef(target)))
            else:
                _logger.warning(
                    'Encountered an invalid URI «%s» for %s which will not be put into RDF', target,
                    self.context.title
                )

        return characterizations
