import sys
sys.path.append('/Users/pati13/Downloads/')
import urllib.request as RE
import time
import os
from parse.MetabolomicsData import MetabolomicsData
import zipfile
from rdflib import URIRef,Graph
import rdflib.namespace
from rdflib.namespace import RDF, FOAF,RDFS,DC,DCTERMS
from builtins import str
from rampConfig.RampConfig import RampConfig

from writeToSQL import writeToSQL

class WikipathwaysRDF(MetabolomicsData):
    
    def __init__(self, resConfig):
        super().__init__()
        
        self.resourceConfig = resConfig
        
        # key: ID for metabolites Value: Common Name (the only name in this database)
        self.metaboliteCommonName = dict()
        #key: ID for pathway, Value: pathway name
        self.pathwayDictionary = dict()
        
        #key: ID for pathway, category: various categories such as cellular process, metabolic process 
        self.pathwayCategory = dict()
        
        #key: gene, value: gene mapping
        self.geneInfoDictionary = dict()
        
        #key: metabolite, value: metabolite mapping
        self.metaboliteIDDictionary = dict()
        
        #key: pathwayID, value: list of genes
        self.pathwaysWithGenesDictionary = dict()
        
        #key: pathwayId, value: list of metabolites
        self.pathwaysWithMetabolitesDictionary = dict()
        
        #empty for wikiPathways
        self.metabolitesWithSynonymsDictionary = dict()
        
        #only not empty when a catalyzed class exists 
        #empty
        self.metabolitesLinkedToGenes = dict()
        
        #key: metabolite, value: list of pathways
        self.metabolitesWithPathwaysDictionary = dict()
        
        #key: current pathway, value: list of pathways linked to this pathway
        self.pathwayOntology = dict()
        
        #stays empty for this class
        self.biofluidLocation = dict()
        
        #stays empty for this class
        self.biofluid = dict()
        
        #stays empty for this class
        self.cellularLocation = dict()
        
        #stays empty for this class
        self.cellular = dict()
        
        #stays empty
        self.exoEndoDictionary = dict()
        self.exoEndo =dict()
        #tissue location stay empty
        self.tissue = dict()
        self.tissueLocation = dict()
        
        self.lipidMapsIdCounterDict = dict()
        
        
    def getEverything(self,writeToFile = False):
        '''
        This function pack all functions in this class together, running this function will parse all data 
        we would like to have.
        - param bool writeToFile if true, write all dictionary to misc/output/wikipathwayRDF/
        '''
        self.getDatabaseFile()
        self.getIDMapingWithPathways()
        if writeToFile:
            self.write_myself_files('wikipathwayRDF')
            
        print("distinct lipidmap ids = " + str(len(self.lipidMapsIdCounterDict)))
            
    def getDatabaseFile(self):
        '''
        Downloaded wikipathway file from the given url
        The url is from current(latest) version of wikipathways
        if the file name is wrong, go the the url to check if the file is updated
        '''
        
        wikiConf = self.resourceConfig.getConfig("wiki_pathways_mets_genes")
        
        url = wikiConf.sourceURL
        filename = wikiConf.sourceFileName
        path = wikiConf.localDir
        
        self.check_path(path)
        existed = os.listdir(path)
        if filename not in existed:
            #print(path + filename)
            self.download_files(url, path + filename)
            with zipfile.ZipFile(path+filename,'r') as zip_ref:
                zip_ref.extractall(path)
        else:
            print('Already downloaded Wiki ...')
    
    def _getAllRDFTypes(self):
        '''
        Find all possible types form rdf files
        return:
        All namespaces for the rdf files:
        ('rdfs', rdflib.term.URIRef('http://www.w3.org/2000/01/rdf-schema#'))
        ('dc', rdflib.term.URIRef('http://purl.org/dc/elements/1.1/'))
        ('biopax', rdflib.term.URIRef('http://www.biopax.org/release/biopax-level3.owl#'))
        ('foaf', rdflib.term.URIRef('http://xmlns.com/foaf/0.1/'))
        ('dcterms', rdflib.term.URIRef('http://purl.org/dc/terms/'))
        ('wp', rdflib.term.URIRef('http://vocabularies.wikipathways.org/wp#'))
        ('void', rdflib.term.URIRef('http://rdfs.org/ns/void#'))
        ('xml', rdflib.term.URIRef('http://www.w3.org/XML/1998/namespace'))
        ('gpml', rdflib.term.URIRef('http://vocabularies.wikipathways.org/gpml#'))
        ('prov', rdflib.term.URIRef('http://www.w3.org/ns/prov#'))
        ('wprdf', rdflib.term.URIRef('http://rdf.wikipathways.org/'))
        ('rdf', rdflib.term.URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#'))
        ('skos', rdflib.term.URIRef('http://www.w3.org/2004/02/skos/core#'))
        ('freq', rdflib.term.URIRef('http://purl.org/cld/freq/'))
        ('xsd', rdflib.term.URIRef('http://www.w3.org/2001/XMLSchema#'))
        ('pav', rdflib.term.URIRef('http://purl.org/pav/'))
        '''
        rdftype = set()
        path = '../misc/data/wikipathwaysRDF/wp/'
        listoffiles = os.listdir(path)
        #print(listoffiles)
        listoffiles.sort()
        for each in listoffiles:
            #print(each)
            g = Graph()
            g.parse(path+each,format = 'n3')
            if not self.isHumanPathway(g):
                print(f'skipping {each} as non-human')
                continue
            #print('length of graph: {}'.format(len(g)))
            for s,p,o in g.triples((None, RDF.type,None)):
                #print('---------------------------')
                #print('Subject: {} \nPredicate: {}\nObject: {}'.format(s,p,o))
                #print('---------------------------')
                obj = o[o.find('wp#') + 3:]
                if obj == -1:
                    raise ValueError('Wrong object value from rdf')
                if obj not in rdftype:
                    rdftype.add(obj)
                #time.sleep(1)
        
        #print(rdftype)
        return(rdftype)
    '''
    All possible types 
    {'Metabolite', 'TranscriptionTranslation', 'DataNode', 'Stimulation', 
    'Catalysis', 'DirectedInteraction', 'Pathway', 'Conversion', 'ComplexBinding'
    , 'Inhibition', 'Protein', 'tp://www.w3.org/2004/02/skos/core#Collection', 
    'Rna', 'Interaction', 'Binding', 'PublicationReference', 'GeneProduct', 'Complex'}        
    '''
    def getPathwayInfoFromGraph(self,g,this_pathway):
        for s,p,o in g.triples((None,DC.title,None)):
            '''
                print('---------------------------')
                print('Subject: {} \nPredicate: {}\nObject: {}'.format(s,p,o))
                print('---------------------------')
            '''
            self.pathwayDictionary[this_pathway] = o
            self.pathwayCategory[this_pathway] = 'NA'

    def isHumanPathway(self, g) -> bool:
        organism_uri = URIRef('http://vocabularies.wikipathways.org/wp#organism')
        for s, p, o in g.triples((None, organism_uri, None)):
            if o.endswith("NCBITaxon_9606"):
                return True
        return False

    def displayRDFfile(self,second = 3):
        path = '../misc/data/wikipathwaysRDF/wp/'
        listoffiles = os.listdir(path)
        
        for each in listoffiles:
            this_pathway = each.replace('.ttl','')
            #print('pathway id is {}'.format(this_pathway))
            g = Graph()
            g.parse(path + each,format = 'n3')
            if not self.isHumanPathway(g):
                print(f'skipping {this_pathway} as non-human')
                continue

            for s,p,o in g.triples((None,None,None)):
                
                print('---------------------------')
                print('Subject: {} \nPredicate: {}\nObject: {}'.format(s,p,o))
                print('---------------------------')
                time.sleep(second)
        
    def getIDMapingWithPathways(self): 
        '''
        This function parse all RDF files from source files. Then call functions
    
        1) self.getPathwayInfoFromGraph(g, this_pathway)
        2) self.getMetabolitesIDFromGraph(g,this_pathway)
        3) self.getGenesIDFromGraph(g, this_pathway)
        4) self.getCatalyzation(g, this_pathway) // Not implemented 
        
        '''
        path = '../misc/data/wikipathwaysRDF/wp/'
        self.check_path(path)
        listoffiles = os.listdir(path)
        
        
        total_files = len(listoffiles)
        for each in listoffiles:
            if not each.endswith(".ttl"):
                continue
            
            # get pathways id
            this_pathway = each.replace('.ttl','')

