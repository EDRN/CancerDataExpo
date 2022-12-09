# encoding: utf-8
# Copyright 2012 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

'''DMCC Committee RDF Generator. An RDF generator that describes EDRN committees using the DMCC's web services.
'''

from .rdfgenerator import IRDFGenerator
from .utils import get_suds_client
from .utils import parseTokens, DEFAULT_VERIFICATION_NUM
from .utils import splitDMCCRows
from .utils import validateAccessibleURL
from Acquisition import aq_inner
from edrn.rdf import _
from rdflib.term import URIRef, Literal
from zope import schema
import rdflib, logging

_logger = logging.getLogger(__name__)


# Map from DMCC key to name of field that contains the corresponding predicate URI in the committees SOAP operation
_committeePredicates = {
    'committee_name': 'titlePredicateURI',
    'committee_name_short': 'abbrevNamePredicateURI',
    'committee_type': 'committeeTypePredicateURI'
}

# Map from DMCC role names to the field that contains the corresponding predicate URI in the membership SOAP operation
_roleNamePredicates = {
    'Chair': 'chairPredicateURI',
    'Co-chair': 'coChairPredicateURI',
    'Consultant': 'consultantPredicateURI',
    'Member': 'memberPredicateURI'
}


class IDMCCCommitteeRDFGenerator(IRDFGenerator):
    '''DMCC Committee RDF Generator.'''
    webServiceURL = schema.TextLine(
        title=_('Web Service URL'),
        description=_('The Uniform Resource Locator to the DMCC SOAP web service.'),
        required=True,
        constraint=validateAccessibleURL,
    )
    committeeOperation = schema.TextLine(
        title=_('Committee Operation Name'),
        description=_('Name of the SOAP operation to invoke in order to retrieve committee information.'),
        required=True,
    )
    membershipOperation = schema.TextLine(
        title=_('Membership Operation Name'),
        description=_('Name of the SOAP operation to invoke in order to retrieve information about whose in what committees.'),
        required=True,
    )
    verificationNum = schema.TextLine(
        title=_('Verification Number String'),
        description=_('Vapid parameter to pass to the operation. A default will be used if unset.'),
        required=False,
    )
    typeURI = schema.TextLine(
        title=_('Type URI'),
        description=_('Uniform Resource Identifier naming the type of committee objects described by this generator.'),
        required=True,
    )
    uriPrefix = schema.TextLine(
        title=_('URI Prefix'),
        description=_('The Uniform Resource Identifier prepended to all committees described by this generator.'),
        required=True,
    )
    personPrefix = schema.TextLine(
        title=_('Person URI Prefix'),
        description=_('The Uniform Resource Identifier prepended to people described as members of committees.'),
        required=True,
    )
    titlePredicateURI = schema.TextLine(
        title=_('Title Predicate URI'),
        description=_('The Uniform Resource Identifier of the predicate that indicates titles (names) of committees.'),
        required=True,
    )
    abbrevNamePredicateURI = schema.TextLine(
        title=_('Abbreviated Name Predicate URI'),
        description=_('The Uniform Resource Identifier of the predicate that indicates abbreviated names of committees.'),
        required=True,
    )
    committeeTypePredicateURI = schema.TextLine(
        title=_('Abbreviated Name Predicate URI'),
        description=_('The Uniform Resource Identifier of the predicate that indicates the kinds of committees.'),
        required=True,
    )
    chairPredicateURI = schema.TextLine(
        title=_('Abbreviated Name Predicate URI'),
        description=_('The Uniform Resource Identifier of the predicate that indicates the chairpeople of committees.'),
        required=True,
    )
    coChairPredicateURI = schema.TextLine(
        title=_('Abbreviated Name Predicate URI'),
        description=_('The Uniform Resource Identifier of the predicate that indicates the co-chairpeople of committees.'),
        required=True,
    )
    consultantPredicateURI = schema.TextLine(
        title=_('Abbreviated Name Predicate URI'),
        description=_('The Uniform Resource Identifier of the predicate that indicates consultants to committees.'),
        required=True,
    )
    memberPredicateURI = schema.TextLine(
        title=_('Abbreviated Name Predicate URI'),
        description=_('The Uniform Resource Identifier of the predicate that indicates members of committees.'),
        required=True,
    )


class DMCCCommitteeGraphGenerator(object):
    '''A graph generator that produces statements about EDRN's committees using the DMCC's web service.'''
    def __init__(self, context):
        self.context = context
    def generateGraph(self):
        graph = rdflib.Graph()
        context = aq_inner(self.context)
        verificationNum = context.verificationNum if context.verificationNum else DEFAULT_VERIFICATION_NUM
        client = get_suds_client(context.webServiceURL, context)
        committees = getattr(client.service, context.committeeOperation)
        members = getattr(client.service, context.membershipOperation)
        unusedSlots = set()

        # Get the committees
        horribleCommittees = committees(verificationNum)
        for row in splitDMCCRows(horribleCommittees):
            subjectURI = None
            statements = {}
            for key, value in parseTokens(row):
                if key == 'Identifier' and not subjectURI:
                    subjectURI = URIRef(context.uriPrefix + value)
                    graph.add((subjectURI, rdflib.RDF.type, URIRef(context.typeURI)))
                elif key in _committeePredicates and len(value) > 0:
                    predicateURI = URIRef(getattr(context, _committeePredicates[key]))
                    statements[predicateURI] = Literal(value)
                else:
                    unusedSlots.add(key)
            for predicateURI, obj in statements.items():
                graph.add((subjectURI, predicateURI, obj))

        # Get the members of the committees
        horribleMembers = members(verificationNum)
        for row in splitDMCCRows(horribleMembers):
            subjectURI = predicateURI = obj = None
            for key, value in parseTokens(row):
                if not value: continue
                if key == 'committee_identifier':
                    subjectURI = URIRef(context.uriPrefix + value)
                elif key == 'Registered_Person_Identifer':
                    obj = URIRef(context.personPrefix + value)
                elif key == 'roleName':
                    if value not in _roleNamePredicates: continue
                    predicateURI = URIRef(getattr(context, _roleNamePredicates[value]))
            if subjectURI and predicateURI and obj:
                graph.add((subjectURI, predicateURI, obj))

        if unusedSlots:
            _logger.warning('For %s the following slots were unused: %s', '/'.join(context.getPhysicalPath()),
                ', '.join(unusedSlots))

        # C'est tout.
        return graph
