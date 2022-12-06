# encoding: utf-8
# Copyright 2012 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

'''External Resources Json Generator. An Json generator that describes EDRN external resource statistics using Biomarker webservices.
'''

from Acquisition import aq_inner
from edrn.summarizer import _

from .summarizergenerator import ISummarizerGenerator
from rdflib.term import URIRef
from rdflib.parser import URLInputSource
from rdflib import ConjunctiveGraph
from .utils import validateAccessibleURL
from zope import schema
from zope.component import queryUtility
from plone.i18n.normalizer.interfaces import IIDNormalizer
import json, re

_typeURI                                 = URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type')
_bmRefResourceURI                        = URIRef('http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#referencesResource')
_biomarkerPredicateURI                   = URIRef('http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#Biomarker')
_isPanelPredicateURI                     = URIRef('http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#IsPanel')
_bmTitlePredicateURI                     = URIRef('http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#Title')
_hgncPredicateURI                        = URIRef('http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#HgncName')

EXT_REF = {
    "genenames": {"link":"http://www.genenames.org/cgi-bin/search?search_type=all&search={}", "description":"HGNC entry for {} from Genenames"},
    "geoprofile": {"link":'http://www.ncbi.nlm.nih.gov/geoprofiles/?term={}[Gene Symbol]+Homo Sapiens[Organism]',"description":"Human GEO Profiles for {} from NCBI GEO Profiles"},
    "geodataset": {"link":'http://www.ncbi.nlm.nih.gov/gds/?term={}[Gene Symbol]+Homo Sapiens[Organism]', "description":"Human Geo Datasets containing term {} from NCBI GEO Datasets"},
    "resentrez": {"link":'http://www.ncbi.nlm.nih.gov/gquery/?term={}[Gene Symbol]+Homo Sapiens[Organism]', "description":"Entrez entry for {} all NCBI Databasese"},
    "ressnp": {"link":'http://www.ncbi.nlm.nih.gov/snp/?term={}[Gene Symbol]+Homo Sapiens[Organism]', "description":"Human Single Nucleotide Polymorphisms info for {}"},
    "resgene": {"link":'http://www.ncbi.nlm.nih.gov/gene/?term={}[Gene]+Homo Sapiens[Organism]', "description":"Human Gene(s) with '{}' as Gene Name/Alias"},
    "generef": {"link":'http://www.ncbi.nlm.nih.gov/nuccore/?term={}[Gene Name]+Homo Sapiens[Organism]+RefSeqGene[Keyword]', "description":"Human Gene RefSeq for {} from NCBI"},
    "genecard": {"link":'http://www.genecards.org/cgi-bin/carddisp.pl?gene={}', "description":"GeneCards entry for human {}"},
    "gwasref": {"link":'http://www.gwascentral.org/generegion/phenotypes?q={}&t=ZERO&m=all&page=1&format=html', "description": "GWAS Study Datasets containing gene {} from GWAS"}
}

EXT_DESC = {
    "uniprotref": {"description":"UniProtKB/Swiss-Prot entry for {} from Uniprot"},
    "keggref": {"description":"KEGG entry for {} from Genome.jp"},
    "fdaref": {"description":"FDA web page describing approval of {}"},
    "protref": {"description":"Human Protein RefSeq for {} from NCBI"}
}


class IExtResourceSummarizerGenerator(ISummarizerGenerator):
    '''DMCC Committee RDF Generator.'''
    biomarkerURL = schema.TextLine(
        title=_('Biomarker Web Service URL'),
        description=_('The Uniform Resource Locator to the BMDB SOAP biomarker web service.'),
        required=True,
        constraint=validateAccessibleURL,
    )

class ExtResourceJsonGenerator(object):
    '''A Json generator that produces statements about EDRN's biomarker external resource statistics using the BMDB's web service.'''
    def __init__(self, context):
        self.context = context

    def _parseRDF(self, graph):
        '''Parse the statements in graph into a mapping {u→{p→o}} where u is a
        resource URI, p is a predicate URI, and o is a list of objects which
        may be literals or URI references.'''
        statements = {}
        for s, p, o in graph:
            if s not in statements:
                statements[s] = {}
            predicates = statements[s]
            if p not in predicates:
                predicates[p] = []
            predicates[p].append(o)
        return statements


    def addExternaResourcesInformation(self, bmId, predicates):
        #This function is a temporary workaround until we generate the knowledge rdfs for these external resources
        extres_gene = []
        extres_prot = []
        added_ref    = []
        other_ref    = []
        for res in predicates.get(_bmRefResourceURI, []):
            if "genenames" in str(res) and "hgnc_data" in str(res) and "hgnc_id" in str(res):
                added_ref.append("genenames")
            elif "http://www.genome.jp/dbget-bin/www_bget" in str(res):
                extres_gene.append({"link":str(res),"description":EXT_DESC["keggref"]["description"].format(bmId)})
            elif "http://www.uniprot.org/uniprot" in str(res):
                extres_prot.append({"link":str(res),"description":EXT_DESC["uniprotref"]["description"].format(bmId)})
            elif "http://www.ncbi.nlm.nih.gov/protein" in str(res):
                extres_prot.append({"link":str(res),"description":EXT_DESC["protref"]["description"].format(bmId)})
            elif "http://www.fda.gov" in str(res):
                extres_prot.append({"link":str(res),"description":EXT_DESC["fdaref"]["description"].format(bmId)})
            elif "http://www.genecards.org/cgi-bin/" in str(res):
                added_ref.append("genecards")
            else:
                description = re.sub(r'^.*www\.', "", str(res))
                description = re.sub(r'\..*', "", description)
                other_ref.append({"link":str(res), "description": description})

        for key in EXT_REF:
            if key not in added_ref:
                extres_gene.append({"link":EXT_REF[key]["link"].format(bmId), "description":EXT_REF[key]["description"].format(bmId)})

        return extres_gene, extres_prot, other_ref

    def generateJson(self):
        #graph = rdflib.Graph()
        context = aq_inner(self.context)
        rdfDataSource= context.biomarkerURL
        if not rdfDataSource:
            raise RDFIngestException(_('This generator folder lacks one or both of its RDF source URLs.'))
        normalizerFunction = queryUtility(IIDNormalizer).normalize
        graph = ConjunctiveGraph()
        graph.parse(URLInputSource(rdfDataSource), format='xml')
        statements = self._parseRDF(graph)
        
        OtherRef = {}
        ProtRef  = {}
        GeneRef  = {}

        for uri, predicates in statements.items():
            try:
                typeURI = predicates[_typeURI][0]
                if typeURI != _biomarkerPredicateURI:
                    continue
                isPanel = bool(int(predicates[_isPanelPredicateURI][0]))
                title = str(predicates[_bmTitlePredicateURI][0])
                hgnc = predicates[_hgncPredicateURI][0] if _hgncPredicateURI in predicates else None

                if hgnc is not None:
                    hgnc = hgnc.strip()
                objID = hgnc if hgnc else normalizerFunction(title)

                if not isPanel:
                    #add external resource information
                    gene_info, prot_info, other_info = self.addExternaResourcesInformation(objID, predicates)
                    ProtRef[objID]  = prot_info
                    GeneRef[objID]  = gene_info
                    OtherRef[objID] = other_info

            except KeyError:
                pass

        jsondata = {"prot":ProtRef, "gene": GeneRef, "other":OtherRef}

        # C'est tout.
        return json.dumps(jsondata)
