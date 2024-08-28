'''
Created on 10 Jan 2013

@author: ebrifol
'''

import TPAPI
import logging
import sys
import traceback
import os
from optparse import OptionParser

logging.basicConfig(filename='DesignRules.log',level=logging.DEBUG)
outputPath = os.getcwd()
tableSizes = ['extrasmall','small','medium','large','extralarge']
attIndexes = ['HG','LF']
output = []

def main():
    logging.info('Design Rules tool started!')

    if len(sys.argv) <= 1 or options.help:
        printUsage()
    else:
        processParams()
        
def processParams():
    
    techpack = None
    
    print 'Loading techpack!'
    logging.info('Loading techpack!')
    
    #Loading from the server
    if options.server != None or options.version != None:
        techpack = loadfromServer(options.sourceserver, options.version)
        
    #Loading from tpi input files
    if options.tpi != None:
        techpack = loadfromtpi(options.tpi)
        
    #Loading from XML input files
    if options.xml != None:
        techpack = loadfromXML(options.xml)
    
    logging.info('Applying design rules to '+techpack.versionID)
    
    
    output.append('################################ DESIGN RULES ################################\n\n')
    output.append('TECHPACK VERSION: '+techpack.versionID+'\n')
    
    if len(techpack.versioning['DESCRIPTION']) == 0 or techpack.versioning['DESCRIPTION'] == None:
        output.append('\tTechpack should have a description\n')
    
    
    output.append('\n')
    for tablename, table in techpack.referenceTableObjects.items():
        errorsFound = False
        tableErrorsList = []
        tableErrorsList.append('----------------------------------------------------------------------------- \n')
        tableErrorsList.append('TABLE NAME:' + tablename +'\n')
        
        
        '''TABLE WARNINGS'''
        tableWarningsFound = False
        tableWarnings = []
        tableWarnings.append('\tWARNINGS:\n')
        if len(table.properties['DESCRIPTION']) == 0 or table.properties['DESCRIPTION'] == None:
            tableWarnings.append('\t\tTable should have a description\n')
            tableWarningsFound = True
        
        keyFound = False 
        for attributename, attribute in table.attributeObjects.items():
            if attribute.attributeType == 'measurementKey' and not keyFound:
                if int(attribute.properties['UNIQUEKEY']) == 1:
                    keyFound = True
        
        if not keyFound:
            tableWarnings.append('\t\tTable should have at least one unique key\n')
            tableWarningsFound = True
        
        if tableWarningsFound:
            tableErrorsList.extend(tableWarnings)
            errorsFound = True
        
        
        '''TABLE ERRORS'''
        tableErrorsFound = False
        tableErrors=[]
        tableErrors.append('\tERRORS:\n')
