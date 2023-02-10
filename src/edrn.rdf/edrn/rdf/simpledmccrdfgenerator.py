# encoding: utf-8
# Copyright 2012 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

'''Simple DMCC RDF Generator. This generator is used to describe the some of the more simple
sets of data available at the DMCC by accessing their web service.
'''

from edrn.rdf import _

from .exceptions import MissingParameterError
from .interfaces import IAsserter
from .rdfgenerator import IRDFGenerator
from .utils import get_suds_client
from .utils import parseTokens, splitDMCCRows
from .utils import validateAccessibleURL
from Acquisition import aq_inner
from rdflib.term import URIRef
from zope import schema
import rdflib, logging

_logger = logging.getLogger(__name__)

DEFAULT_VERIFICATION_NUM = '0' * 40960  # Why, why, why? DMCC, this makes no sense unless you copied a sample
# SOAP app from a book or a website that did credit card number verification and decided to make that the basis
# for all your SOAP apps


class ISimpleDMCCRDFGenerator(IRDFGenerator):
    '''Simple DMCC RDF Generator.'''
    webServiceURL = schema.TextLine(
        title=_('Web Service URL'),
        description=_('The Uniform Resource Locator to the DMCC SOAP web service.'),
        required=True,
        constraint=validateAccessibleURL,
    )
    operationName = schema.TextLine(
        title=_('Operation Name'),
        description=_('Name of the SOAP operation to invoke in order to retrieve data.'),
        required=True,
    )
    verificationNum = schema.TextLine(
        title=_('Verification Number String'),
        description=_('Utterly pointless and needless parameter to pass to the operation. A default will be used if unset.'),
        required=False,
    )
    uriPrefix = schema.TextLine(
        title=_('URI Prefix'),
        description=_('The Uniform Resource Identifier prepended to all subjects described by this generator.'),
        required=True,
    )
    identifyingKey = schema.TextLine(
        title=_('Identifying Key'),
        description=_('Key in the DMCC output serves as the discriminant for objects described by this generator.'),
        required=True,
    )
    typeURI = schema.TextLine(
        title=_('Type URI'),
        description=_('Uniform Resource Identifier naming the type of objects described by this generator.'),
        required=True,
    )


class SimpleDMCCGraphGenerator(object):
    '''A statement graph generator that produces statements based on the DMCC's web service.'''
    def __init__(self, context):
        self.context = context
    def generateGraph(self):
        context = aq_inner(self.context)
        if not context.webServiceURL: raise MissingParameterError(context, 'webServiceURL')
        if not context.operationName: raise MissingParameterError(context, 'operationName')
        if not context.identifyingKey: raise MissingParameterError(context, 'identifyingKey')
        if not context.uriPrefix: raise MissingParameterError(context, 'uriPrefix')
        if not context.typeURI: raise MissingParameterError(context, 'typeURI')
        verificationNum = context.verificationNum if context.verificationNum else DEFAULT_VERIFICATION_NUM
        predicates = {}
        unusedSlots = set()
        usedSlots = set()
        for objID, item in context.contentItems():
            predicates[item.title] = IAsserter(item)
        client = get_suds_client(context.webServiceURL, context)
        function = getattr(client.service, context.operationName)
        horribleString = function(verificationNum)
        graph = rdflib.Graph()
        for row in splitDMCCRows(horribleString):
            subjectURI, statements, statementsMade = None, [], False
            for key, value in parseTokens(row):
                usedSlots.add(key)
                if key == context.identifyingKey and not subjectURI:
                    subjectURI = URIRef(context.uriPrefix + value)
                elif key in predicates and len(value) > 0:
                    statements.extend(predicates[key].characterize(value))
                    statementsMade = True
                elif key not in predicates:
                    unusedSlots.add(key)
            # DMCC is giving out empty rows: they have an Identifier number, but no values in any of the columns.
            # While we may wish to generate RDF for those (essentially just saying "Disease #31 exists", for example)
            # It means we need to update EDRN Portal code to handle them, which we can't do right now.
            # So just drop these.  TODO: Add them back, but update the EDRN Portal.
            if statementsMade:
                graph.add((subjectURI, rdflib.RDF.type, URIRef(context.typeURI)))
                for predicate, obj in statements:
                    graph.add((subjectURI, predicate, obj))
        if unusedSlots:
            _logger.warning('For %s the following slots were unused: %s', '/'.join(context.getPhysicalPath()),
                ', '.join(unusedSlots))
        _logger.info('And the used slots are %s', ', '.join(usedSlots))
        return graph
