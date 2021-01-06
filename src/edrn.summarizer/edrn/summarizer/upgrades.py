# encoding: utf-8
# Copyright 2013–2015 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

from edrn.summarizer import DEFAULT_PROFILE


def nullUpgradeStep(setupTool):
    '''A null step when a profile upgrade requires no custom activity.'''


def upgrade3to4(setupTool):
    setupTool.runImportStepFromProfile(DEFAULT_PROFILE, 'typeinfo')
def upgrade4to5(setupTool):
    setupTool.runImportStepFromProfile(DEFAULT_PROFILE, 'typeinfo')

