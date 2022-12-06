# encoding: utf-8
# Copyright 2012 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

from .exceptions import NoGeneratorError, NoUpdateRequired, SourceNotActive, UnknownGeneratorError
from .interfaces import IJsonGenerator, IGraphGenerator
from Acquisition import aq_inner
from plone.dexterity.utils import createContentInContainer
from plone.namedfile.file import NamedBlobFile
from rdflib import Graph
from rdflib.compare import isomorphic
from z3c.relationfield import RelationValue
from zope.app.intid.interfaces import IIntIds
from zope.component import getUtility
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent
import datetime, json, uuid

SUMMARIZER_XML_MIMETYPE = 'application/rdf+xml'
SUMMARIZER_JSON_MIMETYPE = 'application/json'


class SummarizerUpdater(object):
    '''Update Summarizer.  Adapts Summarizer Sources and updates their content with a fresh Summarizer file, if necessary.'''
    def __init__(self, context):
        self.context = context
    def updateSummary(self):
        context = aq_inner(self.context)
        # If the Summarizer Source is inactive, we're done
        if not context.active:
            raise SourceNotActive(context)
        # Check if the Summarizer Source has an Summarizer Generator
        if not context.generator:
            raise NoGeneratorError(context)
        generator = context.generator.to_object
        generatorPath = '/'.join(generator.getPhysicalPath())
        # Adapt the generator to a graph generator, and get the graph in XML form.
        serialized = mimetype = None
        if generator.datatype == 'json':
            adapter = IJsonGenerator(generator)
            serialized = adapter.generateJson()
            json_result = json.loads(serialized)
            mimetype = SUMMARIZER_JSON_MIMETYPE

            # Is there an active file?
            if context.approvedFile:
                # Is it identical to what we just generated?
                current = json.loads(context.approvedFile.to_object.file.data)
                if sorted(json_result.items()) == sorted(current.items()):
                    raise NoUpdateRequired(context)

        elif generator.datatype == 'rdf':
            adapter = IGraphGenerator(generator)
            rdf = adapter.generateGraph()
            serialized = rdf.serialize()
            mimetype = SUMMARIZER_XML_MIMETYPE

            # Is there an active file?
            if context.approvedFile:
                # Is it identical to what we just generated?
                current = Graph().parse(data=context.approvedFile.to_object.file.data)
                if isomorphic(rdf, current):
                    raise NoUpdateRequired(context)
        else:
            raise UnknownGeneratorError(context)

        # Create a new file and set it active
        # TODO: Add validation steps here

        timestamp = datetime.datetime.utcnow().isoformat()
        fileID = str(uuid.uuid4())
        newFile = createContentInContainer(
            context,
            'File',
            id=fileID,
            title='Summary {}'.format(timestamp),
            description='Generated at {} by {}'.format(timestamp, generatorPath),
            file=NamedBlobFile(serialized, filename=fileID + '.' + generator.datatype, contentType=mimetype)
        )
        newFile.reindexObject()
        intIDs = getUtility(IIntIds)
        newFileID = intIDs.getId(newFile)
        context.approvedFile = RelationValue(newFileID)
        notify(ObjectModifiedEvent(context))