#             if this_pathway == 'WP3668' or this_pathway == 'WP4944':
#                 print("Skipping!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! :" + this_pathway)
#                 continue


            #print('Path '+path + " Each "+each)
            g = Graph()
            g.parse(path + each,format = 'n3')
            
            # get pathway information at first
            if not self.isHumanPathway(g):
                continue
            self.getPathwayInfoFromGraph(g, this_pathway)
            # get metabolites information at second
            self.getMetabolitesIDFromGraph(g,this_pathway)
            self.getGenesIDFromGraph(g, this_pathway)
            #self.getCatalyzation(g, this_pathway)
        print("End of wiki genes")
        
        
    def getGenesIDFromGraph(self,g,this_pathway):
        geneProduct = URIRef('http://vocabularies.wikipathways.org/wp#GeneProduct')
        type_predicate = URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type')
        proteins = URIRef('http://vocabularies.wikipathways.org/wp#Protein')
        possible_source = {
            'ncbigene':'Entrez',
            'ensembl':'Ensembl',
            'uniprot':'Uniprot',
            'ec-code':'Enzyme Nomenclature',
            'wikidata':'WikiData',
            'ncbiprotein':'NCBI-ProteinID',
	        'chebi':'ChEBI',
            'hgnc.symbol':'gene_symbol',
            'brenda':'brenda'
            }
        # These source are not retrieved at this moment
        not_retrieved = ['wikipedia.en','mirbase','hgnc.symbol','ena.embl','mirbase.mature','kegg.genes','go',
                         'interpro','refseq','pfam','ecogene','chembl.compound', 'reactome']
        genelist = set()
        count = 0
        #print("this pathway:", this_pathway)
        for gene in g.subjects(type_predicate,geneProduct):
            count=count+1
            #if this_pathway == 'WP3807':
             #   print("gene: ", gene)
            bdbLinks = {
                'Entrez':'http://vocabularies.wikipathways.org/wp#bdbEntrezGene',
                'UniProt':'http://vocabularies.wikipathways.org/wp#bdbUniprot',
                'Ensembl':'http://vocabularies.wikipathways.org/wp#bdbEnsembl',
                'WikiData':'http://vocabularies.wikipathways.org/wp#bdbWikiData',
                'common_name': 'http://vocabularies.wikipathways.org/wp#bdbHgncSymbol',
            }
            geneMapping = {"kegg": "NA",
                         "common_name": "NA",
                         "Ensembl": "NA", 
                         "HGNC": "NA", 
                         "HPRD": "NA", 
                         "NCBI-GeneID": "NA", 
                         "NCBI-ProteinID": "NA", 
                         "OMIM": "NA", 
                         "UniProt": "NA", 
                         "Vega": "NA", 
                         "miRBase": "NA", 
                         "HMDB_protein_accession": "NA",
                         "Entrez" : "NA",
                         "Enzyme Nomenclature": "NA",
                         'WikiData':'NA'}

            genesource = gene.split('/')[-2]
            if genesource not in possible_source:
                continue
            geneid = gene.split('/')[-1]
            geneid = self.prependID(genesource, geneid)
            if genesource not in not_retrieved:
                geneMapping[possible_source[genesource]] = [geneid]
                genelist.add(geneid)
                for key,value in bdbLinks.items():
                    for links in g.objects(gene,URIRef(value)):
                        link_id = links.split('/')[-1]

                        #print("link id:", link_id)
                        link_id = self.prependID(key, link_id)
                        #if this_pathway == 'WP3807':
                         #   print("link id:", link_id)
                        #print("link id:", link_id)
                        # sometimes URIREF type object accidently appears in link_id var, so avoid it by checking
                        # data type here
                        genelist.add(link_id)
                        if geneMapping[key] == 'NA' and type(link_id) is str:
                            geneMapping[key] = [link_id]
                        elif type(geneMapping[key]) is list and type(link_id) is str:
                            if link_id not in geneMapping[key]:
                                geneMapping[key].append(link_id)
                #print('{}\n{}'.format(geneid,geneMapping))
                self.geneInfoDictionary[geneid] = geneMapping
                #if this_pathway == "WP3807":
                 #   for key, value in geneMapping.items():
                  #      print("key ", key)
                    #     print("value ", value)

        #if this_pathway == "WP3807":
         #   print("count after gene:", count)


        count = 0
        for protein in g.subjects(type_predicate,proteins):
            count=count+1
            #if this_pathway == 'WP3807':
             #   print("protein: ", protein)
            bdbLinks = {
                'Entrez':'http://vocabularies.wikipathways.org/wp#bdbEntrezGene',
                'UniProt':'http://vocabularies.wikipathways.org/wp#bdbUniprot',
                'Ensembl':'http://vocabularies.wikipathways.org/wp#bdbEnsembl',
                'WikiData':'http://vocabularies.wikipathways.org/wp#bdbWikidata',
                'common_name': 'http://vocabularies.wikipathways.org/wp#bdbHgncSymbol',
            }
            geneMapping = {"kegg": "NA",
                         "common_name": "NA",
                         "Ensembl": "NA", 
                         "HGNC": "NA", 
                         "HPRD": "NA", 
                         "NCBI-GeneID": "NA", 
                         "NCBI-ProteinID": "NA", 
                         "OMIM": "NA", 
                         "UniProt": "NA", 
                         "Vega": "NA", 
                         "miRBase": "NA", 
                         "HMDB_protein_accession": "NA",
                         "Entrez" : "NA",
                         "Enzyme Nomenclature": "NA",
                         'WikiData':'NA'}
            genesource = protein.split('/')[-2]
            geneid = protein.split('/')[-1]
            geneid = self.prependID(genesource, geneid)
            if genesource == 'chebi':
                print ("chebi gene error " + genesource + " id = " + geneid)
                print ("protein: " + protein)
                print ("pathway: " + this_pathway)
            if genesource not in not_retrieved:
                # some new source id types we don't want to capture, July 2023 started to get hgnc numbers, wiki only has 154 of them... skip them.
                if genesource not in possible_source:
                    continue
                geneMapping[possible_source[genesource]] = [geneid]
                genelist.add(geneid)
                for key,value in bdbLinks.items():
                    for links in g.objects(protein,URIRef(value)):
                        link_id = links.split('/')[-1]
                        link_id = self.prependID(key, link_id)
                        # sometimes URIREF type object accidently appears in link_id var, so avoid it by checking
                        # data type here
                        genelist.add(link_id)
                        if geneMapping[key] == 'NA' and type(link_id) is str:
                            geneMapping[key] = [link_id]
                        elif type(geneMapping[key]) is list and type(link_id) is str:
                            if link_id not in geneMapping[key]:
                                geneMapping[key].append(link_id)
                self.geneInfoDictionary[geneid] = geneMapping
        self.pathwaysWithGenesDictionary[this_pathway] = list(genelist)
        #if this_pathway == "WP3807":
         #   print("count after protein:", count)
        #print('At pathway {}, total {} genes, {} pathways with genes'\
         #     .format(this_pathway,len(self.geneInfoDictionary),len(self.pathwaysWithGenesDictionary)))
        
    def getMetabolitesIDFromGraph(self,g,this_pathway):
        type_predicate = URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type')
        
        metabolite_object = URIRef('http://vocabularies.wikipathways.org/wp#Metabolite')
        possible_source = {
            'kegg.compound':'kegg_id',
            'hmdb':'hmdb_id',
            'pubchem.compound':'pubchem_compound_id',
            'chebi':'chebi_id',
            'chemspider':'chemspider_id',
            'wikidata':'WikiData',
            'cas':'CAS',
            'lipidmaps':'LIPIDMAPS',
            'kegg.glycan':'kegg_glycan',
            'pharmgkb.drug': 'pharmgkb_drug'
            }
        metabolite_list = set()
        for metabolites in g.subjects(type_predicate,metabolite_object):
                
            source = metabolites.split('/')
            source = source[len(source) - 2]
            # last items by split is retrieved
            metabolites_id = metabolites.split('/')[-1]
            #metabolites_id = self.getIDFromGraphLinks(g, metabolites)
            metabolites_id = self.prependID(source, metabolites_id)
            # predicate in RDF is defined here, this the subject/object with these predicates are extracted.
            
            # JCB Lets get the commonName...
            commonName = g.label(metabolites, default="NA")
            
            if source == 'LIPIDMAPS':
                self.lipidMapsIdCounterDict[metabolites_id] 
            
            id_mapping = {
                'chebi_id':'http://vocabularies.wikipathways.org/wp#bdbChEBI',
                'hmdb_id':'http://vocabularies.wikipathways.org/wp#bdbHmdb',
                'pubchem_compound_id':'http://vocabularies.wikipathways.org/wp#bdbPubChem',
                'WikiData':'http://vocabularies.wikipathways.org/wp#bdbWikidata',
                'chemspider_id':'http://vocabularies.wikipathways.org/wp#bdbChemspider',
                'LIPIDMAPS':'http://vocabularies.wikipathways.org/wp#bdbLipidMaps'        
            }
            # metabolites id mapping created each loop
            metaboliteMapping = {
                              "chebi_id": "NA", 
                              "drugbank_id": "NA", 
                              "drugbank_metabolite_id": "NA", 
                              "phenol_explorer_compound_id": "NA", 
                              "phenol_explorer_metabolite_id": "NA", 
                              "foodb_id": "NA", 
                              "knapsack_id": "NA", 
                              "chemspider_id": "NA",
                              "kegg_id": "NA",
                              "biocyc_id": "NA",
                              "bigg_id": "NA",
                              "wikipedia": "NA",
                              "nugowiki": "NA",
                              "metagene": "NA",
                              "metlin_id": "NA",
                              "pubchem_compound_id": "NA",
                              "het_id": "NA",
                              "hmdb_id": "NA",
                              "CAS": "NA",
                              "WikiData": "NA",
                              "kegg_glycan": "NA",
                              "LIPIDMAPS": "NA"
                              }
            
            for key in metaboliteMapping:
                if type(metaboliteMapping[key]) == list:
                    print("Have list type for NA, for key:" + key)
            
            # skip pubchem.substance id at this moment
            # ttd.drug is new addition for the feb 10 2019 data
            # skip uniprot ids on metabolites... for small peptides
            # lipidbank, reactome, pid.pathway are not supported yet
            if source not in ['pid.pathway', 'reactome', 'lipidbank', 'pubchem.substance','drugbank','chembl.compound','kegg.drug', 'ttd.drug', 'inchikey', 'uniprot']:

                metaboliteMapping[possible_source[source]] = [metabolites_id]
                
                metabolite_list.add(metabolites_id)
                
                for key,value in id_mapping.items():
                    for links in g.objects(metabolites,URIRef(value)):
                        link_id = links.split('/')
                        link_id = link_id[len(link_id) - 1]
                        link_id = self.prependID(key, link_id)

                        if key == 'LIPIDMAPS':
                            self.lipidMapsIdCounterDict[link_id] = link_id
                            
                        metabolite_list.add(link_id)

                        # add id to the metabolites id mapping 
                        if metaboliteMapping[key] == "NA" and type(link_id) is str:
                            metaboliteMapping[key] = [link_id]
                        elif type(metaboliteMapping[key]) is list and type(link_id) is str:
                            if link_id not in metaboliteMapping[key]:                     
                                metaboliteMapping[key].append(link_id) 
                                
                        # JCB populate metabolites to pathway dictionary, this was not previously populated
                        # check the link_ids at this level (in this loop)    
                        if link_id in self.metabolitesWithPathwaysDictionary:
                            if this_pathway not in self.metabolitesWithPathwaysDictionary[link_id]:
                                self.metabolitesWithPathwaysDictionary[link_id].append(this_pathway)
                        else:
                            self.metabolitesWithPathwaysDictionary[link_id] = [this_pathway]
                               
                        #print('Root {} has been linked to {}'.format(metabolites_id,link_id))
                #print(metaboliteMapping)
                self.pathwaysWithMetabolitesDictionary[this_pathway] = list(metabolite_list)
                
                # JCB have to be careful here. A metabolite id is likely found in multiple pathways
                # so this line might have over written the dictionary associated with a metabolite id
                # commenting out
                #self.metaboliteIDDictionary[metabolites_id] = metaboliteMapping
                
                # JCB replacement code. If the metabolite ids exists, run through metaboliteMapping to add entries.
                # JCB if the id isn't in the mapping dict, just add it
                
                if metabolites_id not in self.metaboliteIDDictionary:
                    self.metaboliteIDDictionary[metabolites_id] = metaboliteMapping
                     
                    # this is the first time we've seen the metabolite id. Add it 'metabolite_id' to it's own mapping
                    if source not in self.metaboliteIDDictionary[metabolites_id]:
                        self.metaboliteIDDictionary[metabolites_id][source] = [metabolites_id]
                    else:
                        if metabolites_id not in self.metaboliteIDDictionary[metabolites_id][source]:
                            self.metaboliteIDDictionary[metabolites_id][source].append(metabolites_id)
                           
                # else, run through the linked ids for the main metabolite id and add them as needed.
                else:
                    idDict = self.metaboliteIDDictionary[metabolites_id]
                    for idType in metaboliteMapping:
                        
                        # need to make sure we have a list here, else the NA will be processed as N and A
                        if type(metaboliteMapping[idType]) == list:
                            if idType not in idDict:
                                idDict[idType] = metaboliteMapping[idType]
                            else:
                                for id in metaboliteMapping[idType]:
                                    if id not in idDict[idType]:
                                        idDict[idType].append(id)
                
                
                
                # JCB populate metabolites to pathway dictionary, this was not previously populated]
                # This code bit takes care of the primary metabolite id (link_ids are handled above)
                if metabolites_id in self.metabolitesWithPathwaysDictionary:
                    if this_pathway not in self.metabolitesWithPathwaysDictionary[metabolites_id]:
                        self.metabolitesWithPathwaysDictionary[metabolites_id].append(this_pathway)
                else:
                    self.metabolitesWithPathwaysDictionary[metabolites_id] = [this_pathway]
                
                # JCB grep the 'label' as common name
                self.metaboliteCommonName[metabolites_id] = commonName
                # add the label as a synonym
                self.metabolitesWithSynonymsDictionary[metabolites_id] = commonName
        '''
        print('At pathway {}:{}, there are {} metabolites'\
              .format(this_pathway,self.pathwayDictionary[this_pathway],len(self.metaboliteIDDictionary)))
        print('{} pathway has at least one metabolites'.format(len(self.pathwaysWithMetabolitesDictionary)))
        '''
        #print('WIKI  Total metabolites in this version of pathways (roughly):{}'.format(len(self.metaboliteIDDictionary)))

    # helper functions 
    def getIDFromGraphLinks(self,g,subject):
        '''
        Given RDF graph and subject,
        this function only looks at the object with identifier(source id) predicate
        '''
        for label in g.objects(URIRef(subject),DCTERMS.identifier):
            return label
        return 'NA'
    
    def getCatalyzation(self,g,this_pathway):
        '''
        This function get all catalyzation relations between metabolites and genes from the graph
        - param RDFgraph g The graph given by parsing RDF file
        - param string this_pathway the pathway ID (WP_number) given from the file.
        '''
        for s,p,o in g.triples((None,None,None)):
            if 'Interaction' not in s:
                continue
            print('---------------------------')
            print('Subject: {} \nPredicate: {}\nObject: {}'.format(s,p,o))
            print('---------------------------')
            time.sleep(1)
        
    def prependID(self,prefix,id):
        '''
        This function needs to be changed if the id_mapping dict has been changed
        This function will prepend prefix to id. Modified id based on the given prefix.
        '''
        # change id based on condition
        # Please look raw rdf file to figure out the pattern
        if prefix == 'pubchem_compound_id' or prefix == 'pubchem.compound':
            id = id.replace('CID','')
            id = 'pubchem:'+id
        elif prefix == 'chebi_id' or prefix =='chebi':
            id = id.replace('CHEBI:','')
            id = 'chebi:' + id
        elif prefix == 'hmdb_id' or prefix == 'hmdb':
            if len(id) == 9:
                id = id.replace('HMDB','HMDB00')
            elif len(id) != 9  and len(id) != 11:
                print('#### Check if hmdb id {} is correct ####'.format(id))
                time.sleep(3)
                '''
            elif len(id) == 11:
                print('HMDB id is in primary accession {}'.format(id))
                '''
            id = 'hmdb:' +id
        elif prefix == 'WikiData' or prefix =='wikidata' or prefix == 'entity':
            id = prefix.lower()+':'+id
        elif prefix == 'chemspider_id':
            id = 'chemspider:'+id
        elif prefix == 'chemspider':
            id = 'chemspider:'+id
        elif prefix == 'kegg.compound' or prefix == 'kegg':
            id = 'kegg:' +id
        elif prefix == 'cas':
            id = 'CAS:' + id
        elif prefix == 'lipidmaps':
            id = 'LIPIDMAPS:' + id
        elif prefix == 'LIPIDMAPS':
            id = 'LIPIDMAPS:' + id
        elif prefix == 'ncbigene' or prefix == 'Entrez':
            id = 'entrez:' + id
        elif prefix == 'uniprot' or prefix == 'UniProt':
            id = 'uniprot:' + id
        elif prefix == 'ec-code' or prefix == 'Enzyme Nomenclature':
            id = 'EN:' +id
        elif prefix == 'ensembl' or prefix == 'Ensembl':
            id = 'ensembl:' + id
        elif prefix == 'ncbiprotein':
            id = 'ncbiprotein:' + id
        elif prefix == "hgnc.symbol":
            id = 'gene_symbol:' + id
        elif prefix == "common_name":
            id = 'gene_symbol:' + id
        elif prefix == 'kegg.glycan' or prefix == 'kegg_glycan':
            id = 'kegg_glycan:' +id
        elif prefix == 'brenda':
            id = 'brenda:' +id  
        else:
            id = 'UNKNOWN_ID_TYPE_HEYYYYYY:' + id

        return id


 
