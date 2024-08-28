from __future__ import with_statement
import TPAPI
import re
import logging
import sys

class Universe(object):
    
    def __init__(self,versionID,universeName,universeExtension=None,universeExtensionName=None):
        #print "created universe"
        self.versionID = versionID
        self.universeName = universeName
        self.universeExtension = universeExtension
        self.universeExtensionName = universeExtensionName
        self.universeClassObjects = {}
        self.universeTableObjects = {}
        self.universeJoins = [] # list of universe join objects

    
    def _getPropertiesFromServer(self,server):
        self._getUniverseTables(server)
        self._getUniverseClasses(server)
        pass
    
    def _getUniverseTables(self,server):
        
        with TPAPI.DbAccess(server,'dwhrep') as crsr: 
            if self.universeExtension==None:          
                crsr.execute("SELECT TABLENAME FROM dwhrep.UniverseTable where versionid =? and universeExtension like ?",(self.versionID,'ALL%',))
                resultset = crsr.fetchall()
                for row in resultset:
                    unvTab = TPAPI.UniverseTable(self.versionID,'ALL',row[0])
                    unvTab._getPropertiesFromServer(server)
                    self.universeTableObjects[row[0]] = unvTab
            else:
                # Universe specific tables
                crsr.execute("SELECT TABLENAME FROM dwhrep.UniverseTable where versionid =? and universeExtension like ?",(self.versionID,self.universeExtension +'%',))
                resultset = crsr.fetchall()
                for row in resultset:
                    unvTab = TPAPI.UniverseTable(self.versionID,self.universeExtension,row[0])
                    unvTab._getPropertiesFromServer(server)
                    self.universeTableObjects[row[0]] = unvTab
                    
                # Tables in 'ALL' universes
                crsr.execute("SELECT TABLENAME FROM dwhrep.UniverseTable where versionid =? and universeExtension like ?",(self.versionID,'ALL%',))
                resultset = crsr.fetchall()
                for row in resultset:
                    unvTab = TPAPI.UniverseTable(self.versionID,'ALL',row[0])
                    unvTab._getPropertiesFromServer(server)
                    self.universeTableObjects[row[0]] = unvTab

        return
    
    def _getUniverseClasses(self,server):
        with TPAPI.DbAccess(server,'dwhrep') as crsr:
            crsr.execute("SELECT CLASSNAME FROM dwhrep._UniverseClass where versionid =? and universeExtension like ?",(self.versionID,self.universeExtension+'%',))
            resultset = crsr.fetchall()
            for row in resultset:
                unvClass = TPAPI.UniverseClass(self.versionID,self.universeExtension,row[0])
                self.universeClassObjects[row[0]] = unvClass
                self.universeClassObjects[row[0]]._getPropertiesFromServer(server)
            crsr.execute("SELECT CLASSNAME FROM dwhrep._UniverseClass where versionid =? and universeExtension like ?",(self.versionID,'ALL%',))    
            resultset = crsr.fetchall()
            for row in resultset:
                unvClass = TPAPI.UniverseClass(self.versionID,'ALL',row[0])
                self.universeClassObjects[row[0]] = unvClass
                self.universeClassObjects[row[0]]._getPropertiesFromServer(server)
        
        pass
    
    
    def _getUniverseJoins(self,server):
        with TPAPI.DbAccess(server,'dwhrep') as crsr:
            crsr.execute("SELECT SOURCECOLUMN,SOURCETABLE,TARGETCOLUMN,TARGETTABLE,TMPCOUNTER FROM dwhrep.UniverseJoin where versionid =? and universeExtension like ?",(self.versionID,self.universeExtension+'%',))
            resultset = crsr.fetchall()
            for row in resultset:
                unvJoin = TPAPI.UniverseJoin(self.versionID,self.universeExtension,row[0])
                self.universeClassObjects[row[0]] = unvJoin
                self.universeClassObjects[row[0]]._getPropertiesFromServer(server)
            crsr.execute("SELECT CLASSNAME FROM dwhrep._UniverseClass where versionid =? and universeExtension like ?",(self.versionID,'ALL%',))    
            resultset = crsr.fetchall()
            for row in resultset:
                unvClass = TPAPI.UniverseClass(self.versionID,'ALL',row[0])
                self.universeClassObjects[row[0]] = unvClass
                self.universeClassObjects[row[0]]._getPropertiesFromServer(server)
                
