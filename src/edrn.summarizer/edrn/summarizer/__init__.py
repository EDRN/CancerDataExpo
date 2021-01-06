# encoding: utf-8
# Copyright 2008–2012 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

'''EDRN Sumarizer Service.
'''

from zope.i18nmessageid import MessageFactory

PACKAGE_NAME    = __name__
DEFAULT_PROFILE = 'profile-' + PACKAGE_NAME + ':default'
_               = MessageFactory(PACKAGE_NAME)
ENTREZ_TOOL     = 'edrn-portal'
ENTREZ_EMAIL    = 'sean.kelly@nih.gov'
