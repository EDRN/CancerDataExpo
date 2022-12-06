# encoding: utf-8
# Copyright 2012 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

'''Specimen Json Generator. An Json generator that describes EDRN dataset statistics using dataset webservices.

NOTE: this is entirely obsolete and no longer supported. ERNE doesn't exist anymore.
Leaving this code in place for posterity.
'''

from Acquisition import aq_inner

from edrn.summarizer import _
from .summarizergenerator import ISummarizerGenerator
from .utils import validateAccessibleURL
from zope import schema
import urllib
import json

# Site identifier to ERNE identifier
SITES = {
    'http://edrn.nci.nih.gov/data/sites/167': 'https://telepath-d340.upmc.edu:7576/erne/prod',   # Pittsburgh
    'http://edrn.nci.nih.gov/data/sites/84':  'https://edrn.med.nyu.edu:7576/grid/prod',         # NYU
    'http://edrn.nci.nih.gov/data/sites/189': 'https://ucsf-97-101.ucsf.edu:7576/erne/prod',     # UCSF
    'http://edrn.nci.nih.gov/data/sites/202': 'https://erne.fccc.edu:7576/erne/prod',            # Fox Chase
    'http://edrn.nci.nih.gov/data/sites/203': 'https://profiler.med.cornell.edu:7576/erne/prod', # Beth Israel
    'http://edrn.nci.nih.gov/data/sites/408': 'https://erne.ucsd.edu:7576/erne/prod',            # UCSD
    'http://edrn.nci.nih.gov/data/sites/67':  'https://kepler.dartmouth.edu:7576/erne/prod',     # GLNE Dartmouth
    'http://edrn.nci.nih.gov/data/sites/70':  'https://edrn.partners.org:7576/erne/prod',        # Brigham & Women's
    'http://edrn.nci.nih.gov/data/sites/73':  'https://supergrover.uchsc.edu:7576/erne/prod',    # Colorado
    'http://edrn.nci.nih.gov/data/sites/80':  'https://edrn.creighton.edu:7576/erne/prod',       # Creighton Univ
    'http://edrn.nci.nih.gov/data/sites/81':  'https://surg-oodt.mc.duke.edu:7576/erne/prod',    # Duke Univ
    'http://edrn.nci.nih.gov/data/sites/83':  'https://162.129.227.245:7576/erne/prod',          # Johns Hopkins Urology
    'http://edrn.nci.nih.gov/data/sites/91':  'https://cdc-erne.cdc.gov:7576/erne/prod',         # CDC
    'http://edrn.nci.nih.gov/data/sites/593': 'https://cerc-vm1.fhcrc.org:7576/grid/prod',       # CERC at FHCRC
}

class ISpecimenSummarizerGenerator(ISummarizerGenerator):
    '''Specimen JSON Statistics Generator.'''
    queryDataSource = schema.TextLine(
        title=_('Specimens Web Service URL'),
        description=_('The Uniform Resource Locator to the DMCC Specimens web service.'),
        required=True,
        constraint=validateAccessibleURL,
    )

class SpecimenJsonGenerator(object):
    '''A Json generator that produces statements about EDRN's dataset statistics using the DMCC web service.'''
    def __init__(self, context):
        self.context = context

    def getSpecimens(self, erneID, erneWS):
        cdes = (
            'BASELINE_CANCER-CONFIRMATION_CODE', 'SPECIMEN_STORED_CODE', 'STUDY_PARTICIPANT_ID',
            'SPECIMEN_CONTACT-EMAIL_TEXT', 'SPECIMEN_AVAILABLE_CODE', 'SPECIMEN_TISSUE_ORGAN-SITE_CODE', 'STUDY_PROTOCOL_ID',
            'SPECIMEN_COLLECTED_CODE'
        )
        numCDES = len(cdes)
        queryStr = ' AND '.join(['RETURN = %s' % cde for cde in cdes])
        params = {'q': queryStr, 'url': erneID}
        con = None
        records, available, email = [], None, None
        print("HERE")
        print(erneWS)
        print(urllib.parse.urlencode(params))
        try:
            con = urllib.request.urlopen(erneWS, urllib.parse.urlencode(params))
            stats = {}
            for erneRecord in con.read().split('$'):
                fields = erneRecord.split('\t')
                if len(fields) != numCDES: continue # Avoid partial responses
                for i in range(0, numCDES):
                    fields[i] = fields[i].strip()
                cancerDiag, storage, ppt, email, available, organ, protocolID, collection = fields
                available = available == '1'
                # Avoid garbled responses
                if not cancerDiag or cancerDiag in ('9', 'unknown', 'blank') or not storage or storage in ('unknown', 'blank') \
                    or not ppt or ppt in ('unknown', 'blank') or not collection or collection in ('unknown', 'blank'):
                    continue
                # Group by {diagnosis: {collection: {storage type: {organ: {participant ID: specimen count}}}}}
                diagnoses = stats.get(cancerDiag, {})
                collectionTypes = diagnoses.get(collection, {})
                storageTypes = collectionTypes.get(storage, {})
                organs = storageTypes.get(organ, {})
                specimenCount = organs.get(ppt, 0)
                specimenCount += 1
                organs[ppt] = specimenCount
                storageTypes[organ] = organs
                collectionTypes[storage] = storageTypes
                diagnoses[collection] = collectionTypes
                stats[cancerDiag] = diagnoses
            for cancerDiag, collectionTypes in stats.items():
                withCancer = cancerDiag == '1'
                for collection, storageTypes in collectionTypes.items():
                    for storage, organs in storageTypes.items():
                        for organ, pptIDs in organs.items():
                            totalSpecimens = sum(pptIDs.values())
                            totalPpts = len(pptIDs)
                            cases, controls = totalPpts, 0 # FIXME: but how? No idea how to compute # cases or # controls from ERNE data
                            records.append(ERNESpecimenSummary(
                                storage, totalSpecimens,cases,controls,organ,withCancer,available,email,protocolID,collection
                            ))
            return records
        except urllib.error.HTTPError as ex:
            _logger.info('Ignoring failed attempt to get specimens from %s via %s: %r', erneID, erneWS, ex)
        try:
            con.close()
        except (IOError, AttributeError):
            pass
        return records

    def generateJson(self):
        context = aq_inner(self.context)
        erneWS = context.queryDataSource
        specimenCount = {}
        if erneWS:
            for siteID, erneID in SITES.items():
                specimenCount = self.getSpecimens(erneID, erneWS)

        # C'est tout.
        return json.dumps(specimenCount)
