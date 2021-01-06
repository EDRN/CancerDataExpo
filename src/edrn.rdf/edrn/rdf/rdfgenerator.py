# encoding: utf-8
# Copyright 2012 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

'''RDF Generator'''


from zope import schema
from plone.supermodel import model
from edrn.rdf import _


class IRDFGenerator(model.Schema):
    '''A generator of RDF'''
    title = schema.TextLine(
        title=_('Name'),
        description=_('Name of this RDF generator.'),
        required=True,
    )
    description = schema.Text(
        title=_('Description'),
        description=_('A short summary of this RDF generator.'),
        required=False,
    )

