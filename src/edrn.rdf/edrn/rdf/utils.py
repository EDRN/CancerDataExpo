# encoding: utf-8
# Copyright 2008—2012 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

'''
EDRN RDF Service: utilities.
'''

from suds.client import Client
import urllib, re

# Why, why, why? DMCC, this is utterly pointless.
DEFAULT_VERIFICATION_NUM = '0' * 40960


# URL schemes we consider "accessible"
ACCESSIBLE_SCHEMES = frozenset((
    'file',
    'ftp',
    'gopher',
    'http',
    'https',
    'ldap',
    'ldaps',
    'news',
    'nntp',
    'prospero',
    'telnet',
    'wais',
    'testscheme', # Used during testing.
))

# DMCC no longer separates rows by '!!'. Yay.
_rowSep = re.compile(
    r'<recordNumber>[0-9]+</recordNumber><numberOfRecords>[0-9]+</numberOfRecords>'
    r'<ontologyVersion>[0-9.]+</ontologyVersion>'
)


def splitDMCCRows(horribleString):
    '''Split a horrible DMCC string into rows.  Returns an iterable.'''
    i = _rowSep.split(horribleString)
    i = i[1:]  # Skip first item, which is the empty string to the left of the first row separator
    return i


def validateAccessibleURL(s):
    '''Ensure the unicode string ``s`` is a valid URL and one whose scheme we deem "accessible".
    "Accessible" means that we reasonably expect our network APIs to handle locally- or network-
    retrieval resources.
    '''
    parts = urllib.parse.urlparse(s)
    return parts.scheme in ACCESSIBLE_SCHEMES


START_TAG = re.compile(r'^<([-_A-Za-z0-9]+)>')  # <Key>, saving "Key"


def parseTokens(s):
    '''Parse DMCC-style tokenized key-value pairs in the string ``s``.'''
    if not isinstance(s, str): raise TypeError('Token parsing works on strings only')
    s = s.strip()
    while len(s) > 0:
        match = START_TAG.match(s)
        if not match: raise ValueError('Missing start element')
        key = match.group(1)
        s = s[match.end():]
        match = re.match(r'^(.*)</' + key + '>', s, re.DOTALL)
        if not match: raise ValueError('Unterminated <%s> element' % key)
        value = match.group(1)
        s = s[match.end():].lstrip()
        yield key, value


# The following comes from z3c.suds, an abandoned project that caches suds client connections
# in the context of a Zope application; see https://pypi.org/project/z3c.suds/
# The ZPL 1.0 applies.

try:
    from zope.component.hooks import getSite
    _get_default_context = getSite
except ImportError:
    try:
        from zope.app.component.hooks import getSite
        _get_default_context = getSite
    except ImportError:
        _get_default_context = lambda: None


def get_suds_client(wsdl_uri, context=None):
    if context is None:
        context = _get_default_context()

    if context is None:
        # no cache
        client = Client(wsdl_uri)
    else:
        jar = getattr(context, '_p_jar', None)
        oid = getattr(context, '_p_oid', None)
        if jar is None or oid is None:
            # object is not persistent or is not yet associated with a
            # connection
            cache = context._v_suds_client_cache = {}
        else:
            cache = getattr(jar, 'foreign_connections', None)
            if cache is None:
                cache = jar.foreign_connections = {}

        cache_key = 'suds_%s' % wsdl_uri
        client = cache.get(cache_key)
        if client is None:
            client = cache[cache_key] = Client(wsdl_uri)

    return client
