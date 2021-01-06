# encoding: utf-8
# Copyright 2012 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

from edrn.summarizer.interfaces import ISummarizerUpdater
from edrn.summarizer.summarizersource import ISummarizerSource
from plone.protect.interfaces import IDisableCSRFProtection
from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from zope.interface import alsoProvides
import logging

_logger = logging.getLogger('edrn.summarizer')


class SiteSummarizerUpdater(BrowserView):
    '''A "view" that instructs all Summarizer sources to generate fresh summaries.'''
    def render(self):
        return self.index()
    def __call__(self):
        alsoProvides(self.request, IDisableCSRFProtection)
        self.request.set('disable_border', True)
        catalog = getToolByName(self.context, 'portal_catalog')
        results = catalog(object_provides=ISummarizerSource.__identifier__)
        self.count, self.failures = 0, []
        for i in results:
            source = i.getObject()
            updater = ISummarizerUpdater(source)
            try:
                updater.updateSummary()
                self.count += 1
            except Exception as ex:
                _logger.exception('Failure updating Summarizer for "%s"', i.getPath())
                self.failures.append(dict(title=i.Title, url=source.absolute_url(), message=str(ex)))
        self.numFailed = len(self.failures)
        return self.render()
