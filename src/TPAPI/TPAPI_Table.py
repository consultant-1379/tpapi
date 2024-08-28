
from __future__ import with_statement
import TPAPI
import re
import logging
from copy import deepcopy
import warnings
from TPAPI_Util import deprecated

class Table(object):
        '''Class to represent a table in a Tech Pack Version. Child of TechPackVersion class. Uniquely identified by its
        name and versionid (combined these are know as the typeid). Tables can be of either 'Measurement' or 'Reference' type
        '''
        def __init__(self,name,versionID):
            '''Class is initialised with the name of the table and the teckpack versionID
            
            Instance Variables:
            
               self.versionID:
                    Description: versionID of the parent techpack version. eg DC_E_BSS:((100)).
                    Type:String
                    
                self.tableType:
                    Description: Type of the table either 'Measurement' or 'Reference'.
                    Type:String
                    
                self.name:
                    Description: Name of the table.
                    Type: String
                    
                self.properties:
                    Description: Contains the properties of the table.
                    Type: Dictionary
                    Keys: Dependent on the tableType
                        Reference Table Keys: 
                                              DESCRIPTION
                                              UPDATE_POLICY
                                              TABLE_TYPE
                                              DATAFORMATSUPPORT
                                              
                        Measurement Table Keys: 
                                                TYPECLASSID
                                                DESCRIPTION
                                                JOINABLE
                                                SIZING
                                                TOTALAGG
                                                ELEMENTBHSUPPORT
                                                RANKINGTABLE
                                                DELTACALCSUPPORT
                                                PLAINTABLE
                                                UNIVERSEEXTENSION
                                                VECTORSUPPORT
                                                DATAFORMATSUPPORT
                                                VENDORID
                                                TYPENAME
                                                FOLDERNAME
                                                TYPEID
                                                VERSIONID
                        
                self.attributeObjects:
                    Description: Contains the attribute objects associated with the table.
                    Type:Dictionary
                    Keys: Attribute Names
                    
                self.parserNames:
                    Description: Parser names associated with the fact table.. ie ascii, mdc.
                    Type:List
                    
                self.parserObjects:
                    Description: Contains the Parser Objects associated with a table.
                    Type: Dictionary
                    Keys: Parser Names
                
                self.universeClass:
                    Description: The universe class the table object belongs to.
                    Type: String
                    
                self.typeid:
                    Description: Unique identifier of a table (versionID + ":" + name) eg. DC_E_BSS:((100)):DC_E_BSS_MEASTABLE
                    Type:String
                    
                self.typeClassID:
                    Description: Unique identifier for the universe class the table is associated with (versionid + ":" + tpname + ":" + universeClass).eg. DC_E_STN:((13)):DC_E_STN_IPv6PingMeasurement
                    Type: String
                
                self.mtableIDs:
                    Description: Partition types of the table (versionID+":"+name+":" + RAW/PLAIN/DAY/COUNT) ie DC_E_BSS:((100)):DC_E_BSS_MEASTABLE:RAW).
                    Type: List
            '''
            self.logger = logging.getLogger('TPAPI.TPAPI_TP.TechPackVersion.Table')
            self.versionID = versionID
            self.tableType = '' 
            self.name = name
            self.properties = {} 
            self.attributeObjects = {}
            self.parserNames = []
            self.parserObjects = {} 
            self.universeClass = ''
            self.typeid = versionID + ":" + name
            self.typeClassID = '' 
            self.mtableIDs = []
            self.logger.debug(self.versionID + ":" +self.name + ".__init__()")
            
        def _getTableTypeFromServer(self,server):
            '''Get and sets the tableType of the table from a lookup to the dwhrep
            
            self.tableType is set to either 'Measurement','Reference' or 'UNDEF'
            Depending on result returned.
            
            SQL Executed:
                    SELECT COUNT(*) from dwhrep.MeasurementType WHERE TYPEID =?
                    SELECT COUNT(*) from dwhrep.ReferenceTable WHERE TYPEID =?
            
            Exceptions:
                        Raised if the table is not found in the dwhrep
            '''
            
            self.logger.debug(self.versionID + ":" +self.name + "._getTableTypeFromServer()")
            with TPAPI.DbAccess(server,'dwhrep') as crsr:   
                crsr.execute("SELECT COUNT(*) from dwhrep.MeasurementType WHERE TYPEID =?", (self.typeid,)) 
                row = crsr.fetchone()
                if row[0] > 0:
                    self.tableType = 'Measurement'
                    return
                else:
                    crsr.execute("SELECT COUNT(*) from dwhrep.ReferenceTable WHERE TYPEID =?", (self.typeid,))
                    row = crsr.fetchone()
                    if row[0] > 0:
                        self.tableType = 'Reference'
                        return
                    else:
                        strg = '_getTableTypeFromServer() Table not found in dwhrep'
                        raise Exception(strg)
                        self.logger.error(strg)
         
        def _getPropertiesFromServer(self,server):
            '''Gets all properties (and child objects) of the table from the server
            
            This method triggers multiple sub methods for retrieving information
            from the dwhrep
            '''
            self.logger.debug(self.versionID + ":" +self.name + "._getPropertiesFromServer()")
            self._getTableTypeFromServer(server)            
            if self.tableType == 'Reference':
                self._getReferenceTablePropertiesFromServer(server)
                self._getAllAttributes(server)
            elif self.tableType == 'Measurement':
                self._getMeasurementTablePropertiesFromServer(server)
                self._getAllAttributes(server)
            else:
                pass
            self._getMeasurementTypeClassIDFromServer(server)
            self._getMeasurementUniverseClassFromServer(server)
            self._getParserNamesFromServer(server)
            self._getParserObjects(server)
        
        def _getEventsPropertiesFromServer(self,server):
            '''Gets all properties (and child objects) of the table for an Events Techpack, from the server
            
            This method triggers multiple sub methods for retrieving information
            from the dwhrep
            '''
            self.logger.debug(self.versionID + ":" +self.name + "._getEventsPropertiesFromServer()")
            self._getTableTypeFromServer(server)
            if self.tableType == 'Reference':
                self._getReferenceTablePropertiesFromServer(server)
                self._getAllAttributes(server)
            elif self.tableType == 'Measurement':
                self._getEventMeasurementTablePropertiesFromServer(server)
                self._getAllAttributes(server)
            else:
                pass
            self._getParserNamesFromServer(server)
            self._getParserObjects(server)
        
        def _getPropertiesFromTPI(self,tpidict=None,filename=None):
            '''Populate the objects contents from a tpiDict object or tpi file.
            
            If a tpi file is passed it is converted to a tpiDict object before processing.

            Exceptions: 
                       Raised if tpiDict and filename are both None (ie nothing to process)'''
            self.logger.debug(self.name + "._getPropertiesFromTPI()")
            if tpidict==None and filename==None:
                strg = 'getPropertiesFromTPI() Nothing to Process'
                raise Exception(strg)
                self.logger.error(strg)
            else:
                if filename is not None:
                    tpidict = TPAPI.TpiDict(filename).returnTPIDict()  
                if self.tableType =='Measurement':
                    for row in tpidict['Measurementtype']['TYPEID']:
                        if self.typeid == tpidict['Measurementtype']['TYPEID'][row]:
                            self.tableType = 'Measurement'
                            self.properties['TYPECLASSID'] = tpidict['Measurementtype']['TYPECLASSID'][row]
                            self.properties['DESCRIPTION'] = tpidict['Measurementtype']['DESCRIPTION'][row]
                            self.properties['JOINABLE'] = tpidict['Measurementtype']['JOINABLE'][row]
                            self.properties['SIZING'] = tpidict['Measurementtype']['SIZING'][row]
                            self.properties['TOTALAGG'] = tpidict['Measurementtype']['TOTALAGG'][row]
                            self.properties['ELEMENTBHSUPPORT'] = tpidict['Measurementtype']['ELEMENTBHSUPPORT'][row]
                            self.properties['RANKINGTABLE'] = tpidict['Measurementtype']['RANKINGTABLE'][row]
                            self.properties['DELTACALCSUPPORT'] = tpidict['Measurementtype']['DELTACALCSUPPORT'][row]
                            self.properties['PLAINTABLE'] = tpidict['Measurementtype']['PLAINTABLE'][row]
                            self.properties['UNIVERSEEXTENSION'] = tpidict['Measurementtype']['UNIVERSEEXTENSION'][row]
                            self.properties['VECTORSUPPORT'] = TPAPI.checkNull(tpidict['Measurementtype']['VECTORSUPPORT'][row])
                            self.properties['DATAFORMATSUPPORT'] = tpidict['Measurementtype']['DATAFORMATSUPPORT'][row]
                            self.properties['VENDORID']=tpidict['Measurementtype']['VENDORID'][row]
                            self.properties['TYPEID']=tpidict['Measurementtype']['TYPEID'][row]
                            self.properties['VERSIONID']=tpidict['Measurementtype']['VERSIONID'][row]
                            for row in tpidict['Measurementtypeclass']['TYPECLASSID']:
                                if self.properties['TYPECLASSID'].lower() == tpidict['Measurementtypeclass']['TYPECLASSID'][row].lower():
                                    self.universeClass = tpidict['Measurementtypeclass']['DESCRIPTION'][row]
                            for row in tpidict['Measurementkey']['TYPEID']:
                                if self.typeid == tpidict['Measurementkey']['TYPEID'][row]:
                                    att = TPAPI.Attribute(tpidict['Measurementkey']['DATANAME'][row],'measurementKey')
                                    att._parentTableName = self.typeid
                                    att._getPropertiesFromTPI(tpidict)
                                    self.attributeObjects[tpidict['Measurementkey']['DATANAME'][row]] = att
                            for row in tpidict['Measurementcounter']['TYPEID']:
                                if self.typeid == tpidict['Measurementcounter']['TYPEID'][row]:
                                    att = TPAPI.Attribute(tpidict['Measurementcounter']['DATANAME'][row],'measurementCounter')
                                    att._parentTableName = self.typeid
                                    att._getPropertiesFromTPI(tpidict)
                                    self.attributeObjects[tpidict['Measurementcounter']['DATANAME'][row]] = att                     
                            break
         
                elif self.tableType == 'Reference':
                    for row in tpidict['Referencetable']['TYPEID']:
                        if self.typeid == tpidict['Referencetable']['TYPEID'][row]:
                            self.typeFlag = 'Reference'
                            self.properties['DESCRIPTION'] = tpidict['Referencetable']['DESCRIPTION'][row]
                            self.properties['UPDATEPOLICY'] = tpidict['Referencetable']['UPDATE_POLICY'][row]
                            self.properties['REFERENCETABLETYPE'] = TPAPI.checkNull(tpidict['Referencetable']['TABLE_TYPE'][row])
                            self.properties['DATAFORMATSUPPORT'] = tpidict['Referencetable']['DATAFORMATSUPPORT'][row]
                            for row in tpidict['Referencecolumn']['TYPEID']:
                                if self.typeid == tpidict['Referencecolumn']['TYPEID'][row]:
                                    att = TPAPI.Attribute(tpidict['Referencecolumn']['DATANAME'][row],'referenceKey')
                                    att._parentTableName = self.typeid
                                    att._getPropertiesFromTPI(tpidict)
                                    self.attributeObjects[tpidict['Referencecolumn']['DATANAME'][row]] = att
                            break
                for row in tpidict['Dataformat']['DATAFORMATTYPE']: 
                    if tpidict['Dataformat']['DATAFORMATTYPE'][row] not in self.parserNames:
                        self.parserNames.append(tpidict['Dataformat']['DATAFORMATTYPE'][row])    
                for prsr in self.parserNames:
                    parser = TPAPI.Parser(self.versionID,self.name,prsr)
                    parser._getPropertiesFromTPI(tpidict)
                    self.parserObjects[prsr] = parser
                    
        def _getMeasurementTypeClassIDFromServer(self,server):
            '''Gets the typeClassID for a measurement table from the server
            
            SQL Executed:
                    SELECT TYPECLASSID from dwhrep.measurementType where TYPEID =?
            '''
            self.logger.debug(self.versionID + "._getMeasurementTypeClassIDFromServer()")
            with TPAPI.DbAccess(server,'dwhrep') as crsr:
                if self.name.rsplit('_')[0] != 'DIM' and self.name.rsplit('_')[-1] != 'AGGLEVEL':
                    crsr.execute("SELECT TYPECLASSID from dwhrep.measurementType where TYPEID =?", (self.typeid ,))
                    row = crsr.fetchone()
                    self.typeClassID = str(row[0])
            
        def _getMeasurementUniverseClassFromServer(self,server):     
            '''Gets the universeClass for a measurement table from the server
            
            SQL Executed:
                        SELECT DESCRIPTION from dwhrep.measurementTypeClass where TYPECLASSID =?
            '''
            self.logger.debug(self.versionID + "._getMeasurementUniverseClassFromServer()")
            with TPAPI.DbAccess(server,'dwhrep') as crsr:
                if self.typeClassID != '':
                    crsr.execute("SELECT DESCRIPTION from dwhrep.measurementTypeClass where TYPECLASSID =?", (self.typeClassID ,))
                    row = crsr.fetchone()
                    self.universeClass = str(row[0])
        
        def _getMeasurementTablePropertiesFromServer(self,server):
            '''Populates the properties dictionary of the Measurement table from the server
            
            SQL Executed:
                        SELECT TYPECLASSID,DESCRIPTION,JOINABLE,SIZING,TOTALAGG,ELEMENTBHSUPPORT,RANKINGTABLE,DELTACALCSUPPORT,PLAINTABLE,UNIVERSEEXTENSION,VECTORSUPPORT,DATAFORMATSUPPORT,VENDORID,TYPENAME,FOLDERNAME,TYPEID,VERSIONID from dwhrep.MeasurementType WHERE TYPEID =?
            '''
            self.logger.debug(self.versionID + ":" +self.name + "._getMeasurementTablePropertiesFromServer()")
            with TPAPI.DbAccess(server,'dwhrep') as crsr:      
                crsr.execute("SELECT TYPECLASSID,DESCRIPTION,JOINABLE,SIZING,TOTALAGG,ELEMENTBHSUPPORT,RANKINGTABLE,DELTACALCSUPPORT,PLAINTABLE,UNIVERSEEXTENSION,VECTORSUPPORT,DATAFORMATSUPPORT,VENDORID,TYPENAME,FOLDERNAME,TYPEID,VERSIONID from dwhrep.MeasurementType WHERE TYPEID =?", (self.typeid,)) 
                row = crsr.fetchone()
                self.properties['TYPECLASSID'] = str(row[0])
                self.properties['DESCRIPTION'] = str(row[1]).strip()
                self.properties['JOINABLE'] = str(row[2])
                self.properties['SIZING'] = str(row[3])
                self.properties['TOTALAGG'] = str(row[4])
                self.properties['ELEMENTBHSUPPORT'] = str(row[5])
                self.properties['RANKINGTABLE'] = str(row[6])
                self.properties['DELTACALCSUPPORT'] = str(row[7])
                self.properties['PLAINTABLE'] = str(row[8])
                self.properties['UNIVERSEEXTENSION'] = str(row[9])
                self.properties['VECTORSUPPORT'] = str(row[10])
                self.properties['DATAFORMATSUPPORT'] = str(row[11])
                self.properties['VENDORID']=str(row[12])
                self.properties['TYPEID']=str(row[15])
                self.properties['VERSIONID']=str(row[16])

        def _getReferenceTablePropertiesFromServer(self,server):
            '''Populates the properties dictionary of the Reference table from the server
            
            SQL Executed:
                        SELECT DESCRIPTION,UPDATE_POLICY,TABLE_TYPE,DATAFORMATSUPPORT from dwhrep.ReferenceTable WHERE TYPEID =?
    
            '''
            self.logger.debug(self.versionID + ":" +self.name + "._getReferenceTablePropertiesFromServer()")
            with TPAPI.DbAccess(server,'dwhrep') as crsr:   
                crsr.execute("SELECT DESCRIPTION,UPDATE_POLICY,TABLE_TYPE,DATAFORMATSUPPORT from dwhrep.ReferenceTable WHERE TYPEID =?", (self.typeid,)) 
                row = crsr.fetchone()
                self.properties['DESCRIPTION'] = str(row[0]).strip()
                self.properties['UPDATEPOLICY'] = TPAPI.strFloatToInt(str(row[1]))
                self.properties['REFERENCETABLETYPE'] = TPAPI.checkNull(str(row[2]))
                self.properties['DATAFORMATSUPPORT'] = str(row[3])

        def _getEventMeasurementTablePropertiesFromServer(self,server):
            '''Populates the properties dictionary of the events Measurement table from the server
            
            SQL Executed:
                        SELECT TYPECLASSID,DESCRIPTION,JOINABLE,SIZING,TOTALAGG,ELEMENTBHSUPPORT,RANKINGTABLE,DELTACALCSUPPORT,PLAINTABLE,UNIVERSEEXTENSION,VECTORSUPPORT,DATAFORMATSUPPORT,ONEMINAGG,MIXEDPARTITIONSTABLE,EVENTSCALCTABLE,LOADFILE_DUP_CHECK,FIFTEENMINAGG from dwhrep.MeasurementType WHERE TYPEID =?
            
            '''
            self.logger.debug(self.versionID + ":" +self.name + "._getEventMeasurementTablePropertiesFromServer()")
            with TPAPI.DbAccess(server,'dwhrep') as crsr:
                crsr.execute("SELECT TYPECLASSID,DESCRIPTION,JOINABLE,SIZING,TOTALAGG,ELEMENTBHSUPPORT,RANKINGTABLE,DELTACALCSUPPORT,PLAINTABLE,UNIVERSEEXTENSION,VECTORSUPPORT,DATAFORMATSUPPORT,ONEMINAGG,MIXEDPARTITIONSTABLE,EVENTSCALCTABLE,LOADFILE_DUP_CHECK,FIFTEENMINAGG from dwhrep.MeasurementType WHERE TYPEID =?", (self.typeid,)) 
                row = crsr.fetchone()
                self.properties['TYPECLASSID'] = str(row[0])
                self.properties['DESCRIPTION'] = str(row[1])
                self.properties['JOINABLE'] = str(row[2])
                self.properties['SIZING'] = str(row[3])
                self.properties['TOTALAGG'] = str(row[4])
                self.properties['ELEMBHSUPPORT'] = str(row[5])
                self.properties['RANKINGTABLE'] = str(row[6])
                self.properties['DELTACALCSUPPORT'] = str(row[7])
                self.properties['PLAINTABLE'] = str(row[8])
                self.properties['UNIVERSEEXTENSION'] = str(row[9])
                self.properties['VECTORSUPPORT'] = str(row[10])
                self.properties['DATAFORMATSUPPORT'] = str(row[11])
                self.properties['ONEMINAGG'] = str(row[12])
                self.properties['MIXEDPARTITIONSTABLE'] = str(row[13])
                self.properties['EVENTSCALCTABLE'] = str(row[14])
                self.properties['LOADFILEDUPCHECK'] = str(row[15])
                self.properties['FIFTEENMINAGG'] = str(row[16])
            return   

        def _getAllAttributes(self,server):
            '''Get attributes information associated with the table from the server.
            
             Creates a child attribute object and adds the object to the self.attributeObjects dictionary'''
            self.logger.debug(self.versionID + ":" +self.name + "._getAllAttributes()")
            with TPAPI.DbAccess(server,'dwhrep') as crsr:
                
                if self.tableType == 'Reference':
                    crsr.execute("SELECT DATANAME FROM dwhrep.ReferenceColumn where TYPEID=?",(self.typeid,))
                    row = crsr.fetchall()
                    for refKey in row:
                        att = TPAPI.Attribute(str(refKey[0]),'referenceKey')
                        att._getPropertiesFromServer(server,self.typeid)
                        self.attributeObjects[str(refKey[0])] = att
                elif self.tableType == 'Measurement':
                    crsr.execute("SELECT DATANAME FROM dwhrep.MeasurementKey where TYPEID=?",(self.typeid,))
                    row = crsr.fetchall()
                    for measKey in row:
                        att = TPAPI.Attribute(str(measKey[0]),'measurementKey')
                        att._getPropertiesFromServer(server,self.typeid)
                        self.attributeObjects[str(measKey[0])] = att
                    crsr.execute("SELECT DATANAME FROM dwhrep.MeasurementCounter where TYPEID=?",(self.typeid,))
                    row = crsr.fetchall()
                    for measCounter in row:
                        att = TPAPI.Attribute(str(measCounter[0]),'measurementCounter')
                        att._getPropertiesFromServer(server,self.typeid)
                        self.attributeObjects[str(measCounter[0])] = att 
        
        def _getParserNamesFromServer(self,server):
            '''Get a list of parser names (ie mdc,ascii) associated with the measurement table from the server
            
            Names are appended to self.parserNames list
            '''
            self.logger.debug(self.versionID + ":" +self.name + "._getParserNamesFromServer()")
            with TPAPI.DbAccess(server,'dwhrep') as crsr:
                
                crsr.execute("SELECT DISTINCT DATAFORMATTYPE FROM dwhrep.DataFormat WHERE TYPEID =?", (self.typeid,)) 
                resultset = crsr.fetchall()
                for row in resultset:
                    self.parserNames.append(str(row[0])) 

        def _getParserObjects(self,server):
            '''Gets child parser objects of the table 
            
            Using self.parserNames the method get parser information from the server, creates the child parser
            object and adds the object to the self.parserObjects dictionary'''
            self.logger.debug(self.versionID + ":" +self.name + "._getParserObjects()")
            for prsr in self.parserNames:
                parser = TPAPI.Parser(self.versionID,self.name,prsr)
                parser._getPropertiesFromServer(server)
                self.parserObjects[prsr] = parser
        
              
        def _toXML(self,offset=0):
            '''Write the object to an xml formatted string
            
            Offset value is used for string indentation. Default to 0
            Parent toXML() method is responsible for triggering child object toXML() methods.
    
            Return Value: xmlString 
            '''
            self.logger.debug(self.versionID + ":" +self.name + "._toXML()")
            offset += 4
            os = "\n" + " "*offset
            os2 = os+ " "*4
            outputXML =os+'<Table name="'+self.name+ '" tableType="'+self.tableType+ '" universeClass= "'+self.universeClass +'">'
            for prop in self.properties:
                outputXML += os2+'<'+str(prop)+'>'+ TPAPI.escape(self.properties[prop]) +'</'+str(prop)+'>'
            outputXML  += os2 + '<Attributes>'
            for attribute in self.attributeObjects:
                outputXML += self.attributeObjects[attribute]._toXML(offset)
            outputXML  += os2 + '</Attributes>'
            outputXML  += os2 + '<Parsers>' 
            for parser in self.parserObjects:
                outputXML += self.parserObjects[parser]._toXML(offset)
            outputXML  += os2 + '</Parsers>'
            outputXML +=os+'</Table>'
            return outputXML
        
        def _getPropertiesFromXML(self,xmlElement):
            '''Populates the objects content from an xmlElement.
            
            The method is also responsible for triggering its child objects getPropertiesFromXML() method'''
            
            self.logger.debug(self.versionID + ":" +self.name + "._getPropertiesFromXML()")
            self.tableType = xmlElement.attrib['tableType']
            self.universeClass = xmlElement.attrib['universeClass'] 
            for elem1 in xmlElement:
                if elem1.tag=='Attributes':
                        for elem2 in elem1:
                            if elem2.tag=='Attribute':
                                tpAttrb = TPAPI.Attribute(elem2.attrib['name'],elem2.attrib['attributeType'])
                                tpAttrb._getPropertiesFromXML(elem2)
                                self.attributeObjects[elem2.attrib['name']] = tpAttrb  
                elif elem1.tag=='Parsers':
                        for elem2 in elem1:
                            if elem2.tag=='Parser':
                                if elem2.attrib['type'] not in self.parserNames:
                                    self.parserNames.append(elem2.attrib['type'])
                                tpParser = TPAPI.Parser(self.versionID,self.name,elem2.attrib['type'])
                                tpParser._getPropertiesFromXML(elem2)
                                self.parserObjects[elem2.attrib['type']] = tpParser
                else:
                    self.properties[elem1.tag] = TPAPI.safeNull(elem1.text)

        
        def _difference(self,tableObject,deltaObj,deltaTPV):
            '''Calculates the difference between two table objects
            
            Method takes tableObject,deltaObj and deltaTPV as inputs.
            TableObject: The table to be compared against
            DeltaObj: The single object that gets passed through the entire diff recording the changes.
            DeltaTPV: A TechPackVersion Object that gets passed through the entire diff recording only new content.
            
            The Difference method will trigger the difference method of its child objects, passing
            in the object to compare, deltaObj and deltaTPV. After calculating the diff the child object passes these objects
            back in conjunction with a flag to say whether a (only new or changed content.. not deleted) was found or not. This flag is used to decide
            whether a child object should be added to the parent object in the DeltaTPV.
            
            Returns:
                    diffFlag (Boolean indicating where a change was found or not)
                    deltaObj
                    deltaTPV 
            
            '''
            diffFlag = False
            self.logger.debug(self.versionID + ":" +self.name + "._difference()")
            deltaObj.stack.append(self.tableType+"="+self.name)
            ftvd = TPAPI.Table(self.name,deltaTPV.versionID)
            ftvd.tableType = self.tableType
            # Properties Diff
            if self.universeClass != tableObject.universeClass:
                deltaObj.stack.append("Property=<changed>Classification")
                origVal = self.universeClass
                deltaVal = tableObject.universeClass
                diffFlag = True
                ftvd.universeClass = deltaVal
                deltaObj._addChange(deltaObj.stack,deltaVal,origVal)
                deltaObj.stack.pop()
            propertiesDelta = TPAPI.DictDiffer(self.properties,tableObject.properties)
            for item in propertiesDelta.changed():
                if item != 'TYPEID' and item !=  'TYPECLASSID' and item !=  'VERSIONID':
                    diffFlag = True
                    deltaObj.stack.append("Property=<changed>"+item)
                    origVal = self.properties[item]
                    deltaVal = tableObject.properties[item]
                    ftvd.properties[item] = deltaVal
                    deltaObj._addChange(deltaObj.stack,deltaVal,origVal)
                    deltaObj.stack.pop()
            # Attribute Diff
            origAttributes = list(self.attributeObjects.keys())
            upgradeAttributes = list(tableObject.attributeObjects.keys())
            deltaAttributes = set(upgradeAttributes).difference(set(origAttributes))
            commonAttributes = set(upgradeAttributes).intersection(set(origAttributes))
            removedAttributes = set(origAttributes).difference(set(upgradeAttributes)) 
            #removed attributes
            for removedAttribute in removedAttributes:
                diffFlag = True
                removedAtt = self.attributeObjects[removedAttribute]
                deltaObj.stack.append(removedAtt.attributeType+"=<deleted>"+removedAtt.name)
                for prop in removedAtt.properties:
                    deltaObj.stack.append("Property=<deleted>"+prop)
                    deltaVal = removedAtt.properties[prop]
                    deltaObj._addChange(deltaObj.stack,None,deltaVal)
                    deltaObj.stack.pop()
                deltaObj.stack.pop()
            #new attributes
            for deltaAttribute in deltaAttributes:
                diffFlag = True
                newAtt = tableObject.attributeObjects[deltaAttribute]
                ftvd.attributeObjects[deltaAttribute] = tableObject.attributeObjects[deltaAttribute]
                deltaObj.stack.append(newAtt.attributeType+"=<new>"+newAtt.name)
                for prop in newAtt.properties:
                    deltaObj.stack.append("Property=<new>"+prop)
                    deltaVal = newAtt.properties[prop]
                    deltaObj._addChange(deltaObj.stack,deltaVal,None)
                    deltaObj.stack.pop()
                deltaObj.stack.pop() 
            #common attributes
            for commonAttribute in commonAttributes:
                diffFlag2,deltaObj,ftvd = self.attributeObjects[commonAttribute]._difference(tableObject.attributeObjects.get(commonAttribute),deltaObj,ftvd)
                if diffFlag == True or diffFlag2 == True:
                    diffFlag = True
            ################################################################################
            # Parser Diff
            origParsers = list(self.parserObjects.keys())
            upgradeParsers = list(tableObject.parserObjects.keys())
            deltaParsers = set(upgradeParsers).difference(set(origParsers))
            removedParsers = set(origParsers).difference(set(upgradeParsers))
            commonParsers = set(upgradeParsers).intersection(set(origParsers))
            #removed Parsers
            for removedParser in removedParsers:
                diffFlag = True
                deltaObj.stack.append("Parser=<deleted>"+removedParser)
                for transformation in self.parserObjects[removedParser].transformationObjects:
                    mystr= ''
                    mystr += "transformation=<deleted>,"
                    for prop in transformation.properties:
                        if prop == 'CONFIG' :
                            mystr  += prop + "=" + '"' + transformation.properties[prop]+ '"' + ','
                        else:
                            mystr  += prop + "=" + transformation.properties[prop] + ','
                        mystr +=  "index="+str(transformation.rowID)     
                        deltaObj.stack.append(mystr)
                        deltaObj._addChange(deltaObj.stack,None,None)
                        deltaObj.stack.pop()
                deltaObj.stack.pop()
            #New parsers
            for deltaParser in deltaParsers:
                diffFlag = True
                ftvd.parserObjects[deltaParser] = tableObject.parserObjects[deltaParser]
                deltaObj.stack.append("Parser=<new>"+deltaParser)
                for transformation in tableObject.parserObjects[deltaParser].transformationObjects:
                    mystr= ''
                    mystr += "transformation=<new>,"
                    for prop in transformation.properties:
                        if prop == 'CONFIG' :
                            mystr  += prop + "=" + '"' + transformation.properties[prop]+ '"' + ','
                        else:
                            mystr  += prop + "=" + transformation.properties[prop] + ','
                        mystr +=  "index="+str(transformation.rowID)     
                        deltaObj.stack.append(mystr)
                        deltaObj._addChange(deltaObj.stack,None,None)
                        deltaObj.stack.pop()
                deltaObj.stack.pop()
            diffFlag2 = False
            for commonParser in commonParsers:
                diffFlag2,deltaObj,ftvd= self.parserObjects[commonParser]._difference(tableObject.parserObjects[commonParser],deltaObj,ftvd)
                
            if diffFlag == True or diffFlag2 == True:
                diffFlag = True
                if type(ftvd).__name__ != 'TechPackVersion' and diffFlag == True :
                    deltaTPV.measurementTableObjects[self.name ] = ftvd
            deltaObj.stack.pop()
            return diffFlag,deltaObj,deltaTPV


