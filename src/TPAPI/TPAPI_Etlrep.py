from __future__ import with_statement
import TPAPI
import logging

class EtlrepSetCollection(object):
        '''Class to represent Etlrep MetaCollection Set for a TechPack Version. EtlrepSetCollection is the Top Level class for ETLREP information
        Corresponds to the META_COLLECTIONS_SETS table in the etlrep'''
        def __init__(self,collectionName,versionNumber):
            self.logger = logging.getLogger('TPAPI.TPAPI_TP.TechPackVersion.EtlrepSetCollection')
            self.collectionSetID = ''
            self.collectionName = collectionName
            self.versionNumber = versionNumber  # to use this? - build number
            self.setIDs = {}
            self.setObjects = []
            self.properties = {}
            
        def _getProperties(self,server):
            self._getPropertiesFromServer(server)
            self._getSetsFromServer(server)
            self._getSetObjects(server)
            
        def _getName(self):
            '''Return the unique name of the object'''
            name = ''
            return name
        
        def _getPropertiesFromServer(self,server):
            '''Get the properties of the EtlrepSetCollection Object from a tpifile or dict'''
            with TPAPI.DbAccess(server,'etlrep') as crsr:
                crsr.execute("SELECT * from etlrep.META_COLLECTION_SETS where COLLECTION_SET_NAME=? AND VERSION_NUMBER=?",(self.collectionName,self.versionNumber))
                desc = crsr.description
                row = crsr.fetchone()
                if row is not None:
                    self.properties = {}
                    i = 0
                    for x in desc:
                        self.properties[x[0]] = str(row[i])
                        i+=1  
            return  
        
        def _getPropertiesFromTPI(self,tpiDict=None,filename=None):
            '''Populate the objects contents from a tpiDict object or tpi file.
            
            If a tpi file is passed it is converted to a tpiDict object before processing.
            
            Exceptions: 
                       Raised if tpiDict and filename are both None (ie nothing to process)'''
            
            self.logger.debug(self.collectionName + "._getPropertiesFromTPI()")
            if tpiDict==None and filename==None:
                strg = 'getPropertiesFromTPI() Nothing to Process'
                raise Exception(strg)
                self.logger.error(strg)
            else:
                if filename is not None:
                    tpidict = TPAPI.TpiDict(filename).returnTPIDict()
                # get all the properties (should only be one row returned
                for row in tpiDict['META_COLLECTION_SETS']['COLLECTION_SET_NAME']:
                    if tpiDict['META_COLLECTION_SETS']['COLLECTION_SET_NAME'][row] == self.collectionName and tpiDict['META_COLLECTION_SETS']['VERSION_NUMBER'][row] == self.versionNumber:
                        for col in tpiDict['META_COLLECTION_SETS']:
                            self.properties[col] = tpiDict['META_COLLECTION_SETS'][col][row]

                # now get the child sets of the collection, create the objects and append to setObjects list of the parent
                if 'COLLECTION_SET_ID' in self.properties: # can only fetch children if this property is set
                    #Potential Bug Could cause an issue if interface and tp have same collection set id? -> both will be present in the tpiDict
                    for row in tpiDict['META_COLLECTIONS']['COLLECTION_SET_ID']:
                        if tpiDict['META_COLLECTIONS']['COLLECTION_SET_ID'][row] == self.properties['COLLECTION_SET_ID']: # ie is parent [need to check name also]
                            newSet = TPAPI.EtlrepSet(tpiDict['META_COLLECTIONS']['COLLECTION_NAME'][row]) # create the set
                            newSet._getPropertiesFromTPI(self.properties['COLLECTION_SET_ID'],tpiDict=tpiDict) # get the set properties
                            self.setObjects.append(newSet) # append to the objects list
                             
        def _getSetsFromServer(self,server):
            '''Returns a list of the set names and set ids of all the child sets for the top level etlrep collection object
            This information is used to get properties of the set from the server'''
            with TPAPI.DbAccess(server,'etlrep') as crsr:
                crsr.execute("SELECT COLLECTION_NAME,COLLECTION_ID from etlrep.META_COLLECTIONS where COLLECTION_SET_ID =?",(self.properties['COLLECTION_SET_ID'],))
                resultset = crsr.fetchall()
            for row in resultset:
                self.setIDs[row[0]] = str(row[1])
            return
   
        def _getSetObjects(self,server):
            '''Create a EtlrepSet Object for each set in the setIDs list, gets the properties of the set from the server
            using collection_set_id, and the the object is appended to the list of set objects for the top level collection'''
            for setName in self.setIDs:
                newSet= TPAPI.EtlrepSet(setName)
                newSet._getPropertiesFromServer(server,self.properties['COLLECTION_SET_ID'])
                self.setObjects.append(newSet)

        def _toXML(self,offset=0):
            '''Write the object to an xml formatted string
            
            Offset value is used for string indentation. Default to 0
            Parent toXML() method is responsible for triggering child object toXML() methods.
    
            Return Value: xmlString 
            '''
            offset += 4
            os = "\n" + " "*offset
            outputXML = os
            for prop in self.properties:
                    outputXML += os+'<'+str(prop)+'>'+ TPAPI.escape(self.properties[prop]) +'</'+str(prop)+'>'
            for etlrepset in self.setObjects:
                outputXML +='<MetaCollections collectionName="'+etlrepset.setName +'">'
                outputXML += etlrepset._toXML(offset)
                outputXML += os+'</MetaCollections>'+os
            return outputXML
                 

        
