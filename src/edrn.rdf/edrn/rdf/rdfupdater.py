# encoding: utf-8
# Copyright 2012–2020 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

from .exceptions import NoGeneratorError, NoUpdateRequired, SourceNotActive
from .interfaces import IGraphGenerator
from Acquisition import aq_inner
from plone.dexterity.utils import createContentInContainer
from plone.namedfile.file import NamedBlobFile
from plone.app.contenttypes.interfaces import IFile
from rdflib import Graph
from rdflib.compare import isomorphic
from z3c.relationfield import RelationValue
from zope.app.intid.interfaces import IIntIds
from zope.component import getUtility
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent
import datetime, uuid, plone.api

RDF_XML_MIMETYPE = 'application/rdf+xml'
MAX_FILES = 15


class RDFUpdater(object):
    '''Update RDF.  Adapts RDF Sources and updates their content with a fresh RDF file, if necessary.'''
    def __init__(self, context):
        self.context = context
    def updateRDF(self):
        context = aq_inner(self.context)
        # If the RDF Source is inactive, we're done
        if not context.active:
            raise SourceNotActive(context)
        # Check if the RDF Source has an RDF Generator
        if not context.generator:
            raise NoGeneratorError(context)
        generator = context.generator.to_object
        generatorPath = '/'.join(generator.getPhysicalPath())
        # Adapt the generator to a graph generator, and get the graph in XML form.
        generator = IGraphGenerator(generator)
        graph = generator.generateGraph()
        # Is there an active file?
        if context.approvedFile:
            # Is it identical to what we just generated?
            current = Graph().parse(data=context.approvedFile.to_object.file.data)
            if isomorphic(graph, current):
                raise NoUpdateRequired(context)

        # Create a new file and set it active
        # TODO: Add validation steps here

        # ~~TODO~~ DONE: https://github.com/EDRN/CancerDataExpo/issues/6
        catalog = plone.api.portal.get_tool('portal_catalog')
        contents = catalog(
            path={'query': '/'.join(context.getPhysicalPath()), 'depth': 1},
            object_provides=IFile.__identifier__,
            sort_on='modified'
        )
        toDelete = len(contents) - MAX_FILES
        if toDelete > 0:
            plone.api.content.delete(objects=[i.getObject() for i in contents[0:toDelete]])

        serialized = graph.serialize(format='pretty-xml')
        timestamp = datetime.datetime.utcnow().isoformat()
        fileID = str(uuid.uuid4())
        newFile = createContentInContainer(
            context,
            'File',
            id=fileID,
            title='RDF {}'.format(timestamp),
            description='Generated at {} by {}'.format(timestamp, generatorPath),
            file=NamedBlobFile(serialized, filename=fileID + '.rdf', contentType=RDF_XML_MIMETYPE)
        )
        newFile.reindexObject()
        intIDs = getUtility(IIntIds)
        newFileID = intIDs.getId(newFile)
        context.approvedFile = RelationValue(newFileID)
        notify(ObjectModifiedEvent(context))
