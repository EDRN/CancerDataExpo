# encoding: utf-8
# Copyright 2012 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

'''Summarizer Source'''

from Acquisition import aq_inner
from edrn.summarizer import _
from Products.Five import BrowserView
from plone.app.vocabularies.catalog import CatalogSource
from plone.supermodel import model
from .summarizergenerator import ISummarizerGenerator
from z3c.relationfield.schema import RelationChoice
from zope import schema


class ISummarizerSource(model.Schema):
    '''A source of Summarizer data.'''
    title = schema.TextLine(
        title=_('Name'),
        description=_('Name of this Summarizer source'),
        required=True,
    )
    description = schema.Text(
        title=_('Description'),
        description=_('A short summary of this Summarizer source.'),
        required=False,
    )
    generator = RelationChoice(
        title=_('Generator'),
        description=_('Which Summarizer generator should this source use.'),
        required=False,
        source=CatalogSource(object_provides=ISummarizerGenerator.__identifier__),
    )
    approvedFile = RelationChoice(
        title=_('Active Summarizer File'),
        description=_('Which of the Summarizer files is the active one.'),
        required=False,
        source=CatalogSource(portal_type='File'),
    )
    active = schema.Bool(
        title=_('Active'),
        description=_('Is this source active? If so, it will have Summarizer routinely generated for it.'),
        required=False,
        default=False,
    )


class View(BrowserView):
    '''Sumarizer output from an Summarizer source.'''
    def __call__(self):
        context = aq_inner(self.context)
        if context.approvedFile and context.approvedFile.to_object:
            self.request.response.redirect(context.approvedFile.to_object.absolute_url())
        else:
            raise ValueError('The Summarizer Source at %s does not have an active Summarizer file to send' % '/'.join(context.getPhysicalPath()))