# rConf = RampConfig()
# rConf.loadConfig("../../config/external_resource_config.txt")
# # 
# # # test
# wikipathways = WikipathwaysRDF(rConf)
# wikipathways.getEverything(writeToFile=True)
#wikipathways.write_myself_files(database ="wiki")

# sql = writeToSQL()
# wikicompoundnum = sql.createRampCompoundID(wikipathways.metaboliteIDDictionary, "wiki", 0)
# wikigenenum = sql.createRampGeneID(wikipathways.geneInfoDictionary, "wiki", wikicompoundnum)
# 
# wikipathwaysnumbers = sql.write(
#         wikipathways.metaboliteCommonName,
#         wikipathways.pathwayDictionary, 
#          wikipathways.pathwayCategory,
# #         wikipathways.pathwaysWithMetabolitesDictionary,
#          wikipathways.metabolitesWithPathwaysDictionary,
#          wikipathways.metabolitesWithSynonymsDictionary,
#          wikipathways.metaboliteIDDictionary,
#          wikipathways.pathwaysWithGenesDictionary,
#          wikipathways.metabolitesLinkedToGenes,
#          wikipathways.geneInfoDictionary,
#          wikipathways.biofluidLocation,
#          wikipathways.biofluid,
#          wikipathways.cellularLocation,
#          wikipathways.cellular,
#          wikipathways.pathwayOntology,
#          wikipathways.exoEndoDictionary,
#          wikipathways.exoEndo,
#          wikipathways.tissueLocation,
#          wikipathways.tissue,
#          dict(),
#          "wiki",
#          0,wikigenenum)
  