################################################################################################################################################### 
              
class EtlrepSet(object):
        '''Class to represent an EtlrepSet for a TechPack Version. EtlrepSet is a child object of EtlrepSetCollection object
        Corresponds to the META_COLLECTIONS Table in the etlrep database '''
        
        def __init__(self,setName):
            self.logger = logging.getLogger('TPAPI.TPAPI_TP.TechPackVersion.EtlrepSet')
            self.setName = setName 
            self.actionObjects = [] # list of child EtlrepAction Objects
            self.actions = {}
            self.properties = {}

        def _getProperties(self,server):
            self._getPropertiesFromServer(server)
            self._getActionsFromServer(server)
            self._getActionObjects(server) # needs parent set id # this wont work
            

        def _getName(self):
            '''Return the unique name of the object'''
            name = ''
            return name


        def _getPropertiesFromTPI(self,parentCollectionSetID,tpiDict=None,filename=None):
            '''Populate the objects contents from a tpiDict object or tpi file.
            
            If a tpi file is passed it is converted to a tpiDict object before processing.
            parentCollectionSetID is passed in to ensure correct child sets are identified.
            
            Exceptions: 
                       Raised if tpiDict and filename are both None (ie nothing to process)'''
            
            self.logger.debug(self.setName + "._getPropertiesFromTPI()")
            if tpiDict==None and filename==None:
                strg = 'getPropertiesFromTPI() Nothing to Process'
                raise Exception(strg)
                self.logger.error(strg)
            else:
                if filename is not None:
                    tpidict = TPAPI.TpiDict(filename).returnTPIDict()
    
                for row in tpiDict['META_COLLECTIONS']['COLLECTION_NAME']:
                    if tpiDict['META_COLLECTIONS']['COLLECTION_NAME'][row] == self.setName and tpiDict['META_COLLECTIONS']['COLLECTION_SET_ID'][row] == parentCollectionSetID:
                        for col in tpiDict['META_COLLECTIONS']:
                            self.properties[col] = tpiDict['META_COLLECTIONS'][col][row]
                            
                # Get the EtlrepAction objects and their properties for the parent EtlrepSet object       
                if 'COLLECTION_ID' in self.properties: # This property needs to exist to get the child actions
                    for row in tpiDict['META_TRANSFER_ACTIONS']['TRANSFER_ACTION_NAME']:
                        if tpiDict['META_TRANSFER_ACTIONS']['COLLECTION_ID'][row] == self.properties['COLLECTION_ID']:
                            newAction = TPAPI.EtlrepAction(tpiDict['META_TRANSFER_ACTIONS']['TRANSFER_ACTION_NAME'][row])
                            newAction._getPropertiesFromTPI(self.properties['COLLECTION_ID'],tpiDict=tpiDict)
                            self.actionObjects.append(newAction)
                            
                            
        def _getPropertiesFromServer(self,server,parent_collection_set_id):
            '''Get the properties of the set from the server using the parent collection_set_id'''
            with TPAPI.DbAccess(server,'etlrep') as crsr:
                crsr.execute("SELECT * from etlrep.META_COLLECTIONS where COLLECTION_NAME=? AND COLLECTION_SET_ID =?",(self.setName, parent_collection_set_id,))
                desc = crsr.description
                row = crsr.fetchone()
                if row is not None:
                    self.properties = {}
                    i = 0
                    for x in desc:
                        self.properties[x[0]] = str(row[i])
                        i+=1    
            self._getActionsFromServer(server)
            self._getActionObjects(server,parent_collection_set_id)
            return 
        

        def _getActionsFromServer(self,server):
            '''Returns a list of the action names and action ids of all the child actions for the parent etlrep set object
            This information is used to get properties of the actions from the server'''
            with TPAPI.DbAccess(server,'etlrep') as crsr:
                crsr.execute("SELECT TRANSFER_ACTION_NAME,TRANSFER_ACTION_ID from etlrep.META_TRANSFER_ACTIONS where COLLECTION_ID =?",(self.properties['COLLECTION_ID'],))
                resultset = crsr.fetchall()
            for row in resultset:
                self.actions[row[0]] = str(row[1])

        def _getActionObjects(self,server,parent_collection_id):
            # Not parent_collection_set_id -> should be collection_set_id
            '''Create an EtlrepAction Object for each set in the actions list, get the properties of the action from the server
            using parent_collection_set_id, append the object to the list of action objects for the parent set'''
            for transferActionName in self.actions:
                newActionObject = TPAPI.EtlrepAction(transferActionName)
                newActionObject._getPropertiesFromServer(server,self.properties['COLLECTION_ID'],parent_collection_id)
                self.actionObjects.append(newActionObject)


        def _toXML(self,offset=0):
            '''Write the object to an xml formatted string
            
            Offset value is used for string indentation. Default to 0
            Parent toXML() method is responsible for triggering child object toXML() methods.
    
            Return Value: xmlString 
            '''
            offset += 4
            os = "\n" + " "*offset
            outputXML = os
            for prop in self.properties:
                    outputXML += os+'<'+str(prop)+'>'+ TPAPI.escape(self.properties[prop]) +'</'+str(prop)+'>'
            for action in self.actionObjects:
                outputXML +=os+'<MetaTransferActions transferActionName="'+action.transferActionName+'">'
                outputXML += action._toXML(offset)
                outputXML += os+'</MetaTransferActions>'+os
            return outputXML

        
