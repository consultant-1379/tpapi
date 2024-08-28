# esalste
from __future__ import with_statement
import TPAPI
import logging
import re
import warnings
from TPAPI_Util import deprecated

class BusyHour(object):
        '''Class to represent Busy Hour object associated with a techpack version.
        Uniquely identified by the Busy Hour object name and the techpack versionID.'''
            
        def __init__(self,versionID,name):
            '''Class is instantiated with the versionID and name of the busy hour object
            
            Instance Variables:
            
                self.versionID:
                    Description: VersionID of the TechPackVersion
                    Type:String
                    
                self.name:
                    Description:Name of the busy hour object
                    Type:String
                    
                self.supportedTables:
                    Description: List of tables which retain data for this busy hour
                    Type:List
                    
                self.rankingTable:
                    Description: Ranking table of the busy hour object
                    Type:
                    
                self.busyHourTypeObjects:
                    Description: Dictionary of Child busy hour type objects
                    Type: Dictionary
                    Keys:
                        Child Busy Hour Type names
            
            '''
            self.logger = logging.getLogger('TPAPI.TPAPI_TP.BusyHour')
            self.versionID = versionID
            self.name = name
            self.supportedTables = []
            self.rankingTable = ''
            self.busyHourTypeObjects = {} 

        def _getPropertiesFromServer(self,server):
            '''Get the properties associated with the busy hour object'''
            self._getBusyHourTypes(server)
            self._getBusyHourSupportedTables(server)
            self._getBusyHourRankingTable(server)
            
        def _getBusyHourTypes(self,server):
            '''Gets the busyHour type information for the busy hour object
               
               This function will populate the busyHourTypeObjects dictionary with child busyhour types
               
               SQL Executed: 
                           SELECT BHTYPE FROM dwhrep.BUSYHOUR where VERSIONID=? AND BHOBJECT=?
   
               '''
            with TPAPI.DbAccess(server,'dwhrep') as crsr:
                crsr.execute("SELECT BHTYPE FROM dwhrep.BUSYHOUR where VERSIONID=? AND BHOBJECT=?",(self.versionID,self.name,))
                resultset = crsr.fetchall()
                for row in resultset:
                    bt = BusyHourType(self.versionID,self.name,row[0])
                    bt._getPropertiesFromServer(server)
                    self.busyHourTypeObjects[str(row[0])] = bt
        
        def _getBusyHourSupportedTables(self,server):
            '''Gets the list of measurement tables which load for (support) the busy hour object'''
            with TPAPI.DbAccess(server,'dwhrep') as crsr:
                crsr.execute("SELECT DISTINCT BHTARGETTYPE FROM dwhrep.BUSYHOURMAPPING where VERSIONID=? AND BHOBJECT=?",(self.versionID,self.name,))
                resultset = crsr.fetchall()
                for row in resultset:
                    self.supportedTables.append(str(row[0]))
        
        def _getBusyHourRankingTable(self,server):
            '''Gets the Ranking Table associated with the busyhour object'''
            with TPAPI.DbAccess(server,'dwhrep') as crsr:
                if self.name == 'ELEM':
                    self.rankingTable = self.versionID.rsplit(':')[0] + "_ELEMBH"
                else:
                    crsr.execute("SELECT DISTINCT BHLEVEL FROM dwhrep.BUSYHOURMAPPING where VERSIONID=? AND BHOBJECT=?",(self.versionID,self.name,))
                    row = crsr.fetchone()
                    if row is not None:
                        self.rankingTable = str(row[0])

        def _toXML(self,offset=0):
            '''Write the object to an xml formatted string
            
            Offset value is used for string indentation. Default to 0
            Parent toXML() method is responsible for triggering child object toXML() methods.
    
            Return Value: xmlString 
            '''
            offset += 4
            os = "\n" + " "*offset
            os2 = os+" "*offset
            os3 = os2+" "*offset
            os4 = os3+" "*offset
            os5 = os4+" "*offset
            outputXML = os2+'<BusyHour>'
            outputXML += os3+'<BusyHourObjectName>'+ str(self.name) +'</BusyHourObjectName>'
            outputXML += os3+'<RankingTable>'+ str(self.rankingTable) +'</RankingTable>'
            outputXML += os3+'<BusyHourSupportedTables>'  
            for table in self.supportedTables:  
                    outputXML += os4+'<BHSupportedTable>'+ table +'</BHSupportedTable>'          
            outputXML += os3+'</BusyHourSupportedTables>'  
            outputXML += os3+'<BusyHourTypes>' 
            for bhtype in self.busyHourTypeObjects:
                outputXML += self.busyHourTypeObjects[bhtype]._toXML(offset)
            outputXML += os3+'</BusyHourTypes>'  
            outputXML += os2+'</BusyHour>'  
            return outputXML 
 
        def _getPropertiesFromXML(self,xmlElement):
            '''Populates the objects content from an xmlElement.
            
            The method is also responsible for triggering its child objects getPropertiesFromXML() method'''
            
            self.logger.info(self.name + " Inside _getPropertiesFromXML function")
            for elem in xmlElement:
                if elem.tag=='BusyHourObjectName':
                    for elem1 in elem:
                        self.name = TPAPI.safeNull(elem1.text)
                if elem.tag=='RankingTable': 
                    self.rankingTable = TPAPI.safeNull(elem.text)
                if elem.tag=='BusyHourSupportedTables':
                    for elem3 in elem:
                            self.supportedTables.append(TPAPI.safeNull(elem3.text))
                if elem.tag== 'BusyHourTypes':   
                    for elem1 in elem:
                        bht = TPAPI.BusyHourType(self.versionID,self.name,elem1.attrib['name'])
                        bht._getPropertiesFromXML(elem1)
                        self.busyHourTypeObjects[elem1.attrib['name']] = bht


        def _getPropertiesFromTPI(self,tpiDict=None,filename=None):
            '''Populate the objects contents from a tpiDict object or tpi file.
            
            If a tpi file is passed it is converted to a tpiDict object before processing
            
            Exceptions: 
                       Raised if tpiDict and filename are both None (ie nothing to process)'''
            
            self.logger.debug(self.name + "._getPropertiesFromTPI()")
            if tpiDict==None and filename==None:
                strg = 'getPropertiesFromTPI() Nothing to Process'
                raise Exception(strg)
                self.logger.error(strg)
            else:
                if filename is not None:
                    tpidict = TPAPI.TpiDict(filename).returnTPIDict()
                for row in tpiDict['Busyhour']['BHOBJECT']:
                    if tpiDict['Busyhour']['BHOBJECT'][row] == self.name:
                        bht = TPAPI.BusyHourType(self.versionID,self.name,tpiDict['Busyhour']['BHTYPE'][row])
                        bht._getPropertiesFromTPI(tpiDict)
                        self.busyHourTypeObjects[tpiDict['Busyhour']['BHTYPE'][row]] = bht            
                if 'Busyhourmapping' in tpiDict:         
                    for row in tpiDict['Busyhourmapping']['BHOBJECT']:
                        if tpiDict['Busyhourmapping']['BHOBJECT'][row] == self.name: 
                            if tpiDict['Busyhourmapping']['BHTARGETTYPE'][row] not in self.supportedTables:
                                self.supportedTables.append(tpiDict['Busyhourmapping']['BHTARGETTYPE'][row])  
                if self.name == 'ELEM':
                    self.rankingTable = self.versionID.rsplit(':')[0] + "_ELEMBH"
                else:    
                    if 'Busyhourmapping' in tpiDict:
                        for row in tpiDict['Busyhourmapping']['BHOBJECT']:
                            if tpiDict['Busyhourmapping']['BHOBJECT'][row] == self.name: 
                                if tpiDict['Busyhourmapping']['BHLEVEL'][row] not in self.supportedTables:
                                    self.rankingTable = tpiDict['Busyhourmapping']['BHLEVEL'][row]

        def _difference(self,bhObject,deltaObj,deltaTPV):
            '''Calculates the difference between two busy hour objects
            
            Method takes bhObject,deltaObj and deltaTPV as inputs.
            bhObject: The Busy Hour object to be compared against
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
            deltaObj.stack.append('BusyHour='+self.name)
            diffFlag = False
            deltaBHObj = TPAPI.BusyHour(self.versionID,self.name)        
            origBusyHourTypeObjects = list(self.busyHourTypeObjects.keys())
            upgradeBusyHourTypeObjects= list(bhObject.busyHourTypeObjects.keys())
            deltaBusyHourTypeObjects = set(upgradeBusyHourTypeObjects).difference(set(origBusyHourTypeObjects))
            removedBusyHourTypeObjects = set(origBusyHourTypeObjects).difference(set(upgradeBusyHourTypeObjects))
            commonBusyHourTypeObjects = set(upgradeBusyHourTypeObjects).intersection(set(origBusyHourTypeObjects))
            
            for bht in removedBusyHourTypeObjects:
                deltaObj.stack.append("BHTYPE=<deleted>"+bht)
                for prop in self.busyHourTypeObjects[bht].properties:
                    deltaObj.stack.append("Property=<deleted>"+prop)
                    origVal = self.busyHourTypeObjects[bht].properties[prop]
                    deltaObj._addChange(deltaObj.stack,None,origVal)
                    deltaObj.stack.pop()
                diffFlag = True
                deltaObj.stack.pop()
            #New BusyHourType
            for bht in deltaBusyHourTypeObjects:
                deltaObj.stack.append("BHTYPE=<new>"+bht)
                deltabht = BusyHourType(self.versionID, bhObject.name,bht)
                for prop in bhObject.busyHourTypeObjects[bht].properties:
                    deltaObj.stack.append("Property=<new>"+prop)
                    deltaVal = bhObject.busyHourTypeObjects[bht].properties[prop]
                    deltaObj._addChange(deltaObj.stack,deltaVal,None)
                    deltabht.properties[prop] = deltaVal
                    deltaObj.stack.pop()
                diffFlag = True
                deltaObj.stack.pop()
                deltaBHObj.busyHourTypeObjects[bht] = deltabht
                deltaTPV.busyHourObjects[self.name] = deltaBHObj
            #common BusyHourTypes
            for bht in commonBusyHourTypeObjects:
                dummyFlag,deltaObj,deltaTPV = self.busyHourTypeObjects[bht]._difference(bhObject.busyHourTypeObjects[bht],deltaObj,deltaTPV)
            ################################################################
            # BH Support Tables Diff
            for table in bhObject.supportedTables:
                if table not in self.supportedTables:
                    deltaObj.stack.append('Property=<new>supportedTables')
                    deltaVal = table
                    deltaObj._addChange(deltaObj.stack,deltaVal,None)
                    deltaBHObj.supportedTables.append(deltaVal)
                    diffFlag = True
                    deltaObj.stack.pop()
            # removed supportedTables          
            for table in self.supportedTables:
                if table not in bhObject.supportedTables:
                    deltaObj.stack.append('Property=<deleted>supportedTables')
                    origVal = table
                    deltaObj._addChange(deltaObj.stack,None,origVal)
                    deltaObj.stack.pop()
                    diffFlag = True 
            if diffFlag == True:
                deltaTPV.busyHourObjects[self.name] = deltaBHObj
                diffFlag = False
            deltaObj.stack.pop()
            return diffFlag,deltaObj,deltaTPV

########################################################################################################

class BusyHourType(object):
    
        '''Class to represent Busy Hour Type. Child object of Busy Hour.
        Uniquely identified by the versionID, busy hour type, busy hour name.'''
        
        def __init__(self,versionID,bhobjectname,bhtype):
            '''Class is instantiated with versionID, parent bhObjectName and bhtype name
            
            Instance Variables:
            
                self.name:
                    Description: Busy Hour Type Name ge. PP1
                    Type:String
                    
                self.versionID:
                    Description: VersionID of the TechPackVersion
                    Type:String
                    
                self.properties:
                    Description: Contains the properties of the Busy Hour Type
                    Type:Dictionary
                        KEYS:
                        
                self.BHOBjectName:
                    Description: Name of the Parent Busy Hour Object
                    Type:String
            '''
            self.logger = logging.getLogger('TPAPI.TPAPI_TP.BusyHourType')
            self.name = bhtype
            self.versionID = versionID
            self.properties = {}
            self.BHOBjectName = bhobjectname

        def _getPropertiesFromServer(self,server):
            '''Get all the properties associated with the busy hourType object'''
            with TPAPI.DbAccess(server,'dwhrep') as crsr:
                crsr.execute("SELECT BHCRITERIA,WHERECLAUSE,DESCRIPTION,BHELEMENT,ENABLE FROM dwhrep.BUSYHOUR where VERSIONID=? AND BHTYPE=? AND BHOBJECT=?",(self.versionID,self.name,self.BHOBjectName,))
                resultset = crsr.fetchall()
                for row in resultset:
                    self.properties['BHCRITERIA'] = str(row[0])
                    self.properties['WHERECLAUSE'] = str(row[1])
                    self.properties['DESCRIPTION'] = str(row[2])
                    self.properties['BHELEMENT'] = str(row[3])
                    self.properties['ENABLE'] = str(row[4])
        
        def _toXML(self,offset=0):
            '''Write the object to an xml formatted string
            
            Offset value is used for string indentation. Default to 0
            Parent toXML() method is responsible for triggering child object toXML() methods.
    
            Return Value: xmlString 
            '''
            offset += 4
            os = "\n" + " "*4
            os2 = os+" "*offset
            os3 = os2+" "*offset
            os4 = os3+" "*offset
            os5 = os4+" "*offset
            outputXML = os4+'<BusyHourType name="' + self.name +'">'
            for prop in self.properties:
                outputXML += os5+'<'+str(prop)+'>'+ TPAPI.escape(self.properties[prop]) +'</'+str(prop)+'>'
            outputXML += os4+'</BusyHourType>'
            return outputXML 

        def _getPropertiesFromXML(self,xmlElement):
            '''Populates the objects content from an xmlElement.
            
            The method is also responsible for triggering its child objects getPropertiesFromXML() method'''
            
            self.logger.info(self.name + " Inside getPropertiesFromXML function")
            for prop1 in xmlElement:
                self.properties[prop1.tag] = TPAPI.safeNull(prop1.text)

        def _getPropertiesFromTPI(self,tpiDict=None,filename=None):
            '''Populate the objects contents from a tpiDict object or tpi file.
            
            If a tpi file is passed it is converted to a tpiDict object before processing
            
            Exceptions: 
                       Raised if tpiDict and filename are both None (ie nothing to process)'''
            
            self.logger.debug(self.name + "._getPropertiesFromTPI()")
            if tpiDict==None and filename==None:
                strg = 'getPropertiesFromTPI() Nothing to Process'
                raise Exception(strg)
                self.logger.error(strg)
            else:
                if filename is not None:
                    tpidict = TPAPI.TpiDict(filename).returnTPIDict()
                for row in tpiDict['Busyhour']['BHOBJECT']:
                    if tpiDict['Busyhour']['BHOBJECT'][row] == self.BHOBjectName and tpiDict['Busyhour']['BHTYPE'][row] == self.name:
                        self.properties['BHCRITERIA'] = tpiDict['Busyhour']['BHCRITERIA'][row]
                        self.properties['WHERECLAUSE'] = tpiDict['Busyhour']['WHERECLAUSE'][row]
                        self.properties['DESCRIPTION'] = tpiDict['Busyhour']['DESCRIPTION'][row]
                        self.properties['BHELEMENT'] = tpiDict['Busyhour']['BHELEMENT'][row]
                        self.properties['ENABLE'] = tpiDict['Busyhour']['ENABLE'][row]
                        
        def _difference(self,bhTypeObject,deltaObj,deltaTPV):
            '''Calculates the difference between two busy hour type objects
            
            Method takes bhTypeObject,deltaObj and deltaTPV as inputs.
            bhTypeObject: The Busy Hour Type object to be compared against
            DeltaObj: The single object that gets passed through the entire diff recording the changes.
            DeltaTPV: A TechPackVersion Object that gets passed through the entire diff recording only new content.
            
            The Difference method will trigger the difference method of its child objects, passing
            in the object to compare, deltaObj and deltaTPV. After calculating the diff the child object passes these objects
            back in conjunction with a flag to say whether a (only new or changed content.. not deleted) was found or not. This flag is used to decide
            whether a child object should be added to the parent object in the DeltaTPV.
            
            Note: BHType does not have any child objects
            
            Returns:
                    diffFlag (Boolean indicating where a change was found or not)
                    deltaObj
                    deltaTPV 
            
            '''
            
            deltaObj.stack.append('BusyHourObject='+self.BHOBjectName)
            diffFlag = False
            deltaBHObj = TPAPI.BusyHour(self.versionID,self.BHOBjectName)           
            deltaObj.stack.append("BHTYPE="+self.name)
            commonBHTypePropertiesDelta = TPAPI.DictDiffer(self.properties,bhTypeObject.properties)
            
            if commonBHTypePropertiesDelta.changed():
                deltabht = BusyHourType(self.versionID,bhTypeObject.BHOBjectName,self.name)
                for prop in commonBHTypePropertiesDelta.changed():
                    diffFlag = True
                    deltaObj.stack.append("Property=<changed>"+prop)
                    origVal = self.properties[prop]
                    deltaVal = bhTypeObject.properties[prop]
                    deltaObj._addChange( deltaObj.stack,deltaVal,origVal)
                    deltabht.properties[prop] = deltaVal
                    deltaObj.stack.pop()
                deltaBHObj.BHTypes[self.name] = deltabht
                deltaTPV.busyHourObjects[self.BHOBjectName] = deltaBHObj
            deltaObj.stack.pop()  
            deltaObj.stack.pop()
            return diffFlag,deltaObj,deltaTPV
        
     