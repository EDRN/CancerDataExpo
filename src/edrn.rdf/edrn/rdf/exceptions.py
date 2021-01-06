# encoding: utf-8
# Copyright 2012 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

'''EDRN RDF — Errors and other exceptional conditions'''


class RDFUpdateError(Exception):
    '''An abstract exception indicating a problem during RDF updates.'''
    def __init__(self, rdfSource, message):
        super(Exception, self).__init__('%s (RDF Source at "%s")' % (message, '/'.join(rdfSource.getPhysicalPath())))


class NoGeneratorError(RDFUpdateError):
    '''Exception indicating that an RDF source doesn't have any generator set up for it.'''
    def __init__(self, rdfSource):
        super(NoGeneratorError, self).__init__(rdfSource, 'No RDF generator configured')


class NoUpdateRequired(RDFUpdateError):
    '''A quasi-exceptional condition that indicates no RDF update is necessary.'''
    def __init__(self, rdfSource):
        super(NoUpdateRequired, self).__init__(rdfSource, 'No change to RDF required')


class MissingParameterError(RDFUpdateError):
    '''An error that tells that some required parameters to update RDF are not present.'''
    def __init__(self, rdfSource, parameter):
        super(MissingParameterError, self).__init__(rdfSource, 'Missing parameter: %s' % parameter)


class SourceNotActive(RDFUpdateError):
    '''Error that tells that we cannot update a source that is not marked as active'''
    def __init__(self, rdfSource):
        super(SourceNotActive, self).__init__(rdfSource, 'Source is not active')
