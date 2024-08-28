
from __future__ import with_statement
import TPAPI
import hashlib
import logging
import warnings
from TPAPI_Util import deprecated

class Transformation(object):
        '''Class to represent a transformation. Child object of Parser class.'''
        
        def __init__(self,rowID,transformerID):
            
            '''
            Initialised with RowID and transformerID
            
            self.rowID:
            Description: rowID (position) of the transformation in the sequence of transformations
            Type: String
            
            self.transformerID:
            Description: Unique Identifier of the transformation
            Type: String
            
            self.properties: 
            Description: Contains the properties associed with the transformations
            Type: Dictionary
            Keys: TYPE
                  SOURCE
                  TARGET
                  CONFIG
            
            self._hash:
            Description: Unique hash value of the transformation used for diffing purposes

             '''
            self.logger = logging.getLogger('TPAPI.TPAPI_TP.TechPackVersion.Table.Parser.Transformation')
            self.rowID = str(rowID)
            self.transformerID = transformerID
            self.properties = {} 
            self._hash = None 
         
        def _getPropertiesFromServer(self,server):
            '''Populates the properties dictionary of the transformation from the server
            
            SQL Statement: 
                        SELECT TYPE,SOURCE,TARGET,CONFIG FROM dwhrep.Transformation where TRANSFORMERID=? AND ORDERNO=?
            '''
            with TPAPI.DbAccess(server,'dwhrep') as crsr:
                crsr.execute("SELECT TYPE,SOURCE,TARGET,CONFIG FROM dwhrep.Transformation where TRANSFORMERID=? AND ORDERNO=?",(self.transformerID,self.rowID,))
                desc = crsr.description   
                row = crsr.fetchone()
                if row is not None:
                    i = 0
                    for x in desc:    
                        val = str(row[i]).strip()
                        self.properties[str(x[0])] = val
                        i+=1
            self.rowID = TPAPI.strFloatToInt(self.rowID)

        def _toXML(self,offset=0):
            '''Write the object to an xml formatted string
            
            Offset value is used for string indentation. Default to 0
            Parent toXML() method is responsible for triggering child object toXML() methods.
    
            Return Value: xmlString 
            '''
            offset +=4
            os = "\n" + " "*offset
            os2 = os+ " "*4
            os3 = os2+ " "*4
            outputXML = os + '<OrderNo index="'+str(self.rowID)+'">' 
            outputXML += os3+'<'"TYPE"'>'+TPAPI.escape(self.properties['TYPE'])+'<'"/TYPE"'>'
            outputXML += os3+'<'"SOURCE"'>'+TPAPI.escape(self.properties['SOURCE'])+'<'"/SOURCE"'>'
            outputXML += os3+'<'"TARGET"'>'+TPAPI.escape(self.properties['TARGET'])+'<'"/TARGET"'>'
            outputXML += os3+'<'"CONFIG"'>'+TPAPI.escape(self.properties['CONFIG'])+'<'"/CONFIG"'>'
            outputXML += os2+'<'"/OrderNo"'>'
            return outputXML

        def _getPropertiesFromXML(self,xmlElement):
            '''Populates the objects content from an xmlElement.
            
            The method is also responsible for triggering its child objects getPropertiesFromXML() method'''
            for elem in xmlElement:
                self.properties[elem.tag] = TPAPI.safeNull(elem.text)
        
        def _getPropertiesFromTPI(self,tpiDict=None,filename=None):
            '''Populate the objects contents from a tpiDict object or tpi file.
            
            If a tpi file is passed it is converted to a tpiDict object before processing.

            Exceptions: 
                       Raised if tpiDict and filename are both None (ie nothing to process)'''
            
            print 
            self.logger.debug(self.transformerID + "._getPropertiesFromTPI()")
            if tpiDict==None and filename==None:
                strg = 'getPropertiesFromTPI() Nothing to Process'
                raise Exception(strg)
                self.logger.error(strg)
            else:
                if filename is not None:
                    tpidict = TPAPI.TpiDict(filename).returnTPIDict()
                for row in tpiDict['Transformation']['TRANSFORMERID']:
                    if tpiDict['Transformation']['TRANSFORMERID'][row].lower() == self.transformerID.lower() and tpiDict['Transformation']['ORDERNO'][row] == self.rowID:
                        
                        self.properties['TYPE'] = TPAPI.checkNull(tpiDict['Transformation']['TYPE'][row])
                        self.properties['SOURCE'] = TPAPI.checkNull(tpiDict['Transformation']['SOURCE'][row])
                        self.properties['TARGET'] = TPAPI.checkNull(tpiDict['Transformation']['TARGET'][row])
                        self.properties['CONFIG'] = TPAPI.checkNull(tpiDict['Transformation']['CONFIG'][row])
                        
        def _getHash(self):
            '''Calculates a hash value for the transformation, used for diffing at the parser object level'''
            if self._hash == None:
                m = hashlib.md5()
                for prop in sorted(self.properties.iterkeys()):
                    if self.properties[prop] is None:
                        m.update("")
                    else: 
                        m.update(self.properties[prop])
                self._hash = m.digest()       
            return self._hash
        
