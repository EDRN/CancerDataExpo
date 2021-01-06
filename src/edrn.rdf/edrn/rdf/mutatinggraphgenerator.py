# encoding: utf-8

'''A "mutating" RDF generator, used just for testing to produce ever-changing graphs.
'''


from .rdfgenerator import IRDFGenerator
import rdflib, uuid


class IMutatingRDFGenerator(IRDFGenerator):
    '''A mutating RDF generator that produces ever-changing statements.'''


class MutatingGraphGenerator(object):
    '''A statement graph generator that produces ever-changing graphs.'''

    _typeURI = rdflib.URIRef('urn:edrn:types:MutatingTestObject')

    def __init__(self, context):
        self.context = context
    def generateGraph(self):
        '''Generate always-different graphs.'''
        graph = rdflib.Graph()
        identifier = str(uuid.uuid4())
        subjectURI = rdflib.URIRef(f'urn:edrn:objects:MutatingTestObjects:{identifier}')
        graph.add((subjectURI, rdflib.RDF.type, self._typeURI))
        graph.add((subjectURI, rdflib.namespace.DCTERMS.title, rdflib.Literal(f'Mutating Test Object «{identifier}»')))
        return graph