############################################################################################################################
          
          
class EtlrepAction(object):
        '''Class to represent an EtlrepAction for a TechPack Version. EtlrepSet is a child object of EtlrepSet object
            corresponds to the META_TRANSFER_ACTIONS Table in the etlrep database ''' 

        def __init__(self,transferActionName):
            self.transferActionName = transferActionName
            self.orderNo = None
            self.properties = {}
            
        def _getName(self):
            name = ''
            return name 
          
        def _getPropertiesFromServer(self,server,parent_set_id,parent_collection_id):
            with TPAPI.DbAccess(server,'etlrep') as crsr:
                crsr.execute("select * FROM etlrep.META_TRANSFER_ACTIONS WHERE COLLECTION_ID=? and COLLECTION_SET_ID=? and TRANSFER_ACTION_NAME=?",(parent_set_id,parent_collection_id,self.transferActionName,))
                desc = crsr.description
                row = crsr.fetchone()
                if row is not None:
                    i = 0
                    for x in desc:
                        self.properties[x[0]] = str(row[i])
                        i+=1    
                        
          
        def _getPropertiesFromTPI(self,parentCollectionID,tpiDict=None,filename=None,):
            '''Populate the objects contents from a tpiDict object or tpi file.
            
            If a tpi file is passed it is converted to a tpiDict object before processing.
            parentCollectionID is passed to ensure correct child actions are identified.
            
            Exceptions: 
                       Raised if tpiDict and filename are both None (ie nothing to process)'''
            
            self.logger.debug(self.transferActionName + "._getPropertiesFromTPI()")
            if tpiDict==None and filename==None:
                strg = 'getPropertiesFromTPI() Nothing to Process'
                raise Exception(strg)
                self.logger.error(strg)
            else:
                if filename is not None:
                    tpidict = TPAPI.TpiDict(filename).returnTPIDict()
                    
                for row in tpiDict['META_TRANSFER_ACTIONS']['TRANSFER_ACTION_NAME']:
                    if tpiDict['META_TRANSFER_ACTIONS']['TRANSFER_ACTION_NAME'][row] == self.transferActionName and tpiDict['META_TRANSFER_ACTIONS']['COLLECTION_ID'][row] == parentCollectionID :
                        for col in tpiDict['META_TRANSFER_ACTIONS']:
                            self.properties[col] = tpiDict['META_TRANSFER_ACTIONS'][col][row]

                
        def _toXML(self,offset=0):
            '''Write the object to an xml formatted string
            
            Offset value is used for string indentation. Default to 0
            Parent toXML() method is responsible for triggering child object toXML() methods.
    
            Return Value: xmlString 
            '''
            offset += 4
            os = "\n" + " "*offset
            outputXML = os
            for prop in self.properties:
                outputXML += os+'<'+str(prop)+'>'+ TPAPI.escape(self.properties[prop]) +'</'+str(prop)+'>'
            return outputXML