#        if table.properties['SIZING'].lower() not in tableSizes:
#            tableErrors.append('\t\tTable sizing must be either extrasmall, small, medium, large or extralarge\n')
        
        if tableErrorsFound:
            tableErrorsList.extend(tableErrors)
            errorsFound = True
        
        '''ATTRIBUTES IN THE TABLE'''
        for attributename, attribute in table.attributeObjects.items():
            attErrorsFound = False
            attributeErrorsList=[]
            attributeErrorsList.append('\n\tATTRIBUTE NAME:'+attributename+'\n ')
            
            '''ATTRIBUTE WARNINGS'''
            attributeWarningsFound = False
            attributeWarnings = []
            attributeWarnings.append('\t\tWARNINGS:\n')
            if len(attribute.properties['DESCRIPTION']) == 0 or attribute.properties['DESCRIPTION'] == None:
                attributeWarnings.append('\t\t\tAttribute should have a description\n')
                attributeWarningsFound = True
            
            
            if attributeWarningsFound:
                attributeErrorsList.extend(attributeWarnings)
                attErrorsFound = True
                
            '''ATTRIBUTE ERRORS'''
            attributeErrorsFound = False
            attributeErrors = []
            attributeErrors.append('\t\tERRORS:\n')
            
            if attribute.attributeType == 'measurementKey':
                if attribute.properties['INDEXES'] not in attIndexes:
                    attributeErrors.append('\t\t\tIndexes should be either HG or LF:\n')
                    attributeErrorsFound = True
            
            if attributeErrorsFound:
                attributeErrorsList.extend(attributeErrors)
                attErrorsFound = True
            
            if attErrorsFound:
                tableErrorsList.extend(attributeErrorsList)
                errorsFound = True
                
        tableErrorsList.append('----------------------------------------------------------------------------- \n')
        
        
        if errorsFound:
            output.extend(tableErrorsList)
    
    for tablename, table in techpack.measurementTableObjects.items():
        errorsFound = False
        tableErrorsList = []
        tableErrorsList.append('----------------------------------------------------------------------------- \n')
        tableErrorsList.append('TABLE NAME:' + tablename +'\n')
        
        
        '''TABLE WARNINGS'''
        tableWarningsFound = False
        tableWarnings = []
        tableWarnings.append('\tWARNINGS:\n')
        if len(table.properties['DESCRIPTION']) == 0 or table.properties['DESCRIPTION'] == None:
            tableWarnings.append('\t\tTable should have a description\n')
            tableWarningsFound = True
        
        keyFound = False 
        for attributename, attribute in table.attributeObjects.items():
            if attribute.attributeType == 'measurementKey' and not keyFound:
                if int(attribute.properties['UNIQUEKEY']) == 1:
                    keyFound = True
        
        if not keyFound:
            tableWarnings.append('\t\tTable should have at least one unique key\n')
            tableWarningsFound = True
        
        if tableWarningsFound:
            tableErrorsList.extend(tableWarnings)
            errorsFound = True
        
        
        '''TABLE ERRORS'''
        tableErrorsFound = False
        tableErrors=[]
        tableErrors.append('\tERRORS:\n')
        if table.properties['SIZING'].lower() not in tableSizes:
            tableErrors.append('\t\tTable sizing must be either extrasmall, small, medium, large or extralarge\n')
        
        if tableErrorsFound:
            tableErrorsList.extend(tableErrors)
            errorsFound = True
        
        '''ATTRIBUTES IN THE TABLE'''
        for attributename, attribute in table.attributeObjects.items():
            attErrorsFound = False
            attributeErrorsList=[]
            attributeErrorsList.append('\n\tATTRIBUTE NAME:'+attributename+'\n ')
            
            '''ATTRIBUTE WARNINGS'''
            attributeWarningsFound = False
            attributeWarnings = []
            attributeWarnings.append('\t\tWARNINGS:\n')
            if len(attribute.properties['DESCRIPTION']) == 0 or attribute.properties['DESCRIPTION'] == None:
                attributeWarnings.append('\t\t\tAttribute should have a description\n')
                attributeWarningsFound = True
            
            
            if attributeWarningsFound:
                attributeErrorsList.extend(attributeWarnings)
                attErrorsFound = True
                
            '''ATTRIBUTE ERRORS'''
            attributeErrorsFound = False
            attributeErrors = []
            attributeErrors.append('\t\tERRORS:\n')
            
            if attribute.attributeType == 'measurementKey':
                if attribute.properties['INDEXES'] not in attIndexes:
                    attributeErrors.append('\t\t\tIndexes should be either HG or LF:\n')
                    attributeErrorsFound = True
            
            if attributeErrorsFound:
                attributeErrorsList.extend(attributeErrors)
                attErrorsFound = True
            
            if attErrorsFound:
                tableErrorsList.extend(attributeErrorsList)
                errorsFound = True
                
        tableErrorsList.append('----------------------------------------------------------------------------- \n')
        
        
        if errorsFound:
            output.extend(tableErrorsList)
        
        
    
    if options.output:
        f = open(outputPath+'\\DesignRulesOutput.txt','w')
        for line in output:
            f.write(line)
        f.close()
        print 'Results written to '+outputPath+'\\DesignRulesOutput.txt'
        logging.info('Results written to '+outputPath+'\\DesignRulesOutput.txt')
    
