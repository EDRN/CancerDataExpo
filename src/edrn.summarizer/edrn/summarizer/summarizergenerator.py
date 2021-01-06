# encoding: utf-8
# Copyright 2012 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

'''Summarizer Generator'''


from zope import schema
from plone.supermodel import model
from edrn.summarizer import _


class ISummarizerGenerator(model.Schema):
    '''A generator of Summarizer'''
    title = schema.TextLine(
        title=_('Name'),
        description=_('Name of this Summarizer generator.'),
        required=True,
    )
    description = schema.Text(
        title=_('Description'),
        description=_('A short summary of this Summarizer generator.'),
        required=False,
    )

