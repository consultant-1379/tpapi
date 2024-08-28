'''Copyright Ericsson.. Created 06 Dec 2011 
esalste,esiranv,epausmi'''

from __future__ import with_statement
from xml.etree import ElementTree
import TPAPI
import string
import re
import logging
import traceback
import sys
import warnings
from TPAPI_Util import deprecated


class TechPackVersion(object):
    '''Class to represent a version of a TechPack in TPAPI.

     '''
    
    def __init__(self,versionID=None):
        '''If the versionID is not specified an empty object will be created with versionID set to default value of "UNINITIALISED:((0))". 
        When an UNINITIALISED techpack gets its properties from a tpi the versionID is updated from inside the file.
        When an INITIALISED techpack reads it properties from an xml file, its versionID is not updated from inside the file
        
        
        Instance Variables:
           self.versionID:
                Description: versionID of the techpack version. eg DC_E_BSS:((100)).
                Type:String
                
           self.tpName:
                Description: Name of the techpack. eg DC_E_BSS
                Type:String
                
           self.versionNumber:
               Description: versionNumber of the techpack version with brackets. eg ((100))
               Type:String
            
           self.versionNo:
               Description: versionNo of the techpack versions without brackets: eg 100
               Type:String (int)
               
           self.versioning: 
               Description: Stores top level versioning (properties) information of the techpack version.
               Type: Dictionary
               Keys: VERSIONID, DESCRIPTION, STATUS, TECHPACK_NAME, TECHPACK_VERSION, TECHPACK_TYPE,
                       PRODUCT_NUMBER, LOCKEDBY, LOCKDATE, BASEDEFINITION, BASEVERSION, INSTALLDESCRIPTION,
                       UNIVERSENAME, UNIVERSEEXTENSION, ENIQ_LEVEL, LICENSENAME
                       
           self.measurementTableNames: 
               Description: Measurement table (names) associated with the techpack version.
               Type: List
               
           self.measurementTableObjects: 
               Description: Measurement table objects associated with the techpack version.
               Type: Dictionary
               Keys: Measurement table names
               
           self.referenceTableNames:
               Description: Reference table (names) associated with the techpack version.
               Type: List
           
           self.referenceTableObjects:
               Description: Reference table object associated with the techpack version.
               Type: Dictionary
               Keys: Reference table names
           
           self.supportedVendorReleases:
               Description: Vendor Releases that the techpack version supports.
               Type: List
        
           self.busyHourNames:
               Description: Busy Hour Object (names) associated with the techpack version.. eg UPLINK.
               Type: List
               
           self.busyHourObjects:
               Description: Busy Hour Objects associated with the techpack version.
               Type: Dictionary
               Keys: Busy Hour Object Names
               
           self.groupTypes:
               Description: ENIQ Events only. Dictionary containing groupType information.
               Type: Dictionary of Dictionaries
               Keys: GROUPTYPE
                   Sub Keys: DATANAME, DATATYPE, DATASIZE, DATASCALE, NULLABLE
               
           self.externalStatementObjects:
               Description: External Statement Objects associated with the techpack version.
               Type: Dictionary
               Keys: External Statement Name
               
           self.interfaceNames:
               Description: InterfaceNames and versions associated with the techpack version. Dictionary value is the interface version.
               Type: Dictionary
               Keys: name of the interface
               
           self.interfaceObjects:
               Description: Interface Objects associated with the techpack version.
               Type: Dictionary
               Keys: name of the interface
               
           self.collectionSetID:
               Description: CollectionSetID of the Techpack version. Used to retrieve etlrep information from the database.
               Type: int
               
           self.etlrepMetaCollectionSetObject:
               Description: etlrepMetaCollectionSetObject associated with the techpack version.
               Type: etlrepMetaCollectionSet Object
        
           '''
        self.logger = logging.getLogger('TPAPI.TPAPI_TP.TechPackVersion') 
        self.versionID = None
        self.tpname = None
        self.versionNumber = None
        self.versionNo = None
        self._intialiseVersion(versionID) #Version ID is parsed to get further information from string for versionNumber,versionNo,versionID
        self.logger.debug('Created TechPackVersion instance with versionid =' + self.versionID)
        self.versioning = {}
        self.measurementTableNames = []
        self.measurementTableObjects = {}
        self.referenceTableNames = []
        self.referenceTableObjects = {}
        self.supportedVendorReleases = []
        self.busyHourNames = []
        self.busyHourObjects = {}
        self.groupTypes = {} # events
        self.externalStatementObjects = {}
        self.interfaceNames = {} 
        self.interfaceObjects = {}
        self.collectionSetID = None # could possibly be hidden
        self.etlrepMetaCollectionSetObject = None  # could possibly be hidden

    def _intialiseVersion(self, versionID):
        '''Initialise the TechPackVersion versionID.
        If versionID string is none, the TechPackVersion versionID is populated with a default value of UNINITIALISED:((0))
        TechPackVersion tpName and versionNumber,versionNo properties are set by parsing the versionID string.
        '''
        
        if versionID == None:
            versionID = 'UNINITIALISED:((0))'
        self.tpName = versionID.rsplit(':')[0]
        self.versionNumber = versionID.rsplit(':')[1]
        try:
            self.versionNo = re.search('\(\((.*)\)\)',versionID).group(1)   # build number ie without the brackets eg '6'
        except:
            self.logger.error('Could not get versionNo from versionID ' + versionID)
            return
        self.versionID = versionID
        self.logger.debug(versionID + ".intialiseVersion()")
        
        
    def getPropertiesFromServer(self,server):
        '''Populates the model of the TechPackVersion from metadata on the server
        
        This is a container method for triggering a sequence of methods that populate
        individual parts of the model.
        '''
        self.logger.debug(self.versionID + ".getPropertiesFromServer()")
        self._getVersioning(server)    
        self._getFactTables(server)
        self._getReferenceTables(server)
        self._getInterfaceNames(server)
        self._getInterfaceObjects(server)
        self._getFactTableObjects(server)
        self._getReferenceTableObjects(server)
        self._getBusyHours(server)
        self._getBusyHourObjects(server)
        self._getExternalStatements(server)
        self._getSupportedVendorReleases(server)
        self._getCollectionSetID(server)
        if self.collectionSetID: # Some TPs may not have set information created initially so a check is carried out before attempting to retrieve set information
            self._getEtlrepSetCollectionObject(server)
        if self.versioning['TECHPACK_TYPE'] == 'ENIQ_EVENT':
            self.logger.debug(self.versionID + " = ENIQ EVENTS TECHPACK")
            self._getGroupTypes(server)


    def getPropertiesFromTPI(self,tpiDict=None,filename=None): 
        '''Populate the objects contents from a tpiDict object or tpi file.
        
        If a tpi file is passed it is converted to a tpiDict object before processing.

        Exceptions: 
                   Raised if tpiDict and filename are both None (ie nothing to process)
                   Raised if there is tpi dict key error
                   '''
                   
            
        
        self.logger.debug(self.versionID + ".getPropertiesFromTPI()")

        dict = {'Versioning' : self._tpiVersioning,
        'Measurementtype' : self._tpiMeasurementType,
        'Referencetable' : self._tpiReferenceTable,
        'Busyhour' : self._tpiBusyHour,
        'Supportedvendorrelease' : self._tpiSupportedVendorRelease,
        'Externalstatement' : self._tpiExternalStatement,
        'InterfaceTechpacks' : self._tpiInterfaceTechpacks,
        'META_COLLECTION_SETS' : self._tpiMetaCollectionSets,
        }
        
        if tpiDict==None and filename==None:
            strg = 'getPropertiesFromTPI() Nothing to Process'
            raise Exception(strg)
            self.logger.error(strg)
        else:
            if filename is not None:
                self.logger.debug('getPropertiesFromTPI() extracting from ' + filename)
                tpiDict = TPAPI.TpiDict(filename).returnTPIDict()
            self._tpiVersioning(tpiDictionary=tpiDict)
            for key in tpiDict: 
                try:
                    if key in dict:
                        dict.get(key)(tpiDictionary=tpiDict)
                except:
                    traceback.print_exc(file=sys.stdout)

                    
                    
                    pass