#UPDATE,SQL GENERATION AND INSERT METHODS     
        @deprecated
        def _updateVersionID(self,versionID):
            '''@deprecated 
            Update the versionID of the tpv model
            
            Triggers sub methods
            This is the only method that should be called when updating the versionID
            '''
            self._setVersionID(versionID)
            self._setTypeClassID()
            self._setTypeid()
            self._resetPropertiesDictWithCurrentVersionID()
            
        @deprecated
        def _setVersionID(self,versionID):
            '''@deprecated 
            Setter for self.versionID'''
            self.versionID = versionID
        
        @deprecated
        def _setTypeClassID(self):
            '''@deprecated 
            Setter for self.typeClassID'''
            self.typeClassID = self.versionID + ":" + self.versionID.rsplit(':')[0] + "_" + self.universeClass
            
        @deprecated     
        def _setTypeid(self):
            '''@deprecated 
            Setter for self.typeid'''
            self.typeid = self.versionID + ":" + self.name
        
        @deprecated    
        def _getTypeClassID(self):
            '''@deprecated 
            getter for self.typeClassID'''
            self._setTypeClassID()
            return self.typeClassID
        
        @deprecated            
        def _resetPropertiesDictWithCurrentVersionID(self):
            '''@deprecated 
            Resets occurances of versionID the properties dictionary with the current versionID'''
            self.properties['VERSIONID'] = self.versionID
            self.properties['TYPEID'] = self.typeid
            self.properties['TYPECLASSID'] = self.typeClassID
            
        @deprecated
        def _generateMTABLEIDs(self):
            '''@deprecated 
            Populates list of self.MTABLEIDs with the partiontypes associated with the table
            
            MDTABLEIDs for DAYBH are generated outside of the table class, as they are dependent on information
            in the Busy Hour class'''

            if self.properties['VECTORSUPPORT'] == 'None':
                self.properties['VECTORSUPPORT'] = '0'
                
            if self.properties['DELTACALCSUPPORT'] == '1'  and self.properties['TOTALAGG'] == '1' \
             and self.properties['VECTORSUPPORT'] == '0' and self.properties['RANKINGTABLE'] == '0' \
             and self.properties['PLAINTABLE'] == '0':            
                self.mtableIDs.append(self.typeid + ':RAW')
                self.mtableIDs.append(self.typeid + ':DAY')
                self.mtableIDs.append(self.typeid + ':COUNT')
            elif self.properties['DELTACALCSUPPORT'] == '0' and self.properties['PLAINTABLE'] == '0' \
            and self.properties['RANKINGTABLE'] == '0' and self.properties['VECTORSUPPORT'] == '0':
                self.mtableIDs.append(self.typeid + ':RAW')
                if self.properties['TOTALAGG'] == '1':
                    self.mtableIDs.append(self.typeid + ':DAY' )
            elif self.properties['RANKINGTABLE'] == '1' and self.properties['ELEMENTBHSUPPORT'] == '0' \
                and self.properties['DELTACALCSUPPORT'] == '0' and self.properties['PLAINTABLE'] == '0' \
                and self.properties['VECTORSUPPORT'] == '0' : # ADD EVERYTHING ELSE IS 0
                self.mtableIDs.append(self.typeid + ':RANKBH')
            elif self.properties['RANKINGTABLE'] == '1' and self.properties['ELEMENTBHSUPPORT'] == '1' \
                and self.properties['DELTACALCSUPPORT'] == '0' and self.properties['PLAINTABLE'] == '0' \
                and self.properties['VECTORSUPPORT'] == '0' : # ADD EVERYTHING ELSE IS 0
                self.mtableIDs.append(self.typeid + ':RANKBH')
            elif self.properties['DELTACALCSUPPORT'] == '0' and self.properties['VECTORSUPPORT'] == '0' \
                and self.properties['RANKINGTABLE'] == '0' and self.properties['PLAINTABLE'] == '1':
                self.mtableIDs.append(self.typeid + ':PLAIN')
                if self.properties['TOTALAGG'] == '1':
                    self.mtableIDs.append(self.typeid + ':DAY' )
            elif self.properties['DELTACALCSUPPORT'] == '0' and self.properties['VECTORSUPPORT'] == '1' \
                and self.properties['RANKINGTABLE'] == '0' and self.properties['PLAINTABLE'] == '0':
                self.mtableIDs.append(self.typeid + ':RAW')
                if self.properties['TOTALAGG'] == '1':
                    self.mtableIDs.append(self.typeid + ':DAY' )
    
        @deprecated
        def _generateReferenceTableSQL(self):
            '''@deprecated  
            Generate SQL and VALS for ReferenceTable table
            
            Returns: 
                sql, vals
            '''
            referenceTableDict = {}
            referenceTableDict['VERSIONID'] = self.versionid
            referenceTableDict['TYPENAME'] = self.name
            referenceTableDict['OBJECTID'] = self.versionid + ":" + self.name #self.versionid + ":" + self.name
            referenceTableDict['OBJECTNAME'] = self.name
            referenceTableDict['OBJECTVERSION'] = ''
            referenceTableDict['OBJECTTYPE'] = ''
            referenceTableDict['DESCRIPTION'] = self.properties['DESCRIPTION']
            referenceTableDict['STATUS'] = '' #null or 0
            referenceTableDict['UPDATE_POLICY'] = self.properties['UPDATE_POLICY']
            referenceTableDict['TABLE_TYPE'] = '' #VIEW or NULL
            referenceTableDict['DATAFORMATSUPPORT'] = self.properties['DATAFORMATSUPPORT']
            referenceTableDict['BASEDEF'] = 0 #1 if created automatically by the database O for all else
            sql,vals = TPAPI.dictToSQL(referenceTableDict,'ReferenceTable')
            return sql,vals

        @deprecated
        def _generateMeasurementTypeClassSQL(self):
            '''@deprecated 
            Generate SQL and VALS for MeasurementTypeClass table
        
            Returns:
                     sql, vals
            '''
            measTypeClassDict = {}
            measTypeClassDict['TYPECLASSID'] = self._getTypeClassID()
            measTypeClassDict['VERSIONID'] = self.versionID
            measTypeClassDict['DESCRIPTION'] = self.universeClass
            sql,vals = TPAPI.dictToSQL(measTypeClassDict,'MeasurementTypeClass')
            return sql,vals


        @deprecated
        def _generateMeasurementTypeSQL_UPDATE(self,column,value):
            '''@deprecated 
            Generate UPDATE sql statement for MeasurementType table
            
            Returns:
                    sqlstatement
            '''
            sqlstatement = 'update dwhrep.MeasurementType set ' + column + "='" + value + "' where typeid = '" + self.typeid + "';"      #UPDATE table_name
            return sqlstatement
         
        @deprecated            
        def _generateMeasurementTypeSQL_INSERT(self):
            '''@deprecated 
            Generate Insert SQL and VALS for MeasurementType table
               
            Returns:
                    sql,vals
            '''
            measTypeDict = deepcopy(self.properties)
            measTypeDict['VERSIONID'] = self.versionID
            measTypeDict['TYPEID'] = self.versionID + ":" + self.name
            measTypeDict['TYPECLASSID'] = self._getTypeClassID()
            measTypeDict['TYPENAME'] = self.name
            measTypeDict['VENDORID'] = self.versionID.rsplit(':')[0]
            measTypeDict['FOLDERNAME'] = self.name
            measTypeDict['OBJECTID'] = self.versionID + ":" + self.name
            measTypeDict['OBJECTNAME'] = self.name
            sql,vals = TPAPI.dictToSQL(measTypeDict,'MeasurementType')
            return sql,vals
        
        @deprecated
        def _generateMeasurementTypeClassSQL_UPDATE(self,server):
            '''@deprecated 
            Generate UPDATE sql statement for MeasurementType table'
            
            Returns:
                    sqlstatement
            '''
            with TPAPI.DbAccess(server,'dwhrep') as crsr:
                crsr.execute("SELECT TYPECLASSID from dwhrep.measurementType where TYPEID =?", (self.typeid ,))
                row = crsr.fetchone()
                oldtypeClassID = str(row[0])
            sqlstatement = "insert into dwhrep.measurementTypeClass set (TYPECLASSID,DESCRIPTION) = ('" + self.typeClassID + "','" + self.universeClass + "') where TYPECLASSID = '" + oldtypeClassID + "';"
            return sqlstatement

        @deprecated
        def _generateMeasurementTableSQL_DELETE(self):
            '''@deprecated 
            Generate DELETE sql statement for MeasurementType table'
            
            Returns:
                    sqlstatement
            '''
            sqlstatement = "DELETE FROM dwhrep.MeasurementTable where MTABLEID like '" + self.typeid + "%';"
            return sqlstatement
        
        @deprecated
        def _generateMeasurementTableSQL_INSERT(self):
            '''@deprecated  
            Generate INSERT sql statement for MeasurementTable table

            NB: Generation of DAYBH related Rows is done in the oarent TPV class as the logic is dependent on busyhour information outside of the class
            
            Exception:
                     Raised if unrecognised table config is found 
            
            Returns:
                    sqlstatement
            '''
            if self.properties['VECTORSUPPORT'] == 'None':
                self.properties['VECTORSUPPORT'] = '0'
            sqlStatement = ''
            #COUNT TABLE
            if self.properties['DELTACALCSUPPORT'] == '1'  and self.properties['TOTALAGG'] == '1' \
             and self.properties['VECTORSUPPORT'] == '0' and self.properties['RANKINGTABLE'] == '0' \
             and self.properties['PLAINTABLE'] == '0':
                sqlStatement += "insert into dwhrep.measurementTable(MTABLEID,TABLELEVEL,TYPEID,BASETABLENAME,PARTITIONPLAN) values ('" + self.typeid + ':RAW' +"', 'RAW', '"+self.typeid+ "','"+self.name+"_RAW','"+self.properties['SIZING']+"_raw');\n"
                sqlStatement += "insert into dwhrep.measurementTable(MTABLEID,TABLELEVEL,TYPEID,BASETABLENAME,PARTITIONPLAN) values ('" + self.typeid + ':DAY' +"', 'DAY', '"+self.typeid+ "','"+self.name+"_DAY','"+self.properties['SIZING']+"_day');\n"
                sqlStatement += "insert into dwhrep.measurementTable(MTABLEID,TABLELEVEL,TYPEID,BASETABLENAME,PARTITIONPLAN) values ('" + self.typeid + ':COUNT' +"', 'COUNT', '"+self.typeid+ "','"+self.name+"_COUNT','"+self.properties['SIZING']+"_count');\n"
            #NORMAL TABLE 
            elif self.properties['DELTACALCSUPPORT'] == '0' and self.properties['PLAINTABLE'] == '0' \
            and self.properties['RANKINGTABLE'] == '0' and self.properties['VECTORSUPPORT'] == '0':
                sqlStatement += "insert into dwhrep.measurementTable(MTABLEID,TABLELEVEL,TYPEID,BASETABLENAME,PARTITIONPLAN) values ('" + self.typeid + ':RAW' +"', 'RAW', '"+self.typeid+ "','"+self.name+"_RAW','"+self.properties['SIZING']+"_raw');\n"
                if self.properties['TOTALAGG'] == '1':
                    sqlStatement += "insert into dwhrep.measurementTable(MTABLEID,TABLELEVEL,TYPEID,BASETABLENAME,PARTITIONPLAN) values ('" + self.typeid + ':DAY' +"', 'DAY', '"+self.typeid+ "','"+self.name+"_DAY','"+self.properties['SIZING']+"_day');\n"
                #ELEMBH SUPPORT
            #RANKING TABLE
            elif self.properties['RANKINGTABLE'] == '1' and self.properties['ELEMENTBHSUPPORT'] == '0' \
                and self.properties['DELTACALCSUPPORT'] == '0' and self.properties['PLAINTABLE'] == '0' \
                and self.properties['VECTORSUPPORT'] == '0' : 
                sqlStatement += "insert into dwhrep.measurementTable(MTABLEID,TABLELEVEL,TYPEID,BASETABLENAME,PARTITIONPLAN) values ('" + self.typeid + ':RANKBH' +"', 'RANKBH', '"+self.typeid+ "','"+self.name+"_RANKBH','"+self.properties['SIZING']+"_rankbh');\n"
            #"ELEMENT RANKING TABLE"
            elif self.properties['RANKINGTABLE'] == '1' and self.properties['ELEMENTBHSUPPORT'] == '1' \
                and self.properties['DELTACALCSUPPORT'] == '0' and self.properties['PLAINTABLE'] == '0' \
                and self.properties['VECTORSUPPORT'] == '0' :
                sqlStatement += "insert into dwhrep.measurementTable(MTABLEID,TABLELEVEL,TYPEID,BASETABLENAME,PARTITIONPLAN) values ('" + self.typeid + ':RANKBH' +"', 'RANKBH', '"+self.typeid+ "','"+self.name+"_RANKBH','"+self.properties['SIZING']+"_rankbh');\n"
            #PLAIN TABLE
            elif self.properties['DELTACALCSUPPORT'] == '0' and self.properties['VECTORSUPPORT'] == '0' \
                and self.properties['RANKINGTABLE'] == '0' and self.properties['PLAINTABLE'] == '1':
                sqlStatement += "insert into dwhrep.measurementTable(MTABLEID,TABLELEVEL,TYPEID,BASETABLENAME,PARTITIONPLAN) values ('" + self.typeid + ':PLAIN' +"', 'PLAIN', '"+self.typeid+ "','"+self.name+"_PLAIN','"+self.properties['SIZING']+"_plain');\n"
                if self.properties['TOTALAGG'] == '1':
                    #"PLAIN TABLE WITH AGGREGATION"
                    sqlStatement += "insert into dwhrep.measurementTable(MTABLEID,TABLELEVEL,TYPEID,BASETABLENAME,PARTITIONPLAN) values ('" + self.typeid + ':DAY' +"', 'DAY', '"+self.typeid+ "','"+self.name+"_DAY','"+self.properties['SIZING']+"_day');\n"
            #VECTOR TABLE
            elif self.properties['DELTACALCSUPPORT'] == '0' and self.properties['VECTORSUPPORT'] == '1' \
                and self.properties['RANKINGTABLE'] == '0' and self.properties['PLAINTABLE'] == '0':
                sqlStatement += "insert into dwhrep.measurementTable(MTABLEID,TABLELEVEL,TYPEID,BASETABLENAME,PARTITIONPLAN) values ('" + self.typeid + ':RAW' +"', 'RAW', '"+self.typeid+ "','"+self.name+"_RAW','"+self.properties['SIZING']+"_raw');\n"
                if self.properties['TOTALAGG'] == '1':
                    # VECTOR TABLE WITH AGGREGATION
                    sqlStatement += "insert into dwhrep.measurementTable(MTABLEID,TABLELEVEL,TYPEID,BASETABLENAME,PARTITIONPLAN) values ('" + self.typeid + ':DAY' +"', 'DAY', '"+self.typeid+ "','"+self.name+"_DAY','"+self.properties['SIZING']+"_day');\n"
            else:
                strg = "unrecognised table config"
                self.logger.debug(strg)
                raise Exception(strg)
            return sqlStatement
        
        @deprecated
        def _generateAggregationRuleSQL_INSERT(self):
            '''@deprecated 
            Generate Insert sql statement for AggregationRule table
            
            returns:
                    sqlstatement
            '''
            sqlstatement = ''
            rowcount = 0
            if  self.properties['TOTALAGG'] == '1':
                AGGREGATION = self.name + '_DAY'
                VERSIONID = self.versionID
                RULEID = str(rowcount)
                TARGET_TYPE = self.name
                rowcount += 1
                TARGET_LEVEL ='DAY'
                TARGET_TABLE = self.name + '_DAY'
                TARGET_MTABLEID = self.versionID+ ":" + self.name + ":" + "DAY"
                SOURCE_TYPE = self.name
                if self.properties['DELTACALCSUPPORT'] == '1':
                    SOURCE_LEVEL = 'COUNT'
                    SOURCE_TABLE = self.name + "_COUNT"
                    SOURCE_MTABLEID = self.versionID + ":" + self.name + ":" + "COUNT"
                    RULETYPE = 'TOTAL'
                else:
                    SOURCE_LEVEL = 'RAW'
                    SOURCE_TABLE = self.name + "_RAW"
                    SOURCE_MTABLEID = self.versionID + ":" + self.name + ":" + "RAW"
                    RULETYPE = 'COUNT'
                AGGREGATIONSCOPE = 'DAY'
                sqlstatement += "insert into dwhrep.Aggregationrule(AGGREGATION,VERSIONID,RULEID,TARGET_TYPE,TARGET_LEVEL,TARGET_TABLE,TARGET_MTABLEID,SOURCE_TYPE,SOURCE_LEVEL,SOURCE_MTABLEID,RULETYPE,AGGREGATIONSCOPE) values ('"+AGGREGATION+"','"+VERSIONID+"','"+RULEID+"','"+TARGET_TYPE+"','"+TARGET_LEVEL+"','"+TARGET_TABLE+"','"+TARGET_MTABLEID+"','"+SOURCE_TYPE+"','"+SOURCE_LEVEL+"','"+SOURCE_MTABLEID+"','"+RULETYPE+"','"+AGGREGATIONSCOPE+"');\n"
            if  self.properties['DELTACALCSUPPORT'] == '1':
                AGGREGATION = self.name + '_COUNT'
                VERSIONID = self.versionID
                RULEID = str(rowcount)
                rowcount += 1
                TARGET_TYPE = self.name
                TARGET_LEVEL ='COUNT'
                TARGET_TABLE = self.name + '_COUNT'
                TARGET_MTABLEID = self.versionID + ":" + self.name + ":" + "DAY"
                SOURCE_TYPE = self.name
                SOURCE_LEVEL = 'RAW'
                SOURCE_TABLE = self.name + "_RAW"
                SOURCE_MTABLEID = self.versionID + ":" + self.name + ":" + "RAW"
                AGGREGATIONSCOPE = 'DAY'
                RULETYPE = 'TOTAL'
                sqlstatement += "insert into dwhrep.Aggregationrule(AGGREGATION,VERSIONID,RULEID,TARGET_TYPE,TARGET_LEVEL,TARGET_TABLE,TARGET_MTABLEID,SOURCE_TYPE,SOURCE_LEVEL,SOURCE_MTABLEID,RULETYPE,AGGREGATIONSCOPE) values ('"+AGGREGATION+"','"+VERSIONID+"','"+RULEID+"','"+TARGET_TYPE+"','"+TARGET_LEVEL+"','"+TARGET_TABLE+"','"+TARGET_MTABLEID+"','"+SOURCE_TYPE+"','"+SOURCE_LEVEL+"','"+SOURCE_MTABLEID+"','"+RULETYPE+"','"+AGGREGATIONSCOPE+"');\n"
            return sqlstatement

        @deprecated
        def _generateAggregationSQL_INSERT(self):
            '''@deprecated 
            Generate Insert SQL statement For aggregation table
            
            Returns:
                    sqlstatement
            '''
            sqlstatement = ''
            if  self.properties['TOTALAGG'] == '1':
                sqlstatement += "insert into dwhrep.Aggregation(AGGREGATION,VERSIONID,AGGREGATIONTYPE,AGGREGATIONSCOPE) values ('"+self.name+"_DAY','"+self.versionID+"','TOTAL','DAY');\n"
            if  self.properties['DELTACALCSUPPORT'] == '1':
                sqlstatement += "insert into dwhrep.Aggregation(AGGREGATION,VERSIONID,AGGREGATIONTYPE,AGGREGATIONSCOPE) values ('"+self.name+"_COUNT','"+self.versionID+"','TOTAL','COUNT');\n"
            return sqlstatement
        
        @deprecated
        def _generateAggregationSQL_DELETE(self):
            '''@deprecated 
            \Generate DELETE SQL statement For aggregation table
            
            Returns:
                    sqlstatement
            '''
            sqlstatement  = "delete from dwhrep.Aggregation where versionid ='" + self.versionID +"' and aggregation like '" + self.name + "_%';"
            return sqlstatement
        
        @deprecated
        def _generateAggregationRuleSQL_DELETE(self):
            ''' @deprecated 
            Generate DELETE SQL statement For AggregationRule table
            
            Returns:
                    sqlstatement
            '''
            sqlstatement  = "delete from dwhrep.AggregationRule where versionid ='" + self.versionID +"' and aggregation like '" + self.name + "_%';"
            return sqlstatement
        
        @deprecated
        def _generateMeasurementColumnSQL_DELETE(self):
            '''@deprecated 
            Generate DELETE SQL statement For MeasurementColumn table
            
            Returns:
                    sqlstatement
            '''
            sqlstatement = "DELETE FROM dwhrep.measurementColumn where MTABLEID like'" + self.typeid + "%';"
            return sqlstatement
        
        
        @deprecated    
        def _generateBaseMeasurementColumnSQL_INSERT(self,server,typeid,List_mtableIDs,baseDefinition):
            '''@deprecated 
             Generate Insert Sql and Vals For MeasurementColumn table (Base Techpack columns)
            
            Generated at this (parent) level as table (MTABLEID) information needed for inserts
            
            Returns:
                    sql,vals 
            '''
                
            baseTPVersion = baseDefinition.split(':')[1]
            versionid = typeid.split(':')[0]
            rowNumber = 0
            measurementColumnDict = {} 
            for mtableid in List_mtableIDs:
                partitionType = str(mtableid).rsplit(':')[-1]
                baseMTableID = "TP_BASE:"+ baseTPVersion + ":" + partitionType
                #GET THE BASETECHPACK KEYS
                with TPAPI.DbAccess(server,'dwhrep') as crsr:
                    crsr.execute("SELECT * from dwhrep.measurementColumn where MTABLEID =?", (baseMTableID,))
                    desc = crsr.description
                    rows = crsr.fetchall()
                    for row in rows:
                        y = 0
                        measurementColumnDict[rowNumber] = {}
                        for x in desc:
                            measurementColumnDict[rowNumber][x[0]] = str(row[y])
                            y +=1  
                            measurementColumnDict[rowNumber]['RELEASEID'] = versionid
                            measurementColumnDict[rowNumber]['MTABLEID'] = mtableid   
                        rowNumber += 1
            for row in measurementColumnDict:    
                sql,vals = TPAPI.dictToSQL(measurementColumnDict[row],'measurementColumn')
            return sql,vals   

        @deprecated
        def _create(self,server,basetp): 
            '''@deprecated 
            Create and inserts the sql for a new table into the dwhrep
            
            SQL Executed:
                        INSERT_INTO_MEASUREMENTTYPECLASS...
                        INSERT_INTO_MEASUREMENTTYPE...
                        INSERT_INTO_MEASUREMENTTABLE..
                        INSERT_INTO_AGGREGATION...
                        INSERT_INTO_AGGREGATIONRULE..
            '''     
            
            self._generateMTABLEIDs()
            if self.tableType == 'Measurement':
                SQL_INSERT_MeasurementTypeClass,vals = self._generateMeasurementTypeClassSQL()
                self.logger.debug('INSERT_INTO_MEASUREMENTTYPECLASS: ' + str(SQL_INSERT_MeasurementTypeClass) + ":" + str(vals))
                with TPAPI.DbAccess(server,'dwhrep') as crsr:
                    crsr.execute("SELECT TYPECLASSID from dwhrep.measurementTypeClass where TYPECLASSID =?", (self.typeClassID ,))
                    row = crsr.fetchone()
                    if row != None:
                        #ie there is a row for the typeclassid already
                        pass
                    else:
                        self.logger.debug('INSERT_INTO_MEASUREMENTTYPECLASS: ' + str(SQL_INSERT_MeasurementTypeClass) + ":" + str(vals))
                        crsr.execute(SQL_INSERT_MeasurementTypeClass,vals )
                    
                SQL_INSERT_MeasurementType,vals = self._generateMeasurementTypeSQL_INSERT()    
                self.logger.debug('INSERT_INTO_MEASUREMENTTYPE: ' + str(SQL_INSERT_MeasurementType)+":"+str(vals))
                with TPAPI.DbAccess(server,'dwhrep') as crsr:
                    crsr.execute(SQL_INSERT_MeasurementType,vals)
                SQL_INSERT_MeasurementTableSQL = self._generateMeasurementTableSQL_INSERT()
                self.logger.debug('INSERT_INTO_MEASUREMENTTABLE: ' + str(SQL_INSERT_MeasurementTableSQL))
                with TPAPI.DbAccess(server,'dwhrep') as crsr:
                    crsr.execute(SQL_INSERT_MeasurementTableSQL)
                #Base Measurement Column Inserts
                SQL_INSERT_BaseMeasurementColumnSQL,vals = self._generateBaseMeasurementColumnSQL_INSERT(server,self.typeid,self.mtableIDs,basetp)
                self.logger.debug('INSERT_INTO_MEASUREMENTTABLE Base Keys: ' + str(SQL_INSERT_BaseMeasurementColumnSQL) + ":" + str(vals))
                with TPAPI.DbAccess(server,'dwhrep') as crsr:
                    crsr.execute(SQL_INSERT_BaseMeasurementColumnSQL,vals)
                for att in self.attributeObjects:
                    self.attributeObjects[att]._create(self.typeid,self.mtableIDs,basetp,server)
                #aggregation inserts
                SQLinsertAggregationSql = self._generateAggregationSQL_INSERT()
                self.logger.debug('INSERT_INTO_AGGREGATION: ' + str(SQLinsertAggregationSql))
                with TPAPI.DbAccess(server,'dwhrep') as crsr:
                        crsr.execute(SQLinsertAggregationSql)
                #aggregation rule inserts
                SQLinsertAggregationRule = self._generateAggregationRuleSQL_INSERT()
                self.logger.debug('INSERT_INTO_AGGREGATIONRULE: ' + str(SQLinsertAggregationRule))
                with TPAPI.DbAccess(server,'dwhrep') as crsr:
                    crsr.execute(SQLinsertAggregationRule)
        @deprecated
        def _upgrade(self,deltaTPV,server,basetp):
            '''@deprecated 
            update the sql for a modified table in the dwhrep
            
            '''  
            self.logger.debug(self.name+ "._upgrade()")
            #make sure mtableids are generated first
            self._generateMTABLEIDs()
            flag = 0
            if self.name in deltaTPV.measurementTableObjects:
                if self.tableType == 'Measurement':
                    classifications = [None,'DEFAULT','']
                    if deltaTPV.measurementTableObjects[self.name].universeClass not in classifications :
                        SQL_UPDATE_MeasurementTypeClass = self._generateMeasurementTypeClassSQL_UPDATE(server)
                        self.logger.debug('UPDATE_MEASUREMENTTYPECLASS: ' + str(SQL_UPDATE_MeasurementTypeClass))
                        with TPAPI.DbAccess(server,'dwhrep') as crsr:
                            crsr.execute(SQL_UPDATE_MeasurementTypeClass)
                    if len( deltaTPV.measurementTableObjects[self.name].properties) < 15 and len( deltaTPV.measurementTableObjects[self.name].properties) > 0:
                        for prop in  deltaTPV.measurementTableObjects[self.name].properties:
                            SQL_UPDATE_measurementType = self._generateMeasurementTypeSQL_UPDATE(prop,deltaTPV.measurementTableObjects[self.name].properties[prop])
                            self.logger.debug('UPDATE_MEASUREMENTTYPE: ' + str(SQL_UPDATE_measurementType))
                            with TPAPI.DbAccess(server,'dwhrep') as crsr:
                                crsr.execute(SQL_UPDATE_measurementType)  
                        propertiesThatRequireMeasurementTableinfo_andMeasurementColumnsToBeRegenerated = ['VECTORSUPPORT','DELTACALCSUPPORT','PLAINTABLE','RANKINGTABLE','TOTALAGG','SIZING']
                        
                        for prop in propertiesThatRequireMeasurementTableinfo_andMeasurementColumnsToBeRegenerated:
                            if prop in deltaTPV.measurementTableObjects[self.name].properties.keys():
                                flag = 1
                                #DELETIONS AND REGENERATION DUE TO FACT CERTAIN TABLE PROPERTY CHANGES
                                SQL_DELETE_AGGREGATIONRULE = self._generateAggregationRuleSQL_DELETE()
                                self.logger.debug('DELETE_AGGREGATIONRULE : ' + str(SQL_DELETE_AGGREGATIONRULE))
                                with TPAPI.DbAccess(server,'dwhrep') as crsr:
                                    crsr.execute(SQL_DELETE_AGGREGATIONRULE)
                                SQL_DELETE_AGGREGATION = self._generateAggregationSQL_DELETE()
                                self.logger.debug('DELETE_AGGREGATION : ' + str(SQL_DELETE_AGGREGATION))
                                with TPAPI.DbAccess(server,'dwhrep') as crsr:
                                    crsr.execute(SQL_DELETE_AGGREGATION)
                                SQL_DELETE_MeasurementColumn = self._generateMeasurementColumnSQL_DELETE()
                                self.logger.debug('DELETE_MEASUREMENTCOLUMN: ' + str(SQL_DELETE_MeasurementColumn))
                                with TPAPI.DbAccess(server,'dwhrep') as crsr:
                                    crsr.execute(SQL_DELETE_MeasurementColumn)
                                SQL_DELETE_MeasurementTable = self._generateMeasurementTableSQL_DELETE()
                                self.logger.debug('DELETE_MEASUREMENTTABLE: ' + str(SQL_DELETE_MeasurementTable))
                                with TPAPI.DbAccess(server,'dwhrep') as crsr:
                                    crsr.execute(SQL_DELETE_MeasurementTable)

                                SQL_INSERT_MeasurementTable = self._generateMeasurementTableSQL_INSERT()
                                self.logger.debug('INSERT_INTO_MEASUREMENTTABLE: ' + str(SQL_INSERT_MeasurementTable))
                                #print  SQL_INSERT_MeasurementTable
                                with TPAPI.DbAccess(server,'dwhrep') as crsr:
                                    crsr.execute(SQL_INSERT_MeasurementTable)
                            else:
                                #ie dont regenerate matableid stuff 
                                pass
                            if flag == 1: # ie change to certain table properties regenerate for all?
                                SQL_INSERT_BaseMeasurementColumnSQL,vals = self._generateBaseMeasurementColumnSQL_INSERT(server,self.typeid,self.mtableIDs,basetp)
                                self.logger.debug('INSERT_INTO_MEASUREMENTTABLE Base Keys: ' + str(SQL_INSERT_BaseMeasurementColumnSQL) + ":" + str(vals))
                                with TPAPI.DbAccess(server,'dwhrep') as crsr:
                                    crsr.execute(SQL_INSERT_BaseMeasurementColumnSQL,vals) 
                                for att in self.attributeObjects:
                                    SQL_INSERT_MeasColumnTableSQL,vals =  self.attributeObjects[att]._generateMeasurementColumnSQL_INSERT(server,self.typeid,self.mtableIDs,basetp)
                                    self.logger.debug('INSERT_INTO_MEASUREMENTCOLUMN: ' + str(SQL_INSERT_MeasColumnTableSQL) + ":" + str(vals))
                                    with TPAPI.DbAccess(server,'dwhrep') as crsr:
                                        crsr.execute(SQL_INSERT_MeasColumnTableSQL,vals)      
                                SQLinsertAggregationSql = self._generateAggregationSQL_INSERT()
                                self.logger.debug('INSERT_INTO_AGGREGATION: ' + str(SQLinsertAggregationSql))
                                with TPAPI.DbAccess(server,'dwhrep') as crsr:
                                        crsr.execute(SQLinsertAggregationSql)
                                SQLinsertAggregationRule = self._generateAggregationRuleSQL_INSERT()#
                                self.logger.debug('INSERT_INTO_AGGREGATIONRULE: ' + str(SQLinsertAggregationRule))
                                with TPAPI.DbAccess(server,'dwhrep') as crsr:
                                    crsr.execute(SQLinsertAggregationRule)
                    elif len( deltaTPV.measurementTableObjects[self.name].properties) == 15:
                        #this logic is wrong might not be a new table check the number of properties to be edited
                        #check if an entry for type class already exists in the db
                        with TPAPI.DbAccess(server,'dwhrep') as crsr:
                            crsr.execute("SELECT TYPECLASSID from dwhrep.measurementTypeClass where TYPECLASSID =?", (self.typeClassID ,))
                            row = crsr.fetchone()
                            if row != None:
                                #ie there is a row for the typeclassid already
                                pass
                            else:
                                SQL_INSERT_MeasurementTypeClass,vals = self._generateMeasurementTypeClassSQL()
                                self.logger.debug('INSERT_INTO_MEASUREMENTTYPECLASS: ' + str(SQL_INSERT_MeasurementTypeClass) + ":" + str(vals))
                                crsr.execute(SQL_INSERT_MeasurementTypeClass,vals )      
                        SQL_INSERT_MeasurementType,vals = self._generateMeasurementTypeSQL_INSERT()    
                        self.logger.debug('INSERT_INTO_MEASUREMENTTYPE: ' + str(SQL_INSERT_MeasurementType)+":"+str(vals))
                        with TPAPI.DbAccess(server,'dwhrep') as crsr:
                            crsr.execute(SQL_INSERT_MeasurementType,vals)
                        SQL_INSERT_MeasurementTableSQL = self._generateMeasurementTableSQL_INSERT()
                        self.logger.debug('INSERT_INTO_MEASUREMENTTABLE: ' + str(SQL_INSERT_MeasurementTableSQL))
                        with TPAPI.DbAccess(server,'dwhrep') as crsr:
                            crsr.execute(SQL_INSERT_MeasurementTableSQL)    
                        SQL_INSERT_BaseMeasurementColumnSQL,vals = self._generateBaseMeasurementColumnSQL_INSERT(server,self.typeid,self.mtableIDs,basetp)
                        self.logger.debug('INSERT_INTO_MEASUREMENTTABLE Base Keys: ' + str(SQL_INSERT_BaseMeasurementColumnSQL) + ":" + str(vals))
                        with TPAPI.DbAccess(server,'dwhrep') as crsr:
                            crsr.execute(SQL_INSERT_BaseMeasurementColumnSQL,vals)                                                
                        if len(deltaTPV.measurementTableObjects[self.name].attributeObjects) > 1:
                            for att in deltaTPV.measurementTableObjects[self.name].attributeObjects:
                                deltaAtt = deltaTPV.measurementTableObjects[self.name].attributeObjects[att]
                                self.attributeObjects[att]._upgrade(self.typeid,self.mtableIDs,basetp,deltaAtt,server)
                        else:
                            pass  
                        SQLinsertAggregationSql = self._generateAggregationSQL_INSERT()
                        self.logger.debug('INSERT_INTO_AGGREGATION: ' + str(SQLinsertAggregationSql))
                        with TPAPI.DbAccess(server,'dwhrep') as crsr:
                                crsr.execute(SQLinsertAggregationSql)
                        SQLinsertAggregationRule = self._generateAggregationRuleSQL_INSERT()#
                        self.logger.debug('INSERT_INTO_AGGREGATIONRULE: ' + str(SQLinsertAggregationRule))
                        with TPAPI.DbAccess(server,'dwhrep') as crsr:
                            crsr.execute(SQLinsertAggregationRule)
                    elif len( deltaTPV.measurementTableObjects[self.name].properties) == 0:
                        pass
                    if flag != 1: 
                        if len(deltaTPV.measurementTableObjects[self.name].attributeObjects) > 1:
                            for att in deltaTPV.measurementTableObjects[self.name].attributeObjects:
                                deltaAtt = deltaTPV.measurementTableObjects[self.name].attributeObjects[att]
                                self.attributeObjects[att]._upgrade(self.typeid,self.mtableIDs,basetp,deltaAtt,server)
                elif self.tableType == 'Reference':
                    #TODO
                    pass
          