from __future__ import with_statement
import TPAPI
import string
import re
import logging
from copy import deepcopy
import warnings
from TPAPI_Util import deprecated


class Attribute(object):
        '''Class to represent any column in a table. Identified by its
        name and attributeType. attributeType property is either 'measurementCounter','referenceKey' or 'measurementKey'.
        '''

        def __init__(self,name,attributeType):
            '''
            Initialised with name and the attributeType
            
            self.attributeType:
                Description: Type of the attribute. either 'measurementCounter', 'referenceKey' or 'measurementKey'
                Type:String
                
            self.name:
                Description: name of the attribute
                Type: String
                
            self.properties:
                Description: Contains the properties of for the attribute object
                Type: Dictionary
                Keys: (Dependent on the attribute Type)
                
                'measurementCounter':
                        DESCRIPTION
                        TIMEAGGREGATION
                        GROUPAGGREGATION
                        COUNTAGGREGATION
                        DATATYPE
                        DATASIZE
                        DATASCALE
                        INCLUDESQL
                        UNIVOBJECT
                        UNIVCLASS
                        COUNTERTYPE
                        COUNTERPROCESS
                        DATAID
                        
                        
                'measurementKey':
                        DESCRIPTION
                        ISELEMENT
                        UNIQUEKEY
                        DATATYPE
                        DATASIZE
                        DATASCALE
                        NULLABLE
                        INDEXES
                        INCLUDESQL
                        UNIVOBJECT
                        JOINABLE
                        DATAID
                        
                'referenceKey':
                        DATATYPE
                        DATASIZE
                        DATASCALE
                        NULLABLE
                        INDEXES
                        UNIQUEKEY
                        INCLUDESQL
                        INCLUDEUPD
                        DESCRIPTION
                        DATAID

            '''
            
            self.logger = logging.getLogger('TPAPI.TPAPI_TP.TechPackVersion.FactTableVersion.Attribute')
            validAttTypes = ['measurementCounter','referenceKey','measurementKey']
            if attributeType not in validAttTypes:
                strg = 'TPAPI.TPAPI_TP.TechPackVersion.FactTableVersion.Attribute.init() invalid attributeType'
                self.logger.error(strg)
                raise Exception(strg)
            self.attributeType = attributeType
            self.name = name
            self.properties = {}
            self._parentTableName = '' #this is set outside the class by the get properties from tpi method of the table class, NOT always populated
            self.logger.debug(self.name + ".__init__()")
        
        def _getPropertiesFromServer(self,server,typeid):
            '''Gets the properties of the attribute from the server using the tables typeid.
            
            Populates self.properties dictionary depending on the attributeType
            
            Sql Statement:
                    SELECT DATATYPE,DATASIZE,DATASCALE,NULLABLE,INDEXES,UNIQUEKEY,INCLUDESQL,INCLUDEUPD,DESCRIPTION,DATAID  from dwhrep.ReferenceColumn
                    SELECT DESCRIPTION,ISELEMENT,UNIQUEKEY,DATATYPE,DATASIZE,DATASCALE,NULLABLE,INDEXES,INCLUDESQL,UNIVOBJECT,JOINABLE,DATAID from dwhrep.MeasurementKey
                    SELECT DESCRIPTION,TIMEAGGREGATION,GROUPAGGREGATION,COUNTAGGREGATION,DATATYPE,DATASIZE,DATASCALE,INCLUDESQL,UNIVOBJECT,UNIVCLASS,COUNTERTYPE,COUNTERPROCESS,DATAID from dwhrep.MeasurementCounter WHERE TYPEID=? AND DATANAME=?        
            
            Exceptions:
                    Raised if attributeType is not recognised
            
            '''
            self.logger.debug(self.name + ".getAttributeProperties()")
            with TPAPI.DbAccess(server,'dwhrep') as crsr:      
                if self.attributeType == 'referenceKey':                    
                    self.key = True
                    crsr.execute("SELECT DATATYPE,DATASIZE,DATASCALE,NULLABLE,INDEXES,UNIQUEKEY,INCLUDESQL,INCLUDEUPD,DESCRIPTION,DATAID  from dwhrep.ReferenceColumn WHERE TYPEID =? AND DATANAME=?", (typeid,self.name,))
                elif self.attributeType =='measurementKey':
                    self.key = True
                    crsr.execute("SELECT DESCRIPTION,ISELEMENT,UNIQUEKEY,DATATYPE,DATASIZE,DATASCALE,NULLABLE,INDEXES,INCLUDESQL,UNIVOBJECT,JOINABLE,DATAID from dwhrep.MeasurementKey WHERE TYPEID=? AND DATANAME=?",(typeid,self.name,))
                elif self.attributeType =='measurementCounter':                    
                    self.key = False
                    crsr.execute("SELECT DESCRIPTION,TIMEAGGREGATION,GROUPAGGREGATION,COUNTAGGREGATION,DATATYPE,DATASIZE,DATASCALE,INCLUDESQL,UNIVOBJECT,UNIVCLASS,COUNTERTYPE,COUNTERPROCESS,DATAID from dwhrep.MeasurementCounter WHERE TYPEID=? AND DATANAME=?",(typeid,self.name,))
                else:
                    raise "Error, attribute type %s is not recognised." % self.attributeType
                desc = crsr.description
                row = crsr.fetchone()
                i = 0
                for col in desc:
                    self.properties[col[0]] = str(row[i]).strip()
                    i += 1          
    
        def _difference(self,attObject,deltaObj,ftvd):
            '''Calculates the difference between two attribute objects
            
            Method takes attObject,deltaObj and deltaTPV as inputs.
            attObject: The table to be compared against
            DeltaObj: The single object that gets passed through the entire diff recording the changes.
            DeltaTPV: A TechPackVersion Object that gets passed through the entire diff recording only new content.
            
            The Difference method will trigger the difference method of its child objects, passing
            in the object to compare, deltaObj and deltaTPV. After calculating the diff the child object passes these objects
            back in conjunction with a flag to say whether a (only new or changed content.. not deleted) was found or not. This flag is used to decide
            whether a child object should be added to the parent object in the DeltaTPV.
            
            Note: Attribute does not have any child objects
            
            Returns:
                    diffFlag (Boolean indicating where a change was found or not)
                    deltaObj
                    deltaTPV 
            
            '''
            diffFlag = False
            deltaObj.stack.append(self.attributeType+"="+self.name)
            attd = TPAPI.Attribute(self.name,self.attributeType)
            attributePropertiesDelta = TPAPI.DictDiffer(self.properties,attObject.properties)
            
            for item in attributePropertiesDelta.changed():
                if (self.properties[item] != None and attObject.properties[item] != None): 
                    deltaObj.stack.append("Property=<changed>"+item)
                    origval = self.properties[item]
                    deltaVal = attObject.properties[item]
                    attd.properties[item] = deltaVal
                    deltaObj._addChange(deltaObj.stack,deltaVal,origval)
                    deltaObj.stack.pop()
            deltaObj.stack.pop()
            
            if attributePropertiesDelta.changed():
                diffFlag = True
                ftvd.attributeObjects[self.name] = attd

            return diffFlag,deltaObj,ftvd


        def _toXML(self,offset=0):
            '''Write the object to an xml formatted string
            Offset value is used for string indentation. Default to 0
            Parent toXML() method is responsible for triggering child object toXML() methods.
            Return Value: xmlString 
            '''
            offset += 4
            os = "\n" + " "*offset
            os2 = os+" "*4
            outputXML  =os+'<Attribute name="'+self.name+ '" attributeType ="'+self.attributeType +'">' 
            for attr in self.properties:
                outputXML += os2+'<'+str(attr)+'>'+TPAPI.escape(self.properties[attr])+'</'+str(attr)+'>'
            outputXML +=os+'</Attribute>'
            return outputXML
                      
        def _getPropertiesFromXML(self,xmlElement):
            '''Populates the objects content from an xmlElement.
            The method is also responsible for triggering its child objects getPropertiesFromXML() method'''
            
            self.logger.debug(self.name + "._getPropertiesFromXML()")
            for elem in xmlElement:
                if elem.text is None:
                    self.properties[elem.tag] = ''
                else:
                    self.properties[elem.tag] = TPAPI.safeNull(elem.text)

        def _getPropertiesFromTPI(self,tpidict=None,filename=None):
            '''Populate the objects contents from a tpiDict object or tpi file.
            
            If a tpi file is passed it is converted to a tpiDict object before processing
            
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
                for col in tpidict['Measurementcounter']:    
                    pass
                if self.attributeType =='measurementKey':
                    for row in tpidict['Measurementkey']['DATANAME']:
                        if tpidict['Measurementkey']['DATANAME'][row] == self.name and tpidict['Measurementkey']['TYPEID'][row] == self._parentTableName:
                            self.properties['DESCRIPTION'] = TPAPI.checkNull(tpidict['Measurementkey']['DESCRIPTION'][row])
                            self.properties['ISELEMENT'] = TPAPI.checkNull(tpidict['Measurementkey']['ISELEMENT'][row])
                            self.properties['UNIQUEKEY'] = TPAPI.checkNull(tpidict['Measurementkey']['UNIQUEKEY'][row])
                            self.properties['DATATYPE'] = TPAPI.checkNull(tpidict['Measurementkey']['DATATYPE'][row])
                            self.properties['DATASCALE'] = TPAPI.checkNull(tpidict['Measurementkey']['DATASCALE'][row])
                            self.properties['NULLABLE'] = TPAPI.checkNull(tpidict['Measurementkey']['NULLABLE'][row])
                            self.properties['INDEXES'] = TPAPI.checkNull(tpidict['Measurementkey']['INDEXES'][row])
                            self.properties['INCLUDESQL'] = TPAPI.checkNull(tpidict['Measurementkey']['INCLUDESQL'][row])
                            self.properties['UNIVOBJECT'] = TPAPI.checkNull(tpidict['Measurementkey']['UNIVOBJECT'][row])
                            self.properties['JOINABLE'] = TPAPI.checkNull(tpidict['Measurementkey']['JOINABLE'][row])
                            self.properties['DATAID'] = TPAPI.checkNull(tpidict['Measurementkey']['DATAID'][row])
                            self.properties['DATASIZE'] = TPAPI.checkNull(tpidict['Measurementkey']['DATASIZE'][row])
                elif self.attributeType == 'measurementCounter':
                    for row in tpidict['Measurementcounter']['DATANAME']:
                        if tpidict['Measurementcounter']['DATANAME'][row] == self.name and tpidict['Measurementcounter']['TYPEID'][row] == self._parentTableName:
                            self.properties['DESCRIPTION'] = TPAPI.checkNull(tpidict['Measurementcounter']['DESCRIPTION'][row])
                            self.properties['TIMEAGGREGATION'] = TPAPI.checkNull(tpidict['Measurementcounter']['TIMEAGGREGATION'][row])
                            self.properties['GROUPAGGREGATION'] = TPAPI.checkNull(tpidict['Measurementcounter']['GROUPAGGREGATION'][row])
                            self.properties['COUNTAGGREGATION'] = TPAPI.checkNull(tpidict['Measurementcounter']['COUNTAGGREGATION'][row])
                            self.properties['DATATYPE'] = TPAPI.checkNull(tpidict['Measurementcounter']['DATATYPE'][row])
                            self.properties['DATASIZE'] = TPAPI.checkNull(tpidict['Measurementcounter']['DATASIZE'][row])
                            self.properties['DATASCALE'] = TPAPI.checkNull(tpidict['Measurementcounter']['DATASCALE'][row])
                            self.properties['INCLUDESQL'] = TPAPI.checkNull(tpidict['Measurementcounter']['INCLUDESQL'][row])
                            self.properties['UNIVOBJECT'] = TPAPI.checkNull(tpidict['Measurementcounter']['UNIVOBJECT'][row])
                            self.properties['UNIVCLASS'] = TPAPI.checkNull(tpidict['Measurementcounter']['UNIVCLASS'][row])
                            self.properties['COUNTERTYPE'] = TPAPI.checkNull(tpidict['Measurementcounter']['COUNTERTYPE'][row])
                            self.properties['COUNTERPROCESS'] = TPAPI.checkNull(tpidict['Measurementcounter']['COUNTERPROCESS'][row])
                            self.properties['DATAID'] = TPAPI.checkNull(tpidict['Measurementcounter']['DATAID'][row])
                elif self.attributeType == 'referenceKey':
                    for row in tpidict['Referencecolumn']['DATANAME']:
                        if tpidict['Referencecolumn']['DATANAME'][row] == self.name and tpidict['Referencecolumn']['TYPEID'][row] == self._parentTableName:
                            self.properties['DATATYPE'] = TPAPI.checkNull(tpidict['Referencecolumn']['DATATYPE'][row])
                            self.properties['DATASIZE'] = TPAPI.checkNull(tpidict['Referencecolumn']['DATASIZE'][row])
                            self.properties['DATASCALE'] = TPAPI.checkNull(tpidict['Referencecolumn']['DATASCALE'][row])
                            self.properties['NULLABLE'] = TPAPI.checkNull(tpidict['Referencecolumn']['NULLABLE'][row])
                            self.properties['INDEXES'] = TPAPI.checkNull(tpidict['Referencecolumn']['INDEXES'][row])
                            self.properties['UNIQUEKEY'] = TPAPI.checkNull(tpidict['Referencecolumn']['UNIQUEKEY'][row])
                            self.properties['INCLUDESQL'] = TPAPI.checkNull(tpidict['Referencecolumn']['INCLUDESQL'][row])
                            self.properties['INCLUDEUPD'] = TPAPI.checkNull(tpidict['Referencecolumn']['INCLUDEUPD'][row])
                            self.properties['DESCRIPTION'] = TPAPI.checkNull(tpidict['Referencecolumn']['DESCRIPTION'][row])
                            self.properties['DATAID'] = TPAPI.checkNull(tpidict['Referencecolumn']['DATAID'][row])
                            
        @deprecated
        def _generateSQLInserts(self,typeid):
            '''@deprecated 
            Container method for multiple sql insert methods
            
            depending on the attributeType a different method is called
            
            Returns:
                    sql,vals
            '''
            if self.attributeType == 'measurementKey':
                sql,vals = self._generateMeasurementKeySQL_INSERT(self.typeid)
            elif self.attributeType == 'measurementCounter':
                sql,vals = self._generateMeasurementCounterSQL_INSERT(self.typeid)
            elif self.attributeType == 'referenceKey':
                sql,vals = self._generateReferenceColumnSQL(self.typeid)
            return sql,vals
            
            
        @deprecated    
        def _generateMeasurementKeySQL_INSERT(self,typeid):
            '''@deprecated'''
            attDict = deepcopy(self.properties)
            attDict['DATANAME'] = self.name
            attDict['TYPEID'] = typeid
            attDict['UNIQUEVALUE'] = 255
            sql,vals = TPAPI.dictToSQL(attDict,'MeasurementKey')
            return sql,vals
        
        @deprecated
        def _generateMeasurementCounterSQL_INSERT(self,typeid):
            '''@deprecated'''
            attDict = deepcopy(self.properties)
            attDict['DATANAME'] = self.name
            attDict['TYPEID'] = typeid
            sql,vals = TPAPI.dictToSQL(attDict,'MeasurementCounter')
            return sql,vals
        
        @deprecated      
        def _generateReferenceColumnSQL(self,typeid):
            '''@deprecated'''
            attDict = deepcopy(self.properties)
            attDict['DATANAME'] = self.name
            attDict['TYPEID'] = typeid
            attDict['UNIQUEVALUE'] = 255
            publicColumns = ['CREATED','MODIFIED','MODIFIER','STATUS','VENDOR','BHTYPE','DESCRIPTION']
            if self.name not in publicColumns:
                attDict['COLTYPE'] = 'COLUMN'
            else:
                attDict['COLTYPE'] = 'PUBLICCOL'
            sql,vals = TPAPI.dictToSQL(attDict,'ReferenceColumn')
            return sql,vals
        
        @deprecated
        def _createSQLInserts(self,typeid):
            '''@deprecated'''

            attDict = deepcopy(self.properties)
            attDict['DATANAME'] = self.name
            attDict['TYPEID'] = typeid

            if self.attributeType == 'measurementKey':
                sql,vals = TPAPI.dictToSQL(attDict,'MeasurementKey')
            elif self.attributeType == 'measurementCounter':
                sql,vals = TPAPI.dictToSQL(attDict,'MeasurementCounter')
            elif self.attributeType == 'referenceKey':
                publicColumns = ['CREATED','MODIFIED','MODIFIER','STATUS','VENDOR','BHTYPE','DESCRIPTION']
                if self.name not in publicColumns:
                    attDict['COLTYPE'] = 'COLUMN'
                else:
                    attDict['COLTYPE'] = 'PUBLICCOL'
                sql,vals = TPAPI.dictToSQL(attDict,'ReferenceColumn')
            return sql,vals
        
        @deprecated
        def _generateMeasurementColumnSQL_INSERT(self,server,typeid,List_mtableIDs,baseDefinition):
            '''@deprecated 
            Generated at this level as table (MTABLEID) information needed for inserts'''
                    
            baseTPVersion = baseDefinition.split(':')[1]
            versionid = typeid.split(':')[0]
            rowNumber = 0  #row number
            measurementColumnDict = {} # to hold all the data, used to generate sql,vals
            for mtableid in List_mtableIDs:
                partitionType = str(mtableid).rsplit(':')[-1]
                baseMTableID = "TP_BASE:"+ baseTPVersion + ":" + partitionType
                measurementColumnDict[rowNumber] = {}
                measurementColumnDict[rowNumber]['MTABLEID'] = mtableid
                if self.attributeType == 'measurementCounter':
                    measurementColumnDict[rowNumber] = {}
                    measurementColumnDict[rowNumber]['MTABLEID'] = mtableid
                    measurementColumnDict[rowNumber]['COLNUMBER'] = rowNumber # this will be regenerated at the end
                    measurementColumnDict[rowNumber]['DATANAME'] = self.name
                    measurementColumnDict[rowNumber]['DATATYPE'] = self.properties['DATATYPE']
                    measurementColumnDict[rowNumber]['DATASIZE'] = self.properties['DATASIZE'] 
                    measurementColumnDict[rowNumber]['DATASCALE'] = self.properties['DATASCALE']
                    measurementColumnDict[rowNumber]['UNIQUEVALUE'] = 255
                    measurementColumnDict[rowNumber]['NULLABLE'] = 1
                    measurementColumnDict[rowNumber]['INDEXES'] = ''
                    measurementColumnDict[rowNumber]['DESCRIPTION'] = self.properties['DESCRIPTION'] 
                    measurementColumnDict[rowNumber]['DATAID'] = self.properties['DATAID']
                    measurementColumnDict[rowNumber]['RELEASEID'] = versionid # might be wrong
                    measurementColumnDict[rowNumber]['UNIQUEKEY'] = 0
                    measurementColumnDict[rowNumber]['INCLUDESQL'] = self.properties['INCLUDESQL']
                    measurementColumnDict[rowNumber]['COLTYPE'] = 'COUNTER'
                    measurementColumnDict[rowNumber]['FOLLOWJOHN'] = None # HOW TO HANDLE THIS?
                    rowNumber += 1

                elif self.attributeType == 'measurementKey':
                    measurementColumnDict[rowNumber] = {}
                    measurementColumnDict[rowNumber]['MTABLEID'] = mtableid
                    measurementColumnDict[rowNumber]['COLNUMBER'] = rowNumber # this will be regenerated at the end
                    measurementColumnDict[rowNumber]['DATANAME'] = self.name # keyname?
                    measurementColumnDict[rowNumber]['DATATYPE'] = self.properties['DATATYPE'] 
                    measurementColumnDict[rowNumber]['DATASIZE'] = self.properties['DATASIZE'] 
                    measurementColumnDict[rowNumber]['DATASCALE'] = self.properties['DATASCALE'] 
                    measurementColumnDict[rowNumber]['UNIQUEVALUE'] = 255
                    measurementColumnDict[rowNumber]['NULLABLE'] = self.properties['NULLABLE'] 
                    measurementColumnDict[rowNumber]['INDEXES'] = self.properties['INDEXES'] 
                    measurementColumnDict[rowNumber]['DESCRIPTION'] = self.properties['DESCRIPTION'] 
                    measurementColumnDict[rowNumber]['DATAID'] = self.properties['DATAID'] 
                    measurementColumnDict[rowNumber]['RELEASEID'] = versionid # might be wrong
                    measurementColumnDict[rowNumber]['UNIQUEKEY'] = self.properties['UNIQUEKEY'] 
                    measurementColumnDict[rowNumber]['INCLUDESQL'] = self.properties['INCLUDESQL'] 
                    measurementColumnDict[rowNumber]['COLTYPE'] = 'KEY'
                    measurementColumnDict[rowNumber]['FOLLOWJOHN'] = None # HOW TO HANDLE THIS?
                    rowNumber += 1

            for row in measurementColumnDict:           
                sql,vals = TPAPI.dictToSQL(measurementColumnDict[row],'measurementColumn')
                
            return sql,vals

        @deprecated
        def _updateDatabase(self,server,typeid):
            '''@deprecated'''
            sql,vals = self._createSQLInserts(typeid)
            with TPAPI.DbAccess(server,'dwhrep') as crsr:
                self.logger.debug(self.name + ".update() sql=" + str(sql) + " vals = " + str(vals))
                crsr.execute(sql,(vals))
                
        @deprecated
        def _generateMeasurementKeySQL_UPDATE(self,typeid,column,value):
            '''@deprecated'''
            sqlstatement = 'update dwhrep.MeasurementKey set ' + column + "='" + value + "' where typeid = '" + typeid + "' and DATANAME = '"+self.name+"';"      #UPDATE table_name
            return sqlstatement        
        
        @deprecated
        def _generateMeasurementCounterSQL_UPDATE(self,typeid,column,value):
            '''@deprecated'''
            sqlstatement = 'update dwhrep.MeasurementCounter set ' + column + "='" + value + "' where mtableid like'" + self.typeid + "%' and DATANAME = '"+self.properties['DATANAME']+"';"      #UPDATE table_name
            return sqlstatement
        
        @deprecated
        def _generateMeasurementColumnSQL_UPDATE(self,mtableid,column,value):
            '''@deprecated'''
            sqlstatement = 'update dwhrep.MeasurementColumn set ' + column + "='" + value + "' where mtableid  ='" + mtableid + "' and DATANAME = '"+self.name+"';"      #UPDATE table_name
            return sqlstatement
        
        @deprecated
        def _create(self,typeid,mtableIDs,basetp,server):
            '''@deprecated 
            Create a new attribute on the server'''
            
            if self.attributeType == 'measurementCounter':
                SQL_INSERT_MeasurementCounter,vals = self._generateMeasurementCounterSQL_INSERT(typeid) #RENAME
                self.logger.debug('INSERT_MEASUREMENTCOUNTER ' + str(SQL_INSERT_MeasurementCounter) + ":"+ str(vals))
                with TPAPI.DbAccess(server,'dwhrep') as crsr:
                    crsr.execute(SQL_INSERT_MeasurementCounter,vals)
                SQL_INSERT_MeasurementColumn,vals = self._generateMeasurementColumnSQL_INSERT(server,typeid,mtableIDs,basetp)
                self.logger.debug('INSERT_MEASUREMENTCOLUMN ' + str(SQL_INSERT_MeasurementColumn) + ":" + str(vals))
                with TPAPI.DbAccess(server,'dwhrep') as crsr:
                    crsr.execute(SQL_INSERT_MeasurementColumn,vals)
            elif self.attributeType == 'measurementKey':
                print "NEW KEY"
                SQL_INSERT_MeasurementKey,vals = self._generateMeasurementKeySQL_INSERT(typeid)
                self.logger.debug('INSERT_MEASUREMENTKEY' + str(SQL_INSERT_MeasurementKey) + ":"+ str(vals))
                with TPAPI.DbAccess(server,'dwhrep') as crsr:
                    crsr.execute(SQL_INSERT_MeasurementKey,vals)
                SQL_INSERT_MeasurementColumnTable,vals = self._generateMeasurementColumnSQL_INSERT(server,typeid,mtableIDs,basetp)
                self.logger.debug('INSERT_MEASUREMENTCOLUMN' + str(SQL_INSERT_MeasurementColumnTable) + ":"+ str(vals))
                with TPAPI.DbAccess(server,'dwhrep') as crsr:
                    crsr.execute(SQL_INSERT_MeasurementColumnTable,vals)                   
        
        @deprecated
        def _upgrade(self,typeid,mtableids,baseTPDefinition,deltaAtt,server):
            '''@deprecated
            Upgrade or Insert a new Attribute object into the dwhrep using the deltaAtt'''
            self.logger.debug('Attribute:'+self.name+': _upgrade()')
            if self.attributeType == 'measurementCounter':
                if len( deltaAtt.properties) < 12:
                    for prop in deltaAtt.properties:
                        SQLupdateMeasurementCounterTable = self._generateMeasurementCounterSQL_UPDATE(typeid,prop,deltaAtt.properties[prop])
                        self.logger.debug('UPDATE_MEASUREMENTCOUNTER ' + str(SQLupdateMeasurementCounterTable))
                        with TPAPI.DbAccess(server,'dwhrep') as crsr:
                                crsr.execute(SQLupdateMeasurementCounterTable)
                        measurementColumnAffectedKeys = ['DATAID','DATATYPE','DATASIZE','DATASCALE','INCLUDESQL','DESCRIPTION']
                        if prop in measurementColumnAffectedKeys:
                            for mtableid in mtableids:
                                SQL_UPDATE_MeasurementColumnTable = self.generateMeasurementColumn_SQL_UPDATE(mtableid,prop,deltaAtt.properties[prop])
                                self.logger.debug('UPDATE_MEASUREMENTCOLUMN ' + str(SQL_UPDATE_MeasurementColumnTable))
                                with TPAPI.DbAccess(server,'dwhrep') as crsr:
                                    crsr.execute(SQL_UPDATE_MeasurementColumnTable)
                else:
                    SQL_INSERT_MeasurementCounter,vals = self._generateMeasurementCounterSQL_INSERT(typeid)
                    self.logger.debug('INSERT_MEASUREMENTCOUNTER ' + str(SQL_INSERT_MeasurementCounter) + ":"+ str(vals))
                    with TPAPI.DbAccess(server,'dwhrep') as crsr:
                        crsr.execute(SQL_INSERT_MeasurementCounter,vals)
                    SQL_INSERT_MeasurementColumn,vals = self._generateMeasurementColumnSQL_INSERT(server,typeid,mtableids,baseTPDefinition)
                    self.logger.debug('INSERT_MEASUREMENTCOLUMN ' + str(SQL_INSERT_MeasurementColumn) + ":" + str(vals))
                    with TPAPI.DbAccess(server,'dwhrep') as crsr:
                        crsr.execute(SQL_INSERT_MeasurementColumn,vals)
            elif self.attributeType == 'measurementKey':
                if len( deltaAtt.properties) < 12:
                    for prop in deltaAtt.properties:
                        SQL_UPDATE_MeasurementKeyTable = self._generateMeasurementKeySQL_UPDATE(typeid,prop,deltaAtt.properties[prop])
                        self.logger.debug('UPDATE_MEASUREMENTKEY' + str(SQL_UPDATE_MeasurementKeyTable))
                        with TPAPI.DbAccess(server,'dwhrep') as crsr:
                            crsr.execute(SQL_UPDATE_MeasurementKeyTable)
                    measurementColumnAffectedKeys = ['DATAID','DATATYPE','DATASIZE','DATASCALE','INCLUDESQL','DESCRIPTION']
                    if prop in measurementColumnAffectedKeys:
                        for mtableid in mtableids:
                            SQL_UPDATE_MeasurementColumnTable = self._generateMeasurementColumnSQL_UPDATE(mtableid,prop,deltaAtt.properties[prop])
                            self.logger.debug('UPDATE_MEASUREMENTCOLUMN' + str(SQL_UPDATE_MeasurementColumnTable))
                            with TPAPI.DbAccess(server,'dwhrep') as crsr:
                                crsr.execute(SQL_UPDATE_MeasurementColumnTable)
                else:
                    SQL_INSERT_MeasurementKey,vals = self._generateMeasurementKeySQL_INSERT(typeid)
                    self.logger.debug('INSERT_MEASUREMENTKEY' + str(SQL_INSERT_MeasurementKey) + ":"+ str(vals))
                    with TPAPI.DbAccess(server,'dwhrep') as crsr:
                        crsr.execute(SQL_INSERT_MeasurementKey,vals)
                    SQL_INSERT_MeasurementColumnTable,vals = self._generateMeasurementColumnSQL_INSERT(server,typeid,mtableids,baseTPDefinition)
                    self.logger.debug('INSERT_MEASUREMENTCOLUMN' + str(SQL_INSERT_MeasurementColumnTable) + ":"+ str(vals))
                    with TPAPI.DbAccess(server,'dwhrep') as crsr:
                        crsr.execute(SQL_INSERT_MeasurementColumnTable,vals)                                  
            elif self.attributeType == 'referenceKey':
                #not handled currently
                pass
            
