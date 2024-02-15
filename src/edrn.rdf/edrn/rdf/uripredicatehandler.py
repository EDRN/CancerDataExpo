# encoding: utf-8
# Copyright 2024 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

from .predicatehandler import ISimplePredicateHandler
from Acquisition import aq_inner
from rfc3986_validator import validate_rfc3986
import rdflib, logging

_logger = logging.getLogger(__name__)


class IURIPredicateHandler(ISimplePredicateHandler):
    '''A handler for DMCC web services that contains single URI references.'''
    pass


class URIAsserter(object):
    '''Describes subjects using a predicate with a single complementary references to some other URI.'''
    def __init__(self, context):
        self.context = context

    def characterize(self, obj):
        context = aq_inner(self.context)

        if validate_rfc3986(obj):
            return [(rdflib.URIRef(context.predicateURI), rdflib.URIRef(obj))]
        else:
            _logger.warning(
                "Got an invalid URI «%s» for %s which won't be put into RDF", obj, self.context.title
            )
            return []
