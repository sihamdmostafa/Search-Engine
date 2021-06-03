

from src.TextRepresenter import PorterStemmer
import numpy as np
import json
import re







class Document:
    def __init__(self, id, titre = None, auteur = None, date = None, keys = None, text = None, linkTo=dict(),linkFrom=[]):
        self.id = id 
        self.titre = titre
        self.date = date
        self.auteur = auteur
        self.keys = keys
        self.text = text
        self.linkTo = linkTo
        self.linkFrom=linkFrom
        
    def getID(self):
        #retourne l'ID de document
        return self.id

    def getText(self):
        #retourne le text de document
        return self.text
    
    def setLinkFrom(self, l):
        
        self.linkFrom = l

    def getHyperlinksTo(self):
        #permete de récupérer les documents qui citent un document
        return self.linkTo
    
    def getHyperlinksFrom(self):
        #permete de récupérer les documents cités par un document
        return self.linkFrom


class Parser:
    #permet de parser la collection stockée sous la forme d’un dictionnaire de Documents.
    def __init__(self):
        self.documents = dict()
       
    def parse(self,fichier):
        #Parse fichier sous la forme d’un dictionnaire de Document
        docs = open(fichier, "r").read().split('.I ')
        allLinkFrom = dict()
         
        for i in range(1,len(docs)):
            linkTo = dict()
            idDoc = re.search(r"[0-9]+",docs[i])
            if idDoc is not None:
                idDoc = idDoc.group(0)
            title = self.get_element("T",docs[i])
            date = self.get_element("B",docs[i])
            auteur = self.get_element("A",docs[i])
            text = self.get_element("W",docs[i])
            keys = self.get_element("K",docs[i])
            links = self.get_element("X",docs[i])
            
            if links is not None:
                l = links.split("\n")
                for i in range(1,len(l)):
                    linkID = l[i].split()[0]
                    linkTo[int(linkID)] = linkTo.get(int(linkID), 0) + 1
                    
                    allLinkFrom[linkID] = allLinkFrom.get(linkID, []) + [idDoc]
                    
            d = Document(idDoc,title,auteur,date,keys,text,linkTo)
            self.documents[idDoc]=d 
            
        for idDoc in allLinkFrom:
            self.documents[idDoc].setLinkFrom(allLinkFrom[idDoc])
                
        return self.documents

    def get_element(self,balise,doc):
        res = re.search(r"\."+balise+"([\s\S]*?)\.[ITBAKNWX]",doc)
        if res is not None:
            return res.group(1)
        else:
            res = re.search(r"\."+balise+"([\s\S]*?)\n\n",doc)
            if res is not None:
                return res.group(1)
            else:
                return None   
    
class Query():
    #permet de stocker l’identifiant de la requéte, son texte et la liste des identifiants des documents pertinents
    def __init__(self, id, text, pertinences):
        
        self.id = id
        self.txt = text
        self.listPert = pertinences 

        
    def getID(self):
        #retourne l'ID de la requête 
        return self.id

    def getText(self):
        #retourne le contenu de la requête
        return self.txt
    
    
class QueryParser():
    
    def __init__(self):
        
        self.queries = dict()  
       
    def parse(self,fichierQ,fichierQrels):
        #Parse le fichier des requêtes sous la forme d’un dictionnaire de Query
        with open(fichierQrels) as fqrels:
            lines = fqrels.readlines()
            qrels = dict()
            
            for l in lines: 
                tmp = l.split()
                if(tmp[0] in qrels.keys()):
                    qrels[tmp[0]].append(tmp[1])
                else:
                    qrels[tmp[0]] = [tmp[1]]
                    
        docs = open(fichierQ, "r").read().split('.I ')

        for i in range(1,len(docs)):

            idQ = re.search(r"[0-9]+",docs[i])
            if idQ is not None:
                idQ = idQ.group(0)
                
            text = self.get_element("W",docs[i])


            pert = qrels.get(idQ,[])        
            q = Query(idQ,text,pert)
            self.queries[idQ]=q

        return self.queries

    def get_element(self,balise,doc):
        res = re.search(r"\."+balise+"([\s\S]*?)\.[ITBAKNWX]",doc)
        if res is not None:
            return res.group(1)
        else:
            res = re.search(r"\."+balise+"([\s\S]*)\n",doc)
            if res is not None:
                return res.group(1)
            else:
                return None   

        

