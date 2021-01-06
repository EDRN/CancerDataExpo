# encoding: utf-8
# Copyright 2012 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

'''Simple Predicate Handlers.'''


from zope import schema
from plone.supermodel import model
from edrn.rdf import _


class ISimplePredicateHandler(model.Schema):
    '''An abstract handler for a predicate in the simple DMCC RDF generator.'''
    title = schema.TextLine(
        title=_('Token Key'),
        description=_("Key name of the token in the DMCC's web service description."),
        required=True,
    )
    description = schema.Text(
        title=_('Description'),
        description=_('A short summary of this RDF source.'),
        required=False,
    )
    predicateURI = schema.TextLine(
        title=_('Predicate URI'),
        description=_('URI of the predicate to use when encountering tokenized keys of this kind.'),
        required=True,
    )