#SOURCECOLUMN
#SOURCETABLE
#TARGETCOLUMN
#TARGETTABLE
#TMPCOUNTER
#VERSIONID
        
        pass
    
    def _getPropertiesFromXML(self):
        pass
        
    def _toXML(self,offset=0):

            #self.logger.debug(self.versionID + ":" +self.name + "._toXML()")
            offset += 4
            offsetStr = "\n" + " "*offset
            outputXML = offsetStr
            outputXML +='<Universe name="'+self.universeName+ '" universeExtension="'+str(self.universeExtension) + '" universeExtensionName ="'+str(self.universeExtensionName)  +'">'+offsetStr
            for unvClass in self.universeClassObjects:
                outputXML += self.universeClassObjects[unvClass]._toXML()
            for unvTable in self.universeTableObjects:
                outputXML += self.universeTableObjects[unvTable]._toXML()
            outputXML +='</Universe>'
            return outputXML
        
    def _difference(self):
        pass
    
    
class _UniverseClass(object):
            
    def __init__(self,versionID,universeExtension,universeClassName):
        
        
        self.versionID = versionID
        self.universeClassName = universeClassName
        self.universeExtension = universeExtension
        self.properties = {}
        self.universeObjObjects = {}
        self.universeConditionObjects = {}
#        
#        print "universe class created for extenstion = " + self.universeExtension
#        print "universe classname = " + self.universeClassName
#        print "universe class created for versionID= " + self.versionID
        return
    
    def _toXML(self,offset=0):

        #self.logger.debug(self.versionID + ":" +self.name + "._toXML()")
        offset += 4
        offsetStr = "\n" + " "*offset
        outputXML = offsetStr
        outputXML +='<_UniverseClass name="'+self.universeClassName  +'">'+offsetStr
        for prop in self.properties:
            outputXML +=    '    <Property key="'+str(prop)+'" val="'+TPAPI.escape(self.properties[prop])+'"/>'+offsetStr
        for unvObj in self.universeObjObjects:
            #outputXML +=    '    <Universe Class name="'+unvClass+'"/>'+offsetStr
            outputXML += self.universeObjObjects[unvObj]._toXML()
        for unvCondition in self.universeConditionObjects:
            outputXML += self.universeConditionObjects[unvCondition]._toXML()
        outputXML +='</_UniverseClass>'
        return outputXML
            
    def _getPropertiesFromXML(self):
        '''Populates the objects content from an xmlElement
        
        The method is also responsible for triggering its child objects getPropertiesFromXML() method
        '''
        return
                
    def _getPropertiesFromServer(self,server):
        with TPAPI.DbAccess(server,'dwhrep') as crsr:
            crsr.execute("SELECT DESCRIPTION,PARENT,OBJ_BH_REL,ELEM_BH_REL,INHERITANCE,ORDERNRO FROM dwhrep._UniverseClass where VERSIONID =? and universeExtension=? and CLASSNAME=?",(self.versionID,self.universeExtension,self.universeClassName))
            row = crsr.fetchone()
            desc = crsr.description
            if row is not None:
                i = 0
                for x in desc:
                    self.properties[x[0]] = row[i]
                    i+=1
        self._getUniverseObjects(server)
        self._getUniverseConditions(server)
        
    def _getUniverseObjects(self,server):
        with TPAPI.DbAccess(server,'dwhrep') as crsr:
            crsr.execute("SELECT OBJECTNAME FROM dwhrep.UniverseObject where versionid =? and universeExtension=? and CLASSNAME=?",(self.versionID,self.universeExtension,self.universeClassName))
            resultset = crsr.fetchall()
            for row in resultset:
                unvObj = TPAPI.UniverseObject(self.versionID,self.universeExtension,self.universeClassName,row[0])
                self.universeObjObjects[row[0]] = unvObj
                self.universeObjObjects[row[0]]._getPropertiesFromServer(server)
        return
    
    def _getUniverseConditions(self,server):
        with TPAPI.DbAccess(server,'dwhrep') as crsr:
            crsr.execute("SELECT UNIVERSECONDITION FROM dwhrep.UniverseCondition where versionid =? and universeExtension=? and CLASSNAME=?",(self.versionID,self.universeExtension,self.universeClassName))
            resultset = crsr.fetchall()
            for row in resultset:
                unvCondition = TPAPI.UniverseCondition(self.versionID,self.universeExtension,self.universeClassName,row[0])
                self.universeConditionObjects[row[0]] = unvCondition 
                self.universeConditionObjects[row[0]]._getPropertiesFromServer(server)
        return
    

    