#TODO Throw exception lower down
                    strg  = 'getPropertiesFromTPI() tpi dict key error = ' + key
                    raise Exception(strg)
                    self.logger.error(strg)
                    
        
    def _tpiMeasurementType(self, tpiDictionary):
            '''Extracts MeasurementType information from the tpiDictionary'''
            for row in tpiDictionary['Measurementtype']['TYPENAME']:
                self.measurementTableNames.append(tpiDictionary['Measurementtype']['TYPENAME'][row])
                ft = TPAPI.Table(tpiDictionary['Measurementtype']['TYPENAME'][row],self.versionID)
                ft.tableType = 'Measurement'
                ft._getPropertiesFromTPI(tpiDictionary)
                self.measurementTableObjects[ft.name] = ft
     
    def _tpiReferenceTable(self, tpiDictionary):    
            '''Extracts referenceType information from the tpiDictionary'''             
            for row in tpiDictionary['Referencetable']['TYPENAME']:
                self.referenceTableNames.append(tpiDictionary['Referencetable']['TYPENAME'][row])
                ft = TPAPI.Table(tpiDictionary['Referencetable']['TYPENAME'][row],self.versionID)
                ft.tableType = 'Reference'
                ft._getPropertiesFromTPI(tpiDictionary)
                self.referenceTableObjects[ft.name] = ft
                    
    def _tpiBusyHour(self, tpiDictionary):
            '''Extracts BusyHour information from the tpiDictionary'''            
            for row in tpiDictionary['Busyhour']['BHOBJECT']:
                if tpiDictionary['Busyhour']['BHOBJECT'][row] not in self.busyHourNames:
                    
                    self.busyHourNames.append(tpiDictionary['Busyhour']['BHOBJECT'][row])
     
            for bh in self.busyHourNames:
                bho = TPAPI.BusyHour(self.versionID,bh)
                bho._getPropertiesFromTPI(tpiDictionary)
                self.busyHourObjects[bh] = bho  
            
            
    def _tpiSupportedVendorRelease(self, tpiDictionary):
            '''Extracts SupportedVendorRelease information from the tpiDictionary'''           
            for row in tpiDictionary['Supportedvendorrelease']['VENDORRELEASE']:
                self.supportedVendorReleases.append(tpiDictionary['Supportedvendorrelease']['VENDORRELEASE'][row])
                 
            
    def _tpiExternalStatement(self, tpiDictionary):   
            '''Extracts ExternalStatement information from the tpiDictionary'''            
            for row in tpiDictionary['Externalstatement']['STATEMENTNAME']:
                ext = TPAPI.ExternalStatement(self.versionID, tpiDictionary['Externalstatement']['STATEMENTNAME'][row])
                ext._getPropertiesFromTPI(tpiDict=tpiDictionary)
                self.externalStatementObjects[tpiDictionary['Externalstatement']['STATEMENTNAME'][row]] = ext
             

    def _tpiInterfaceTechpacks(self, tpiDictionary):                
            '''Extracts InterfaceTechpacks information from the tpiDictionary'''
            for row in tpiDictionary['InterfaceTechpacks']['interfacename']:
                self.interfaceNames[tpiDictionary['InterfaceTechpacks']['interfacename'][row]] = tpiDictionary['InterfaceTechpacks']['interfaceversion'][row]
            for intf in self.interfaceNames:
                intfObject = TPAPI.InterfaceVersion(intf,self.interfaceNames[intf])
                intfObject.getPropertiesFromTPI(tpiDict=tpiDictionary)
                self.interfaceObjects[intf] = intfObject            
                
             
             
    def _tpiMetaCollectionSets(self, tpiDictionary):
        '''Extract EtlrepMestatCollectionObject information from the tpiDictionary'''

        self._tpiVersioning(tpiDictionary=tpiDictionary)             
        for row in tpiDictionary['META_COLLECTION_SETS']['COLLECTION_SET_NAME']:
            self.collectionSetID = tpiDictionary['META_COLLECTION_SETS']['COLLECTION_SET_ID'][row]
            metaCollectionSetObject = TPAPI.EtlrepSetCollection(self.tpName,self.versionNumber)
            metaCollectionSetObject.getPropertiesFromTPI(tpiDictionary)
            self.etlrepMetaCollectionSetObject = metaCollectionSetObject


    def _tpiVersioning(self, tpiDictionary):
        '''Extracts Versioning information from the tpiDictionary'''
        self._intialiseVersion(tpiDictionary['Versioning']['VERSIONID'][1])
        for column in tpiDictionary['Versioning']:
            self.versioning[column] = TPAPI.checkNull(tpiDictionary['Versioning'][column][1])

    def addInterface(self,interfaceVersionObject):
        '''Add Interface to self.interfaceObjects dictionary of the TechPackVersion
        '''
        self.interfaceObjects[interfaceVersionObject.name] = interfaceVersionObject
    
    
    def removeInterface(self,interfaceVersionName):
        '''Remove Interface from the dictionary of interface objects of the TechPackVersion
         '''
        del self.interfaceObjects[interfaceVersionName]
  
    def _getVersioning(self,server):
        '''Populate the versioning dictionary of the TechPackVersion from the server
        
        SQL Statement:
                 SELECT * from dwhrep.Versioning where VERSIONID =?
        Exceptions:
                 Raised if the Techpack is not present on the server
        ''' 
        
        self.logger.debug(self.versionID + "._getVersioning()")
        with TPAPI.DbAccess(server,'dwhrep') as crsr:
            crsr.execute("SELECT * from dwhrep.Versioning where VERSIONID =?", (self.versionID,))
            desc = crsr.description
            row = crsr.fetchone()
            if row is not None:
                self.versioning = {}
                i = 0
                for x in desc:
                    value = str(row[i])
                    if x[0] == 'STATUS':
                        value = TPAPI.strFloatToInt(value)
                    self.versioning[x[0]] = value
                    i+=1
            else:
                strg = self.versionID + ": Techpack not installed on server"
                self.logger.warning(strg)
                raise Exception(strg)
        # Force compulsory values
        if 'TECHPACK_TYPE' not in self.versioning:
            self.versioning['TECHPACK_TYPE'] = 'Not set'
        if 'TECHPACK_VERSION' not in self.versioning:
            self.versioning['TECHPACK_VERSION'] = self.versionID

    def _getFactTables(self,server):
        '''Populate measurementTableNames list with the table names from the server
    
        SQL Statement:
                "SELECT TYPENAME from dwhrep.MeasurementType where VERSIONID =?
        '''
        self.logger.debug(self.versionID + ".getFactTables()")
        with TPAPI.DbAccess(server,'dwhrep') as crsr:
            crsr.execute("SELECT TYPENAME from dwhrep.MeasurementType where VERSIONID =?", (self.versionID,))
            self.measurementTableNames = TPAPI.rowToList(crsr.fetchall())
            
    def _getFactTableObjects(self,server):
        '''Get measurement table objects associated with the TechPackVersion from the server.
        
        Creates measurementTableVersion objects using names from the measurementTable list.
        Calls the TPAPI_Table.getPropertiesFromServer() method on the measurementTableVersion
        and then adds the measurementTableVersion object to the measurementTableObjects dictionary
        '''
        self.logger.debug(self.versionID + ".getFactTableObjects()")
        for measurementtable in self.measurementTableNames:
            ft = TPAPI.Table(measurementtable,self.versionID)
            if self.versioning['TECHPACK_TYPE'] == 'ENIQ_EVENT':
                ft._getEventsPropertiesFromServer(server)
            else:
                ft._getPropertiesFromServer(server)
            self.measurementTableObjects[ft.name] = ft # add table object to the measurementtable dictionary
    
    def _getReferenceTables(self,server):
        '''Populate referenceTableNames list with the table names from the server
        
        SQL Statement:
                "SELECT TYPENAME from dwhrep.dwhrep.ReferenceTable where VERSIONID =?
        '''
        self.logger.debug(self.versionID + ".getReferenceTables()")
        with TPAPI.DbAccess(server,'dwhrep') as crsr:
            crsr.execute("SELECT TYPENAME from dwhrep.ReferenceTable where VERSIONID =?", (self.versionID,))
            self.referenceTableNames = TPAPI.rowToList(crsr.fetchall())
            
    def _getReferenceTableObjects(self,server):
        '''Get reference table objects associated with the TechPack Version from the server
        
        Creates factTableVersion objects using the names from the referenceTable list.
        Calls the TPAPI_Table.getPropertiesFromServer() method on the referenceTableVersion
        and then adds the referenceTableVersion object to the referenceTableObjects dictionary
        '''
        self.logger.debug(self.versionID + ".getReferenceTableObjects()")
        for refTable in self.referenceTableNames:
            rt = TPAPI.Table(refTable,self.versionID)
            rt._getPropertiesFromServer(server)
            self.referenceTableObjects[rt.name] = rt
              
    #TODO Rename to getInterfaceInformation
    def _getInterfaceNames(self,server):
        '''Gets the interfaces dependent on the techpack
        
        Gets all interface information from the server for the techpack, and does a comparison using TPAPI.compareRStates to discover
        if the particular interface is dependent on the techpack version. If it is dependent a self.interfaces dictionary is
        populated with interface name and the InterfaceVersion object. This information is used to instantiate interface objects.
        
        SQL Statement:
                SELECT TECHPACKVERSION, INTERFACENAME,INTERFACEVERSION FROM dwhrep.InterfaceTechpacks WHERE TECHPACKNAME =?  
        '''
        self.logger.debug(self.versionID + ".getInterfaceNames()")
        with TPAPI.DbAccess(server,'dwhrep') as crsr:
            crsr.execute("SELECT TECHPACKVERSION, INTERFACENAME,INTERFACEVERSION FROM dwhrep.InterfaceTechpacks WHERE TECHPACKNAME =?", (self.tpName,) )
            resultset = crsr.fetchall()
            for row in resultset:
                tpVersion=str(row[0])
                #TODO is a try necessary?
                try : 
                    if self.versioning['TECHPACK_VERSION'] == tpVersion or TPAPI.compareRStates(self.versioning['TECHPACK_VERSION'], tpVersion):
                        self.interfaceNames[str(row[1])] = str(row[2])
                except:
                    #Interface not dependent
                    pass

            
    def _getInterfaceObjects(self,server):

        '''Gets dependant interface objects associated with the TechPack Version from the server
        
        Using the information in the interfaces dictionary InterfaceVersion objects are
        created and the TPAPI_Intf.getPropertiesFromServer() method is called for each.
        InterfaceVersion Objects are then appended to the interfaceObject dictionary
        '''
        self.logger.debug(self.versionID + ".getInterfaceObjects()")
        for intf in self.interfaceNames:
            intfObject = TPAPI.InterfaceVersion(intf,self.interfaceNames[intf])
            intfObject.getPropertiesFromServer(server)
            self.interfaceObjects[intf] = intfObject
                

    def _getBusyHours(self,server):
        '''Get the list of all busy hour object names associated with the TP from the server

        The Busy Hour names are appended to busyHourNames list. This list of name is used to 
        create Busy Hour objects in the TechPackVersion model
        
        SQL Statement:
                    SELECT DISTINCT BHOBJECT from dwhrep.busyhour where VERSIONID =?
        
        '''
        self.logger.debug(self.versionID + ".getBusyHours()")
        with TPAPI.DbAccess(server,'dwhrep') as crsr:
            crsr.execute("SELECT DISTINCT BHOBJECT from dwhrep.busyhour where VERSIONID =?", (self.versionID,))
            resultset = crsr.fetchall()
            for row in resultset:
                self.busyHourNames.append(str(row[0]))
    
    def _getBusyHourObjects(self,server):
        '''Create busy hour (object) objects
        
        Busy hour objects are initiated using busy hour object names in the busyHourNames list
        their getPropertiesFromServer method is called and the object is then appended
        to the busyHourObjects list
        '''
        
        self.logger.debug(self.versionID + ".getBusyHourObjects()")
        for bh in self.busyHourNames:
            bho = TPAPI.BusyHour(self.versionID,bh)
            bho._getPropertiesFromServer(server)
            self.busyHourObjects[bh] = bho

    def _getExternalStatements(self,server):
        '''Create External Statement objects associated with the TechPackVersion
        
        Fetches the names of statements from the server, initialises the objects,
        calls the TPAPI_ExternalStatement.getPropertiesFromServer() and appends the objects to the
        externalStatementObjects dictionary
        
        SQL Statement:
            SELECT STATEMENTNAME FROM dwhrep.ExternalStatement WHERE VERSIONID =?"   
        '''

        self.logger.debug(self.versionID + "._getExternalStatements()")
        with TPAPI.DbAccess(server,'dwhrep') as crsr:
            crsr.execute("SELECT STATEMENTNAME FROM dwhrep.ExternalStatement WHERE VERSIONID =?", (self.versionID,))
            resultset = crsr.fetchall()
            for row in resultset:
                name = str(row[0])
                ext = TPAPI.ExternalStatement(self.versionID, name)
                ext._getPropertiesFromServer(server)
                self.externalStatementObjects[name] = ext

    def _getSupportedVendorReleases(self,server):
        ''' Gets the vendor releases associated with a TechPackVersion from the server
        
        Vendor Releases are appended to the supportedVendorReleases list
        
        SQL Statement:
                    SELECT VENDORRELEASE FROM dwhrep.SupportedVendorRelease WHERE VERSIONID =?"                    
        '''
        self.logger.debug(self.versionID + ".getSupportedVendorReleases()")
        with TPAPI.DbAccess(server,'dwhrep') as crsr:
            crsr.execute("SELECT VENDORRELEASE FROM dwhrep.SupportedVendorRelease WHERE VERSIONID =?", (self.versionID,))
            resultset = crsr.fetchall()
            for row in resultset:
                self.supportedVendorReleases.append(str(row[0]))
    
    #####################################################
    ### ENIQ EVENTS SPECIFIC
    
    def _getGroupTypes(self,server):
        
        #TODO Group types could be remeasurementored to an object
        #TODO rename method to getGroupTypesFromServer()
        '''Get the group types associated with an ENIQ Events TPV
        
        Returned information is added to the groupTypes Dictionary
        
        SQL Statement:
                    SELECT GROUPTYPE,DATANAME,DATATYPE,DATASIZE,DATASCALE,NULLABLE FROM dwhrep.GroupTypes WHERE VERSIONID =?"
        '''

        self.logger.debug(self.versionID + ".getGroupTypes()")
        with TPAPI.DbAccess(server,'dwhrep') as crsr:
            crsr.execute("SELECT GROUPTYPE,DATANAME,DATATYPE,DATASIZE,DATASCALE,NULLABLE FROM dwhrep.GroupTypes WHERE VERSIONID =?", (self.versionID,))
            resultset = crsr.fetchall()
            for row in resultset:
                if str(row[0]) not in self.groupTypes:
                    self.groupTypes[str(row[0])] = {}
                self.groupTypes[str(row[0])][str(row[1])] = {'DATATYPE':str(row[2]),'DATASIZE':str(row[3]),'DATASCALE':str(row[4]),'NULLABLE':str(row[5])}
    
    
    ###############################################
    # ETLREP

    def _getCollectionSetID(self,server):
        #TODO Rename to getCollectionSetIDFromServer
        '''Get the CollectionSetID for the techpack from the server and set the collectionSetID string of the 
        TechPackVersion object with the returned value. 
        
        This will only be present if the techpack has had sets generated for it. The collectionSetID string 
        is used to fetch set information from the etlrep db.
        
        SQL Statement:
                    SELECT COLLECTION_SET_ID from etlrep.META_COLLECTION_SETS where COLLECTION_SET_NAME =? and VERSION_NUMBER =?"
        '''
        with TPAPI.DbAccess(server,'etlrep') as crsr:
            crsr.execute("SELECT COLLECTION_SET_ID from etlrep.META_COLLECTION_SETS where COLLECTION_SET_NAME =? and VERSION_NUMBER =?", (self.tpName,self.versionNumber,))
            row = crsr.fetchone()
            if row:
                self.collectionSetID = str(row[0])
            else:
                pass

    
    def _getEtlrepSetCollectionObject(self,server):
        '''Create the EtlrepSetCollection object associated with the TechPackVersion
        '''
        metaCollectionSetObject = TPAPI.EtlrepSetCollection(self.tpName,self.versionNumber)
        metaCollectionSetObject._getProperties(server)
        self.etlrepMetaCollectionSetObject = metaCollectionSetObject

    def difference(self,tpvObject):
        ''' Calculates the difference between two TechPackVersion Objects
            
            Method takes the TechPackVersion to be compared against as input
            Prior to the diff a deltaObject is created for recording the differences
            A DeltaTPV (TechPackVersion Object) is created for capturing objects that have new or changed content (depreciated)
            
            The Difference method will trigger the difference method of its child objects, passing
            in the object to compare, deltaObj and deltaTPV. After calculating the diff the child object passes these objects
            back in conjunction with a flag to say whether a (only new or changed content.. not deleted) was found or not. This flag is used to decide
            whether a child object should be added to the parent object in the DeltaTPV.
            
            Returns:
                    deltaObj
            
        '''
        
        self.logger.debug(self.versionID + ".difference()")
        deltaObj = TPAPI.Delta(self.versionID,tpvObject.versionID)
        deltaTPV = TPAPI.TechPackVersion('DELTA_TPV:((1))')
        origVal = ''
        deltaVal = ''
        deltaObj.stack.append("Techpack="+self.tpName)
        deltaObj.stack.append("VersionID="+self.versionID)
        
        #########################################################################################################################################
        # Versioning diff
        versDelta = TPAPI.DictDiffer(self.versioning,tpvObject.versioning)
        for item in versDelta.changed():
            if item != 'LOCKDATE' and item != 'VERSIONID' and item != 'LOCKEDBY':
                deltaObj.stack.append("Property=<changed>"+item)
                origVal = self.versioning[item]
                deltaVal = tpvObject.versioning[item]
                deltaTPV.versioning[item] = deltaVal
                # change type
                deltaObj._addChange(deltaObj.stack,deltaVal,origVal)
                deltaObj.stack.pop()
          
          
        ##############################################################################################################################################
        #Measurement Table Diff
        origtables = list(self.measurementTableObjects.keys())
        upgradeTables = list(tpvObject.measurementTableObjects.keys())
        deltaTables = set(upgradeTables).difference(set(origtables))
        removedTables = set(origtables).difference(set(upgradeTables))
        
        for Table in removedTables:
            removedTable = self.measurementTableObjects[Table]
            deltaObj.stack.append(removedTable.tableType+"=<deleted>"+removedTable.name)
            for prop in removedTable.properties:
                deltaObj.stack.append("Property=<deleted>"+prop)
                deltaVal = removedTable.properties[prop]
                deltaObj._addChange(deltaObj.stack,None,deltaVal)
                deltaObj.stack.pop()
                for attribute in removedTable.attributeObjects:
                    deltaObj.stack.append(removedTable.attributeObjects[attribute].attributeType+"=<deleted>"+removedTable.attributeObjects[attribute].name)
                    for prop in removedTable.attributeObjects[attribute].properties:
                        deltaObj.stack.append("Property=<deleted>"+prop)
                        deltaVal = removedTable.attributeObjects[attribute].properties[prop]
                        deltaObj._addChange(deltaObj.stack,None,deltaVal)
                        deltaObj.stack.pop()
                    deltaObj.stack.pop()
            deltaObj.stack.pop()
                           
        #deltaTables
        for deltaTable in deltaTables:
            #diffFlag = True
            newTable = tpvObject.measurementTableObjects[deltaTable]
            deltaFTV = TPAPI.Table(deltaTable,deltaTPV.versionID)
            deltaObj.stack.append(newTable.tableType+"=<new>"+newTable.name)
            for prop in newTable.properties:
                deltaFTV.properties[prop] = newTable.properties[prop]
                deltaObj.stack.append("Property=<new>"+prop)
                deltaVal = newTable.properties[prop]
                deltaObj._addChange(deltaObj.stack,deltaVal,None)
                deltaObj.stack.pop()
                for attribute in newTable.attributeObjects:
                    deltaObj.stack.append(newTable.attributeObjects[attribute].attributeType+"=<new>"+newTable.attributeObjects[attribute].name)
                    for prop in newTable.attributeObjects[attribute].properties:
                        deltaObj.stack.append("Property=<new>"+prop)
                        deltaVal = newTable.attributeObjects[attribute].properties[prop]
                        deltaObj._addChange(deltaObj.stack,deltaVal,None)
                        deltaObj.stack.pop()
                    deltaObj.stack.pop()
                    deltaFTV.attributeObjects[attribute] = newTable.attributeObjects[attribute]
            deltaTPV.measurementTableObjects[deltaTable] = deltaFTV  
            deltaObj.stack.pop()
                  
        commonTables = set(origtables).intersection(set(upgradeTables))
        
        #common tables
        for common in commonTables:
            #print "diffing commonTables" + common  # debugging
            dummyFlag,deltaObj,deltaTPV =self.measurementTableObjects[common]._difference(tpvObject.measurementTableObjects[common],deltaObj,deltaTPV)
        
        ##############################################################################################################################################
        # Reference(Topology) table diff 
        origtables = list(self.referenceTableObjects.keys())
        upgradeTables = list(tpvObject.referenceTableObjects.keys())
        deltaTables = set(upgradeTables).difference(set(origtables))
        removedTables = set(origtables).difference(set(upgradeTables))
        
        for Table in removedTables:
            removedTable = self.referenceTableObjects[Table]
            deltaObj.stack.append(removedTable.tableType+"=<deleted>"+removedTable.name)
            for prop in removedTable.properties:
                deltaObj.stack.append("Property=<deleted>"+prop)
                deltaVal = removedTable.properties[prop]
                deltaObj._addChange(deltaObj.stack,None,deltaVal)
                deltaObj.stack.pop()
                for attribute in removedTable.attributeObjects:
                    deltaObj.stack.append(removedTable.attributeObjects[attribute].attributeType+"=<deleted>"+removedTable.attributeObjects[attribute].name)
                    for prop in removedTable.attributeObjects[attribute].properties:
                        deltaObj.stack.append("Property=<deleted>"+prop)
                        deltaVal = removedTable.attributeObjects[attribute].properties[prop]
                        deltaObj._addChange(deltaObj.stack,None,deltaVal)
                        deltaObj.stack.pop()
                    deltaObj.stack.pop()
            deltaObj.stack.pop()


        #delta tables
        for deltaTable in deltaTables:
            newTable = tpvObject.referenceTableObjects[deltaTable]
            deltaFTV = TPAPI.Table(deltaTable,deltaTPV.versionID)
            deltaObj.stack.append(newTable.tableType+"=<new>"+newTable.name)
            for prop in newTable.properties:
                deltaFTV.properties[prop] = newTable.properties[prop]
                deltaObj.stack.append("Property=<new>"+prop)
                deltaVal = newTable.properties[prop]
                deltaObj._addChange(deltaObj.stack,deltaVal,None)
                deltaObj.stack.pop()
                for attribute in newTable.attributeObjects:
                    deltaObj.stack.append(newTable.attributeObjects[attribute].attributeType+"=<new>"+newTable.attributeObjects[attribute].name)
                    for prop in newTable.attributeObjects[attribute].properties:
                        deltaObj.stack.append("Property=<new>"+prop)
                        deltaVal = newTable.attributeObjects[attribute].properties[prop]
                        deltaObj._addChange(deltaObj.stack,deltaVal,None)
                        deltaObj.stack.pop()
                    deltaObj.stack.pop()
                    deltaFTV.attributeObjects[attribute] = newTable.attributeObjects[attribute]
            deltaTPV.referenceTableObjects[deltaTable] = deltaFTV  
            deltaObj.stack.pop()
            
            
        # common tables diff
        commonTables = set(origtables).intersection(set(upgradeTables))
        for common in commonTables:
            dummyFlag,deltaObj,deltaTPV = self.referenceTableObjects[common]._difference(tpvObject.referenceTableObjects[common],deltaObj,deltaTPV)
        
        
            
        ##################################################################################################################################################
        # Interface diff
        
        #Test is there any interfaces to diff. tpi files need seperate intf file for tpi
        #print len(self.interfaceObjects)
        if len(self.interfaceObjects) != 0:
            origInterfaces = list(self.interfaceObjects.keys())
            upgradeInterfaces = list(tpvObject.interfaceObjects.keys())
            deltaInterfaces = set(upgradeInterfaces).difference(set(origInterfaces))
            removedInterfaces = set(origInterfaces).difference(set(upgradeInterfaces))
            commonInterfaces = set(origInterfaces).intersection(set(upgradeInterfaces))
            
            for removedInterface in removedInterfaces:
                deltaObj.stack.append("Interface=<deleted>"+self.interfaceObjects[removedInterface].name)
                deltaObj.stack.append("Version =<deleted>"+self.interfaceObjects[removedInterface].intfVersion)
                for prop in self.interfaceObjects[removedInterface].versioning:
                    deltaObj.stack.append('versioning=<deleted>'+prop)
                    origVal = str(self.interfaceObjects[removedInterface].versioning[prop])
                    deltaObj._addChange(deltaObj.stack,None,origVal)
                    deltaObj.stack.pop()
                for prop in self.interfaceObjects[removedInterface].dependencies:
                    deltaObj.stack.append('dependencies=<deleted>'+prop)
                    origVal = str(self.interfaceObjects[removedInterface].dependencies[prop])
                    deltaObj._addChange(deltaObj.stack,None,origVal)
                    deltaObj.stack.pop()
                for prop in self.interfaceObjects[removedInterface].intfTechpacks:
                    deltaObj.stack.append('intfTechpacks=<deleted>'+prop)
                    origVal = str(self.interfaceObjects[removedInterface].intfTechpacks[prop])
                    deltaObj._addChange(deltaObj.stack,None,origVal)
                    deltaObj.stack.pop()               
                for prop in self.interfaceObjects[removedInterface].intfConfig:
                    deltaObj.stack.append('intfConfig=<deleted>'+prop)
                    origVal = str(self.interfaceObjects[removedInterface].intfConfig[prop])
                    deltaObj._addChange(deltaObj.stack,None,origVal)
                    deltaObj.stack.pop()
                deltaObj.stack.pop()
                deltaObj.stack.pop()
                
            
            # Delta Interfaces
            for deltaInterface in deltaInterfaces:
                #newInterface = tpvObject.interfaceObjects[deltaInterface]
                #deltaIntfv = TPAPI.InterfaceVersion(newInterface.name,newInterface.intfVersion)
                deltaObj.stack.append("Interface=<new>"+tpvObject.interfaceObjects[deltaInterface].name)
                deltaObj.stack.append("Version =<new>"+tpvObject.interfaceObjects[deltaInterface].intfVersion)
                #add delta interface
                deltaTPV.interfaceObjects[deltaInterface] = tpvObject.interfaceObjects[deltaInterface] #(does this work)
                #d#eltaIntf = TPAPI.InterfaceVersion(tpvObject.interfaceObjects[intf].name,tpvObject.interfaceObjects[intf].intfVersion)
                for prop in tpvObject.interfaceObjects[deltaInterface].versioning:
                    deltaObj.stack.append('versioning=<new>'+prop)
                    deltaVal = str(tpvObject.interfaceObjects[deltaInterface].versioning[prop])
                    deltaObj._addChange(deltaObj.stack,deltaVal,None)
                    deltaObj.stack.pop()
                for prop in tpvObject.interfaceObjects[deltaInterface].dependencies:
                    deltaObj.stack.append('dependencies=<new>'+prop)
                    deltaVal = str(tpvObject.interfaceObjects[deltaInterface].dependencies[prop])
                    deltaObj._addChange(deltaObj.stack,deltaVal,None)
                    deltaObj.stack.pop()
                for prop in tpvObject.interfaceObjects[deltaInterface].intfTechpacks:
                    deltaObj.stack.append('intfTechpacks=<new>'+prop)
                    deltaVal = str(tpvObject.interfaceObjects[deltaInterface].intfTechpacks[prop])
                    deltaObj._addChange(deltaObj.stack,deltaVal,None)
                    deltaObj.stack.pop()               
                for prop in tpvObject.interfaceObjects[deltaInterface].intfConfig:
                    deltaObj.stack.append('intfConfig=<new>'+prop)
                    deltaVal = str(tpvObject.interfaceObjects[deltaInterface].intfConfig[prop])
                    deltaObj._addChange(deltaObj.stack,deltaVal,None)
                    deltaObj.stack.pop()
                deltaObj.stack.pop()
                deltaObj.stack.pop()
                
            #common interface    
            # TODO
            for intf in commonInterfaces: # common interfaces
                dummyFlag,deltaObj,deltaTPV  = self.interfaceObjects[intf]._difference(tpvObject.interfaceObjects[intf],deltaObj,deltaTPV)
            
        ##########################################################################################################################################
        #Busy Hour Diff
        
        origBusyHourObjects = list(self.busyHourObjects.keys())
        upgradeBusyHourObjects= list(tpvObject.busyHourObjects.keys())
        deltaBusyHourObjects = set(upgradeBusyHourObjects).difference(set(origBusyHourObjects))
        removedBusyHourObjects = set(origBusyHourObjects).difference(set(upgradeBusyHourObjects))
        commonBusyHourObjects = set(upgradeBusyHourObjects).intersection(set(origBusyHourObjects))
        
        
        for removedBH in removedBusyHourObjects:
            deltaObj.stack.append('BusyHour=<deleted>'+removedBH)
            
            for name, BHType in self.busyHourObjects[removedBH].busyHourTypeObjects.iteritems():
                deltaObj.stack.append('Property=<deleted>BHType'+name)
                for prop in BHType.properties:
                    deltaObj.stack.append("Property=<deleted>"+prop)
                    origVal = BHType.properties[prop]
                    deltaObj._addChange(deltaObj.stack,None,origVal)
                    deltaObj.stack.pop()
                deltaObj.stack.pop()
            
            for table in self.busyHourObjects[removedBH].supportedTables:
                deltaObj.stack.append('Property=<deleted>BHSupportTable'+table)
                origVal = table
                deltaObj._addChange(deltaObj.stack,None,origVal)
                deltaObj.stack.pop()
            deltaObj.stack.pop()
        
        #Delta BusyHours
        for deltaBH in deltaBusyHourObjects:
            deltaBHObj = TPAPI.BusyHour(self.versionID,deltaBH)
            deltaObj.stack.append('BusyHour=<new>'+deltaBH)
            deltaBHObj = tpvObject.busyHourObjects[deltaBH]
            
            for name, BHType in tpvObject.busyHourObjects[deltaBH].BusyHourTypeObjects.iteritems():
                deltaObj.stack.append('Property=<new>BHType'+name)
                for prop in BHType.properties:
                    deltaObj.stack.append("Property=<new>"+prop)
                    deltaVal = BHType.properties[prop]
                    deltaObj._addChange(deltaObj.stack,deltaVal,None)
                    deltaObj.stack.pop()
                deltaObj.stack.pop()
            
            for table in tpvObject.busyHourObjects[deltaBH].supportedTables:
                deltaObj.stack.append('Property=<new>BHSupportTable'+table)
                deltaVal = table
                deltaObj._addChange(deltaObj.stack,deltaVal,None)
                deltaObj.stack.pop()
            deltaObj.stack.pop()
            deltaTPV.busyHourObjects[tpvObject.busyHourObjects[deltaBH].name] = deltaBHObj

        #Common BusyHours
        for commonBH in commonBusyHourObjects:
            dummyFlag,deltaObj,deltaTPV = self.busyHourObjects[commonBH]._difference(tpvObject.busyHourObjects[commonBH],deltaObj,deltaTPV)
        
        #############################################################################################################################################
        #External statements diff
        
        deltaObj.stack.pop()
        origExternalStatements = list(self.externalStatementObjects.keys())
        upgradeExternalStatements = list(tpvObject.externalStatementObjects.keys())
        deltaExternalStatements = set(upgradeExternalStatements).difference(set(origExternalStatements))
        removedExternalStatements = set(origExternalStatements).difference(set(upgradeExternalStatements))
        commonExternalStatements = set(upgradeExternalStatements).intersection(set(origExternalStatements))
        
        #Delta External Statements
        for deltaExtStatement in deltaExternalStatements:
            deltaESObj = TPAPI.ExternalStatement(self.versionID, deltaExtStatement)
            deltaObj.stack.append('External Statement=<new>'+deltaExtStatement)
            deltaESObj = tpvObject.externalStatementObjects[deltaExtStatement]
            
            for property in tpvObject.externalStatementObjects[deltaExtStatement].properties:
                deltaObj.stack.append('Property=<new>'+property)
                deltaVal = tpvObject.externalStatementObjects[deltaExtStatement].properties[property]
                deltaObj._addChange(deltaObj.stack,deltaVal,None)
                deltaObj.stack.pop()
            deltaObj.stack.pop()
            deltaTPV.externalStatementObjects[deltaExtStatement] = deltaESObj
            
        #Removed External Statements
        for removedExtStatement in removedExternalStatements:
            deltaObj.stack.append('External Statement=<deleted>'+removedExtStatement)
            for prop in self.externalStatementObjects[removedExtStatement].properties:
                deltaObj.stack.append('Property=<deleted>'+prop)
                origVal = self.externalStatementObjects[removedExtStatement].properties[prop]
                deltaObj._addChange(deltaObj.stack,None,origVal)
                deltaObj.stack.pop()
            deltaObj.stack.pop()

        #Common External Statements
        for ExtStatement in commonExternalStatements:
            dummyFlag,deltaObj,deltaTPV = self.externalStatementObjects[ExtStatement]._difference(tpvObject.externalStatementObjects[ExtStatement],deltaObj,deltaTPV) 

        #############################################################################################################################################
        #Vendor Release Diff

        listRemoved =list(set(self.supportedVendorReleases) - set(tpvObject.supportedVendorReleases))
        listAdded = list(set(tpvObject.supportedVendorReleases) - set(self.supportedVendorReleases))
        for key1 in listAdded:
            deltaObj.stack.append('SupportedVendorReleases=<new>'+key1)
            deltaObj._addChange(deltaObj.stack,key1,None)
            deltaObj.stack.pop()
            deltaTPV.supportedVendorReleases.append(key1)
        for key1 in listRemoved:
            deltaObj.stack.append('SupportedVendorReleases=<deleted>'+key1)
            deltaObj._addChange(deltaObj.stack,None,key1)
            deltaObj.stack.pop()
            #deltaTPV.supportedVendorReleases.append(key1)
        
        #############################################################################################################################################
        #Group Types Diff
        for groupType in tpvObject.groupTypes:
            if self.groupTypes.get(groupType) is not None:
                deltaObj.stack.append('Grouptype='+groupType)
                
                for dataName in self.groupTypes[groupType]:
                    if self.groupTypes[groupType].get(dataName) is not None:
                        deltaObj.stack.append('dataName='+dataName)
                        for prop in self.groupTypes[groupType][dataName]:
                            if self.groupTypes[groupType][dataName][prop] != tpvObject.groupTypes[groupType][dataName][prop]:
                                deltaObj.stack.append('Property='+prop)
                                deltaVal = str(tpvObject.groupTypes[groupType][dataName][prop])
                                origVal = str(self.groupTypes[groupType][dataName][prop])
                                deltaObj._addChange(deltaObj.stack,deltaVal)

                                if deltaTPV.groupTypes.get(groupType) is None:
                                    deltaTPV.groupTypes[groupType] = {}
                                    deltaTPV.groupTypes[groupType][dataName] = {}
                                    deltaTPV.groupTypes[groupType][dataName][prop] = tpvObject.groupTypes[groupType][dataName][prop]
                                else:
                                    if deltaTPV.groupTypes[groupType].get(dataName) is None:
                                        deltaTPV.groupTypes[groupType][dataName] = {}
                                        deltaTPV.groupTypes[groupType][dataName][prop] = tpvObject.groupTypes[groupType][dataName][prop] 
                                    else:
                                        deltaTPV.groupTypes[groupType][dataName][prop] = tpvObject.groupTypes[groupType][dataName][prop]
                                deltaObj.stack.pop()
                        deltaObj.stack.pop()
                        
                    else:
                        deltaObj.stack.append('DataName=<new>'+dataName)
                        if deltaTPV.groupTypes.get(groupType) is None:
                            deltaTPV.groupTypes[groupType] = {}
                            deltaTPV.groupTypes[groupType][dataName] = {}
                        else:
                            deltaTPV.groupTypes[groupType][dataName] = {}
                        for prop in tpvObject.groupTypes[groupType][dataName]:
                            deltaObj.stack.append('Property=<new>'+prop)
                            deltaVal = str(tpvObject.groupTypes[groupType][prop])
                            deltaObj._addChange(deltaObj.stack,deltaVal.None)
                            deltaTPV.groupTypes[groupType][prop] = tpvObject.groupTypes[groupType][prop]
                            deltaObj.stack.pop()
                        deltaObj.stack.pop()

            else:
                
                deltaObj.stack.append('Grouptype=<new>'+groupType)
                deltaTPV.groupTypes[groupType] = {}
                for dataName in tpvObject.groupTypes[groupType]:
                    deltaObj.stack.append('DataName=<new>'+dataName)
                    deltaTPV.groupTypes[groupType][dataName] = {}
                    for prop in tpvObject.groupTypes[groupType]:
                        deltaObj.stack.append('Property=<new>'+prop)
                        deltaVal = str(tpvObject.groupTypes[groupType][prop])
                        deltaObj._addChange(deltaObj.stack,None)
                        deltaTPV.groupTypes[groupType][prop] = tpvObject.groupTypes[groupType][prop]
                        deltaTPV.groupTypes[groupType][prop] = tpvObject.groupTypes[groupType][prop]  
                        deltaObj.stack.pop()
                    deltaObj.stack.pop()
                deltaObj.stack.pop()
            deltaObj.stack.pop()
            deltaTPV.versioning['TECHPACK_TYPE'] = 'ENIQ_EVENT'
        
        deltaObj.deltaTPV = deltaTPV
        return deltaObj    

   #TODO add toString method

    def toXML(self,offset=0):
        '''Converts the object to an xmlString representation
        
        Offset value is used for string indentation. Default to 0
        Parent toXML() method is responsible for triggering child object toXML() methods.

        Return Value: xmlString 
        '''
        
        self.logger.debug(self.versionID + ".toXML()")
        offset +=8
        os = "\n" + " "*offset
        os2 = os + " "*4
        os3 = os2 + " "*4
        os4 = os3 + " "*4
        os5 = os4 + " "*4
        outputXML = ''
        outputXML  += '<Techpack>'
        outputXML += os+'<Versioning name="' + self.versionID +'">'
        outputXML += os2+'<VersionInfo>'
        for item in self.versioning:
            outputXML += os3+'<'+str(item)+'>'+TPAPI.escape(self.versioning[item])+'</'+str(item)+'>'
        outputXML += os2+'</VersionInfo>'
        outputXML += os2+'<SupportedVendorReleases>'
        for item in self.supportedVendorReleases:
            outputXML += os3+'<VendorRelease>' + item + '</VendorRelease>'
        outputXML += os2+'</SupportedVendorReleases>'
        outputXML += os2+'<Tables>'
        for table in self.measurementTableObjects:
            outputXML += self.measurementTableObjects[table]._toXML(offset)
        for table in self.referenceTableObjects:
            outputXML += self.referenceTableObjects[table]._toXML(offset)
        outputXML += os2+'</Tables>'
        outputXML += os2+'<BusyHours>'
        for bh in self.busyHourObjects:
            outputXML += self.busyHourObjects[bh]._toXML(offset)
        outputXML += os2+'</BusyHours>'
        outputXML += os2+'<ExternalStatement>'
        order=0
        while order <= len(self.externalStatementObjects):
            for ES in self.externalStatementObjects:
                exeorder = self.externalStatementObjects[ES].properties['EXECUTIONORDER']
                if exeorder == str(float(order)) or exeorder == str(order):
                    outputXML += self.externalStatementObjects[ES]._toXML(offset)     
            order=order+1     
        outputXML += os2+'</ExternalStatement>'
        if 'TECHPACK_TYPE' in self.versioning:
            if self.versioning['TECHPACK_TYPE']=='ENIQ_EVENT':
                for groupType in self.groupTypes:
                    outputXML += os2+'<GroupType name="' + TPAPI.escape(groupType) + '">'
                    for dataName in self.groupTypes[groupType]:
                        outputXML += os3+'<DataName name="' + TPAPI.escape(dataName) + '">' 
                        for prop in self.groupTypes[groupType][dataName]:
                            outputXML += os4+'<Property  key="' + str(prop) + '" val="' + TPAPI.escape(self.groupTypes[groupType][dataName][prop]) + '"/>'   
                        outputXML += os3+'</DataName> '
                    outputXML += os2+'</GroupType>'   
        # ETLREP
        if self.collectionSetID and self.etlrepMetaCollectionSetObject != None:
            outputXML += os2+'<MetaCollectionSets>'            
            outputXML += os3+'<MetaCollectionSet CollectionSetName="' + self.tpName + '" CollectionSetID="' +str(self.collectionSetID) +'">'
            outputXML += self.etlrepMetaCollectionSetObject._toXML(offset+4)
            outputXML += os3+'</MetaCollectionSet>'
            outputXML += os2+'</MetaCollectionSets>'
        outputXML += os2+'<Interfaces>'
        for intf in self.interfaceObjects:
            outputXML += self.interfaceObjects[intf].toXML(offset)
        outputXML += os2+'</Interfaces>'
        outputXML += os+'</Versioning>'
        outputXML +='\n</Techpack>'
        return outputXML 
    
        
    def getPropertiesFromXML(self,xmlElement=None,filename=None):
        '''Populates the objects content from an xmlElement or an XML file
        
        getPropertiesFromXML() method is responsible for triggering its child objects getPropertiesFromXML() method
        
        '''
        self.logger.debug(self.versionID + ".getPropertiesFromXML()")
        if filename is not None:
            xmlElement = TPAPI.fileToXMLObject(open(filename,'r'))
        for elem1 in xmlElement:
            # Populate Versioning Dictionary
            if elem1.tag=='Versioning':
                self._intialiseVersion(elem1.attrib['name'])
                for elem2 in elem1:
                        if elem2.tag=='VersionInfo':
                            for elem3 in elem2:
                                self.versioning[elem3.tag] = TPAPI.safeNull(elem3.text)
                        if elem2.tag=='SupportedVendorReleases':
                            for elem3 in elem2:
                                if elem3.tag=='VendorRelease':
                                    self.supportedVendorReleases.append(TPAPI.safeNull(elem3.text))
                        if elem2.tag=='Tables':
                            for elem3 in elem2:
                                if elem3.tag=='Table':
                                    t = TPAPI.Table(elem3.attrib['name'],self.versionID)
                                    t.tableType = elem3.attrib['tableType']
                                    t._getPropertiesFromXML(elem3)

                                    if elem3.attrib['tableType'] == 'Measurement':
                                            self.measurementTableObjects[elem3.attrib['name']] = t
                                    if elem3.attrib['tableType'] == 'Reference':
                                            self.referenceTableObjects[elem3.attrib['name']] = t
                        if elem2.tag=='Parsers':
                            for elem3 in elem2:
                                if elem3.tag=='Parser':
                                    if elem3.attrib['type'] not in self.parserNames:
                                        self.parserNames.append(elem3.attrib['type'])
                                    tpParser = TPAPI.Parser(self.versionID,self.tpName,elem3.attrib['type'])
                                    tpParser.getPropertiesFromXML(elem3)
                                    self.parserObjects[elem3.attrib['type']] = tpParser
                        if elem2.tag == 'BusyHours':
                            for elem3 in elem2:
                                for elem4 in elem3:
                                    bhName =  elem4.text
                                    if elem4.tag == 'BusyHourObjectName':
                                        bh = TPAPI.BusyHour(self.versionID,bhName)
                                        bh._getPropertiesFromXML(elem3)
                                        self.busyHourObjects[bhName] = bh
                    
                        if elem2.tag == 'Interfaces':
                                for elem3 in elem2:
                                    if elem3.tag == 'Interface':   
                                        name = elem3.attrib['name']
                                        for elem4 in elem3:
                                            if elem4.tag == 'IntfVersioning':                                             
                                                intf = TPAPI.InterfaceVersion(name,elem4.attrib['intfVersion'])
                                                intf.getPropertiesFromXML(elem3)
                                                self.interfaceObjects[elem3.attrib['name']]= intf

                        if elem2.tag == 'ExternalStatement':
                            for elem3 in elem2:
                                if elem3.tag == 'ExternalStatement':
                                    name = elem3.attrib['name']
                                    es = TPAPI.ExternalStatement(self.versionID, name)
                                    es._getPropertiesFromXML(elem3)
                                    self.externalStatementObjects[name] = es
                                    