class IndexerSimple():
    #permet d’indexer une collection dans une méthode indexation
    def __init__(self):

        self.index = dict()
        self.indexInv = dict()
        
            
    def getIndex(self):
        #retroune l'index
        return self.index

    def getIndexInv(self):
        #retourne l'index inverse
        return self.indexInv
    
    def indexation(self,dictDoc):  
        #construire les fichiers index (index + index inversé) des collections qui ont été parsées
        """
        dictDoc:dictionnaire des documents retourner par la méthode de parsing
        """
        self.dictDoc = dictDoc
        Trep=PorterStemmer()
        for i in dictDoc.keys():   
            txt = dictDoc[i].getText()
            if txt is not None:
                terms= Trep.getTextRepresentation(dictDoc[i].getText())
                self.index[i] = dict(terms)
            else:
                self.index[i] = dict()
            
            for t in self.index[i].keys():
                if (t in self.indexInv.keys()):
                    if(i in self.indexInv[t].keys()):
                        self.indexInv[t][i] += self.index[i][t]
                    else:
                        self.indexInv[t][i]= self.index[i][t]
                else:
                    self.indexInv[t] = {}
                    self.indexInv[t][i]=self.index[i][t]
    
    def save(self,folder):
        #enregistre l'index et l'index inverse
        with open(folder+"Ind",'w') as f:
            json.dump(self.index, f)
        with open(folder+"IndInv",'w') as f:
            json.dump(self.indexInv, f)
        
    def load(self,folder,docs):
        #charge l'index et l'index inverse 
        try:
            with open(folder+"Ind",'r') as f:
                self.index = json.load(f)
            with open(folder+"IndInv",'r') as f:
                self.indexInv = json.load(f)
            self.dictDoc = docs
        except:
            print("Error loading the index please check the folder you entered.")
        
        
    def getTfsForDoc(self,doc):
        #retourne la représentation (stem-tf) d’un document a partir de l’index ;
        """
        doc : id d'un document
        """
        return self.index[doc]
    
    
    
    def getTfIDFsForDoc(self,doc):
        #retourne la représentation (stem-TFIDF) d’un document a partir de l’index ;
        """
        doc : id d'un document
        """
        N=len(self.index)
        dic = dict()
        for t in self.index[doc].keys():
            dic[t] = self.index[doc][t] * np.log((1+N) /(1+ len(self.indexInv[t])))
        return dic
    
    def getTfsForStem(self,stem):
        #retourne la représentation (doc-tf) d’un stem a partir de l’index inverse ;
        """
        stem : represente le stem 
        """
        return self.indexInv[stem]
    
    def getTfIDFsForStem(self,stem):
        #retourne la représentation (doc-TFIDF) d’un stem a partir de l’index inverse ;
        N = len(self.index)
        """
        stem : represente le stem 
        """
        tfidf = dict()
        for t in self.indexInv[stem].keys():
            tfidf[t] = self.index[t][stem] * np.log((1+N)/(1 + len(self.indexInv[stem])))
        return tfidf
    
    def getIDFsForStem(self,stem):
        #retourne la représentation (doc-IDF) d’un stem a partir de l’index inverse ;
        N = len(self.index)
        if stem not in self.indexInv.keys():
            return 0
        return np.log((1+N)/(1 + len(self.indexInv[stem])))
    
    def getStrDoc(self,parser,doc):
        #retourne la chaine de caractére dont est issu un document donné dans le fichier source
        """
        parser : objet de la classe Parser
        doc : id d'un document 
        """
        return parser.documents[doc].txt
    
    def getCollection(self):   
        #retourne le dictionnaire des documents
        return self.dictDoc
		
    def getCollectionSize(self):
        #retourne le nombre des terme dans la collection
        return sum(self.getDocumentSize(k) for k in self.index.keys())
    
    def getDocumentSize(self,idDoc):
        #retourne le nombre des termes dans un document 
        return sum(self.index[idDoc].values())


    def getHyperlinksTo(self,doc):
        #permete de récupérer les documents qui citent le document doc
        return self.dictDoc[doc].getHyperlinksTo()
    
    def getHyperlinksFrom(self,doc):
        #permete de récupérer les documents cités par le document doc        
        return self.dictDoc[doc].getHyperlinksFrom()

    
