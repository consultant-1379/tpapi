#!/usr/bin/python
# -*- coding: latin-1 -*-

'''
Created on 13 Nov 2012

@author: XMOHIAH
'''
from __future__ import with_statement
from __future__ import division
import TPAPI
import sys
import os
import re
import logging
import traceback
from optparse import OptionParser

logging.basicConfig(filename='DatacoverageTool.log',level=logging.DEBUG)
outputPath = os.getcwd()

def main():
    logging.info('DatacoverageTool tool started!')

    if len(sys.argv) <= 1 or options.help:
        printUsage()
    else:
        processParams()
        
        
def processParams():
    logging.info('Processing the parameters')
    if options.server != None:
        print "SERVER : " + options.server
        server = options.server
    else:
        print "Please Enter the Server to be connected"

    if options.techpack != None:
        print "techpack : " + options.techpack
        VersionID = options.techpack
    else:
        print "Please Enter the Techpack Name"

    if options.rows != None:
        print "rows : " + options.rows
        count = options.rows
    else:
        print "ROW COUNT IS NOT CONFIGUIRED : SETTING DEFAULT COUNT AS 10"
        count = 10
    DataCoverage(server,VersionID,count )
        
        
def DataCoverage(server,VersionID,count ):        
    LoadedTables = {}
    EmptyTables = {}
    result = []
    logging.info('Calculating the Data Coverage')
    properties = TPAPI.getTechpackDwhInfo(server, VersionID)



    filename = "DATA_COVERAGE"
    f = open(filename+".txt",'w')
    f.write("################################ DATA COVERAGE ########################################### \n")    
    for table,colmns in properties.iteritems():
        table = str(table)
        with TPAPI.DbAccess(server,'dwhdb') as crsr:
            crsr.execute("SELECT * FROM "+table,)
            resultset = crsr.fetchone()
            if resultset is not None:
                LoadedTables[table] = colmns
            else:
                EmptyTables[table] = colmns
      
    f.write("\n\n")
    f.write("LOADED TABLES \n")
    for lt in  LoadedTables:
        f.write(lt + "\n")
    f.write("\n\n")
    f.write("EMPTY TABLES \n")
    for et in EmptyTables:
        f.write(et + "\n")
    f.write("\n\n")
    f.write("PER TABLE ANALYSIS \n")
    tp = TPAPI.TechPackVersion(VersionID)
    tp.getPropertiesFromServer(server)
    for table in LoadedTables:
        emptyCounterList = []
        m = re.match('.*_RAW', table)
        if m is not None:
            t = re.search('(.*)_RAW', table)
            tempTable = t.group(1)
            loadedCounters = 0
            emptyCounters = 0 
            f.write("-------------------------------------------------------------------------------------- \n")
            f.write("TABLE NAME : "+ table + "\n") 
            f.write("NULL AND BLANK KEYS \n")    
            for attribute in tp.measurementTableObjects[tempTable].attributeObjects:
                if tp.measurementTableObjects[tempTable].attributeObjects[attribute].attributeType == 'measurementKey':
    #                with TPAPI.DbAccess(server,'dwhrep') as crsr:
    #                    crsr.execute("SELECT BASETABLENAME FROM dwhrep.MeasurementTable WHERE MTABLEID like ?", (temp,))
                    data_Type = str(tp.measurementTableObjects[tempTable].attributeObjects[attribute].properties['DATATYPE'])
                    if data_Type == 'integer':
                        with TPAPI.DbAccess(server,'dwhdb') as crsr:
                            crsr.execute("SELECT TOP ("+str(count)+") " + tp.measurementTableObjects[tempTable].attributeObjects[attribute].name + " FROM " + table + " WHERE "+str(attribute)+" = 0 ",)
                            desc = crsr.description
                            row = crsr.fetchone()
                            if row is not None:
                                f.write("    KEY NAME  : "+attribute + "\n")
                    elif data_Type == 'varchar':
                        with TPAPI.DbAccess(server,'dwhdb') as crsr:
                            crsr.execute("SELECT TOP ("+str(count)+") " + tp.measurementTableObjects[tempTable].attributeObjects[attribute].name + " FROM " + table + " WHERE "+str(attribute)+" = '' ",)
                            desc = crsr.description
                            row = crsr.fetchone()
                            if row is not None:
                                f.write("    KEY NAME  : "+attribute + "\n")
                    else:
                        with TPAPI.DbAccess(server,'dwhdb') as crsr:
                            crsr.execute("SELECT TOP ("+str(count)+") " + tp.measurementTableObjects[tempTable].attributeObjects[attribute].name + " FROM " + table + " WHERE "+str(attribute)+" IS NULL ",)
                            desc = crsr.description
                            row = crsr.fetchone()
                            if row is not None:
                                f.write("    KEY NAME  : "+attribute + "\n")

                if tp.measurementTableObjects[tempTable].attributeObjects[attribute].attributeType == 'measurementCounter':
                    with TPAPI.DbAccess(server,'dwhdb') as crsr:
                        crsr.execute("SELECT TOP ("+str(count)+") DATETIME_ID," + tp.measurementTableObjects[tempTable].attributeObjects[attribute].name + " FROM " + table + " WHERE "+attribute+" IS NULL AND ROWSTATUS = 'LOADED' ",)
                        desc = crsr.description
                        rows = crsr.fetchall()
                        for row1 in rows:
                            emptyCounters = emptyCounters+1
                        crow = crsr.fetchone()
                        if crow is not None:
                            emptyCounterList.append(attribute)
                                
                        crsr.execute("SELECT TOP ("+str(count)+") " + tp.measurementTableObjects[tempTable].attributeObjects[attribute].name + " FROM " + table + " WHERE ROWSTATUS = 'LOADED' ",)
                        counterrows = crsr.fetchall()
                        for row in counterrows:
                            loadedCounters = loadedCounters +1
            f.write("NULL AND BLANK COUNTERS \n")                
            for counter in emptyCounterList:
                f.write("    COUNTER NAME  : "+counter + "\n")
            with TPAPI.DbAccess(server,'dwhdb') as crsr:
                crsr.execute("SELECT TOP ("+str(count)+") DATETIME_ID"  + " FROM " + table + " WHERE ROWSTATUS = 'DUPLICATE' OR ROWSTATUS = 'SUSPECTED'",)
                rows = crsr.fetchall()
                f.write("DUPLICATE / SUSPECTED ATTRIBUTES \n")
                k = 0
                for row in rows:
                    k = k+1
                    f.write("    ROW : "+str(k)+" ROP TIME = " + str(row)+ "\n")
            with TPAPI.DbAccess(server,'dwhdb') as crsr:
                crsr.execute("SELECT count(*) FROM " + table + " WHERE ROWSTATUS = 'LOADED'",)  
                (rowCount,)=crsr.fetchone()
                loadedRowCount = long(count)
                if rowCount is not None:
                    rwCnt =  long(rowCount)
            Counter_Coverage = ((loadedCounters-emptyCounters)/(loadedCounters))*100
            completeCoverage = ((loadedRowCount)/(rwCnt))*100
            f.write("Average counter coverage from "+str(float(completeCoverage))+"% of total rows : "+str(float(Counter_Coverage))+"% \n ")
        else:
            "NO RAW Tables are loaded"
    f.close()
    print filename+ ".txt written"              
       
