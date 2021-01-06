# encoding: utf-8
# Copyright 2012 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

'''RDF Source'''

from .rdfgenerator import IRDFGenerator
from Acquisition import aq_inner
from edrn.rdf import _
from plone.app.vocabularies.catalog import CatalogSource
from plone.supermodel import model
from Products.Five import BrowserView
from z3c.relationfield.schema import RelationChoice
from zope import schema


class IRDFSource(model.Schema):
    '''A source of RDF data.'''
    title = schema.TextLine(
        title=_('Name'),
        description=_('Name of this RDF source'),
        required=True,
    )
    description = schema.Text(
        title=_('Description'),
        description=_('A short summary of this RDF source.'),
        required=False,
    )
    generator = RelationChoice(
        title=_('Generator'),
        description=_('Which RDF generator should this source use.'),
        required=False,
        source=CatalogSource(object_provides=IRDFGenerator.__identifier__),
    )
    approvedFile = RelationChoice(
        title=_('Active RDF File'),
        description=_('Which of the RDF files is the active one.'),
        required=False,
        source=CatalogSource(portal_type='File'),
    )
    active = schema.Bool(
        title=_('Active'),
        description=_('Is this source active? If so, it will have RDF routinely generated for it.'),
        required=False,
        default=False,
    )


class View(BrowserView):
    '''RDF output from an RDF source.'''
    def __call__(self):
        context = aq_inner(self.context)
        if context.approvedFile and context.approvedFile.to_object:
            self.request.response.redirect(context.approvedFile.to_object.absolute_url())
        else:
            raise ValueError('The RDF Source at %s does not have an active RDF file to send' % '/'.join(context.getPhysicalPath()))
