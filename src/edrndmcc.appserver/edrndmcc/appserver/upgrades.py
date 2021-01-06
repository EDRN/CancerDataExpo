# encoding: utf-8
# Copyright 2016 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

import plone.api


def upgrade2to3(setupTool):
    qi = plone.api.portal.get_tool('portal_quickinstaller')
    qi.installProduct('edrn.summarizer')
def upgrade3to4(setupTool):
    qi = plone.api.portal.get_tool('portal_quickinstaller')
    qi.upgradeProduct('edrn.summarizer')