class UniverseObject(object):
            
    def __init__(self,versionID,universeExtension,universeClassName,universeObjectName):
        self.versionID = versionID
        self.universeClassName = universeClassName
        self.universeExtension = universeExtension
        self.universeObjectName = universeObjectName
        #print "self.universeObjectName "+self.universeObjectName
        self.properties = {}
        #self.universeObjects = {}
        return
    
    def _toXML(self,offset=0):

        #self.logger.debug(self.versionID + ":" +self.name + "._toXML()")
        offset += 4
        offsetStr = "\n" + " "*offset
        outputXML = offsetStr
        outputXML +='<UniverseObject name="'+self.universeObjectName  +'">'+offsetStr
        for prop in self.properties:
            outputXML +=    '    <Property key="'+str(prop)+'" val="'+TPAPI.escape(self.properties[prop])+'"/>'+offsetStr
        outputXML +='</UniverseObject>'
        return outputXML  
    
    def _getPropertiesFromServer(self,server):
        with TPAPI.DbAccess(server,'dwhrep') as crsr:
            crsr.execute("SELECT DESCRIPTION,OBJECTTYPE,QUALIFICATION,AGGREGATION,OBJSELECT,OBJWHERE,PROMPTHIERARCHY,OBJ_BH_REL,ELEM_BH_REL,INHERITANCE,ORDERNRO FROM dwhrep.UniverseObject where versionid =? and universeExtension=? and CLASSNAME=? AND OBJECTNAME =? ",(self.versionID,self.universeExtension,self.universeClassName,self.universeObjectName))
            row = crsr.fetchone()
            desc = crsr.description
            #sprint "row[0] " + str(row[0])
            if row is not None:
                i = 0
                for x in desc:
                    self.properties[x[0]] = row[i]
                    i+=1
            return
        
class UniverseTable(object):
    
    
    def __init__(self,versionID,universeExtension,tableName):
        self.versionID = versionID
        self.universeExtension = universeExtension
        self.parentTableName = tableName
        self.properties = {}
        
        return
        
    def _toXML(self,offset=0):
        offset += 4
        offsetStr = "\n" + " "*offset
        outputXML = offsetStr
        outputXML +='<UniverseTable name="'+self.parentTableName  +'">'+offsetStr
        for prop in self.properties:
            outputXML +=    '    <Property key="'+str(prop)+'" val="'+TPAPI.escape(self.properties[prop])+'"/>'+offsetStr
        outputXML +='</UniverseTable>'
        return outputXML 
    
    def _getPropertiesFromServer(self,server):
#        print "universe table _getPropertiesFromServer"
#        print self.versionID
#        print self.universeExtension 
#        print self.parentTableName
        with TPAPI.DbAccess(server,'dwhrep') as crsr:
            crsr.execute("SELECT OWNER,ALIAS,OBJ_BH_REL,ELEM_BH_REL,INHERITANCE,ORDERNRO FROM dwhrep.UniverseTable where versionid =? and universeExtension=? and parentTableName=?",(self.versionID,self.universeExtension,self.parentTableName,))
            row = crsr.fetchone()
            desc = crsr.description
            if row is not None:
                i = 0
                for x in desc:
                    print "in table properties" + str(row[i])
                    self.properties[x[0]] = row[i]
                    i+=1
        return
    
    def _getPropertiesFromXML(self):
        return
    
    def _difference(self):
        return
    
class UniverseJoin(object):
    