def printUsage():
    print '''---------------------------------------------------------------------------------------------------  
    Name: Datacoverage.py
    
    Description:
     Tool for calcuating DataCoverage from a server and preforming the counter related coverage details.
    
    Command:
     python Data_Coverage.py [-s <server to connect> -–tp <techpack version> --r <row count for DataCoverage>]

    
    Command options:
     --s    --server           Server name where techpack is loaded from 
                                i.e. atrcx888zone3.athtem.eei.ericsson.se

     --tp   --techpack         Version ID of techpack. Must exist on the server
                                i.e. DC_S_TEST:((20)) 
    
     --r    --rows             row count for Datacoverage , if this not passed by default 10 rows Data is calculated
     
---------------------------------------------------------------------------------------------------'''
    sys.exit(' ')
  
  
'''
    Parse in the command line arguments
'''   
try:
    parser = OptionParser(conflict_handler="resolve")
    parser.add_option("--s", "--server", dest="server",
                      help="Server To Connect To", metavar="SERVER")

    parser.add_option("--tp", "--techpack", dest="techpack",
                      help=" Techpack for Data Coverage", metavar="techpack")

    parser.add_option("--r", "--rows", dest="rows",
                      help="No of rows to be checked in dwhdb", metavar="rows")
    parser.add_option("-h", "--help", action="store_true", dest="help",
                     default=False, help="Prints the usage of the script")
    
    (options,args) = parser.parse_args()
except:
    traceback.print_exc(file=sys.stdout)
    printUsage()   

#-------------------------------
if __name__ == "__main__":
    main()