# encoding: utf-8
# Copyright 2012 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

'''A "null" Summarizer generator.  This is a content object (Null Summarizer Generator) and an adapter that, when asked to generate
a statement graph, always produces an empty graph containing no statements whatsoever.
'''


from zope import schema
from edrn.summarizer import _
from .summarizergenerator import ISummarizerGenerator
import json


class INullJsonGenerator(ISummarizerGenerator):
    '''A null Summarizer generator that produces no statements at all.'''
    # @yuliujpl why does just the null-json generator have a datatype? Is this even used?
    datatype = schema.TextLine(
        title=_('Datatype'),
        description=_('Datatype of summary to be exposed.'),
        required=True
    )


class NullGraphGenerator(object):
    '''A statement graph generator that always produces an empty graph.'''
    def __init__(self, context):
        self.context = context

    def generateJson(self):
        '''Generate an empty graph.'''
        return json.dumps({})
