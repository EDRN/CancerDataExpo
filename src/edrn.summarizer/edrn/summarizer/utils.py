# encoding: utf-8
# Copyright 2008—2012 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

'''
EDRN Summarizer Service: utilities.
'''

import urllib.parse, re

# Why, why, why? DMCC, you so stupid!
# @yuliujpl: why is this even here?
DEFAULT_VERIFICATION_NUM = '0' * 40960

# URL schemes we consider "accessible"
# @yuliujpl: and this?
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
# @yuliujpl: and this?
_rowSep = re.compile(r'<recordNumber>[0-9]+</recordNumber><numberOfRecords>[0-9]+</numberOfRecords>'
    r'<ontologyVersion>[0-9.]+</ontologyVersion>')


# @yuliujpl: and this?
def splitDMCCRows(horribleString):
    '''Split a horrible DMCC string into rows.  Returns an iterable.'''
    i = _rowSep.split(horribleString)
    i = i[1:] # Skip first item, which is the empty string to the left of the first row separator
    return i


# converts csv file into dictionary, colkey and colvay determines which column
# is key and which column is value in the dictionary
# @yuliujpl: in the absence of coding standards, it's poite to adopt the style already in the file
# and not inject your own.
def csvToDict(file, colkey, colval):
    dict = {}
    with open(file) as f:
        for line in f:
            line_split = line.split(",")
            if line_split[colkey].strip() not in list(dict.keys()):
                dict[line_split[colkey].strip()] = []
            dict[line_split[colkey].strip()].append(line_split[colval].strip())
        # f.close() @yuliujpl: you don't need to close because you wrapped it in ``with``
    return dict


_biomutaRowSep = re.compile(',')


def splitBiomutaRows(horribleString):
    '''Split a horrible Biomuta string into rows.  Returns an iterable.'''
    i = _biomutaRowSep.split(horribleString)
    return i


# @yuliujpl: and this?
def validateAccessibleURL(s):
    '''Ensure the unicode string ``s`` is a valid URL and one whose scheme we deem "accessible".
    "Accessible" means that we reasonably expect our network APIs to handle locally- or network-
    retrieval resources.
    '''
    parts = urllib.parse.urlparse(s)
    return parts.scheme in ACCESSIBLE_SCHEMES


# @yuliujpl: and this?
START_TAG = re.compile(r'^<([-_A-Za-z0-9]+)>') # <Key>, saving "Key"


# @yuliujpl: and this?
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