##############################################################################################
#UPDATE,SQL GENERATION AND INSERT METHODS   

#MODIFY VERSION ID

    @deprecated
    def changeTechpackVersionID(self,versionID):
        '''@deprecated Change the versionID of the TechPackVersion model and propagate the change to its child members.
        Restricted to tables and attributes currently'''
        self._intialiseVersion(versionID)
        self._changeTablesVersionID(versionID)
        self.versioning['VERSIONID'] = versionID
    
    @deprecated 
    def _changeTablesVersionID(self,versionID):
        '''@deprecated Change the versionID of each table loaded in the TechPackVersion model'''
        for table in self.measurementTableObjects:
            self.measurementTableObjects[table]._updateVersionID(versionID)

#SQL GENERATION
    @deprecated  
    def _generateVersioningSQL_INSERT(self):
        '''@deprecated Generate Versioning Table sql inserts statments

        Return Value:
            String of SQL statement
            List of values 
        '''
        versDict = self.versioning
        sql,vals = TPAPI.dictToSQL(versDict,'Versioning') 
        return sql,vals
    
    @deprecated  
    def _generateVersioningSQL_UPDATE(self,column,value):
        '''@deprecated Update a column in the versioning table'''
        sqlstatement = 'update dwhrep.versioning set ' + column + "='" + value + "' where versionid = '" + self.versionID + "';"      #UPDATE table_name
        return sqlstatement

    @deprecated  
    def _generateMeasurementTableSQL(self):
        '''@deprecated This method generates sql inserts for all measurementTable objects loaded in the model. 
        Its is called here because information from busyhour objects is needed to create the DAYBH rows. All other rows 
        are generated by the measurement table itself
        '''
        
        sqlvals = ''
        for tablname in self.measurementTableObjects:
            tablObj = self.measurementTableObjects[tablname]
            sqlvals += tablObj.generateMeasTableSql()
            for bh in self.busyHourObjects:
                if tablname in self.busyHourObjects[bh].supportedTables:
                    #_create the DAYBH row and break
                    sqlvals += tablObj.typeid + ':DAYBH' +",DAYBH, "+tablObj.typeid+ ","+tablObj.name+"_DAYBH,"+tablObj.properties['SIZING']+"_DAYBH\n" 
                    break
        return sqlvals
    
    @deprecated
    def _insertVersioning(self,server):
        '''@deprecated Inserts versioning information into the dwhrep.versioning table
        ie First step in creating a new new tp. 
        
        Return Value:
            0 if insert failed
            1 if insert was successful
        '''
        
        self.logger.debug(self.versionID + "._insertVersioning()")
        versDict = self.versioning
        with TPAPI.DbAccess(server,'dwhrep') as crsr:
            crsr.execute("SELECT * from dwhrep.Versioning where VERSIONID =?", (self.versionID,))
            desc = crsr.description
            row = crsr.fetchone()
            #Check that versionid is not already present in the versioning table
            if row is not None:
                self.logger.error('insertVersioning():Insert Failed: VersionID' +self.versionID +'already exists')
                return 0
            else:        
                sql,vals = TPAPI.dictToSQL(versDict,'Versioning') 
                self.logger.debug('._insertVersioning(): Update Versioning SQL = ' + str(sql) + '\n vals = ' + str(vals))     
                with TPAPI.DbAccess(server,'dwhrep') as crsr:
                    crsr.execute(sql,(vals))
                    return 1
                
    @deprecated            
    def createTP(self,server,versionID):            

        '''@deprecated 
        Create a new techpack on the server with the new versionID
        
        Techpack with versionID should not be present on the server before the
        creation of the techpack.        
        '''
        self.logger.debug(self.versionID + ".createTP()")
        self.changeTechpackVersionID(versionID)
        SQL_INSERT_Versioning,vals = self.generateVersioningSQL_INSERT()
        with TPAPI.DbAccess(server,'dwhrep') as crsr:
            crsr.execute(SQL_INSERT_Versioning,vals )
            
        for table in self.measurementTableObjects:
            self.measurementTableObjects[table]._create(server,self.versioning['BASEDEFINITION'])
     
    @deprecated           
    def upgradeTP(self,server,deltaObject):    
        '''@deprecated Upgrade techpack details on the server using deltaObject information

        To upgrade, first a copy of the techpack with a new versionID must be made with the IDE .
        The versionID of the techpack on the server should match that of the tpv object which calls
        this upgrade message.
        '''
        self.logger.debug(self.versionID + ".upgradeTP()")
        deltaTPV = deltaObject.deltaTPV
        self.changeTechpackVersionID(self.versionID)
        #Permitted Changes to Versioning Table
        legalColumnsToChange = ['LICENSENAME','UNIVERSENAME','PRODUCT_NUMBER','TECHPACK_TYPE','INSTALLDESCRIPTION','DESCRIPTION','TECHPACK_VERSION','UNIVERSEEXTENSION']
        
        #update versioning table with any changes
        try:
            for column in deltaTPV.versioning:
                if column in legalColumnsToChange:
                    updateStatement = self._generateVersioningSQL_UPDATE(column,deltaTPV.versioning[column])
                    self.logger.debug('INSERT_INTO_VERSIONING: ' + str(updateStatement))
                    #
                    with TPAPI.DbAccess(server,'dwhrep') as crsr:
                        crsr.execute(updateStatement)
        #upgrade measurementable and child attributes
            for table in deltaTPV.measurementTableObjects:
                self.measurementTableObjects[table]._upgrade(deltaTPV,server,self.versioning['BASEDEFINITION'])
            
        except:
            #TODO ask brian about this
            print traceback.print_exc(file=sys.stdout)
            errorMessage = str(sys.exc_info()[0])
            self.logger.debug('Error occured while upgrading:: ' + str(sys.exc_info()[0]))
            print "Error occured while upgrading: "+ errorMessage

            

