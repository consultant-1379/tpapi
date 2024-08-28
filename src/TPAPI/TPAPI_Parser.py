
from __future__ import with_statement
import TPAPI
import logging
import copy
import sys, traceback

class Parser(object):
    '''Class to represent a parser object. Identified by VersionID, parentTableName and parserType. Child object of TechPackVersion'''

    def __init__(self,versionID,parentTableName,parserType):
        '''Class is instantiated using versionID, parentTableName and parserType
        
        Instance Variables:
        
            self.versionID:
                Description: VersionID of the TechPackVersion
                Type:String
                
            self.parserType:
                Description: Type of parser eg Ascii,mdc
                Type:String
                
            self.parentTableName = parentTableName # parent table name
                Description: Parent Table name
                Type:String
            
            self.transformationObjects:
                Description: List of child transformation objects in sequence
                Type:List
        
            self.attributeTags:
                Description: stores the mappings between attribute "column names" and their data tags
                Type:Dictionary
                Keys: Attribute (Column) Names
                          
            self.dataTags:
                Description: A list of data tags which load to the table
                Type:List

            self.dataFormatID:
                Description: Unique Identifier of the parser (self.versionID + ":" + self.parentTableName + ":" + self.parserType)
                Type:String
                
            self.transformerID: 
                Description: Unique Identifier of the transformation (self.versionID + ":" + self.parentTableName + ":" + self.parserType)
                            Used to fetch transformations from db
                Type:String
        
        
        '''
        self.logger = logging.getLogger('TPAPI.TPAPI_TP.Parser')
        self.versionID = versionID
        self.parserType = parserType 
        self.parentTableName = parentTableName
        self.transformationObjects = []
        self.attributeTags = {} # stores the mappings between attribute "column names" and their data tags.. ie database vs data
        self.dataTags = [] # stores the mappings between table names and their data tags
        self.dataFormatID = self.versionID + ":" + self.parentTableName + ":" + self.parserType
        self.transformerID = self.versionID + ":" + self.parentTableName + ":" + self.parserType # used to fetch transformationObjects for the parser object
    
    
    def _getPropertiesFromServer(self,server):
        ''''Gets all properties (and child objects) from the server
    
        In this particular case Parser objects dont have a properties dictionary.
        They have transformation objects,tagids and dataids associated with them'''
        
        self._getTransformations(server)
        self._getTagIDs(server)
        self._getDataIDs(server)
    
    def _getTagIDs(self,server):
        '''Gets TableTags information for the server for the parser object.
        
        Gets the TAGID tags and appends it to a list of dataTags.
        This list defines the default mappings between measurement files received from network elements and measurement tables
        
        
        SQL Executed:
                    SELECT TAGID FROM dwhrep.DefaultTags where DATAFORMATID=?
                    
        
        '''
        with TPAPI.DbAccess(server,'dwhrep') as crsr:
            crsr.execute("SELECT TAGID FROM dwhrep.DefaultTags where DATAFORMATID=?",(self.dataFormatID,))
            resultset = crsr.fetchall()
            for row in resultset:
                self.dataTags.append(str(row[0]))
                       
    def _getDataIDs(self,server):
        '''Gets attributeTags information for the server for the parser object
        
        Gets the DATANAME  and DATAID
        
        creates the parser object and appends it
        to the list of attributeTags
        
        The Dictionary contains the tags for each counter with respect to each table
        
        The Dictionary defines the default mappings between counters of the measurement files received from network elements and 
        Counters in the measurement tables of TECHPACK
        
        
        SQL Executed:
                    SELECT DATANAME,DATAID FROM dwhrep.DataItem where DATAFORMATID=?
        
        '''
        with TPAPI.DbAccess(server,'dwhrep') as crsr:
            crsr.execute("SELECT DATANAME,DATAID FROM dwhrep.DataItem where DATAFORMATID=?",(self.dataFormatID,))
            rows = crsr.fetchall()        
            for row in rows:
                if row is not None:
                    self.attributeTags[row[0]] = str(row[1])

    def _getTransformations(self,server):
        '''Gets transformation information for the server for the parser object,creates the transformation object and appends it
        to the list of transformationObjects'''
        rowIDs = []
        
        with TPAPI.DbAccess(server,'dwhrep') as crsr:
            crsr.execute("SELECT ORDERNO FROM dwhrep.Transformation where TRANSFORMERID=?",(self.transformerID,))
            row = crsr.fetchall()
            for x in row:
                rowIDs.append(str(x[0]))
            
        for rowid in rowIDs:
            transformation = TPAPI.Transformation(rowid, self.transformerID)
            transformation._getPropertiesFromServer(server)
            self.transformationObjects.append(transformation)

    def _toXML(self,offset=0):
        '''Write the object to an xml formatted string
        
        Offset value is used for string indentation. Default to 0
        Parent toXML() method is responsible for triggering child object toXML() methods.

        Return Value: xmlString 
        '''
        offset += 4
        os = "\n" + " "*offset
        os2 = os + " "*4
        os3 = os2 + " "*4
        os4 = os3 + " "*4
        outputXML  = os+ '<Parser type="'+self.parserType+'">'
        outputXML +=os2+ '<Transformations transformerID="'+self.transformerID+'">'
        for transformer in self.transformationObjects:
            outputXML += os3+transformer._toXML(offset)
        outputXML +=os2+'</Transformations>'
        outputXML +=os+'<Dataformats>'
        outputXML +=os2+ '<Dataformat DataFormatID="'+self.transformerID+'">'
        tags = []
        for tag in self.dataTags:
            tags.append(tag)
        outputXML +=os3+'<TableTags>'
        for tag in tags:
            outputXML +=os4+ '<TableTag>'+str(tag)+'</TableTag>'
        outputXML +=os3+'</TableTags>'
        outputXML +=os3+'<attributeTags>'
        tagID = []
        for col,row in self.attributeTags.iteritems():
            outputXML += os4+'<'+str(col)+'>'+str(row)+'</'+str(col)+'>'
        outputXML +=os3+'</attributeTags>'
        outputXML +=os2+ '</Dataformat>'
        outputXML +=os+'</Dataformats>'
        outputXML +=os+'</Parser>'
        return outputXML
    
    def _getPropertiesFromXML(self,xmlElement):
        '''Populates the objects content from an xmlElement.
        
        The method is also responsible for triggering its child objects getPropertiesFromXML() method'''
        index = 0 
        for elem in xmlElement:
            if elem.tag=='Transformations':
                for elem1 in elem:
                    if elem1.tag == "OrderNo":
                        transformation = TPAPI.Transformation(elem1.attrib['index'], self.transformerID)
                        transformation._getPropertiesFromXML(elem1)
                        self.transformationObjects.append(transformation)
                        index = index + 1
            if elem.tag == 'Dataformats':
                for elem1 in elem:
                    for elem2 in elem1:
                        for elem3 in elem2:
                            if elem2.tag == "TableTags":
                                self.dataTags.append(elem3.text)
                            if elem2.tag == 'attributeTags':
                                self.attributeTags[elem3.tag]= elem3.text
    
    
    def _getPropertiesFromTPI(self,tpiDict=None,filename=None):
            '''Populate the objects contents from a tpiDict object or tpi file.
            
            If a tpi file is passed it is converted to a tpiDict object before processing.

            Exceptions: 
                       Raised if tpiDict and filename are both None (ie nothing to process)'''
            
            self.logger.debug(self.parserType + "._getPropertiesFromTPI()")
            if tpiDict==None and filename==None:
                strg = 'getPropertiesFromTPI() Nothing to Process'
                raise Exception(strg)
                self.logger.error(strg)
            else:
                if filename is not None:
                    tpidict = TPAPI.TpiDict(filename).returnTPIDict()

            rowIDs = []
            index = 0
            for row in tpiDict['Transformation']['TRANSFORMERID']:
                if tpiDict['Transformation']['TRANSFORMERID'][row].lower() == self.transformerID.lower():
                    if row in tpiDict['Transformation']['ORDERNO']:
                        rowIDs.append(int(tpiDict['Transformation']['ORDERNO'][row]))
            
            rowIDs.sort()           
            for rowid in rowIDs:
                transformation = TPAPI.Transformation(rowid ,self.transformerID)
                transformation._getPropertiesFromTPI(tpiDict)
                self.transformationObjects.append(transformation)
                
    def _difference(self,prsrObj,deltaObj,deltaFTV):
        '''Calculates the difference between two parser objects
        
            Method takes prsrObj,deltaObj and deltaTPV as inputs.
            prsrObj: The parser to be compared against
            DeltaObj: The single object that gets passed through the entire diff recording the changes.
            DeltaTPV: A TechPackVersion Object that gets passed through the entire diff recording only new content.
            
            The Difference method will trigger the difference method of its child objects, passing
            in the object to compare, deltaObj and deltaTPV. After calculating the diff the child object passes these objects
            back in conjunction with a flag to say whether a (only new or changed content.. not deleted) was found or not. This flag is used to decide
            whether a child object should be added to the parent object in the DeltaTPV.
            
            
            Parser Difference method deviates from other diff methods in that it explicity calculates the diff for transformations.
            Transformation objects do not have a diff method.
            Transformation Hash value is used to find index changes in transformationObjects. If a transformation has moved sequence it index will be reported as
            having being moved, if the other transformationObjects have not changed sequence (but their index has moved) they are ignored . Transformations 
            are either new, deleted or have has their index changed. Diff does not happen at the transformation object level
            because its possible to have two transformationObjects under the same parser object with exactly the same properties/config
            
            Returns:
                    diffFlag (Boolean indicating where a change was found or not)
                    deltaObj
                    deltaTPV 
        '''
        
        self.logger.debug(self.transformerID + "._difference()")
        deltaObj.stack.append('Parser=' +self.parserType)
        diffFlag = False
        deltaParserObject = TPAPI.Parser(self.versionID,self.parentTableName,self.parserType)
        upgradeHashList = list()
        origHashList = list()
        origHashDict = {}
        upgradeHashDict = {}
        
        for transformation in self.transformationObjects:
            hashval = transformation._getHash()
            origHashDict[hashval] = transformation
            origHashList.append(hashval)
        
        for transformation in prsrObj.transformationObjects:
            hashval = transformation._getHash()
            upgradeHashDict[hashval] = transformation
            upgradeHashList.append(hashval)

        upgradeHashListCopy = copy.deepcopy(upgradeHashList) 
        origHashListCopy = copy.deepcopy(origHashList) 
        deltaTransforms = set(upgradeHashList).difference(set(origHashList))
        removedTransforms = set(origHashList).difference(set(upgradeHashList))     
        
        for x in removedTransforms:
            origHashListCopy.remove(x)
            mystr= ''
            mystr += "transformation=<deleted>,"
            for prop in origHashDict[x].properties:
                if prop == 'CONFIG' :
                    mystr  += prop + "=" + '"' + origHashDict[x].properties[prop]+ '"' + ','
                else:
                    mystr  += prop + "=" + origHashDict[x].properties[prop] + ','                    
            mystr +=  "index="+str(origHashList.index(x)) 
            deltaObj.stack.append(mystr)
            deltaObj._addChange(deltaObj.stack,None,None)
            deltaObj.stack.pop() 
            
        for x in deltaTransforms:
            upgradeHashListCopy.remove(x)
            mystr= ''
            mystr += "transformation=<new>,"
            deltaParserObject.transformationObjects.append(upgradeHashDict[x])
            for prop in upgradeHashDict[x].properties:
                if prop == 'CONFIG' :
                    mystr  += prop + "=" + '"' + str(upgradeHashDict[x].properties[prop])+ '"' + ','
                else:
                    mystr  += prop + "=" + str(upgradeHashDict[x].properties[prop]) + ','
            mystr += "index="+str(upgradeHashList.index(x))
            deltaObj.stack.append(mystr)
            deltaObj._addChange(deltaObj.stack,None,None)
            deltaObj.stack.pop()
            diffFlag = True
            
        for trans in list(origHashListCopy):
            if upgradeHashListCopy.index(trans) != origHashListCopy.index(trans) :
                origVal=origHashList.index(trans)
                deltaVal=upgradeHashList.index(trans)
                mystr= ''
                mystr += "transformation=<index_change>,"
                for prop in origHashDict[trans].properties:
                    if prop == 'CONFIG' :
                        mystr  += prop + "=" + '"' + origHashDict[trans].properties[prop]+ '"' + ','
                    else:
                        mystr  += prop + "=" + origHashDict[trans].properties[prop] + ','
                mystr += "prop=index"
                deltaObj.stack.append(mystr)
                deltaObj._addChange(deltaObj.stack,deltaVal,origVal)
                deltaObj.stack.pop()
            upgradeHashListCopy.remove(trans)
            origHashListCopy.remove(trans)             
        deltaObj.stack.pop()
        
        if len(deltaTransforms) > 0:
            diffFlag = True
            deltaFTV.parserObjects[self.parserType] = deltaParserObject 
        return diffFlag,deltaObj,deltaFTV



