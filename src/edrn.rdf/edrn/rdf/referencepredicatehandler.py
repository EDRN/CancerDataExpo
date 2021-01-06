# encoding: utf-8
# Copyright 2012–2020 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

from . import _
from .predicatehandler import ISimplePredicateHandler
from Acquisition import aq_inner
from zope import schema
import rdflib


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
            characterizations.append((rdflib.URIRef(context.predicateURI), rdflib.URIRef(target)))
        return characterizations