#VERSIONID
#SOURCETABLE
#SOURCELEVEL
#SOURCECOLUMN
#TARGETTABLE
#TARGETLEVEL
#TARGETCOLUMN
#EXPRESSION
#CARDINALITY
#CONTEXT
#EXCLUDEDCONTEXTS
#TMPCOUNTER
#ORDERNRO
#UNIVERSEEXTENSION

# primary keys
#SOURCECOLUMN
#SOURCETABLE
#TARGETCOLUMN
#TARGETTABLE
#TMPCOUNTER
#VERSIONID

    def __init__(self,versionID,sourceColumn,sourceTable,targetColumn,targetTable,tmpCounter):
        
        self.versionID = versionID
        self.sourceColumn = sourceColumn
        self.sourceTable = sourceTable
        self.targetColumn = targetColumn
        self.targetTable = targetTable
        self.tmpCounter = tmpCounter # is this needed?
        self.properties = {}
        return
        
    def _toXML(self,offset=0):
        offset += 4
        offsetStr = "\n" + " "*offset
        outputXML = offsetStr
        outputXML +='<UniverseJoin name="">'+offsetStr
        for prop in self.properties:
            outputXML +=    '    <Property key="'+str(prop)+'" val="'+TPAPI.escape(self.properties[prop])+'"/>'+offsetStr
        outputXML +='</UniverseJoin>'
        return outputXML 
    
    
    def _getPropertiesFromServer(self,server):    
        with TPAPI.DbAccess(server,'dwhrep') as crsr:
            crsr.execute("SELECT SOURCELEVEL,TARGETLEVEL,TARGETLEVEL,EXPRESSION,CARDINALITY,CONTEXT,EXCLUDEDCONTEXTS FROM dwhrep.UniverseJoin where versionid =? and sourceColumn=? and sourceTable=? and targetColumn=? and targettable=?",(self.versionID,self.sourceColumn,self.sourceTable,self.targetColumn,self.targettable))
            row = crsr.fetchone()
            desc = crsr.description
            if row is not None:
                i = 0
                for x in desc:
                    self.properties[x[0]] = row[i]
                    i+=1
        return
    
    def _getPropertiesFromXML(self):
        return
    
    def _difference(self):
        return
    
    
    
    
    
class UniverseCondition(object):
    

    def __init__(self,versionID,universeExtension,universeClassName,universeConditionName):
        self.versionID = versionID
        self.universeExtension  = universeExtension
        self.universeClassName = universeClassName
        self.universeConditionName = universeConditionName
        self.properties = {}
        return
        
    def _toXML(self,offset=0):
        offset += 4
        offsetStr = "\n" + " "*offset
        outputXML = offsetStr
        outputXML +='<UniverseCondition name="'+self.universeConditionName  +'">'+offsetStr
        for prop in self.properties:
            outputXML +=    '    <Property key="'+str(prop)+'" val="'+TPAPI.escape(self.properties[prop])+'"/>'+offsetStr
        outputXML +='</UniverseCondition>'
        return outputXML 
    
    def _getPropertiesFromServer(self,server):
#        print "in get properties from server"
#        print "self.universeExtension  = " + self.universeExtension
#        print "self.universeClassName  = " + self.universeClassName
#        print "self.universeConditionName  = " + self.universeConditionName
        with TPAPI.DbAccess(server,'dwhrep') as crsr:
            crsr.execute("SELECT DESCRIPTION,CONDWHERE,AUTOGENERATE,CONDOBJCLASS,CONDOBJECT,PROMPTTEXT,MULTISELECTION,FREETEXT,OBJ_BH_REL,ELEM_BH_REL,INHERITANCE,ORDERNRO FROM dwhrep.UniverseCondition where versionid =? and universeextension=? and classname=? and universecondition=? ",(self.versionID,self.universeExtension,self.universeClassName,self.universeConditionName,))
            row = crsr.fetchone()
            desc = crsr.description
            if row is not None:
                i = 0
                for x in desc:
                    self.properties[x[0]] = row[i]
                    i+=1
        return
    
    def _getPropertiesFromXML(self):
        return
    
    def _difference(self):
        return
        
