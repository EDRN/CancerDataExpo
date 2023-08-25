# encoding: utf-8
# Copyright 2023 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.


from .predicatehandler import ISimplePredicateHandler
from Acquisition import aq_inner
import rdflib


class IMultiPipePredicateHandler(ISimplePredicateHandler):
    '''A handler for DMCC web services that maps tokenized |-separated keys to multiple literal RDF values.'''
    # No further fields are necessary.


class MultiPipeAsserter(object):
    '''Describes subjects using predicates with multiple literal complementary objects separated by |.'''
    def __init__(self, context):
        self.context = context
    def characterize(self, obj):
        context = aq_inner(self.context)
        rc = [(rdflib.URIRef(context.predicateURI), rdflib.Literal(i.strip())) for i in obj.split('|')]
        return rc
