# encoding: utf-8
# Copyright 2023 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

'''Member group RDF generator.'''

from .rdfgenerator import IRDFGenerator
from .utils import parseTokens, validateAccessibleURL, DEFAULT_VERIFICATION_NUM, splitDMCCRows, get_suds_client
from Acquisition import aq_inner
from edrn.rdf import _
from rdflib.term import URIRef, Literal
from zope import schema
from dataclasses import dataclass
from urllib.parse import quote
import rdflib, logging

_logger = logging.getLogger(__name__)


# Predicate URIs
_member_site_uri  = URIRef('urn:edrn:predicates:member_site')
_site_ref_uri     = URIRef('urn:edrn:predicates:site')
_person_ref_uri   = URIRef('urn:edrn:predicates:person')
_organ_name_uri   = URIRef('urn:edrn:predicates:organ_name')
_group_number_uri = URIRef('urn:edrn:predicates:group_number')
_sort_order_uri   = URIRef('urn:edrn:predicates:sort_order')
_member_type_uri  = URIRef('urn:edrn:predicates:member_type')
_role_uri         = URIRef('urn:edrn:predicates:role')


# Type URIs
_org_group_type_uri = URIRef('urn:edrn:types:org_group')
_site_type_uri      = URIRef('urn:edrn:types:site')


# URI prefixes
_org_group_prefix  = 'urn:edrn:objects:org_group:'
_site_group_prefix = 'urn:edrn:objects:site:'  
_site_prefix       = 'http://edrn.nci.nih.gov/data/sites/'
_person_perfix     = 'http://edrn.nci.nih.gov/data/registered-person/'


class IMemberGroupRDFGenerator(IRDFGenerator):
    '''Generator for RDF using data from the MemberGroup API'''
    web_service_url = schema.TextLine(
        title=_('Web Service URL'),
        description=_('The Uniform Resource Locator to the DMCC SOAP web service.'),
        required=True,
        constraint=validateAccessibleURL,
    )
    verification_num = schema.TextLine(
        title=_('Verification Number String'),
        description=_('Vapid parameter to pass to the operation. A default will be used if unset.'),
        required=False,
    )


@dataclass(frozen=True)
class _Site:
    '''Attributes of a site that's a member of organizational group.'''
    site_id: str
    staff_id: str
    organ: str
    group_number: str
    sort_order: str
    member_types: str
    role: str

    def uriref(self):
        '''Return this site's subject URI.'''
        f = f'{self.site_id}:{self.staff_id}:'
        f += f'{quote(self.organ)}:{self.group_number}:{self.sort_order}:'
        f += f'{quote(self.member_types)}:{quote(self.role)}'
        return URIRef(_site_group_prefix + f)

    def add_to_graph(self, graph):
        '''Describe this site in the given ``graph``.'''
        subject = self.uriref()
        graph.add((subject, rdflib.RDF.type, _site_type_uri))
        graph.add((subject, _site_ref_uri, URIRef(_site_prefix + self.site_id)))
        graph.add((subject, _person_ref_uri, URIRef(_person_perfix + self.staff_id)))
        graph.add((subject, _organ_name_uri, Literal(self.organ)))
        graph.add((subject, _group_number_uri, Literal(self.group_number)))
        graph.add((subject, _sort_order_uri, Literal(self.sort_order)))
        graph.add((subject, _member_type_uri, Literal(self.member_types)))
        graph.add((subject, _role_uri, Literal(self.role)))


class MemberGroupGraphGenerator(object):
    '''A graph generator that produces statements about EDRN's organizational groups and their site members.'''

    def __init__(self, context):
        self.context = context

    def generateGraph(self):
        context = aq_inner(self.context)
        verification_num = context.verificationNum if context.verification_num else DEFAULT_VERIFICATION_NUM
        client = get_suds_client(context.web_service_url, context)
        member_group_func = getattr(client.service, 'MemberGroup')
        horrible_member_groups = member_group_func(verification_num)

        # Start off with a mapping of org groups to sites and a set of unique sites
        org_units, unique_sites = {}, set()

        # For each row given in the horrible string returned from SOAP:
        for row in splitDMCCRows(horrible_member_groups):
            org_name = None
            slots = {}
            for key, value in parseTokens(row):
                # Look for the MemberGroup key and save that as the org name. The rest of the keys are slots
                # for the site being described.
                if key == 'MemberGroup':
                    org_name = value
                else:
                    slots[key] = value

            # Make a site out of those slots and save it in unique_sites; since it's a frozen
            # dataclass and going into a set, it won't matter how many times the DMCC repeats the
            # same site info.
            site = _Site(
                slots['siteid'].strip(),
                slots['staffid'].strip(),
                slots['OrganGroup'].strip(),
                slots['OrganGroupSet'].strip(),
                slots['SortOrder'].strip(),
                slots['MemberType'].strip(),
                slots['RoleName'].strip()
            )
            if site not in unique_sites:
                unique_sites.add(site)

            # Now add that site to the organizational grouping
            sites = org_units.get(org_name, set())
            sites.add(site)
            org_units[org_name] = sites

        # First, add all the sites to the graph
        graph = rdflib.Graph()
        for site in unique_sites:
            site.add_to_graph(graph)

        # Now add each org unit, referencing those sites described above
        for org_name, sites in org_units.items():
            org_subject = URIRef(_org_group_prefix + quote(org_name))
            graph.add((org_subject, rdflib.RDF.type, _org_group_type_uri))
            graph.add((org_subject, rdflib.namespace.DCTERMS.title, Literal(org_name)))
            for site in sites:
                site_subject = site.uriref()
                graph.add((org_subject, _member_site_uri, site_subject))

        return graph
