
from __future__ import with_statement
import TPAPI
import logging




class ExternalStatement(object):
    
    '''Class to represent ExternalStatement object. A child object of TechPack Version'''
        
    def __init__(self,versionID, name):
        '''Class is instantiated with the versionID and name of the External Statement
            
            Instance Variables:
            
            self.versionID:
                Description: VersionID of the TechPackVersion
                Type:String
                
           self.name:
               Description: name of the external statement
               Type: String
               
            self.properties:
                Description: Properties of the external statement
                Type: Dictionary
                Keys: 
                    EXECUTIONORDER
                    DBCONNECTION
                    STATEMENT
        '''
        self.logger = logging.getLogger('TPAPI.TPAPI_TP.BusyHour')
        self.versionID = versionID
        self.name = name
        self.properties = {}

    def _getPropertiesFromServer(self,server):
        '''Get all the properties associated with the External statement object'''
        self._getExternalStatements(server)

    def _getExternalStatements(self,server):
        '''Gets external statement information from the dwhrep
        
        SQL Executed:
                    SELECT EXECUTIONORDER,DBCONNECTION,STATEMENT,\BASEDEF FROM dwhrep.ExternalStatement WHERE VERSIONID =? AND STATEMENTNAME =?
        '''
        self.logger.debug(self.versionID + "._getExternalStatements()")
        with TPAPI.DbAccess(server,'dwhrep') as crsr:
            crsr.execute("SELECT EXECUTIONORDER,DBCONNECTION,STATEMENT,\
            BASEDEF FROM dwhrep.ExternalStatement WHERE VERSIONID =? AND STATEMENTNAME =?", (self.versionID, self.name,))
            resultset = crsr.fetchall()
            for row in resultset:
                self.properties['EXECUTIONORDER'] = TPAPI.strFloatToInt(str(row[0]))
                self.properties['DBCONNECTION'] = str(row[1])
                self.properties['STATEMENT'] = str(row[2]).strip()

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
        outputXML = os2+'<ExternalStatement name="' + self.name + '">'
        for prop in self.properties:
            outputXML += os3+'<'+prop+'>'+ TPAPI.escape(self.properties[prop]) +'</'+prop+'>'
        outputXML += os2+'</ExternalStatement>'   
        return outputXML 

    def _getPropertiesFromXML(self,xmlElement):
        '''Populates the objects content from an xmlElement
        
        The method is also responsible for triggering its child objects getPropertiesFromXML() method'''
        self.logger.info(self.versionID + " Inside _getPropertiesFromXML function") 
        for elem in xmlElement:
            self.properties[elem.tag] = TPAPI.safeNull(elem.text)     
    
    def _getPropertiesFromTPI(self,tpiDict=None,filename=None):
            '''Populate the objects contents from a tpiDict object or tpi file.
            
            If a tpi file is passed it is converted to a tpiDict object before processing.

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
            for row in tpiDict['Externalstatement']['STATEMENTNAME']:
                if tpiDict['Externalstatement']['STATEMENTNAME'][row] == self.name:
                    self.properties['EXECUTIONORDER'] = tpiDict['Externalstatement']['EXECUTIONORDER'][row]
                    self.properties['DBCONNECTION'] = tpiDict['Externalstatement']['DBCONNECTION'][row]
                    self.properties['STATEMENT'] = tpiDict['Externalstatement']['STATEMENT'][row]
       
    def _difference(self,extStateObject,deltaObj,deltaTPV):
        '''Calculates the difference between two external statement objects
            
            Method takes extStateObject,deltaObj and deltaTPV as inputs.
            extStateObject: The External Statement to be compared against
            DeltaObj: The single object that gets passed through the entire diff recording the changes.
            DeltaTPV: A TechPackVersion Object that gets passed through the entire diff recording only new content.
            
            The Difference method will trigger the difference method of its child objects, passing
            in the object to compare, deltaObj and deltaTPV. After calculating the diff the child object passes these objects
            back in conjunction with a flag to say whether a (only new or changed content.. not deleted) was found or not. This flag is used to decide
            whether a child object should be added to the parent object in the DeltaTPV.
            
            Note: External statement does not have any child objects
            
            Returns:
                    diffFlag (Boolean indicating where a change was found or not)
                    deltaObj
                    deltaTPV 
            
        '''
        diffFlag = False
        ExtStatementPropertiesDelta = TPAPI.DictDiffer(self.properties,extStateObject.properties)
        deltaObj.stack.append('External Statement='+self.name)
        if ExtStatementPropertiesDelta.changed():
            deltaESObj = TPAPI.ExternalStatement(self.versionID, self.name)   
            for prop in ExtStatementPropertiesDelta.changed():
                deltaObj.stack.append("Property=<changed>"+prop)
                origVal = self.properties[prop]
                deltaVal = extStateObject.properties[prop]
                deltaObj._addChange(deltaObj.stack,deltaVal,origVal)
                deltaESObj.properties[prop] = deltaVal
                deltaObj.stack.pop()
            
            deltaTPV.externalStatementObjects[self.name] = deltaESObj
            deltaObj.stack.pop()
        return diffFlag,deltaObj,deltaTPV
    