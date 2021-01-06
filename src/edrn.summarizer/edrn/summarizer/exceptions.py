# encoding: utf-8
# Copyright 2012 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

'''EDRN Summarizer — Errors and other exceptional conditions'''


class SummarizerUpdateError(Exception):
    '''An abstract exception indicating a problem during Summarizer updates.'''
    def __init__(self, summarizationSource, message):
        super(Exception, self).__init__('%s (Summarizer Source at "%s")' % (message, '/'.join(summarizationSource.getPhysicalPath())))


class NoGeneratorError(SummarizerUpdateError):
    '''Exception indicating that an Summarizer source doesn't have any generator set up for it.'''
    def __init__(self, summarizationSource):
        super(NoGeneratorError, self).__init__(summarizationSource, 'No Summarizer generator configured')


class UnknownGeneratorError(SummarizerUpdateError):
    '''Exception indicating that an Summarizer generator is an unknown generator type.'''
    def __init__(self, summarizationSource):
        super(UnknownGeneratorError, self).__init__(summarizationSource, 'Unknown Summarizer generator configured')


class NoUpdateRequired(SummarizerUpdateError):
    '''A quasi-exceptional condition that indicates no Summarizer update is necessary.'''
    def __init__(self, summarizationSource):
        super(NoUpdateRequired, self).__init__(summarizationSource, 'No change to Summarizer required')


class MissingParameterError(SummarizerUpdateError):
    '''An error that tells that some required parameters to update Summarizer are not present.'''
    def __init__(self, summarizationSource, parameter):
        super(MissingParameterError, self).__init__(summarizationSource, 'Missing parameter: %s' % parameter)


class SourceNotActive(SummarizerUpdateError):
    '''Error that tells that we cannot update a source that is not marked as active'''
    def __init__(self, summarizationSource):
        super(SourceNotActive, self).__init__(summarizationSource, 'Source is not active')