class TechPack(object): 
    '''Class to represent a techpack. ie a container for multiple techpack versions
        
        Techpack = DC_E_BSS,
        Techpack Version = DC_E_BSS:((100))
    '''
    
    versionID = ''
    tpName =''
    ACTIVETP ='NOT_ACTIVE' 
    listOfVersionIDs = ''
    listTechPackVersionObjects =[]

    def __init__(self,tpName):
        '''Class'''
        
        self.logger = logging.getLogger('TPAPI.TPAPI_TP.TechPack')
        self.logger.debug(self.tpName+ ".init()")

        self.tpName = tpName
        self.listOfVersionIDs =[]

        
    def toString(self):
        self.logger.debug(self.tpName+ ".toString()")
        outputString = ''
        outputString += self.tpName + "\n"
        outputString += "Active Version: " + self.ACTIVETP + "\n\n"
        for tpv in self.listTechPackVersionObjects:
            outputString += tpv.toString()
        return outputString
    
    def fileToXML(self,xmlfile):
        xmlString = xmlfile.read()
        xmlObject = ElementTree.fromstring(xmlString)
        return xmlObject
    
    def toXML(self,offset=0):
        '''Write the object to an xml formatted string
        
        Offset value is used for string indentation. Default to 0
        Parent toXML() method is responsible for triggering child object toXML() methods.

        Return Value: xmlString 
        '''
        
        self.logger.debug(self.tpName+ ".toXML()")
        offsetStr = "\n" + " "*offset
        outputXML = offsetStr
        outputXML += '<Techpack name="' + self.tpName +'" activeTechPack="' + self.ACTIVETP +'">' + offsetStr
        for tpv in self.listTechPackVersionObjects:
            outputXML += tpv.toXML(offset)
        outputXML += '</Techpack>' + offsetStr 
        return outputXML
    
    def getInstalledVersions(self, server):
        ''' return a list of the versions of the named TP installed on the specified server'''
        self.logger.debug(self.tpName+ ".getInstalledVersions()")
        reslist = []
        with TPAPI.DbAccess(server,'dwhrep') as crsr:
            crsr.execute("SELECT VERSIONID FROM dwhrep.Versioning WHERE TECHPACK_NAME=?", [self.tpName])
            for res in crsr.fetchall():
                reslist.append(res[0])
        return reslist
    
    def getAllProperties(self,server):
        ''' Get Versioning Information for all versions of the techpack on the server'''
        self.logger.debug(self.tpName+ ".getAllProperties()")
        with TPAPI.DbAccess(server,'dwhrep') as crsr:
            crsr.execute("SELECT VERSIONID FROM dwhrep.Versioning WHERE TECHPACK_NAME=?", [self.tpName])
            for res in crsr.fetchall():
                versionID=res[0]
                self.__populateProperties(versionID, server)
                
        self.getActiveTP(server)
        return
                
    def getPropertiesFromServer(self,server, versionID):
        '''Get Versioning Information for a specific version of a techpack'''
        self.logger.debug(self.tpName+ ".getPropertiesFromServer()")
        if versionID not in self.listOfVersionIDs:
            self.__populateProperties(versionID, server)
        return self.listTechPackVersionObjects[versionID]        
              
    def __populateProperties(self, versionID, server):
        '''makes sure we have the current tech pack version properties loaded'''
        self.logger.debug(self.tpName+ ".__populateProperties()")
        if versionID not in self.listOfVersionIDs: 
            self.listOfVersionIDs.append(versionID)
            tpv = TechPackVersion(versionID)
            tpv.getPropertiesFromServer(server)
            self.listTechPackVersionObjects.append(tpv)
        
    def getActiveTP(self, server):
        ''' Gets the active version of the techpack '''
        ''' If not active ACTIVETP attribute is set to NOT_ACTIVE'''
        self.logger.debug(self.tpName+ ".getActiveTP()")
        if self.ACTIVETP is not 'NOT_ACTIVE':
            return self.ACTIVETP
        with TPAPI.DbAccess(server,'dwhrep') as crsr:        
            
            crsr.execute("SELECT VERSIONID FROM dwhrep.TPActivation WHERE TECHPACK_NAME =?", (self.tpName,))
            row=crsr.fetchone()
            if row:
                self.ACTIVETP = str(row[0])
            else:
                self.ACTIVETP = 'NOT_ACTIVE'
            return self.ACTIVETP
            
 
    def printTPInfo(self):
        self.logger.debug(self.tpName+ ".printTPInfo()")
        #print self.versionID
        self.cursorDwhrep.execute('SELECT TECHPACK_VERSION,PRODUCT_NUMBER,DESCRIPTION,BASEDEFINITION,LICENSENAME  FROM dwhrep.Versioning WHERE VERSIONID=?',self.versionID )
        row = self.cursorDwhrep.fetchall();
        for i in row:
            print "\n"
            print "TechPack: " + self.versionID
            print "RState: " + i.TECHPACK_VERSION
            print "Product Number: " + i.PRODUCT_NUMBER
            print "Description: " + i.DESCRIPTION
            print "Base Definition: " + i.BASEDEFINITION
            print "Licenses: " + i.LICENSENAME
    
        self.cursorDwhrep.execute("SELECT UNIVERSENAME,UNIVERSEEXTENSION,UNIVERSEEXTENSIONNAME FROM dwhrep.UniverseName WHERE VERSIONID =?", self.versionID)
        row = self.cursorDwhrep.fetchall();
        print "\nUniverse Info: "
        for i in row:
            print "Universe Name: " + i.UNIVERSENAME
            print "Universe Extension: " + i.UNIVERSEEXTENSION
            print "Universe Extension Name: " + i.UNIVERSEEXTENSIONNAME
    
        self.cursorDwhrep.execute("SELECT VENDORRELEASE FROM dwhrep.SupportedVendorRelease WHERE VERSIONID =?",self.versionID)
        row = self.cursorDwhrep.fetchall();
        print "\nVendor Releases: "
        for i in row:
            print i.VENDORRELEASE
        return
