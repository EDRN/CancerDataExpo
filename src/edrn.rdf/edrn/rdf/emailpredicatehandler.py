# encoding: utf-8
# Copyright 2012–2020 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

from .predicatehandler import ISimplePredicateHandler
from Acquisition import aq_inner
from email_validator import validate_email, EmailNotValidError
import rdflib, logging

_logger = logging.getLogger(__name__)


class IEmailPredicateHandler(ISimplePredicateHandler):
    '''A handler for DMCC web services that maps tokenized keys to mailto: URLs.'''


class EmailAsserter(object):
    '''Describes subjects using predicates with email references.'''

    def __init__(self, context):
        self.context = context

    def characterize(self, obj):
        context = aq_inner(self.context)
        characterizations = []
        for i in obj.split(', '):
            i = i.strip()
            if not i: continue
            try:
                validation = validate_email(i)
            except EmailNotValidError as ex:
                _logger.warning('Encountered an invalid email address «%s» which will not be put into RDF: %s', i, ex)
                continue
            target = 'mailto:' + validation.email
            characterizations.append((rdflib.URIRef(context.predicateURI), rdflib.URIRef(target)))
        return characterizations
