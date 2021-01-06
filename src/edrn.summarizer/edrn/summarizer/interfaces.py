# encoding: utf-8
# Copyright 2008—2012 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

'''EDRN Summarizer Service: interfaces
'''

from zope.interface import Interface

class ISummarizerUpdater(Interface):
    '''An object whose Summarizer may be updated'''
    def updateSummary():
        '''Update this object's Summarizer file.'''

class IGraphGenerator(Interface):
    '''An object that creates statement graphs.'''
    def generateGraph():
        '''Generate this object's Summarizer graph.'''

class IJsonGenerator(Interface):
    '''An object that creates json.'''
    def generateJson():
        '''Generate this object's Summarizer json.'''

class IAsserter(Interface):
    '''An object that describes subjects with a known predicate and a given object'''
    def characterize(obj):
        '''Characterize some subject using a known predicate for complementary ``obj``.  Returns a sequence of doubles
        containing a predicate URI (a URIRef) and an appropriate Literal or URIRef object.'''

