# encoding: utf-8

from .utils import csvToDict
from plone.rest import Service
from ZODB import FileStorage, DB
from zope.interface import implementer
from zope.publisher.interfaces import IPublishTraverse
import mygene, json
import pickle, requests, os, urllib, re
import transaction


@implementer(IPublishTraverse)
class IDSearch(Service):
    def __init__(self, context, request):
        super(IDSearch, self).__init__(context, request)
        self.params = []

    def publishTraverse(self, request, name):
        self.params.append(name)
        return self
    def queryMyGene(self, query):
        results = None
        #number of times to retry connecting to mygene
        retries = 0
        while True:
            try:
                mg = mygene.MyGeneInfo()
                results = mg.query(query, fields="symbol,ensembl.gene,pdb,pfam,summary,taxid,type_of_gene,reporter,generif.pubmed,uniprot.Swiss-Prot,uniprot.TrEMBL,entrezgene,refseq.rna,refseq.protein,pathway.kegg,HGNC", species="human", size="1")
                break
            except requests.ConnectionError:
                #connection not working, retry
                retries += 1
                if retries < 5:
                    continue
                else:
                    print("MyGene not responding, try next symbol")
                    results = {}
                    results.pop("total",None)
                    results['info'] = "Not able to connect to mygene webservice"
                    break
        # check mygene
        if 'total' not in results:
            #debugging why total is not available in json
            results['success'] = False
            results['info'] = "No total in results for {}".format(query)
        else:
            results['success'] = True

        return results
    def basestring_check(self,query, dic):
        if query in dic:
            if not isinstance(dic[query], str):
                return dic[query]
            else:
                return [dic[query]]
    def packageMyGeneResp(self, response):
        newresponse = {}
        if response['success'] and response['total'] > 0:
            newresponse["uniprot"] = []
            newresponse["trembl"] = []
            newresponse["probe_id"] = []
            newresponse["pubmed"] = []
            newresponse["pdb"] = []
            newresponse["pfam"] = []
            newresponse["symbol"] = []
            newresponse["ensembl"] = []
            newresponse["entrezgene"] = []
            newresponse["refseqrna"] = []
            newresponse["refseqprotein"] = []
            newresponse["keggid"] = []
            newresponse["keggpathwayid"] = []
            newresponse["keggpathwayname"] = []
            newresponse["hgncid"] = []
            newresponse["summary"] = []
            newresponse["taxid"] = []
            newresponse["type_of_gene"] = []
            newresponse["gwas"] = []
            newresponse["genecard"] = []

            for hit in response['hits']:
                if 'ensembl' in hit:  #hits for ensembl database
                    newresponse['ensembl'] += self.basestring_check('gene', hit['ensembl'])
                if 'uniprot' in hit:    #hits for uniprot trembl and swiss-prot database
                    newresponse['uniprot'] += self.basestring_check('Swiss-Prot', hit['uniprot'])
                    newresponse['trembl'] += self.basestring_check('TrEMBL', hit['uniprot'])
                if 'refseq' in hit:    #hits for uniprot trembl and swiss-prot database
                    newresponse['refseqrna'] += self.basestring_check('rna', hit['refseq'])
                    newresponse['refseqprotein'] += self.basestring_check('protein', hit['refseq'])
                if 'pathway' in hit:
                    if 'kegg' in hit['pathway']:
                        if 'id' in hit['pathway']['kegg']:
                            newresponse["keggpathwayid"] += [hit['pathway']['kegg']['id']]
                        if 'name' in hit['pathway']['kegg']:
                            newresponse["keggpathwayname"] += [hit['pathway']['kegg']['name']]
                if 'generif' in hit:
                    pubmeds = []
                    for dic in hit["generif"]:
                        pubmeds.append(str(dic['pubmed']))
                    newresponse['pubmed'] += pubmeds
                if "reporter" in hit:
                    probeids = []
                    for key in hit["reporter"].keys():
                        if isinstance(hit["reporter"][key], str):
                            hit["reporter"][key] = [hit["reporter"][key]]
                        for item in hit["reporter"][key]:
                            if item.endswith("_at"):
                                probeids.append(item)

                    newresponse['probe_id'] += probeids

                if 'pdb' in hit:
                    newresponse['pdb'].append(hit['pdb'])
                if 'pfam' in hit:
                    newresponse['pfam'].append(hit['pfam'])
                if 'taxid' in hit:
                    newresponse['taxid'].append(hit['taxid'])
                if 'type_of_gene' in hit:
                    newresponse['type_of_gene'].append(hit['type_of_gene'])
                if 'summary' in hit:
                    newresponse['summary'].append(hit['summary'])
                if 'entrezgene' in hit:
                    newresponse['entrezgene'].append(hit['entrezgene'])
                    newresponse['keggid'].append(hit['entrezgene'])
                if 'HGNC' in hit:
                    newresponse['hgncid'].append(hit['HGNC'])
                if 'symbol' in hit:
                    newresponse['symbol'].append(hit['symbol'])
                    newresponse["gwas"].append(hit['symbol'])
                    newresponse["genecard"].append(hit['symbol'])

        return newresponse

    #pickle csv file into dictionaries so you don't have to create them everytime
    def pickleCSVDict(self, ifile, keycol, valcol, pickleExt):
      pickleref = ifile+pickleExt
      if os.path.isfile(pickleref):
        fref = open(pickleref, "rb")
        refDict = pickle.load(fref)
      else:
        refDict = csvToDict(ifile, keycol, valcol)
        pickle.dump(refDict, open(pickleref, "wb"))
      return refDict

    def getBiomartDicts(self):
        biomartfiles = ["pdb", "embl", "protein_id", "unigene", "uniprot_sptrembl", "uniprot_swissprot", "uniprot_genename", "uniparc", "hgnc_symbol"]

        dictionary = None
        biomartdicts = []
        biomartrevdicts = []
        for ifile in biomartfiles:
            dictionary = self.pickleCSVDict("edrn/summarizer/data/mart_"+ifile+".csv", 1, 0, ".pickle")
            biomartdicts.append(dictionary)
        for ifile in biomartfiles:
            dictionary = self.pickleCSVDict("edrn/summarizer/data/mart_"+ifile+".csv", 0, 1, ".rev.pickle")
            biomartrevdicts.append(dictionary)
        return biomartfiles, biomartdicts, biomartrevdicts    

    def queryBiomart(self, query):
        biomartfiles, biomartdicts, biomartrevdicts = self.getBiomartDicts()
        results = {}
        #check biomart
        for idx in range(0, len(biomartfiles)):
            if query in list(biomartdicts[idx].keys()):
                if biomartfiles[idx] not in results:
                  results[biomartfiles[idx]] = []
                results[biomartfiles[idx]] += biomartdicts[idx][query]
            if query in list(biomartrevdicts[idx].keys()):
                if "probeset_id" not in results:
                  results["probeset_id"] = []
                results["probeset_id"].append(biomartrevdicts[idx][query])
        return results
    def queryBioDBnet(self, query):
        biodbresp = {}
        #taxons can be used: human-9606
        url = 'http://biodbnet-abcc.ncifcrf.gov/webServices/rest.php/biodbnetRestApi.json'
        annotservice = '?method=db2db&format=row&input={}&inputValues={}&outputs={}&taxonId={}'
        typeservice = '?method=dbfind&inputValues={}&output=geneid&taxonId={}&format=row'
        taxon = "9606"
        output_types = 'genesymbol,ensemblgeneid,pdbid,affyid,pubmedid,uniprotaccession'
        types = urllib.request.urlopen(url+typeservice.format(query,taxon))
        typesresp = json.loads(types.read())
        querytype = ""
        if len(typesresp) > 0:
            if 'Input Type' in list(typesresp[0].keys()):
                querytype = typesresp[0]['Input Type']

        if querytype != "":
            annot = urllib.request.urlopen(url+annotservice.format(querytype, query,output_types,taxon))
            annotresp = json.loads(annot.read())
            if len(annotresp) > 0:
                biodbresp = annotresp[0]
                
        return biodbresp

    def replaceBDBwithMyGene(self, bdbresp, packagedmygene):
        bdbMygeneMapping = {
                "symbol":"Gene Symbol",
                "ensembl":"Ensembl Gene ID",
                "pdb":"PDB ID",
                "probe_id":"Affy ID",
                "pubmed":"PubMed ID",
                "uniprot":"UniProt Accession"
            }
        for key in bdbMygeneMapping.keys():
            if bdbresp[bdbMygeneMapping[key]] != "-":
                packagedmygene[key] = re.compile(r'\/\/+').split(bdbresp[bdbMygeneMapping[key]])

        return packagedmygene

    def addLinkAnnotation(self, geneinfo):
        urlMapping = {
                "symbol":"http://www.genecards.org/cgi-bin/carddisp.pl?gene=",
                "ensembl":"http://uswest.ensembl.org/Homo_sapiens/Gene/Summary?g=",
                "pdb":"http://www.rcsb.org/pdb/explore.do?structureId=",
                "pubmed":"http://www.ncbi.nlm.nih.gov/pubmed/",
                "uniprot":"http://www.uniprot.org/uniprot/",
                "trembl":"http://www.uniprot.org/uniprot/",
                "gwas":"https://www.ebi.ac.uk/gwas/search?query=",
                "pfam":"http://pfam.xfam.org/family/",
                "genecard":"http://www.genecards.org/cgi-bin/carddisp.pl?gene=",
                "hgncid":"http://www.genenames.org/cgi-bin/gene_symbol_report?q=data/hgnc_data.php&hgnc_id=",
                "refseqprotein":"https://www.ncbi.nlm.nih.gov/protein/",
                "refseqrna":"https://www.ncbi.nlm.nih.gov/nuccore/",
                "entrezgene":"https://www.ncbi.nlm.nih.gov/gene/",
                "keggpathwayid":"http://www.genome.jp/dbget-bin/www_bget?",
                "keggid":"http://www.genome.jp/dbget-bin/www_bget?hsa:",
            }
        titleMapping = {
                "symbol":"GeneCards",
                "ensembl":"Ensembl",
                "pdb":"PDB",
                "pubmed":"PubMed",
                "uniprot":"SwissProt",
                "trembl":"Trembl",
                "probe_id":"Probe ID",
                "gwas":"GWAS Catalog",
                "pfam":"Pfam",
                "genecard":"Genecard",
                "hgncid":"Genenames",
                "refseqprotein":"Protein Refseq",
                "refseqrna":"DNA/RNA Refseq",
                "entrezgene":"Entrez Gene",
                "keggpathwayid":"KEGG Pathway",
                "keggid":"KEGG Pathway"
            }
        newgeneinfo = {}
        for key in geneinfo.keys():

            newgeneinfo[key] = {}
            if key in list(titleMapping.keys()):
                newgeneinfo[key]['Title'] = titleMapping[key]

            uriprefix = ""
            newgeneinfo[key]['Items'] = []
            newgeneinfo[key]['Labels'] = []
            if key in list(urlMapping.keys()):
                uriprefix = urlMapping[key]
            for item in geneinfo[key]:
                if not isinstance(item, str):
                    for i in item:
                        newgeneinfo[key]['Labels'].append(str(i))
                        newgeneinfo[key]['Items'].append(uriprefix + str(i))
                else:
                    newgeneinfo[key]['Labels'].append(str(item))
                    newgeneinfo[key]['Items'].append(uriprefix + str(item))

        return newgeneinfo
    def closedb(self):
        self.connection.close()
        self.biomarkerdb.close()
        self.storage.close()
    def opendb(self):
        self.storage = FileStorage.FileStorage('biomarkerids.fs')
        self.biomarkerdb = DB(self.storage)
        self.connection = self.biomarkerdb.open()
        self.biomarkerids = self.connection.root()
    def render(self):
        if len(self.params) > 0:
            id = self.params[0]
            final_ids = None
            self.opendb()
            try:
                if id in self.biomarkerids:
                    if len(self.biomarkerids[id])> 0:
                        final_ids = self.biomarkerids[id]
                if not final_ids:
                    mygeneresults = self.queryMyGene(id)
                    tempids = self.packageMyGeneResp(mygeneresults)
                    #disabled because biomart is currently under maintenance
                    #biomartresults = self.queryBiomart(id)
                    #disabled until BioDBnet is updated with the latest alias information
                    #bdbresp = self.queryBioDBnet(id)
                    #if len(bdbresp.keys()) > 0:
                    #    tempids = self.replaceBDBwithMyGene(bdbresp, tempids)
                    final_ids = self.addLinkAnnotation(tempids)
                    self.biomarkerids[id] = final_ids
                    transaction.commit()
            except:
                self.closedb()
            self.closedb()
            return final_ids

        else:
            return {'Error': "No query inputed. Please use idsearch/query to get info on your prospective id"}
