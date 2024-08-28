''' TPAPI Functions'''
from __future__ import with_statement
import subprocess
import TPAPI
from xml.etree import ElementTree
import os
import zipfile
import zlib
import shutil
import re
import csv 
import pickle
import itertools
import logging
import warnings
logger = logging.getLogger('TPAPI.TPAPI_TP.TechPackVersion')

DTD = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE Techpack
  [     <!ELEMENT Techpack (Versioning*)>
    <!ELEMENT Versioning (VersionInfo*,SupportedVendorReleases*,Tables*, BusyHours*, ExternalStatements*, Interfaces*)>
        <!ATTLIST Versioning name CDATA #REQUIRED >
    <!ELEMENT VersionInfo ANY>
    <!ELEMENT SupportedVendorReleases (VendorRelease*) >
    <!ELEMENT VendorRelease (#PCDATA) >
    <!ELEMENT Tables (Table*) >
    <!ELEMENT Table ANY >
        <!ATTLIST Table name CDATA #REQUIRED >
        <!ATTLIST Table tableType CDATA #REQUIRED >
        <!ATTLIST Table classification CDATA #REQUIRED >
    <!ELEMENT Attributes (Attribute*) >
    <!ELEMENT Attribute ANY>
        <!ATTLIST Attribute name CDATA #REQUIRED >
        <!ATTLIST Attribute attributeType CDATA #REQUIRED >
    <!ELEMENT Parsers (Parser*) >
    <!ELEMENT Parser (Transformations*,Dataformats*) >
        <!ATTLIST Parser type CDATA #REQUIRED >
    <!ELEMENT Transformations (OrderNo*) >
        <!ATTLIST Transformations transformerID CDATA #REQUIRED >
    <!ELEMENT OrderNo ANY>
        <!ATTLIST OrderNo index CDATA #REQUIRED >
    <!ELEMENT Dataformats (Dataformat*) >
    <!ELEMENT Dataformat (TableTags*,AttributeTags*) >
        <!ATTLIST Dataformat DataFormatID CDATA #REQUIRED >
    <!ELEMENT TableTags (TableTag*) >
    <!ELEMENT TableTag (#PCDATA) >
    <!ELEMENT AttributeTags ANY>
    <!ELEMENT BusyHours (BusyHour*)>
    <!ELEMENT BusyHour (BusyHourObjectName, RankingTable, BusyHourSupportedTables, BusyHourTypes*)>
    <!ELEMENT BusyHourObjectName (#PCDATA) >
    <!ELEMENT RankingTable (#PCDATA)>
    <!ELEMENT BusyHourSupportTables (BusyHourSupportTable*)>
    <!ELEMENT BusyHourSupportTable (#PCDATA)>
    <!ELEMENT BusyHourTypes (BusyHourType*)>
    <!ELEMENT BusyHourType ANY>
        <!ATTLIST BusyHourType name CDATA #REQUIRED>
    <!ELEMENT GroupTypes (GroupType*) >
    <!ELEMENT GroupType (Dataname*)>
        <!ATTLIST GroupType name CDATA #REQUIRED>
    <!ELEMENT Dataname (Property*)>
        <!ATTLIST Dataname name CDATA #REQUIRED>
    <!ELEMENT ExternalStatements (ExternalStatement*) >
    <!ELEMENT ExternalStatement ANY >
        <!ATTLIST ExternalStatement name CDATA #REQUIRED >
    <!ELEMENT MetaCollectionSets (MetaCollectionSet*) >
    <!ELEMENT MetaCollectionSet (ANY, MetaCollections) >
        <!ATTLIST MetaCollectionSet CollectionSetName CDATA #REQUIRED >
        <!ATTLIST MetaCollectionSet CollectionSetID CDATA #REQUIRED >
    <!ELEMENT MetaCollections (ANY, MetaTransferActions) >
        <!ATTLIST MetaCollections collectionName CDATA #REQUIRED >
    <!ELEMENT MetaTransferActions ANY>
        <!ATTLIST MetaTransferActions transferActionName CDATA #REQUIRED >
    <!ELEMENT Interfaces (Interface*) >
    <!ELEMENT Interface (IntfVersioning*,Dependencies*,Techpacks*,Configuration*)>
        <!ATTLIST Interface name CDATA #REQUIRED >
    <!ELEMENT IntfVersioning ANY >
        <!ATTLIST IntfVersioning intfVersion CDATA #REQUIRED >
    <!ELEMENT Dependencies ANY>
    <!ELEMENT Techpacks ANY>
    <!ELEMENT Configuration ANY>
  ]>
'''

def unzipTpi(tpiFile,outDir):
    '''Unzips a tpi (tpiFile) file to the specified output directory. Function
    
    tpiFile: tpiFile to be extracted
    outDir: Output directory destination
    
   Exceptions:
            Raised if the file does not end with .tpi
            Raised if its not a valid zipfFile'''
    
    logger.debug("TPAPI.unzipTpi() on file" +tpiFile)
    extractDirName = tpiFile.split('.')[0]
    if os.path.splitext(tpiFile)[1] != '.tpi':
        strg = "TPAPI.unzipTpi() file " +tpiFile + " : is not a .tpi file.. exiting"
        logger.debug(strg)
        raise Exception(strg)
    if not zipfile.is_zipfile(tpiFile):
        strg()
        logger.debug("TPAPI.unzipTpi() file " +tpiFile + " is not a valid zip file..exiting")
        logger.debug(strg)
        raise Exception(strg)
    tmp_file = tpiFile.replace('.tpi','.zip')
    shutil.copyfile(tpiFile , os.path.join(os.path.dirname(tpiFile),tmp_file) )
    currDir = os.getcwd()
    src = open( tmp_file, "rb" )
    
    zf = zipfile.ZipFile( src )
    for entry in zf.namelist():
        (relativeDir, fileName) = os.path.split(entry)
        fullPath = os.path.join(currDir, relativeDir)
        if not os.path.exists(fullPath):
            os.makedirs(fullPath)
    for m in  zf.infolist():
        # Examine the header
        #print m.filename, m.header_offset, m.compress_size, repr(m.extra), repr(m.comment)
        src.seek( m.header_offset )
        src.read( 30 ) # 
        nm= src.read( len(m.filename) )
        if len(m.extra) > 0: ex= src.read( len(m.extra) )
        if len(m.comment) > 0: cm= src.read( len(m.comment) )
        decomp= zlib.decompressobj(-15)
        tempDir = m.filename.split('/')
        fullOutputDir = os.path.join(os.getcwd(),outDir,extractDirName)
        #creates a dir with the same name as the tpi filename
        if not os.path.exists(fullOutputDir):
            os.makedirs(fullOutputDir)
        # create the sub directories s under the tpi filename dir   
        if not os.path.exists(os.path.join(fullOutputDir,tempDir[0])):
            os.makedirs(os.path.join(fullOutputDir,tempDir[0]))
        fullOutputFileName = os.path.join(fullOutputDir,m.filename,)  
        out= open(fullOutputFileName, "wb" )
        result= decomp.decompress( src.read( m.compress_size ) )
        out.write( result )
        result = decomp.flush()
        out.write( result )
        out.close()
    
    zf.close()
    src.close()  
    
    
#def createDictFromTPI(sqlFileObject): 
#    '''Creates a tpiDict'''
#    tpidict = {}    
#    lines = sqlFileObject.readlines()
#    for line in lines:
#        matchObj = re.match('insert into\s(.+?)\s\(?.+? ',line)
#        if matchObj:
#            tableName = matchObj.group(1) 
#            if tableName not in tpidict:
#                tpidict[tableName] = {}
#            columns = line[line.find('(')+1:line.find(')')].split(',')
#            values = line[line.find('(',line.index(')'))+1:line.rfind(')')].split(',')
#            tpidict[tableName][len(tpidict[tableName])+1] = {}
#            for col,val in zip(columns,values):
#                tpidict[tableName][len(tpidict[tableName])][col.strip()] = val.strip().strip("'")
#                
#    return tpidict

import java.lang.Runtime as RT




def printMem():
    '''Prints System Memory'''
    rt = RT.getRuntime()
    mb = 1024*1024
    free = rt.freeMemory() / mb
    tot = rt.totalMemory() / mb
    print "Free Memory:" + str(free) + "Mb"
    print "Used Memory:" + str((tot - free)) + "Mb"
    print "Total Memory:" + str(tot) + "Mb"

def printRow(resultset):
    ''' Print a row'''
    for row in resultset:
        numofcols = len(row)
        while numofcols > 0: 
            print row[numofcols-1] + " |" ,
            numofcols-= 1
        print "\n",

def printColumnNames(desc):
    '''Print column Names for the result'''
    for x in desc:
        print x[0]
        
def dictToSQL(mydict,tablename):
    '''Prepare SQL from a dict'''
    # one row!
    dictCopy = mydict
    for k,v in dictCopy.items():
        if v is None:
            del dictCopy[k] 
        sql = 'INSERT INTO dwhrep.' +tablename
        sql += ' ('
        sql += ', '.join(dictCopy)
        sql += ') VALUES ('
        sql += ','.join(map(pad,dictCopy))
        sql += ');'
        values = dictCopy.values()
    return sql,values

def pad(key):
    '''Used during sql updates'''
    return '?'

def rowToDictionary(row, desc):
    '''Conver a row to a dictionary'''
    mydict = {}
    i = 0
    for x in desc:
        mydict[x[0]] = row[i]
        i+=1
    return mydict
                             
def rowToList(resultset):
    '''Convert single column resultset to a list'''
    mylist = []
    for i in resultset:
        mylist.append(i[0],)
    return mylist     

def printDict(dictionary):    
    '''Print Dictionary'''
    for i in dictionary:
        print i +  "=" + str(dictionary[i])
        
def compareRStates(rstate1,rstate2):
    '''Compare two rstates 
        
        returns -1 if rtate1 is newer than rstate2, 0 if they are equal and 1 if rstate is older than rstate2'''
    if rstate1[0] == 'R' and rstate2[0] == 'R':
        if rstate1[1:-1].isdigit and rstate2[1:-1].isdigit:
            digit1 = rstate1[1:-1]
            digit2 = rstate2[1:-1]
            if int(digit1) > int(digit2):
                return -1
            elif int(digit1) == int(digit2):
                if rstate1[-1].isalpha and rstate2[-1].isalpha:
                    alpha1 = rstate1[-1]
                    alpha2 = rstate2[-1]
                    if alpha1 > alpha2:
                        return -1
                    elif alpha1 == alpha2:
                        return 0
                    else:
                        return 1
            else:
                return 1

def pingServer(addr):
    '''Returns a True or False value if the server is pingable'''
    return_code = True
    if os._name == "nt":  # running on windows
        cmd = "ping -n 1 %s" % addr
    else: 
        cmd = "/usr/sbin/ping %s" % addr
    try:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        retcode = p.wait()
        if retcode == 1:
            return_code = False
        else:
            return_code = True
    except subprocess.CalledProcessError:
        return_code = False
    return return_code

def safeNull(elementText):
    '''Converts a None type object to an empty string.Used by FromXML methods for handling element tags with empty
    values'''
    if elementText == None:
        elementText = ''
        return elementText
    else:
        return elementText    
    
def strFloatToInt(value):
    '''Converts string float to string int'''
    value = value.replace(".0", "")
    return value

def checkNull(inputStr):
    '''Check if string is null'''
    if inputStr == 'null':
        return 'None'
    else:
        return inputStr
    
def fileToXMLObject(xmlfile):
    '''Convert File to XML Object'''
    xmlString = xmlfile.read()
    xmlObject = ElementTree.fromstring(xmlString)
    return xmlObject
    
def escape(text):
    '''return text that is safe to use in an XML string'''
    html_escape_table = {
        "&": "&amp;",
        '"': "&quot;",
        ">": "&gt;",
        "<": "&lt;",
    }   
    return "".join(html_escape_table.get(c,c) for c in str(text))

def unescape(s):
    '''change XML string to text'''
    s = s.replace("&lt;", "<")
    s = s.replace("&gt;", ">")
    s = s.replace("&apos;", "'")
    s = s.replace("&quot;", '"')
    s = s.replace("&amp;", "&")
    return s    

def pickleTechpack(VersionID,server):
    '''Function to convert techpack to python bytestream. For Faster testing - No need to load from tpi or server'''
    tpv = TPAPI.TechPackVersion(VersionID)
    tpv.getPropertiesFromServer(server)
    myPickle = pickle()
    myPickle.dump(tpv, file.open('testpickle',"w"))
    
def getTechpackDwhInfo(server,VersionID):
    ''' Retrieves DWH info of tech pack
    
        Returns: A Dictionary structure of all tables and  columns
    
    '''
    with TPAPI.DbAccess(server,'dwhrep') as crsr:
        temp = "%"+VersionID+"%"
        tables = []
        tpDwhInfo = {}
        crsr.execute("SELECT BASETABLENAME FROM dwhrep.MeasurementTable WHERE MTABLEID like ?", (temp,))
        resultset = crsr.fetchall()
        for row in resultset:
            tables.append(str(row[0]))
        for table in tables:
            tablename = VersionID + ":"+str(table) 
            crsr.execute("SELECT DATANAME FROM dwhrep.MeasurementColumn WHERE MTABLEID like ?",(str(tablename),))
            resultset = crsr.fetchall()
            i = 0
            columns = []
            for row in resultset:
                columns.append(str(row[0]))
                i =i+1
            tpDwhInfo[str(table)] = columns
    return tpDwhInfo   
    
   
def writeXMLFile(toXMLString,filename):
    '''Writes an XMLString to a file'''
    fh = open(filename,"w")
    offset = 0
    os = "\n" + " "*offset
    os2 = os + " "*offset
    fh.writelines(DTD)
    fh.writelines(toXMLString)
    fh.close()
    return

def getTechPacks(server):
    '''Get list of all techpacks on a server.
    
    Returns:
            List of Techpacks on the server
    
    '''
    techpacks=[]
    db = TPAPI.DbAccess(server, "dwhrep")
    try:
        crsr = db.getCursor() 
        crsr.execute("SELECT DISTINCT TECHPACK_NAME FROM dwhrep.Versioning")
        for i in crsr.fetchall():
            techpacks.append(i[0])
    finally:
        del db 
    return techpacks

def getTechPackVersions(server):
    '''get list of all techpacks on a server.
    
    Returns:
            Dictionary of tchpack versions on the server
    '''
    techpackVersions ={}
    db = TPAPI.DbAccess(server, "dwhrep")
    try:
        crsr = db.getCursor() 
        crsr.execute("SELECT VERSIONID,TECHPACK_NAME,TECHPACK_VERSION FROM dwhrep.Versioning ORDER BY VERSIONID")
        for i in crsr.fetchall():
            techpackVersions[i[0]]=(i[1],i[2])
    finally:
        del db 
    return techpackVersions

def getInterfaces(server):
    '''get list of all interfaces on the server'''
    '''Columns:INTERFACENAME,STATUS,INTERFACETYPE,DESCRIPTION,DATAFORMATTYPE,INTERFACEVERSION,LOCKEDBY,LOCKDATE,PRODUCTNUMBER,ENIQ_LEVEL,RSTATE'''
    interfaces=[]
    db = TPAPI.DbAccess(server, "dwhrep")
    try:
        crsr = db.getCursor() 
        crsr.execute("SELECT INTERFACENAME,INTERFACEVERSION,DATAFORMATTYPE,RSTATE FROM dwhrep.DataInterface")
        c = 0
        for res in crsr.fetchall():
            interfaces.append([])
            interfaces[c].append(res[0])
            interfaces[c].append(res[1])
            interfaces[c].append(res[2])
            interfaces[c].append(res[3])
            c+=1 
    finally:
        del db
    return interfaces

def getRepositoryInfo(server):
        '''return a nested dictionary of the dwhrep structure, containing tables,column and column parameters'''
        dwhrepDict = {}
        db = TPAPI.DbAccess(server, "DBA")
        try:
            crsr = db.getCursor()
            crsr.execute("SELECT table_name FROM sys.systable where creator=104")
            resultset = crsr.fetchall()
            for row in resultset:
                tableName = row[0].rstrip()
                dwhrepDict[tableName] = {}
                crsr.execute("select CNAME,coltype,length,nulls,default_value from sys.syscolumns where TNAME =?",(tableName,))
                rset2 = crsr.fetchall()
                for column in rset2:
                    dwhrepDict [tableName][column[0]] = {'coltype':column[1],'lenght':column[2],'nulls':column[3],'default_value':column[4]}
        finally:
                del db 
        return  dwhrepDict 

def compareRepositories(dwhrepDict1,dwhrepDict2):
        '''Compare Tables & Keys and properties of two dwhreps'''
        additionalTables = {}
        modifiedTables = {}
        if len(dwhrepDict1) > len(dwhrepDict2):
            print "extra tables found in first rep"
            for table in dwhrepDict1:
                if table not in dwhrepDict2:
                    print "extra table is " + table
                    additionalTables[table] = {}
                if table in dwhrepDict2:
                    if len(dwhrepDict1[table]) > len(dwhrepDict2[table]):
                        print "extra columns found in " + table
                        modifiedTables[table] = {}
                    else:
                        pass
        print "                                    "
        print "New Tables"
        print "                                    "    
        for addTable in additionalTables:
            print "NEW TABLE: " + addTable
            print "****************************"
            for column in dwhrepDict1[addTable]:
                print str(column)
            print "*****************************" 
        print "                                    "
        print "New Columns in Existing Tables"
        print "                                    "         
        for modTable in modifiedTables:
            print "*****************************"
            print modTable
            for column in dwhrepDict1[modTable]:
                if column not in dwhrepDict2[modTable]:
                    print "NEW COLUMN :" + str(column) 
            print "*****************************"

def generate_dicts(cur):    
    ''' easy access to data by column name
        example usage:
            versionID = 'DC_E_BSS:((66))'
            with TPAPI.DbAccess(server,'dwhrep') as crsr:
                crsr.execute("SELECT * from dwhrep.Versioning WHERE VERSIONID =?", (versionID,))
                for row in TPAPI.generate_dicts(crsr):
                    print row['TECHPACK_NAME'], row['TECHPACK_VERSION'], row['DESCRIPTION'] 
    '''
    column_names = [d[0].upper() for d in cur.description ]
    while True:
        rows = cur.fetchall()
        if not rows:
            return 
        for row in rows:
            yield dict(itertools.izip(column_names, row))
            
import warnings

def deprecated(func):
    """This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emmitted
    when the function is used."""
    def newFunc(*args, **kwargs):
        warnings.warn("Call to deprecated function %s." % func.__name__,
                      category=DeprecationWarning)
        return func(*args, **kwargs)
    newFunc.__name__ = func.__name__
    newFunc.__doc__ = func.__doc__
    newFunc.__dict__.update(func.__dict__)
    return newFunc

class DictDiffer(object):
    """
    Class for calculating the difference between two dictionaries.
    
    """
    def __init__(self, current_dict, past_dict):
        '''Initialised with the two dictionary objects to be compared'''
        self.current_dict, self.past_dict = current_dict, past_dict
        self.set_current, self.set_past = set(current_dict.keys()), set(past_dict.keys())
        self.intersect = self.set_current.intersection(self.set_past)
    def added(self):
        '''Returns:
                Dictionary of added items'''
        return self.set_current - self.intersect 
    def removed(self):
        '''Returns:
                Dictionary of removed items'''
        return self.set_past - self.intersect 
    def changed(self):
        '''Returns:
                Dictionary of changed items'''
        return set(o for o in self.intersect if self.past_dict[o] != self.current_dict[o])
    def unchanged(self):
        '''Returns:
                Dictionary of unchanged items'''
        return set(o for o in self.intersect if self.past_dict[o] == self.current_dict[o])
    
class TpiDict(object):
    '''Class for extraction and intermediate storage of metadata from inside a tpi file.'''
    
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(TpiDict, cls).__new__(
                                cls, *args, **kwargs)
        return cls._instance    
    
    def __init__(self,filename=None,directory=None):
        self.logger = logging.getLogger('TPAPI.TPAPI_Util.tpiDict()')
        if filename == None and directory == None:
            self.logger.error('TPAPI.TPAPI_Util.tpiDict() error no filename or directory specified..exiting')
            return
        self.tpidict = {}
        tpis = [] 
        extractedDirs = [] 
        self.filename = filename
        self.directory = directory
        if filename is not None:
            if os.path.exists(filename):
                self.logger.debug('TPAPI.TPAPI_Util.tpiDict() file ' + filename + 'exists')
                fileName = os.path.basename(filename)
                directoryName = os.path.dirname(filename)
                if directoryName != '':
                    absInputDir = os.path.abspath(directoryName)
                else:
                    # No path found, use current directory
                    absInputDir = os.path.abspath(os.path.dirname(os.getcwd()))
                filePath = os.path.join(absInputDir,fileName)
                unzipDest = os.path.join(absInputDir,'tmp')
                self.logger.info('TPAPI.TPAPI_Util.tpiDict() unzipping  ' + filePath)
                TPAPI.unzipTpi(filePath,unzipDest)
                extractedDirs.append(filePath.split('.')[0])                     
        elif directory is not None:
            if os.path.isdir(directory):
                absInputDir = os.path.abspath(directory)
                for myfile in os.listdir(absInputDir):
                    if myfile.endswith(".tpi"):
                        tpiFile = os.path.join(absInputDir,myfile)
                        destDir = os.path.join(absInputDir,'/tmp')
                        TPAPI.unzipTpi(tpiFile,destDir)
                        tpis.append(myfile)
                        print "....> " + myfile.split('.')[0]
                        extractedDirs.append(myfile.split('.')[0])
        for dir in extractedDirs:
            if os.path.exists(os.path.join(absInputDir,dir)):
                # Dirs contained in  the tpi file
                for dir2 in os.listdir(os.path.join(absInputDir,dir)):
                    for fileName in os.listdir(os.path.join(absInputDir,dir,dir2)):
                        if fileName.find('Tech_Pack') == 0:    
                            if re.match('.*(\.sql)',fileName):
                                interfaceSql = False
                                if fileName.find('Tech_Pack_INTF') == 0:
                                    interfaceSql = True
                                path = os.getcwd()
                                sqlFile = open(os.path.join(absInputDir,dir,dir2,fileName))
                                lines = sqlFile.readlines()
                                count=0
                                testString = ''
                                string = ''
                                completelines=[]
                                while count <= len(lines)-1:
                                    if interfaceSql:
                                        testString = lines[count]
                                        if len(testString) > 2 and not testString.startswith('--'):
                                            string = string + lines[count]
                                            if re.match('.*\)(\r)?', string):
                                                completelines.append(string)
                                                string = ''
                                    else:
                                        string = string + lines[count]
                                        if string[:-1].endswith(');'):
                                            completelines.append(string)
                                            string = ''     
                                    count = count +1        
                                for line in completelines:
                                    matchObj = re.match('insert into\s(.+?)[\s|\(]\(?.+? ',line)
                                    tableName = matchObj.group(1) 
                                    if tableName not in self.tpidict:
                                        self.tpidict[tableName] = {}                       
                                    columns = line[line.find('(')+1:line.find(')')].split(',')
                                    if interfaceSql :
                                        vals = line[line.find('(',line.index(')'))+1:-2]
                                    else:
                                        vals = line[line.find('(',line.index(')'))+1:-3]
                                    p=[]
                                    p.append(vals)
                                    testReader = csv.reader(p,quotechar="'", skipinitialspace=True)
                                    for row in testReader:   
                                        for col,val in zip(columns,row):
                                            col = col.strip()
                                            val = val.strip().strip("'")
                                            val = val.rstrip('\\')                 
                                            if col not in self.tpidict[tableName]:
                                                self.tpidict[tableName][col] = {}
                                            self.tpidict[tableName][col][len(self.tpidict[tableName][col])+1 ] =  val                            
                                self.printDict()                      
                            elif re.match('.*(\.xml)',fileName):
                                xmlFile = open(os.path.join(absInputDir,dir,dir2,fileName),"rb")
                                for line in xmlFile:
                                    # escape commas found in the description field
                                    line = re.sub("'.+\s,'.+(,).+'\s,.+'",' &comma ',line)
                                    matchObj = re.search('.+<(.+?)\s.+?',line)
                                    if matchObj:
                                        tableName = matchObj.group(1)
                                        if tableName not in self.tpidict:
                                            self.tpidict[tableName] = {}
                                        matchObj1 = re.search('.+<.+?\s(.+?)/>',line)
                                        if matchObj1:
                                            kevals = matchObj1.group(1)
                                        mysplit = re.split('"\s', kevals)
                                        for entry in mysplit:
                                            # Where clause can have multiple equals signs which mess up the splitting of the string
                                            s = re.split('="',entry)
                                            if len(s) > 1:
                                                column =  s[0]
                                                value = s[1].strip('"')
                                            if column not in self.tpidict[tableName]:
                                                self.tpidict[tableName][column] = {}    
                                            self.tpidict[tableName][column][len(self.tpidict[tableName][column])+1 ] =  value 
                                xmlFile.close()
               
    def printDict(self):
        f = open('tpiDict.txt', 'w')
        for table in self.tpidict:
            f.write("table is " + table +"\n")
            for column in self.tpidict[table]:
                f.write("column is " + column+"\n")
                for row in self.tpidict[table][column]:
                    f.write("row is " + str(row)+"\n")
                    f.write("value is " +self.tpidict[table][column][row]+"\n")

    def returnTPIDict(self):
        return self.tpidict      