def loadfromServer(server, techpackID):
    techpack = None
    if server != None and techpackID != None:
        techpack = TPAPI.TechPackVersion(techpackID)
        print 'collecting techpack'
        techpack.getPropertiesFromServer(server)
        print 'properties collected from server'
        print techpackID + ' was loaded from ' + server
        logging.debug(techpackID + ' was loaded from ' + server)    
    elif server != None and techpackID == None:
        isntalledtps = TPAPI.getTechPackVersions(server)
        print 'No techpack version ID was given. The following techpacks are installed on '+server+':'
        for tpVersions in isntalledtps:
            print tpVersions
    else:
        print 'Server name and techpack version ID are required to retrieve a techpack from a server'

    return techpack

def loadfromXML(path):
    techpack = None
    try:
        techpack = TPAPI.TechPackVersion()
        techpack.getPropertiesFromXML(filename=path)
        print techpack.versionID + ' was loaded from XML input file ' + path
        logging.debug(techpack.versionID + ' was loaded from XML input file ' + path)
    except:
        print 'Input XML file '+ path +' was not valid'
        
    return techpack

def loadfromtpi(path):
    techpack = None
    try:
        techpack = TPAPI.TechPackVersion()
        techpack.getPropertiesFromTPI(filename=path)
        print techpack.versionID + ' was loaded from tpi input file ' + path
        logging.debug(techpack.versionID + ' was loaded from tpi input file ' + path)
    except:
        traceback.print_exc(file=sys.stdout)
        print 'Input tpi file '+ path +' was not valid'
    return techpack

        
def printUsage():
    print '''---------------------------------------------------------------------------------------------------  
    Name: DesignRulesTool.py
    
    Description:
     Tool to demo checking design rules in a techpack loaded from a server, xml file or tpi file. Output can be 
     written to a txt file or to the command line. The design rules that will be checked are:
         1. Description is not empty the techpack versioning, table or attributes. 
         2. Fact table sizes are either extra small, small, medium, large or extra large
         3. Each table has at least one measurementkey attribute with a uniquekey value of 1 or greater
         4. Each measurementkey attribute has an indexes value of either HG or LF
    
    Command:
     python DesignRulesTool.py [-s <server> [ -v <techpack version>] | -x <XML file> | -t <TPI file>] -o

    
    Command options:
     -s    --server     Server name where source techpack is loaded from 
                                i.e. atrcx888zone3.athtem.eei.ericsson.se

     -v   --version     Version ID of source techpack. Must exist on the server
                                i.e. DC_S_TEST:((20)) 
    
     -x    --xml        Absolute path to xml file
    
     -t    --tpi        Absolute path to tpi file

     -o    --output     Write results to output file
---------------------------------------------------------------------------------------------------'''
    sys.exit(' ')

'''
    Parse in the command line arguments
'''   
try:
    parser = OptionParser(conflict_handler="resolve")
    parser.add_option("-s", "--server", dest="server",
                      help="Server name", metavar="SERVER")
        
    parser.add_option("-v", "--version", dest="version",
                      help="Version ID of techpack", metavar="VERSION")
    
    parser.add_option("-x", "--xml", dest="xml",
                      help="File path for XML file", metavar="XML")
    
    parser.add_option("-t", "--tpi", dest="tpi",
                      help="File path for tpi file", metavar="TPI")
    
    parser.add_option("-o", "--output", action="store_true", dest="output",
                     default=False, help="Print results to txt file")
    
    parser.add_option("-h", "--help", action="store_true", dest="help",
                     default=False, help="Prints the usage of the script")
    
    (options,args) = parser.parse_args()
except:
    traceback.print_exc(file=sys.stdout)
    printUsage()   
    
#-------------------------------
if __name__ == "__main__":
    main()