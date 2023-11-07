# encoding: utf-8
# Copyright 2012 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

from .exceptions import SourceNotActive, NoUpdateRequired
from .notifications import notify_update_failures
from edrn.rdf.interfaces import IRDFUpdater
from edrn.rdf.rdfsource import IRDFSource
from plone.protect.interfaces import IDisableCSRFProtection
from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from zope.interface import alsoProvides
import logging

_logger = logging.getLogger('edrn.rdf')


class SiteRDFUpdater(BrowserView):
    '''A "view" that instructs all RDF sources to generate fresh RDF.'''
    def render(self):
        return self.index()

    def __call__(self):
        alsoProvides(self.request, IDisableCSRFProtection)
        self.request.set('disable_border', True)
        catalog = getToolByName(self.context, 'portal_catalog')
        results = catalog(object_provides=IRDFSource.__identifier__)
        self.count, self.failures = 0, []
        for i in results:
            source = i.getObject()
            updater = IRDFUpdater(source)
            try:
                updater.updateRDF()
                self.count += 1
            except (SourceNotActive, NoUpdateRequired) as ex:
                _logger.info('Ignoring exception "%s" on "%s"', ex, '/'.join(source.getPhysicalPath()))
            except Exception as ex:
                _logger.exception('Failure updating RDF for "%s"', '/'.join(source.getPhysicalPath()))
                self.failures.append(dict(title=i.Title, url=source.absolute_url(), message=str(ex)))
        self.numFailed = len(self.failures)
        if self.numFailed > 0:
            notify_update_failures(self.context, self.failures)
        return self.render()
